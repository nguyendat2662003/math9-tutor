"""Xác thực: phiên đăng nhập trong cookie HttpOnly (JavaScript của trang không đọc được -> an toàn
hơn cất mã trong localStorage trước lỗi XSS). SameSite=Lax chặn trang lạ gửi yêu cầu POST kèm cookie.

Ba mức:
  session_user  — đã đăng nhập (xem mình là ai, đổi mật khẩu, đăng xuất)
  current_user  — đã đăng nhập VÀ đã đổi mật khẩu do admin cấp (mọi tính năng học)
  admin_user    — tài khoản admin (trang quản trị)
"""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException, Request, Response
from math9_accounts import service
from math9_accounts.service import UserInfo

COOKIE = "m9_session"


def set_session_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        COOKIE, token, max_age=service.SESSION_DAYS * 86400, httponly=True, samesite="lax",
        secure=os.environ.get("COOKIE_SECURE", "0") == "1",       # bật khi chạy HTTPS
        path="/",
    )


def clear_session_cookie(resp: Response) -> None:
    resp.delete_cookie(COOKIE, path="/")


def session_user(request: Request) -> UserInfo:
    user = service.user_by_token(request.cookies.get(COOKIE))
    if user is None:
        raise HTTPException(401, "Cần đăng nhập")
    return user


def current_user(user: UserInfo = Depends(session_user)) -> UserInfo:
    """Mật khẩu do admin cấp thì admin biết — chặn ở server (không chỉ ở giao diện) tới khi học sinh đổi."""
    if user.must_change_password:
        raise HTTPException(403, "Cần đổi mật khẩu trước khi dùng — mật khẩu hiện tại do thầy cô cấp")
    return user


def admin_user(user: UserInfo = Depends(current_user)) -> UserInfo:
    if not user.is_admin:
        raise HTTPException(403, "Chỉ tài khoản quản trị mới dùng được chức năng này")
    return user
