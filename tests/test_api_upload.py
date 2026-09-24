"""Endpoint upload: chỉ nhận ảnh thật, không cho client chỉ định đường dẫn."""

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apps.api.routes import upload as up  # noqa: E402

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a"
    "49444154789c6360000002000100ffff03000006000557bfabd40000000049454e44ae426082"
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(up, "UPLOAD_DIR", tmp_path / "uploads")
    app = FastAPI()
    app.include_router(up.router)
    return TestClient(app)


def test_upload_and_lookup(client, tmp_path, monkeypatch):
    r = client.post("/api/upload", files={"file": ("de.png", PNG, "image/png")})
    assert r.status_code == 200
    image_id = r.json()["image_id"]
    assert up.path_for(image_id).exists()


def test_rejects_non_image(client):
    r = client.post("/api/upload", files={"file": ("note.txt", b"x" * 500, "text/plain")})
    assert r.status_code == 415


def test_rejects_too_large(client):
    r = client.post("/api/upload", files={"file": ("big.png", PNG + b"\0" * (13 * 1024 * 1024), "image/png")})
    assert r.status_code == 413


def test_content_type_lie_falls_back_to_magic(client):
    """Client khai image/png nhưng nội dung là text -> từ chối."""
    r = client.post("/api/upload", files={"file": ("fake.png", b"KHONG PHAI ANH" * 40, "application/octet-stream")})
    assert r.status_code == 415


@pytest.mark.parametrize("bad", ["../../../etc/passwd", "a/b", "a\\b", "x.png", ""])
def test_path_traversal_blocked(bad):
    with pytest.raises(HTTPException) as e:
        up.path_for(bad)
    assert e.value.status_code == 400
