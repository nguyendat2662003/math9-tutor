import os
import sys
from pathlib import Path

import pytest

# Test dùng LLM giả — không được đẩy trace giả lên Langfuse thật trong .env
os.environ["LANGFUSE_TRACING"] = "0"
# Test không được đụng kho đề Qdrant thật; test cần kho thì gắn kho trong bộ nhớ (set_index)
os.environ["QDRANT_DISABLED"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def mem_db():
    """CSDL tài khoản trong bộ nhớ, mới cho từng test — không bao giờ đụng Supabase thật."""
    from math9_accounts import db

    db.configure("sqlite://")
    db.init_db()
    yield db
    db.engine().dispose()


PASSWORD = "matkhau-123"


def make_client(*routers, username: str = "hocsinh1", login: bool = True, role: str = "student",
                must_change: bool = False):
    """TestClient gắn các router cho trước (+ router đăng nhập). Không có tự đăng ký nên tài khoản
    được tạo thẳng qua service (như admin tạo), rồi đăng nhập qua API để có cookie phiên."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from math9_accounts import service

    from api.routes import auth

    app = FastAPI()
    app.include_router(auth.router)
    for r in routers:
        app.include_router(r)
    c = TestClient(app)
    if login:
        service.create_user(username, PASSWORD, "Em A", role=role, must_change_password=must_change)
        r = c.post("/api/auth/login", json={"username": username, "password": PASSWORD})
        assert r.status_code == 200, r.text
    return c
