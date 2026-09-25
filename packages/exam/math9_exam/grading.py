"""Chấm bài làm.

Trắc nghiệm, đúng/sai, trả lời ngắn và tự luận có đáp số được chấm tự động. Bài
chứng minh KHÔNG chấm tự động: so khớp lập luận bằng máy không đáng tin, chấm sai
còn tệ hơn không chấm. Học sinh xem lời giải rồi tự chấm (status "tu_cham").
"""

from __future__ import annotations

from typing import Any

from math9_verifier.answer import grade as grade_answer
from math9_verifier.answer import grade_ordered

from .models import Exam, Question

LETTERS = "ABCD"
# Thang điểm đúng/sai 4 ý theo kiểu đề mới: đúng 1/2/3/4 ý được 10/25/50/100% số điểm
TF_SCALE = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}


def answer_display(q: Question) -> str:
    a = q.answer
    if q.format == "trac_nghiem" and isinstance(a, dict):
        i = LETTERS.find(a.get("letter", ""))
        shown = q.options[i] if q.options and 0 <= i < len(q.options) else a.get("value", "")
        return f"{a.get('letter')}. {shown}"
    if q.format == "dung_sai" and isinstance(a, list):
        return " · ".join(f"{'abcd'[i]}) {'Đúng' if v else 'Sai'}" for i, v in enumerate(a))
    if a:
        return str(a)
    return ""


def grade_question(q: Question, resp: Any) -> dict:
    out = {"qid": q.qid, "points": q.points, "earned": 0.0, "auto": q.auto,
           "answer": answer_display(q), "solution": q.solution, "response": resp}

    if q.format == "trac_nghiem":
        letter = str(resp or "").strip().upper()[:1]
        if not letter:
            return {**out, "status": "bo_trong"}
        ok = isinstance(q.answer, dict) and letter == q.answer.get("letter")
        return {**out, "status": "dung" if ok else "sai", "earned": q.points if ok else 0.0}

    if q.format == "dung_sai":
        picks = resp if isinstance(resp, list) else []
        gold = q.answer if isinstance(q.answer, list) else []
        if not any(p is not None for p in picks):
            return {**out, "status": "bo_trong"}
        n_ok = sum(1 for p, g in zip(picks, gold) if p is not None and bool(p) == g)
        frac = TF_SCALE.get(n_ok, 0.0) if len(gold) == 4 else n_ok / max(len(gold), 1)
        status = "dung" if n_ok == len(gold) else "mot_phan" if n_ok else "sai"
        return {**out, "status": status, "earned": round(q.points * frac, 2), "n_correct": n_ok}

    if not q.auto:
        # Bài chứng minh: học sinh tự chấm theo lời giải
        return {**out, "status": "tu_cham"}

    text = str(resp or "").strip()
    if not text:
        return {**out, "status": "bo_trong"}
    if q.check == "ordered":
        ok = grade_ordered(text, str(q.answer))
    else:
        ok = grade_answer(text, q.answer)
    return {**out, "status": "dung" if ok else "sai", "earned": q.points if ok else 0.0}


def grade_exam(exam: Exam, responses: dict[str, Any]) -> dict:
    items = [grade_question(q, responses.get(q.qid)) for q in exam.questions]
    auto_score = round(sum(i["earned"] for i in items), 2)
    self_max = round(sum(i["points"] for i in items if i["status"] == "tu_cham"), 2)
    return {
        "exam_id": exam.id,
        "total_points": exam.total_points,
        "auto_score": auto_score,
        "self_grade_points": self_max,        # phần điểm học sinh tự chấm
        "items": items,
    }
