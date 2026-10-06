"""Một admin duy nhất tạo tài khoản học sinh: tạo từng em / cả lớp, bắt đổi mật khẩu lần đầu,
đặt lại mật khẩu, khóa/mở khóa, chỉ admin vào được trang quản trị."""

import pytest
from conftest import PASSWORD, make_client
from math9_accounts import service
from math9_accounts.service import AccountError


def _admin_client(**kw):
    from api.routes import admin

    return make_client(admin.router, username="admin", role="admin", **kw)


def test_only_one_admin(mem_db):
    service.create_user("admin", "matkhau-admin", "Quản trị", role="admin")
    with pytest.raises(AccountError, match="MỘT admin"):
        service.create_user("admin2", "matkhau-admin", "", role="admin")
    assert service.admin_exists()


def test_username_from_vietnamese_name():
    assert service.username_from_name("Nguyễn Văn Đức") == "nguyenvanduc"
    assert service.username_from_name("Trần Thị Ánh Tuyết") == "tranthianhtuyet"
    pw = service.generate_password()
    assert len(pw) == 10 and not set(pw) & set("01lOI")         # không ký tự dễ nhầm khi chép tay


def test_student_cannot_use_admin_routes(mem_db):
    from api.routes import admin

    student = make_client(admin.router)
    assert student.get("/api/admin/users").status_code == 403
    assert student.post("/api/admin/users", json={"lines": ["Ai Đó"]}).status_code == 403
    anon = make_client(admin.router, login=False)
    assert anon.get("/api/admin/users").status_code == 401


def test_admin_creates_class_and_students_must_change_password(mem_db):
    from api.routes import admin, history

    a = _admin_client()
    r = a.post("/api/admin/users", json={"lines": [
        "Nguyễn Văn An", "Nguyễn Văn An", "hs.minh, Lê Minh", "Ab, sai tên", "", "admin, trùng admin",
    ]}).json()
    ok = [x for x in r["results"] if x["ok"]]
    bad = [x for x in r["results"] if not x["ok"]]
    assert [x["username"] for x in ok] == ["nguyenvanan", "nguyenvanan2", "hs.minh"]   # trùng tên -> thêm số
    assert len(bad) == 2 and r["created"] == 3
    users = {u["username"]: u for u in a.get("/api/admin/users").json()}
    assert users["hs.minh"]["must_change_password"] and users["admin"]["role"] == "admin"

    # Học sinh đăng nhập bằng mật khẩu được cấp: bị chặn mọi tính năng tới khi đổi mật khẩu
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api.routes import auth

    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(history.router)
    s = TestClient(app)
    first = next(x for x in ok if x["username"] == "hs.minh")
    assert s.post("/api/auth/login", json={"username": "hs.minh", "password": first["password"]}).status_code == 200
    assert s.get("/api/auth/me").json()["must_change_password"] is True
    assert s.get("/api/history/solves").status_code == 403
    assert s.post("/api/auth/change-password", json={"old_password": first["password"],
                                                     "new_password": first["password"]}).status_code == 400
    assert s.post("/api/auth/change-password", json={"old_password": first["password"],
                                                     "new_password": "cua-rieng-em-1"}).status_code == 200
    assert s.get("/api/auth/me").json()["must_change_password"] is False
    assert s.get("/api/history/solves").status_code == 200


def test_admin_reset_and_lock(mem_db):
    from api.routes import auth as auth_route

    a = _admin_client()
    service.create_user("hocsinh1", PASSWORD, "Em", must_change_password=False)
    s = make_client(auth_route.router, login=False)
    assert s.post("/api/auth/login", json={"username": "hocsinh1", "password": PASSWORD}).status_code == 200

    # Khóa: đăng xuất ngay, đăng nhập lại (đúng mật khẩu) bị báo khóa
    assert a.post("/api/admin/users/hocsinh1/active", json={"active": False}).status_code == 200
    assert s.get("/api/auth/me").status_code == 401
    r = s.post("/api/auth/login", json={"username": "hocsinh1", "password": PASSWORD})
    assert r.status_code == 400 and "bị khóa" in r.json()["detail"]
    r = s.post("/api/auth/login", json={"username": "hocsinh1", "password": "sai-mat-khau"})
    assert "bị khóa" not in r.json()["detail"]                   # sai mật khẩu thì không lộ trạng thái khóa
    assert a.post("/api/admin/users/admin/active", json={"active": False}).status_code == 400

    # Mở khóa + đặt lại mật khẩu tự sinh -> bắt đổi lần đăng nhập tới
    a.post("/api/admin/users/hocsinh1/active", json={"active": True})
    new_pw = a.post("/api/admin/users/hocsinh1/reset-password", json={}).json()["password"]
    assert len(new_pw) == 10
    assert s.post("/api/auth/login", json={"username": "hocsinh1", "password": new_pw}).json()["must_change_password"]


def test_admin_must_also_change_initial_password(mem_db):
    from api.routes import admin

    a = _admin_client(must_change=True)
    assert a.get("/api/admin/users").status_code == 403          # admin mới tạo cũng phải đổi mật khẩu tạm


def test_cookie_samesite_cross_domain(mem_db, monkeypatch):
    """Deploy frontend/backend khác tên miền: COOKIE_SAMESITE=none phải kèm Secure."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api.routes import auth

    service.create_user("hocsinh1", PASSWORD, "Em", must_change_password=False)
    app = FastAPI()
    app.include_router(auth.router)
    login = {"username": "hocsinh1", "password": PASSWORD}

    cookie = TestClient(app).post("/api/auth/login", json=login).headers["set-cookie"].lower()
    assert "samesite=lax" in cookie and "secure" not in cookie

    monkeypatch.setenv("COOKIE_SAMESITE", "none")
    cookie = TestClient(app).post("/api/auth/login", json=login).headers["set-cookie"].lower()
    assert "samesite=none" in cookie and "secure" in cookie
