"""Nhận ảnh đề bài.

Client KHÔNG gửi đường dẫn — chỉ gửi file, nhận lại một `image_id`. `/api/solve`
nhận id đó và server tự tra ra đường dẫn. Nếu nhận đường dẫn từ client thì mở
đường cho path traversal (đọc file bất kỳ trên máy chủ).
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import current_user

router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])
log = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
MAX_BYTES = 12 * 1024 * 1024
KEEP_SECONDS = 24 * 3600
ALLOWED = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/heic": ".heic"}
# Chữ ký đầu file — content-type do client khai báo, không tin được
MAGIC = [(b"\x89PNG\r\n\x1a\n", ".png"), (b"\xff\xd8\xff", ".jpg"), (b"RIFF", ".webp")]


def path_for(image_id: str) -> Path:
    """Đường dẫn của một image_id đã upload. Ném HTTPException nếu id lạ."""
    if not image_id or "/" in image_id or "\\" in image_id or "." in image_id:
        raise HTTPException(400, "image_id không hợp lệ")
    for p in UPLOAD_DIR.glob(f"{image_id}.*"):
        return p
    raise HTTPException(404, "Không tìm thấy ảnh đã tải lên (có thể đã hết hạn)")


def _cleanup() -> None:
    now = time.time()
    for f in UPLOAD_DIR.glob("*.*"):
        if now - f.stat().st_mtime > KEEP_SECONDS:
            f.unlink(missing_ok=True)


@router.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"Ảnh quá lớn ({len(raw) // 1024 // 1024} MB). Tối đa 12 MB.")
    if len(raw) < 32:
        raise HTTPException(400, "File rỗng hoặc hỏng")

    ext = next((e for sig, e in MAGIC if raw.startswith(sig)), None) or ALLOWED.get(file.content_type or "")
    if not ext:
        raise HTTPException(415, "Chỉ nhận ảnh PNG, JPG hoặc WEBP")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup()
    image_id = uuid.uuid4().hex
    (UPLOAD_DIR / f"{image_id}{ext}").write_bytes(raw)
    log.info("Nhận ảnh %s%s (%d KB)", image_id, ext, len(raw) // 1024)
    return {"image_id": image_id, "bytes": len(raw)}
