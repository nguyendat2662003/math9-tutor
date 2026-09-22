"""Agent Parser.

Model: VLM/OCR
Đầu vào: ảnh hoặc text thô
Đầu ra: latex, entities

Chạy song song: không
"""

from __future__ import annotations

from pathlib import Path

from ..state import ProblemState
from .base import Agent

PROMPT = Path(__file__).resolve().parents[4].parent / "prompts" / "parser.md"


class ParserAgent(Agent):
    role = "parser"

    def run(self, state: ProblemState) -> ProblemState:
        raise NotImplementedError(
            "TODO: nạp prompts/parser.md, gọi self.llm.complete(), ghi kết quả vào state"
        )
