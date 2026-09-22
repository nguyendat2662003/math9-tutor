"""Agent Router.

Model: model nhỏ
Đầu vào: latex
Đầu ra: topic, difficulty, goal_type cho từng ý

Chạy song song: không
"""

from __future__ import annotations

from pathlib import Path

from ..state import ProblemState
from .base import Agent

PROMPT = Path(__file__).resolve().parents[4].parent / "prompts" / "router.md"


class RouterAgent(Agent):
    role = "router"

    def run(self, state: ProblemState) -> ProblemState:
        raise NotImplementedError(
            "TODO: nạp prompts/router.md, gọi self.llm.complete(), ghi kết quả vào state"
        )
