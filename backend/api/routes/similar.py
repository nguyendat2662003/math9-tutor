"""Gợi ý bài tương tự để luyện thêm — tìm theo nghĩa trên kho đề Qdrant.

Chỉ trả đề, không trả đáp án (học sinh tự làm, rồi mới bấm giải).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from math9_exam.index import get_index, text_hash

from ..auth import current_user

router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])
PUBLIC = ("id", "number", "source", "format", "options", "claims", "topic", "difficulty", "score")


@router.get("/similar")
def similar(text: str = Query(..., min_length=10, max_length=4000), topic: str | None = None,
            k: int = Query(5, ge=1, le=10)) -> dict:
    idx = get_index()
    if idx is None:
        return {"enabled": False, "items": []}
    try:
        # Không gợi ý lại chính bài đang giải; bài na ná tới mức gần như trùng cũng bỏ
        hits = idx.similar(text, k=k * 3, topic=topic, exclude_hash=text_hash(text))
    except Exception as e:
        return {"enabled": True, "items": [], "error": f"Không tìm được bài tương tự: {type(e).__name__}"}
    items = []
    groups: set[str] = set()
    for h in hits:
        if h["score"] >= 0.97 or h.get("needs_figure"):
            continue
        if h.get("group"):                       # các ý a, b, c của cùng một bài: chỉ gợi ý một lần
            if h["group"] in groups:
                continue
            groups.add(h["group"])
        full = f"{h['lead']}\n{h['statement']}" if h.get("lead") else h["statement"]
        items.append({k2: h.get(k2) for k2 in PUBLIC} | {"statement": full})
        if len(items) == k:
            break
    return {"enabled": True, "items": items}
