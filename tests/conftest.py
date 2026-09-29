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


def make_client(*routers, username: str = "hocsinh1", login: bool = True):
    """TestClient gắn các router cho trước (+ router đăng nhập); mặc định đã đăng ký và đăng nhập."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from apps.api.routes import auth

    app = FastAPI()
    app.include_router(auth.router)
    for r in routers:
        app.include_router(r)
    c = TestClient(app)
    if login:
        r = c.post("/api/auth/register", json={"username": username, "password": "matkhau-123", "display_name": "Em A"})
        assert r.status_code == 200, r.text
    return c
