"""Giao diện chung cho mọi agent. Agent đọc và ghi ProblemState, không trả text thô."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from ..llm.client import LLMClient, pick_model
from ..state import ProblemState


class Agent(ABC):
    role: str = "agent"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm

    @abstractmethod
    def run(self, state: ProblemState) -> ProblemState: ...

    def __call__(self, state: ProblemState) -> ProblemState:
        t0 = time.time()
        out = self.run(state)
        out.log(
            agent=self.role,
            model=pick_model(self.role, state.difficulty),
            ms=int((time.time() - t0) * 1000),
        )
        return out
