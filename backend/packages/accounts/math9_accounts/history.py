"""Lịch sử: bài đã giải và đề đã luyện của từng học sinh. Mọi hàm đều lọc theo user_id —
không có đường nào đọc được lịch sử của người khác."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select

from . import db
from .models import ChatMessage, ExamAttempt, SolveRecord, now

IMAGE_DIR = Path(__file__).resolve().parents[3] / "data" / "user_images"
PAGE = 20


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


# ---------- bài đã giải ----------

def start_solve(user_id: int, question: str, mode: str, image_path: str | None) -> str:
    """Ghi lượt giải ngay khi bắt đầu (đếm hạn mức kể cả khi lỗi). Ảnh đề được chép sang chỗ
    lưu lâu dài — thư mục upload tự xóa sau 24 giờ."""
    with db.session() as s:
        rec = SolveRecord(user_id=user_id, question=question, mode=mode)
        s.add(rec)
        s.flush()
        if image_path:
            src = Path(image_path)
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            name = f"{rec.id}{src.suffix.lower()}"
            shutil.copyfile(src, IMAGE_DIR / name)
            rec.image_file = name
        return rec.id


def finish_solve(record_id: str, state: dict) -> None:
    with db.session() as s:
        rec = s.get(SolveRecord, record_id)
        if rec is None:
            return
        rec.status, rec.state = "done", state
        rec.topic, rec.confidence = state.get("topic"), state.get("confidence")
        if not rec.question:
            rec.question = state.get("latex") or state.get("raw_input") or ""


def fail_solve(record_id: str, message: str) -> None:
    with db.session() as s:
        rec = s.get(SolveRecord, record_id)
        if rec is not None:
            rec.status, rec.error = "error", message[:1000]


def list_solves(user_id: int, offset: int = 0, limit: int = PAGE) -> dict:
    with db.session() as s:
        rows = s.scalars(select(SolveRecord).where(SolveRecord.user_id == user_id)
                         .order_by(SolveRecord.created_at.desc()).offset(offset).limit(limit + 1)).all()
        items = [{"id": r.id, "created_at": _iso(r.created_at), "status": r.status, "question": r.question[:300],
                  "has_image": bool(r.image_file), "topic": r.topic, "confidence": r.confidence} for r in rows[:limit]]
        return {"items": items, "more": len(rows) > limit}


def get_solve(user_id: int, record_id: str) -> dict | None:
    with db.session() as s:
        r = s.scalar(select(SolveRecord).where(SolveRecord.id == record_id, SolveRecord.user_id == user_id))
        if r is None:
            return None
        return {"id": r.id, "created_at": _iso(r.created_at), "status": r.status, "question": r.question,
                "has_image": bool(r.image_file), "error": r.error, "state": r.state}


def solve_image(user_id: int, record_id: str) -> Path | None:
    with db.session() as s:
        name = s.scalar(select(SolveRecord.image_file)
                        .where(SolveRecord.id == record_id, SolveRecord.user_id == user_id))
    p = IMAGE_DIR / name if name else None
    return p if p and p.exists() else None


def delete_solve(user_id: int, record_id: str) -> bool:
    img = solve_image(user_id, record_id)
    with db.session() as s:
        # Xóa hỏi-đáp trước (SQLite mặc định không thực thi ON DELETE CASCADE như PostgreSQL)
        s.execute(delete(ChatMessage).where(ChatMessage.solve_id == record_id, ChatMessage.user_id == user_id))
        n = s.execute(delete(SolveRecord).where(SolveRecord.id == record_id, SolveRecord.user_id == user_id)).rowcount
    if n and img:
        img.unlink(missing_ok=True)
    return bool(n)


# ---------- hỏi đáp về bài đã giải ----------

def chat_messages(user_id: int, solve_id: str) -> list[dict]:
    with db.session() as s:
        rows = s.scalars(select(ChatMessage).where(ChatMessage.solve_id == solve_id, ChatMessage.user_id == user_id)
                         .order_by(ChatMessage.created_at, ChatMessage.role.desc())).all()
        return [{"id": m.id, "role": m.role, "content": m.content, "created_at": _iso(m.created_at)} for m in rows]


def add_chat_message(user_id: int, solve_id: str, role: str, content: str,
                     tokens_in: int = 0, tokens_out: int = 0) -> str:
    with db.session() as s:
        m = ChatMessage(solve_id=solve_id, user_id=user_id, role=role, content=content,
                        tokens_in=tokens_in, tokens_out=tokens_out)
        s.add(m)
        s.flush()
        return m.id


def chat_questions_today(user_id: int) -> int:
    from .service import VN

    start = datetime.now(VN).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    with db.session() as s:
        return s.scalar(select(func.count()).select_from(ChatMessage).where(
            ChatMessage.user_id == user_id, ChatMessage.role == "user", ChatMessage.created_at >= start)) or 0


def solve_state_for_chat(user_id: int, solve_id: str) -> dict | None:
    """ProblemState công khai của bài đã giải XONG, thuộc đúng học sinh này."""
    with db.session() as s:
        r = s.scalar(select(SolveRecord).where(SolveRecord.id == solve_id, SolveRecord.user_id == user_id))
        return r.state if r is not None and r.status == "done" else None


# ---------- đề đã luyện ----------

def save_exam(user_id: int, exam: dict, request: dict) -> None:
    """exam: Exam.model_dump() đầy đủ (kèm đáp án) — chỉ server đọc."""
    with db.session() as s:
        s.add(ExamAttempt(id=exam["id"], user_id=user_id, title=exam["title"], blueprint=exam["blueprint"],
                          request=request, exam=exam, total=round(sum(q["points"] for q in exam["questions"]), 2)))


def get_exam_row(user_id: int, exam_id: str) -> dict | None:
    with db.session() as s:
        a = s.scalar(select(ExamAttempt).where(ExamAttempt.id == exam_id, ExamAttempt.user_id == user_id))
        if a is None:
            return None
        return {"id": a.id, "exam": a.exam, "request": a.request, "responses": a.responses, "result": a.result,
                "self_marks": a.self_marks or {}, "created_at": _iso(a.created_at),
                "submitted_at": _iso(a.submitted_at), "score": a.score, "total": a.total}


def submit_exam(user_id: int, exam_id: str, responses: dict, result: dict) -> None:
    with db.session() as s:
        a = s.scalar(select(ExamAttempt).where(ExamAttempt.id == exam_id, ExamAttempt.user_id == user_id))
        if a is None:
            return
        a.responses, a.result, a.submitted_at = responses, result, now()
        a.self_marks = {}
        a.score = result.get("auto_score")


def set_self_marks(user_id: int, exam_id: str, marks: dict[str, float]) -> float | None:
    """Điểm tự chấm câu chứng minh; không vượt số điểm của câu. -> điểm tổng mới."""
    with db.session() as s:
        a = s.scalar(select(ExamAttempt).where(ExamAttempt.id == exam_id, ExamAttempt.user_id == user_id))
        if a is None or a.result is None:
            return None
        allowed = {i["qid"]: i["points"] for i in a.result["items"] if i["status"] == "tu_cham"}
        clean = {q: max(0.0, min(float(v), allowed[q])) for q, v in marks.items() if q in allowed}
        a.self_marks = clean
        a.score = round(a.result.get("auto_score", 0) + sum(clean.values()), 2)
        return a.score


def list_exams(user_id: int, offset: int = 0, limit: int = PAGE) -> dict:
    with db.session() as s:
        rows = s.scalars(select(ExamAttempt).where(ExamAttempt.user_id == user_id)
                         .order_by(ExamAttempt.created_at.desc()).offset(offset).limit(limit + 1)).all()
        items = [{"id": a.id, "title": a.title, "blueprint": a.blueprint, "created_at": _iso(a.created_at),
                  "submitted_at": _iso(a.submitted_at), "score": a.score, "total": a.total,
                  "n_questions": len(a.exam.get("questions", []))} for a in rows[:limit]]
        return {"items": items, "more": len(rows) > limit}


def delete_exam(user_id: int, exam_id: str) -> bool:
    with db.session() as s:
        return bool(s.execute(delete(ExamAttempt)
                              .where(ExamAttempt.id == exam_id, ExamAttempt.user_id == user_id)).rowcount)


def stats(user_id: int) -> dict[str, Any]:
    with db.session() as s:
        solves = s.scalars(select(SolveRecord.status).where(SolveRecord.user_id == user_id)).all()
        exams = s.scalars(select(ExamAttempt.submitted_at).where(ExamAttempt.user_id == user_id)).all()
    return {"solves": len(solves), "exams": len(exams), "exams_submitted": sum(1 for x in exams if x)}
