"""Nghiệp vụ tài khoản: đăng ký, đăng nhập (có khóa tạm khi sai nhiều), phiên, hạn mức giải bài."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select

from . import db
from .models import AuthSession, SolveRecord, User, now
from .security import DUMMY_HASH, hash_password, new_token, token_hash, verify_password

USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,32}$")
MIN_PASSWORD = 8
SESSION_DAYS = 30
MAX_FAILED = 5
LOCK_MINUTES = 15
VN = timezone(timedelta(hours=7))          # "mỗi ngày" tính theo giờ Việt Nam


class AccountError(ValueError):
    """Lỗi hiển thị được cho người dùng."""


@dataclass(frozen=True)
class UserInfo:
    id: int
    username: str
    display_name: str

    def public(self) -> dict:
        return {"username": self.username, "display_name": self.display_name}


def _info(u: User) -> UserInfo:
    return UserInfo(u.id, u.username, u.display_name)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite trả datetime không múi giờ; PostgreSQL trả có múi giờ. Quy về UTC để so sánh."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def register(username: str, password: str, display_name: str) -> UserInfo:
    username = normalize_username(username)
    display_name = (display_name or "").strip() or username
    if not USERNAME_RE.fullmatch(username):
        raise AccountError("Tên đăng nhập 3–32 ký tự, chỉ gồm chữ thường không dấu, số, dấu chấm, gạch dưới")
    if len(password or "") < MIN_PASSWORD:
        raise AccountError(f"Mật khẩu cần ít nhất {MIN_PASSWORD} ký tự")
    if password.lower() == username:
        raise AccountError("Mật khẩu không được trùng tên đăng nhập")
    if len(display_name) > 60:
        raise AccountError("Tên hiển thị tối đa 60 ký tự")
    with db.session() as s:
        if s.scalar(select(User.id).where(User.username == username)):
            raise AccountError("Tên đăng nhập đã có người dùng")
        u = User(username=username, display_name=display_name, password_hash=hash_password(password))
        s.add(u)
        s.flush()
        return _info(u)


def authenticate(username: str, password: str) -> UserInfo:
    """Sai 5 lần liên tiếp -> khóa 15 phút. Thông báo lỗi không tiết lộ tên đăng nhập có tồn tại hay không."""
    username = normalize_username(username)
    error: str | None = None
    with db.session() as s:
        u = s.scalar(select(User).where(User.username == username))
        if u is None:
            verify_password(password or "", DUMMY_HASH)          # cân thời gian phản hồi
            error = "Sai tên đăng nhập hoặc mật khẩu"
        elif (locked := _aware(u.locked_until)) and locked > now():
            mins = int((locked - now()).total_seconds() // 60) + 1
            error = f"Tài khoản tạm khóa do nhập sai nhiều lần — thử lại sau {mins} phút"
        elif not verify_password(password or "", u.password_hash):
            u.failed_logins = (u.failed_logins or 0) + 1
            if u.failed_logins >= MAX_FAILED:
                u.locked_until = now() + timedelta(minutes=LOCK_MINUTES)
                u.failed_logins = 0
            error = "Sai tên đăng nhập hoặc mật khẩu"
        else:
            u.failed_logins, u.locked_until, u.last_login_at = 0, None, now()
            info = _info(u)
    # Báo lỗi SAU khi phiên đã commit: raise bên trong `with` sẽ rollback mất bộ đếm sai,
    # và khóa tài khoản không bao giờ kích hoạt.
    if error:
        raise AccountError(error)
    return info


def create_session(user_id: int) -> str:
    token = new_token()
    with db.session() as s:
        s.add(AuthSession(token_hash=token_hash(token), user_id=user_id,
                          expires_at=now() + timedelta(days=SESSION_DAYS)))
        # dọn phiên hết hạn của người này
        s.execute(delete(AuthSession).where(AuthSession.user_id == user_id, AuthSession.expires_at < now()))
    return token


def user_by_token(token: str | None) -> UserInfo | None:
    if not token:
        return None
    with db.session() as s:
        row = s.execute(
            select(User, AuthSession.expires_at).join(AuthSession, AuthSession.user_id == User.id)
            .where(AuthSession.token_hash == token_hash(token))
        ).first()
        if row is None or _aware(row[1]) < now():
            return None
        return _info(row[0])


def end_session(token: str | None) -> None:
    if token:
        with db.session() as s:
            s.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(token)))


def change_password(user_id: int, old: str, new: str, keep_token: str | None) -> None:
    """Đổi mật khẩu và đăng xuất mọi phiên khác (vd máy ở trường quên đăng xuất)."""
    if len(new or "") < MIN_PASSWORD:
        raise AccountError(f"Mật khẩu mới cần ít nhất {MIN_PASSWORD} ký tự")
    with db.session() as s:
        u = s.get(User, user_id)
        if u is None or not verify_password(old or "", u.password_hash):
            raise AccountError("Mật khẩu hiện tại không đúng")
        u.password_hash = hash_password(new)
        keep = token_hash(keep_token) if keep_token else ""
        s.execute(delete(AuthSession).where(AuthSession.user_id == user_id, AuthSession.token_hash != keep))


def reset_password(username: str, new: str) -> None:
    """Cho quản trị đặt lại mật khẩu khi học sinh quên (không có email để tự khôi phục)."""
    if len(new or "") < MIN_PASSWORD:
        raise AccountError(f"Mật khẩu cần ít nhất {MIN_PASSWORD} ký tự")
    with db.session() as s:
        u = s.scalar(select(User).where(User.username == normalize_username(username)))
        if u is None:
            raise AccountError("Không có tài khoản này")
        u.password_hash, u.failed_logins, u.locked_until = hash_password(new), 0, None
        s.execute(delete(AuthSession).where(AuthSession.user_id == u.id))


# ---------- hạn mức ----------

def daily_limit() -> int:
    return int(os.environ.get("SOLVE_DAILY_LIMIT", "30"))


def solves_today(user_id: int) -> int:
    # Đầu ngày giờ VN, đổi sang UTC — SQLite không lưu múi giờ, so trực tiếp sẽ lệch 7 tiếng
    start = datetime.now(VN).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    with db.session() as s:
        return s.scalar(select(func.count()).select_from(SolveRecord)
                        .where(SolveRecord.user_id == user_id, SolveRecord.created_at >= start)) or 0
