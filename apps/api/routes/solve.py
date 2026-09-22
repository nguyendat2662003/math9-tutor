"""Endpoint giải toán.

Trả về ProblemState đầy đủ, không phải chuỗi text. Frontend cần steps, figure
và confidence riêng biệt để render hình đồng bộ với bước giải.
"""

from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from math9_core.state import ProblemState
from math9_curriculum.schema import Mode
from pydantic import BaseModel, Field

from ..streaming.sse import stream_pipeline

router = APIRouter(prefix="/api")


class SolveRequest(BaseModel):
    text: str = Field(min_length=5, max_length=4000)
    mode: Mode = Mode.EXAM10
    image_path: str | None = None
    stream: bool = True
    hints: bool = True


def _public_state(s: ProblemState) -> dict:
    """Phần frontend cần; bỏ RAG context và trace chi tiết cho gọn."""
    d = s.model_dump(mode="json", exclude={"retrieved", "trace", "created_at"})
    d["confidence"] = s.confidence().value
    d["verification"]["detail"] = {
        k: v for k, v in d["verification"]["detail"].items()
        if k in ("geometry", "algebra", "bad_predicates", "draftsman_error", "retry_feedback")
    }
    d["tokens"] = {"in": sum(t.tokens_in for t in s.trace), "out": sum(t.tokens_out for t in s.trace)}
    return d


@router.post("/solve")
async def solve(req: SolveRequest, request: Request):
    base = request.app.state.pipeline
    state = ProblemState(raw_input=req.text.strip(), mode=req.mode, image_path=req.image_path)

    if req.stream:
        return StreamingResponse(
            stream_pipeline(base, state, enable_hints=req.hints, to_public=_public_state),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    pipe = replace(base, enable_hints=req.hints, on_stage=None)
    result = await run_in_threadpool(pipe.run, state)
    return _public_state(result)
