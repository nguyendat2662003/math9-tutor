"""Xác thực: phiên đăng nhập trong cookie HttpOnly (JavaScript của trang không đọc được -> an toàn
hơn cất mã trong localStorage trước lỗi XSS). SameSite=Lax chặn trang lạ gửi yêu cầu POST kèm cookie."""

from __future__ import annotations

import os

from fastapi import HTTPException, Request, Response
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


def current_user(request: Request) -> UserInfo:
    """Dependency cho mọi route cần đăng nhập."""
    user = service.user_by_token(request.cookies.get(COOKIE))
    if user is None:
        raise HTTPException(401, "Cần đăng nhập")
    return user
