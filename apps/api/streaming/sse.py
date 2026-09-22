"""Phát sự kiện SSE cho từng giai đoạn pipeline.

Bài mức 3 có thể mất tới 90 giây. Độ trễ đó chấp nhận được NẾU giao diện nói
rõ đang làm gì, thay vì để học sinh nhìn màn hình trắng.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from math9_core.state import ProblemState

STAGE_LABELS = {
    "parsing": "Đang đọc đề bài",
    "routing": "Đang xác định dạng toán",
    "solving": "Đang giải",
    "drawing": "Đang dựng hình",
    "verifying": "Đang kiểm tra lại kết quả",
    "retrying": "Kết quả chưa khớp, đang thử hướng khác",
    "rendering": "Đang vẽ hình",
    "hinting": "Đang soạn gợi ý",
}


def event(kind: str, payload: dict) -> str:
    return f"event: {kind}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_pipeline(state: ProblemState) -> AsyncIterator[str]:
    yield event("stage", {"stage": "parsing", "label": STAGE_LABELS["parsing"]})
    # TODO: chạy Pipeline theo từng giai đoạn, yield sau mỗi bước.
    yield event("done", {"confidence": state.confidence()})
