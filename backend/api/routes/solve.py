"""Endpoint giải toán.

Trả về ProblemState đầy đủ, không phải chuỗi text. Frontend cần steps, figure
và confidence riêng biệt để render hình đồng bộ với bước giải.
"""

from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from math9_accounts import history, service
from math9_accounts.service import UserInfo
from math9_core.state import ProblemState
from math9_curriculum.schema import Mode
from pydantic import BaseModel, Field, model_validator

from ..auth import current_user
from ..streaming.sse import stream_pipeline
from .upload import path_for

router = APIRouter(prefix="/api")


class SolveRequest(BaseModel):
    """Cần `text` (đề gõ tay) hoặc `image_id` (ảnh đã tải qua /api/upload), hoặc cả hai."""

    text: str = Field(default="", max_length=4000)
    mode: Mode = Mode.EXAM10
    image_id: str | None = None
    stream: bool = True
    hints: bool = True

    @model_validator(mode="after")
    def _need_input(self):
        if not self.image_id and len(self.text.strip()) < 5:
            raise ValueError("Cần đề bài (ít nhất 5 ký tự) hoặc một ảnh đề")
        return self


def _public_state(s: ProblemState) -> dict:
    """Phần frontend cần; bỏ RAG context và trace chi tiết cho gọn."""
    d = s.model_dump(mode="json", exclude={"retrieved", "trace", "created_at", "image_path"})
    d["confidence"] = s.confidence().value
    d["verification"]["detail"] = {
        k: v for k, v in d["verification"]["detail"].items()
        if k in ("geometry", "algebra", "bad_predicates", "draftsman_error", "retry_feedback")
    }
    d["tokens"] = {"in": sum(t.tokens_in for t in s.trace), "out": sum(t.tokens_out for t in s.trace)}
    return d


@router.post("/solve")
async def solve(req: SolveRequest, request: Request, user: UserInfo = Depends(current_user)):
    used = await run_in_threadpool(service.solves_today, user.id)
    if used >= service.daily_limit():
        raise HTTPException(429, f"Hôm nay em đã giải {used} bài — đạt giới hạn {service.daily_limit()} bài/ngày. "
                                 "Mai quay lại nhé, hoặc xem lại các bài trong Lịch sử.")
    base = request.app.state.pipeline
    image_path = str(path_for(req.image_id)) if req.image_id else None
    state = ProblemState(raw_input=req.text.strip(), mode=req.mode, image_path=image_path)
    # Ghi lịch sử ngay từ đầu: lượt lỗi cũng tính vào hạn mức (vẫn đã tốn lượt gọi model)
    record_id = await run_in_threadpool(history.start_solve, user.id, state.raw_input, req.mode.value, image_path)

    def to_public(s: ProblemState) -> dict:
        d = _public_state(s)
        history.finish_solve(record_id, d)
        return d | {"history_id": record_id}

    if req.stream:
        return StreamingResponse(
            stream_pipeline(base, state, enable_hints=req.hints, to_public=to_public,
                            on_error=lambda msg: history.fail_solve(record_id, msg)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
        )

    pipe = replace(base, enable_hints=req.hints, on_stage=None)
    try:
        result = await run_in_threadpool(pipe.run, state)
    except Exception as e:
        await run_in_threadpool(history.fail_solve, record_id, f"{type(e).__name__}: {e}")
        raise
    return await run_in_threadpool(to_public, result)
