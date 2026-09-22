"""Agent Draftsman.

Model: model trung bình
Đầu vào: latex + entities
Đầu ra: construction (kịch bản dựng hình)

Chạy song song: Solver và Draftsman cùng nhận latex, không phụ thuộc nhau
"""

from __future__ import annotations

from pathlib import Path

from ..state import ProblemState
from .base import Agent

PROMPT = Path(__file__).resolve().parents[4].parent / "prompts" / "draftsman.md"


class DraftsmanAgent(Agent):
    role = "draftsman"

    def run(self, state: ProblemState) -> ProblemState:
        raise NotImplementedError(
            "TODO: nạp prompts/draftsman.md, gọi self.llm.complete(), ghi kết quả vào state"
        )
