"""Lịch sử của học sinh đang đăng nhập: bài đã giải, đề đã luyện."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from math9_accounts import history
from math9_accounts.service import UserInfo
from math9_exam.models import Exam
from pydantic import BaseModel

from ..auth import current_user

router = APIRouter(prefix="/api/history")


class SelfMarks(BaseModel):
    marks: dict[str, float]


@router.get("/solves")
def solves(offset: int = Query(0, ge=0), user: UserInfo = Depends(current_user)) -> dict:
    return history.list_solves(user.id, offset)


@router.get("/solves/{record_id}")
def solve(record_id: str, user: UserInfo = Depends(current_user)) -> dict:
    rec = history.get_solve(user.id, record_id)
    if rec is None:
        raise HTTPException(404, "Không tìm thấy bài này trong lịch sử")
    return rec


@router.get("/solves/{record_id}/image")
def solve_image(record_id: str, user: UserInfo = Depends(current_user)):
    p = history.solve_image(user.id, record_id)
    if p is None:
        raise HTTPException(404, "Không có ảnh")
    return FileResponse(p, headers={"Cache-Control": "private, max-age=86400"})


@router.delete("/solves/{record_id}")
def delete_solve(record_id: str, user: UserInfo = Depends(current_user)) -> dict:
    if not history.delete_solve(user.id, record_id):
        raise HTTPException(404, "Không tìm thấy bài này")
    return {"ok": True}


@router.get("/exams")
def exams(offset: int = Query(0, ge=0), user: UserInfo = Depends(current_user)) -> dict:
    return history.list_exams(user.id, offset)


@router.get("/exams/{exam_id}")
def exam(exam_id: str, user: UserInfo = Depends(current_user)) -> dict:
    row = history.get_exam_row(user.id, exam_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy đề này")
    # Đề công khai (không đáp án); đáp án chỉ có trong `result` — tức là SAU khi đã nộp
    return {k: row[k] for k in ("id", "request", "responses", "result", "self_marks", "created_at",
                                "submitted_at", "score", "total")} | {"exam": Exam.model_validate(row["exam"]).public()}


@router.put("/exams/{exam_id}/self-marks")
def self_marks(exam_id: str, req: SelfMarks, user: UserInfo = Depends(current_user)) -> dict:
    score = history.set_self_marks(user.id, exam_id, req.marks)
    if score is None:
        raise HTTPException(404, "Không tìm thấy đề đã nộp")
    return {"score": score}


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: str, user: UserInfo = Depends(current_user)) -> dict:
    if not history.delete_exam(user.id, exam_id):
        raise HTTPException(404, "Không tìm thấy đề này")
    return {"ok": True}
