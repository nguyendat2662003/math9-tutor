"""Agent Critic.

Model: model trung bình
Đầu vào: state + violations
Đầu ra: danh sách lỗi cần sửa

Chạy song song: không
"""

from __future__ import annotations

from pathlib import Path

from ..state import ProblemState
from .base import Agent

PROMPT = Path(__file__).resolve().parents[4].parent / "prompts" / "critic.md"


class CriticAgent(Agent):
    role = "critic"

    def run(self, state: ProblemState) -> ProblemState:
        raise NotImplementedError(
            "TODO: nạp prompts/critic.md, gọi self.llm.complete(), ghi kết quả vào state"
        )
