"""Phát sự kiện SSE cho từng giai đoạn pipeline.

Bài mức 3 có thể mất tới 90 giây. Độ trễ đó chấp nhận được NẾU giao diện nói
rõ đang làm gì, thay vì để học sinh nhìn màn hình trắng.

Pipeline chạy đồng bộ trong thread; callback on_stage đẩy sự kiện vào hàng đợi
asyncio, generator này đọc và phát ra. Mỗi 15 giây không có sự kiện, gửi một
dòng comment để proxy không cắt kết nối.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import replace
from typing import AsyncIterator, Callable

from math9_core.state import ProblemState

log = logging.getLogger(__name__)

STAGE_LABELS = {
    "parsing": "Đang đọc đề bài",
    "routing": "Đang xác định dạng toán",
    "routed": "Đã xác định dạng toán",
    "solving": "Đang giải",
    "drawing": "Đang dựng hình",
    "verifying": "Đang kiểm tra lại kết quả",
    "retrying": "Kết quả chưa khớp, đang thử hướng khác",
    "rendering": "Đang vẽ hình",
    "hinting": "Đang soạn gợi ý",
}


def event(kind: str, payload: dict) -> str:
    return f"event: {kind}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_pipeline(
    base, state: ProblemState, *, enable_hints: bool, to_public: Callable[[ProblemState], dict],
) -> AsyncIterator[str]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def on_stage(stage: str, payload: dict) -> None:
        label = STAGE_LABELS.get(stage, stage)
        if stage == "solving" and payload.get("geometry"):
            label = "Đang giải và dựng hình song song"
        loop.call_soon_threadsafe(queue.put_nowait, ("stage", {"stage": stage, "label": label, **payload}))

    pipe = replace(base, enable_hints=enable_hints, on_stage=on_stage)

    async def run() -> None:
        try:
            result = await asyncio.to_thread(pipe.run, state)
            queue.put_nowait(("done", to_public(result)))
        except Exception as e:
            log.exception("Pipeline lỗi")
            queue.put_nowait(("error", {"message": f"{type(e).__name__}: {e}"}))
        finally:
            queue.put_nowait(None)

    task = asyncio.create_task(run())
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if item is None:
                break
            yield event(*item)
    finally:
        if not task.done():
            task.cancel()
