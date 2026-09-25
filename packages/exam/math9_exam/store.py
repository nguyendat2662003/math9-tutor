"""Lưu đề đã sinh (kèm đáp án) trên server, tra bằng id ngẫu nhiên.

Giống ảnh upload: client chỉ cầm `exam_id` (uuid hex), không bao giờ gửi đường
dẫn. Đề cũ quá `KEEP_SECONDS` bị xóa khi có đề mới.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from .models import Exam

EXAM_DIR = Path(__file__).resolve().parents[3] / "data" / "exams"
KEEP_SECONDS = 7 * 24 * 3600
_RE_ID = re.compile(r"^[0-9a-f]{32}$")


class ExamNotFound(KeyError):
    pass


def _path(exam_id: str, root: Path) -> Path:
    if not _RE_ID.fullmatch(exam_id or ""):
        raise ValueError("exam_id không hợp lệ")
    return root / f"{exam_id}.json"


def save(exam: Exam, root: Path | None = None) -> None:
    root = root or EXAM_DIR
    root.mkdir(parents=True, exist_ok=True)
    now = time.time()
    for f in root.glob("*.json"):
        if now - f.stat().st_mtime > KEEP_SECONDS:
            f.unlink(missing_ok=True)
    _path(exam.id, root).write_text(exam.model_dump_json(), encoding="utf-8")


def load(exam_id: str, root: Path | None = None) -> Exam:
    p = _path(exam_id, root or EXAM_DIR)
    if not p.exists():
        raise ExamNotFound(exam_id)
    return Exam.model_validate_json(p.read_text(encoding="utf-8"))
