"""Hỏi đáp sau khi giải: hỏi thêm về MỘT bài đã giải, trả lời stream qua SSE.

Giới hạn: CHAT_PER_SOLVE_LIMIT câu hỏi mỗi bài (mặc định 15) và CHAT_DAILY_LIMIT câu hỏi mỗi ngày
(mặc định 100) — mỗi câu hỏi là một lượt gọi model.
"""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from math9_accounts import history
from math9_accounts.service import UserInfo
from math9_core.llm.client import default_model
from math9_core.tutor import answer_stream
from pydantic import BaseModel, Field

from ..auth import current_user
from ..streaming.sse import event

router = APIRouter(prefix="/api/chat", dependencies=[Depends(current_user)])
log = logging.getLogger(__name__)


class Ask(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def per_solve_limit() -> int:
    return int(os.environ.get("CHAT_PER_SOLVE_LIMIT", "15"))


def daily_limit() -> int:
    return int(os.environ.get("CHAT_DAILY_LIMIT", "100"))


@router.get("/{solve_id}")
def messages(solve_id: str, user: UserInfo = Depends(current_user)) -> dict:
    if history.get_solve(user.id, solve_id) is None:
        raise HTTPException(404, "Không tìm thấy bài này")
    msgs = history.chat_messages(user.id, solve_id)
    asked = sum(1 for m in msgs if m["role"] == "user")
    return {"messages": msgs, "remaining": max(0, per_solve_limit() - asked)}


@router.post("/{solve_id}")
async def ask(solve_id: str, req: Ask, request: Request, user: UserInfo = Depends(current_user)):
    state = await run_in_threadpool(history.solve_state_for_chat, user.id, solve_id)
    if state is None:
        raise HTTPException(404, "Không tìm thấy bài đã giải xong để hỏi thêm")
    past = await run_in_threadpool(history.chat_messages, user.id, solve_id)
    asked = sum(1 for m in past if m["role"] == "user")
    if asked >= per_solve_limit():
        raise HTTPException(429, f"Bài này đã hỏi {asked} câu — tối đa {per_solve_limit()} câu mỗi bài. "
                                 "Hãy giải một bài mới hoặc xem lại lời giải.")
    if await run_in_threadpool(history.chat_questions_today, user.id) >= daily_limit():
        raise HTTPException(429, f"Hôm nay em đã hỏi {daily_limit()} câu — mai hỏi tiếp nhé.")

    question = req.message.strip()
    await run_in_threadpool(history.add_chat_message, user.id, solve_id, "user", question)
    solver = request.app.state.pipeline.solver          # dùng chung client + model với Solver
    model = solver.model or default_model()

    return StreamingResponse(_stream(solver.llm, model, state, past, question, user.id, solve_id),
                             media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"})


async def _stream(llm, model, state, past, question, user_id, solve_id):
    """Chạy LLM (đồng bộ) trong thread, đẩy từng đoạn qua hàng đợi asyncio ra SSE.
    Học sinh đóng trang giữa chừng thì vẫn chạy nốt và lưu câu trả lời vào lịch sử."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def work() -> None:
        usage: dict = {}
        parts: list[str] = []
        try:
            for piece in answer_stream(llm, model, state, past, question, usage=usage):
                parts.append(piece)
                loop.call_soon_threadsafe(queue.put_nowait, ("token", {"t": piece}))
            text = "".join(parts).strip()
            mid = history.add_chat_message(user_id, solve_id, "assistant", text,
                                           usage.get("input", 0), usage.get("output", 0))
            loop.call_soon_threadsafe(queue.put_nowait, ("done", {"id": mid}))
        except Exception as e:
            log.exception("Hỏi đáp lỗi")
            loop.call_soon_threadsafe(queue.put_nowait, ("error", {"message": f"{type(e).__name__}: {e}"}))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    task = loop.run_in_executor(None, work)
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=15)
        except TimeoutError:
            yield ": keep-alive\n\n"
            continue
        if item is None:
            break
        yield event(*item)
    await task
