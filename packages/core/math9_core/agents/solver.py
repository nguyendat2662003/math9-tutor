"""Agent Solver.

Model: model mạnh
Đầu vào: latex + allowed_tools + sổ tay phương pháp
Đầu ra: steps của mỗi subproblem

Chạy song song: Solver và Draftsman cùng nhận latex, không phụ thuộc nhau
"""

from __future__ import annotations

from pathlib import Path

from ..state import ProblemState
from .base import Agent

PROMPT = Path(__file__).resolve().parents[4].parent / "prompts" / "solver.md"


class SolverAgent(Agent):
    role = "solver"

    def run(self, state: ProblemState) -> ProblemState:
        raise NotImplementedError(
            "TODO: nạp prompts/solver.md, gọi self.llm.complete(), ghi kết quả vào state"
        )
