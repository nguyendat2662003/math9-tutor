"""Endpoint giải toán.

Trả về ProblemState đầy đủ, không phải chuỗi text. Frontend cần steps, figure
và confidence riêng biệt để render hình đồng bộ với bước giải.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from math9_core.state import ProblemState
from math9_curriculum.schema import Mode
from pydantic import BaseModel

from ..streaming.sse import stream_pipeline

router = APIRouter(prefix="/api")


class SolveRequest(BaseModel):
    text: str
    mode: Mode = Mode.EXAM10
    image_path: str | None = None
    stream: bool = True


@router.post("/solve")
async def solve(req: SolveRequest):
    state = ProblemState(raw_input=req.text, mode=req.mode, image_path=req.image_path)
    if req.stream:
        return StreamingResponse(stream_pipeline(state), media_type="text/event-stream")
    raise NotImplementedError("Dựng Pipeline từ DI container và chạy đồng bộ")
