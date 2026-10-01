"""Nghiệp vụ tài khoản: một admin duy nhất tạo tài khoản cho học sinh (không tự đăng ký), đăng nhập
(khóa tạm khi sai nhiều), phiên, bắt đổi mật khẩu do admin cấp, hạn mức giải bài."""

from __future__ import annotations

import os
import re
import secrets
import unicodedata
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
# Mật khẩu cấp cho học sinh: bỏ ký tự dễ nhầm khi chép tay (0/O, 1/l/I)
PASSWORD_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


class AccountError(ValueError):
    """Lỗi hiển thị được cho người dùng."""


@dataclass(frozen=True)
class UserInfo:
    id: int
    username: str
    display_name: str
    role: str = "student"
    must_change_password: bool = False

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def public(self) -> dict:
        return {"username": self.username, "display_name": self.display_name, "role": self.role,
                "must_change_password": self.must_change_password}


def _info(u: User) -> UserInfo:
    return UserInfo(u.id, u.username, u.display_name, u.role or "student", bool(u.must_change_password))


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite trả datetime không múi giờ; PostgreSQL trả có múi giờ. Quy về UTC để so sánh."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def generate_password(n: int = 10) -> str:
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(n))


def username_from_name(name: str) -> str:
    """'Nguyễn Văn An' -> 'nguyenvanan' (bỏ dấu, đ -> d, chỉ giữ chữ + số)."""
    s = unicodedata.normalize("NFD", name.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]", "", s)[:28]


def _validate(username: str, password: str, display_name: str) -> None:
    if not USERNAME_RE.fullmatch(username):
        raise AccountError("Tên đăng nhập 3–32 ký tự, chỉ gồm chữ thường không dấu, số, dấu chấm, gạch dưới")
    if len(password or "") < MIN_PASSWORD:
        raise AccountError(f"Mật khẩu cần ít nhất {MIN_PASSWORD} ký tự")
    if password.lower() == username:
        raise AccountError("Mật khẩu không được trùng tên đăng nhập")
    if len(display_name) > 60:
        raise AccountError("Tên hiển thị tối đa 60 ký tự")


def create_user(username: str, password: str, display_name: str = "", *, role: str = "student",
                must_change_password: bool = True) -> UserInfo:
    """Tạo tài khoản. Chỉ admin gọi (qua API quản trị) hoặc tools/create_admin.py."""
    username = normalize_username(username)
    display_name = (display_name or "").strip() or username
    _validate(username, password, display_name)
    if role not in ("student", "admin"):
        raise AccountError("Vai trò không hợp lệ")
    with db.session() as s:
        if role == "admin" and s.scalar(select(User.id).where(User.role == "admin")):
            raise AccountError("Đã có tài khoản admin — hệ thống chỉ có MỘT admin")
        if s.scalar(select(User.id).where(User.username == username)):
            raise AccountError(f"Tên đăng nhập '{username}' đã có người dùng")
        u = User(username=username, display_name=display_name, password_hash=hash_password(password),
                 role=role, active=True, must_change_password=must_change_password)
        s.add(u)
        s.flush()
        return _info(u)


def create_students(lines: list[str]) -> list[dict]:
    """Tạo nhiều tài khoản một lần. Mỗi dòng: 'tên_đăng_nhập, Tên hiển thị' hoặc chỉ 'Tên hiển thị'
    (tên đăng nhập tự sinh từ tên, trùng thì thêm số). Mật khẩu tự sinh, bắt đổi ở lần đăng nhập đầu.
    Trả về từng dòng: tên đăng nhập + mật khẩu (để in phát cho học sinh) hoặc lỗi."""
    out: list[dict] = []
    with db.session() as s:
        taken = set(s.scalars(select(User.username)).all())
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if "," in line:
            username, name = (x.strip() for x in line.split(",", 1))
            username = normalize_username(username)
        else:
            name = line
            base = username_from_name(name) or "hocsinh"
            base = base if len(base) >= 3 else base + "hs"
            username, k = base, 2
            while username in taken:
                username, k = f"{base}{k}", k + 1
        pw = generate_password()
        try:
            u = create_user(username, pw, name, role="student", must_change_password=True)
            taken.add(u.username)
            out.append({"line": line, "username": u.username, "display_name": u.display_name, "password": pw, "ok": True})
        except AccountError as e:
            out.append({"line": line, "username": username, "display_name": name, "error": str(e), "ok": False})
    return out


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
        elif not u.active:
            # Chỉ báo "đã bị khóa" khi mật khẩu ĐÚNG — không để ai dò được tài khoản nào có thật
            error = "Tài khoản đã bị khóa — liên hệ thầy cô quản trị"
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
        if row is None or _aware(row[1]) < now() or not row[0].active:
            return None
        return _info(row[0])


def end_session(token: str | None) -> None:
    if token:
        with db.session() as s:
            s.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(token)))


def change_password(user_id: int, old: str, new: str, keep_token: str | None) -> None:
    """Đổi mật khẩu (xóa cờ bắt đổi) và đăng xuất mọi phiên khác (vd máy ở trường quên đăng xuất)."""
    if len(new or "") < MIN_PASSWORD:
        raise AccountError(f"Mật khẩu mới cần ít nhất {MIN_PASSWORD} ký tự")
    if new == old:
        raise AccountError("Mật khẩu mới phải khác mật khẩu cũ")
    with db.session() as s:
        u = s.get(User, user_id)
        if u is None or not verify_password(old or "", u.password_hash):
            raise AccountError("Mật khẩu hiện tại không đúng")
        if new.lower() == u.username:
            raise AccountError("Mật khẩu không được trùng tên đăng nhập")
        u.password_hash, u.must_change_password = hash_password(new), False
        keep = token_hash(keep_token) if keep_token else ""
        s.execute(delete(AuthSession).where(AuthSession.user_id == user_id, AuthSession.token_hash != keep))


# ---------- quản trị (chỉ admin) ----------

def _student(s, username: str) -> User:
    u = s.scalar(select(User).where(User.username == normalize_username(username)))
    if u is None:
        raise AccountError("Không có tài khoản này")
    return u


def reset_password(username: str, new: str | None = None) -> str:
    """Học sinh quên mật khẩu: đặt mật khẩu mới (tự sinh nếu không đưa), bắt đổi ở lần đăng nhập
    tới, đăng xuất mọi phiên cũ. Trả về mật khẩu mới để admin báo cho học sinh."""
    new = new or generate_password()
    if len(new) < MIN_PASSWORD:
        raise AccountError(f"Mật khẩu cần ít nhất {MIN_PASSWORD} ký tự")
    with db.session() as s:
        u = _student(s, username)
        u.password_hash, u.failed_logins, u.locked_until = hash_password(new), 0, None
        u.must_change_password = True
        s.execute(delete(AuthSession).where(AuthSession.user_id == u.id))
    return new


def set_active(username: str, active: bool) -> None:
    """Khóa / mở khóa tài khoản học sinh. Khóa thì đăng xuất ngay mọi máy. Không khóa được admin."""
    with db.session() as s:
        u = _student(s, username)
        if u.role == "admin":
            raise AccountError("Không khóa tài khoản admin")
        u.active = active
        if not active:
            s.execute(delete(AuthSession).where(AuthSession.user_id == u.id))


def list_users() -> list[dict]:
    with db.session() as s:
        users = s.scalars(select(User).order_by(User.role, User.username)).all()
        counts = dict(s.execute(select(SolveRecord.user_id, func.count()).group_by(SolveRecord.user_id)).all())
        return [{"username": u.username, "display_name": u.display_name, "role": u.role, "active": u.active,
                 "must_change_password": u.must_change_password, "solves": counts.get(u.id, 0),
                 "created_at": u.created_at.isoformat() if u.created_at else None,
                 "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None} for u in users]


def admin_exists() -> bool:
    with db.session() as s:
        return bool(s.scalar(select(User.id).where(User.role == "admin")))


# ---------- hạn mức ----------

def daily_limit() -> int:
    return int(os.environ.get("SOLVE_DAILY_LIMIT", "30"))


def solves_today(user_id: int) -> int:
    # Đầu ngày giờ VN, đổi sang UTC — SQLite không lưu múi giờ, so trực tiếp sẽ lệch 7 tiếng
    start = datetime.now(VN).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    with db.session() as s:
        return s.scalar(select(func.count()).select_from(SolveRecord)
                        .where(SolveRecord.user_id == user_id, SolveRecord.created_at >= start)) or 0
