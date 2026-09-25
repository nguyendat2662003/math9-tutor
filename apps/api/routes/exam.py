"""Luyện đề: sinh đề theo cấu trúc tỉnh hoặc tự chọn, nộp bài, chấm.

Đáp án chỉ nằm trên server. `POST /api/exam` trả đề KHÔNG kèm đáp án; đáp án và
lời giải chỉ trả về sau khi nộp bài.
"""

from __future__ import annotations

from random import Random
from typing import Any

from fastapi import APIRouter, HTTPException
from math9_curriculum.loader import curriculum
from math9_exam import store
from math9_exam.bank import load_bank
from math9_exam.builder import CustomSpec, build_exam, custom_blueprint, load_blueprints
from math9_exam.grading import grade_exam
from math9_exam.variants import TEMPLATES
from pydantic import BaseModel, model_validator

router = APIRouter(prefix="/api/exam")


class CreateExam(BaseModel):
    blueprint: str | None = None
    custom: CustomSpec | None = None
    seed: int | None = None

    @model_validator(mode="after")
    def _one_of(self):
        if bool(self.blueprint) == bool(self.custom):
            raise ValueError("Chọn một cấu trúc đề (blueprint) hoặc tự chọn (custom)")
        return self


class Submit(BaseModel):
    responses: dict[str, Any]


@router.get("/blueprints")
def blueprints() -> dict:
    bank = load_bank()
    topics = {t.id: t.name for t in curriculum().topics.values()}
    return {
        "blueprints": [
            {"id": b.id, "name": b.name, "style": b.style, "minutes": b.minutes, "based_on": b.based_on,
             "n_questions": sum(len(s.group_points) if s.group else 1 for s in b.slots)}
            for b in load_blueprints().values()
        ],
        "topics": topics,
        "bank_size": len(bank.items),
        "templates": len(TEMPLATES),
    }


@router.post("")
def create(req: CreateExam) -> dict:
    if req.blueprint:
        bp = load_blueprints().get(req.blueprint)
        if not bp:
            raise HTTPException(404, f"Không có cấu trúc đề '{req.blueprint}'")
    else:
        unknown = set(req.custom.topics) - set(curriculum().topics)
        if unknown:
            raise HTTPException(400, f"Chuyên đề không hợp lệ: {', '.join(sorted(unknown))}")
        bp = custom_blueprint(req.custom, Random(req.seed))
    exam = build_exam(bp, seed=req.seed)
    if not exam.questions:
        raise HTTPException(422, "Không đủ câu hỏi cho lựa chọn này — thử thêm chuyên đề khác.")
    store.save(exam)
    return exam.public()


def _load(exam_id: str):
    try:
        return store.load(exam_id)
    except ValueError:
        raise HTTPException(400, "exam_id không hợp lệ")
    except store.ExamNotFound:
        raise HTTPException(404, "Không tìm thấy đề (có thể đã hết hạn)")


@router.get("/{exam_id}")
def get(exam_id: str) -> dict:
    return _load(exam_id).public()


@router.post("/{exam_id}/submit")
def submit(exam_id: str, req: Submit) -> dict:
    return grade_exam(_load(exam_id), req.responses)
