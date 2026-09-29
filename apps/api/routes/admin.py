"""Trang quản trị: tải tài liệu đề lên, duyệt bài, đưa vào kho Qdrant.

Mọi route yêu cầu header `X-Admin-Token` khớp `ADMIN_TOKEN` trong .env. Chưa đặt
ADMIN_TOKEN thì cả nhóm route này TẮT — không có chuyện ai vào được web cũng nhét
đề vào kho.
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Header,
    HTTPException,
    UploadFile,
)
from math9_exam import intake
from math9_exam.bank import load_bank, refresh_bank
from math9_exam.index import get_index
from pydantic import BaseModel

MAX_BYTES = 20 * 1024 * 1024
# Chữ ký đầu file — phần mở rộng và content-type do client gửi, không tin được
MAGIC = [(b"%PDF", ".pdf"), (b"PK\x03\x04", ".docx"), (b"\x89PNG\r\n\x1a\n", ".png"),
         (b"\xff\xd8\xff", ".jpg"), (b"RIFF", ".webp")]


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected = os.environ.get("ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(503, "Trang quản trị đang tắt — đặt ADMIN_TOKEN trong .env rồi khởi động lại API")
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), expected.encode()):
        raise HTTPException(401, "Sai mã quản trị")


router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class Ids(BaseModel):
    ids: list[str]


def _index_or_503():
    idx = get_index()
    if idx is None:
        raise HTTPException(503, "Chưa cấu hình kho Qdrant (QDRANT_URL + QDRANT_API_KEY, hoặc QDRANT_PATH)")
    return idx


def _batch(batch_id: str) -> dict:
    try:
        return intake.load_batch(batch_id)
    except ValueError:
        raise HTTPException(400, "batch_id không hợp lệ")
    except KeyError:
        raise HTTPException(404, "Không tìm thấy lô")


def _llm():
    from math9_core.llm.client import client_from_env, default_model

    return client_from_env(), default_model()


@router.get("/stats")
def stats() -> dict:
    idx = get_index()
    base = {"bank_builtin": len(load_bank(include_uploads=False).items), "qdrant": None}
    if idx is None:
        return base
    uploads = idx.all(status="approved", origin="upload")
    by_topic: dict[str, int] = {}
    for p in uploads:
        by_topic[p.get("topic") or "?"] = by_topic.get(p.get("topic") or "?", 0) + 1
    return base | {"qdrant": {"mode": idx.mode, "collection": idx.collection, "total_points": idx.count(),
                              "uploads": len(uploads), "uploads_by_topic": dict(sorted(by_topic.items()))}}


@router.post("/documents")
async def upload_document(bg: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "Tài liệu quá lớn (tối đa 20 MB) — tách thành nhiều file")
    ext = next((e for sig, e in MAGIC if raw.startswith(sig)), None)
    if not ext:
        raise HTTPException(415, "Chỉ nhận PDF, Word (.docx) hoặc ảnh PNG/JPG/WEBP")
    idx = _index_or_503()
    batch = intake.new_batch(Path(file.filename or f"tai-lieu{ext}").name[:120])
    files_dir = intake.INBOX_DIR / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    path = files_dir / f"{batch['id']}{ext}"
    path.write_bytes(raw)
    intake.save_batch(batch)
    llm, model = _llm()
    bg.add_task(intake.process_upload, batch, path, llm, model, idx)
    return {"id": batch["id"], "status": batch["status"]}


@router.get("/batches")
def batches() -> list[dict]:
    return intake.list_batches()


@router.get("/batches/{batch_id}")
def batch(batch_id: str) -> dict:
    return _batch(batch_id)


@router.patch("/batches/{batch_id}/problems/{pid}")
def edit_problem(batch_id: str, pid: str, changes: dict[str, Any]) -> dict:
    b = _batch(batch_id)
    p = next((x for x in b["problems"] if x["id"] == pid), None)
    if p is None:
        raise HTTPException(404, "Không tìm thấy bài trong lô")
    if p["status"] == "approved":
        raise HTTPException(409, "Bài đã vào kho — gỡ khỏi kho trước khi sửa")
    bad = set(changes) - intake.EDITABLE
    if bad:
        raise HTTPException(400, f"Không sửa được trường: {', '.join(sorted(bad))}")
    p.update(changes)
    intake.validate(p)
    intake.mark_duplicates([p], get_index())
    intake.save_batch(b)
    return p


@router.post("/batches/{batch_id}/approve")
def approve(batch_id: str, req: Ids) -> dict:
    b = _batch(batch_id)
    n, skipped = intake.approve(b, req.ids, _index_or_503())
    refresh_bank()                                  # đề sinh ra lần sau có bài mới
    return {"approved": n, "skipped": skipped}


@router.post("/batches/{batch_id}/reject")
def reject(batch_id: str, req: Ids) -> dict:
    b = _batch(batch_id)
    n = 0
    for p in b["problems"]:
        if p["id"] in set(req.ids) and p["status"] == "pending":
            p["status"] = "rejected"
            n += 1
    intake.save_batch(b)
    return {"rejected": n}


class ResetPassword(BaseModel):
    new_password: str


@router.post("/users/{username}/reset-password")
def reset_password(username: str, req: ResetPassword) -> dict:
    """Học sinh quên mật khẩu (không có email để tự khôi phục): quản trị đặt mật khẩu mới,
    mọi phiên đăng nhập cũ của tài khoản đó bị đăng xuất."""
    from math9_accounts.service import AccountError
    from math9_accounts.service import reset_password as do_reset

    try:
        do_reset(username, req.new_password)
    except AccountError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@router.post("/batches/{batch_id}/unpublish")
def unpublish(batch_id: str, req: Ids) -> dict:
    """Gỡ bài đã duyệt khỏi kho (duyệt nhầm, phát hiện đáp án sai) — bài về lại trạng thái chờ."""
    b = _batch(batch_id)
    ids = [p["id"] for p in b["problems"] if p["id"] in set(req.ids) and p["status"] == "approved"]
    if ids:
        _index_or_503().delete(ids)
        for p in b["problems"]:
            if p["id"] in ids:
                p["status"] = "pending"
        intake.save_batch(b)
        refresh_bank()
    return {"unpublished": len(ids)}
