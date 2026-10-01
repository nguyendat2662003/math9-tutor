"""Đăng nhập, đăng xuất, đổi mật khẩu. KHÔNG có tự đăng ký — tài khoản do admin tạo."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from math9_accounts import service
from math9_accounts.service import AccountError, UserInfo
from pydantic import BaseModel, Field

from ..auth import COOKIE, clear_session_cookie, session_user, set_session_cookie

router = APIRouter(prefix="/api/auth")


class Login(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=200)


class ChangePassword(BaseModel):
    old_password: str = Field(max_length=200)
    new_password: str = Field(max_length=200)


async def _run(fn, *a):
    """Băm mật khẩu tốn vài chục ms CPU — chạy ngoài event loop để không chặn các request khác."""
    try:
        return await run_in_threadpool(fn, *a)
    except AccountError as e:
        raise HTTPException(400, str(e))


@router.post("/register")
def register() -> None:
    raise HTTPException(403, "Không tự tạo tài khoản được — nhờ thầy cô quản trị cấp tài khoản cho em")


@router.post("/login")
async def login(req: Login, resp: Response) -> dict:
    user = await _run(service.authenticate, req.username, req.password)
    set_session_cookie(resp, await run_in_threadpool(service.create_session, user.id))
    return user.public()


@router.post("/logout")
def logout(request: Request, resp: Response) -> dict:
    service.end_session(request.cookies.get(COOKIE))
    clear_session_cookie(resp)
    return {"ok": True}


@router.get("/me")
def me(user: UserInfo = Depends(session_user)) -> dict:
    return user.public() | {"solves_today": service.solves_today(user.id), "daily_limit": service.daily_limit()}


@router.post("/change-password")
async def change_password(req: ChangePassword, request: Request, user: UserInfo = Depends(session_user)) -> dict:
    await _run(service.change_password, user.id, req.old_password, req.new_password, request.cookies.get(COOKIE))
    return {"ok": True}
