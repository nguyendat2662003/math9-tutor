"""Agent Pedagogue.

Model: model nhỏ
Đầu vào: solution đã kiểm chứng
Đầu ra: hints — gợi ý từng bước

Chạy song song: không
"""

from __future__ import annotations

from pathlib import Path

from ..state import ProblemState
from .base import Agent

PROMPT = Path(__file__).resolve().parents[4].parent / "prompts" / "pedagogue.md"


class PedagogueAgent(Agent):
    role = "pedagogue"

    def run(self, state: ProblemState) -> ProblemState:
        raise NotImplementedError(
            "TODO: nạp prompts/pedagogue.md, gọi self.llm.complete(), ghi kết quả vào state"
        )
