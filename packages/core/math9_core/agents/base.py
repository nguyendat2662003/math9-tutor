"""Giao diện chung cho mọi agent. Agent đọc và ghi ProblemState, không trả text thô."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Template

from ..llm.client import LLMClient, LLMResponse, pick_model
from ..state import ProblemState

PROMPT_DIR = Path(__file__).resolve().parents[4] / "prompts"
log = logging.getLogger(__name__)


class Agent(ABC):
    role: str = "agent"
    prompt_file: str | None = None

    def __init__(self, llm: LLMClient | None = None, model: str | None = None):
        self.llm = llm
        self.model = model          # ghi đè MODEL_POLICY khi chỉ có một model khả dụng
        self._template: Template | None = None

    @abstractmethod
    def run(self, state: ProblemState) -> ProblemState: ...

    def __call__(self, state: ProblemState) -> ProblemState:
        t0 = time.time()
        out = self.run(state)
        out.log(
            agent=self.role,
            model=self.model_for(state),
            ms=int((time.time() - t0) * 1000),
        )
        return out

    # -- tiện ích dùng chung -------------------------------------------------

    def model_for(self, state: ProblemState) -> str:
        return self.model or pick_model(self.role, state.difficulty)

    def render(self, **ctx) -> str:
        if self._template is None:
            if not self.prompt_file:
                raise RuntimeError(f"Agent {self.role} chưa khai báo prompt_file")
            self._template = Template((PROMPT_DIR / self.prompt_file).read_text(encoding="utf-8"))
        return self._template.render(**ctx)

    def complete(self, state: ProblemState, user: str, *, system: str, max_tokens: int = 4000,
                 temperature: float = 0.2) -> LLMResponse:
        if self.llm is None:
            raise RuntimeError(f"Agent {self.role} chưa được gắn LLM client")
        resp = self.llm.complete(system=system, user=user, model=self.model_for(state),
                                 max_tokens=max_tokens, temperature=temperature)
        state.log(agent=f"{self.role}.llm", model=resp.model, tokens_in=resp.tokens_in, tokens_out=resp.tokens_out)
        return resp

    @staticmethod
    def parse_json(resp: LLMResponse) -> dict:
        """Bóc JSON kể cả khi model bọc trong ```json hoặc kèm text thừa."""
        try:
            return resp.json()
        except json.JSONDecodeError:
            t = resp.text
            a, b = t.find("{"), t.rfind("}")
            if a >= 0 and b > a:
                return json.loads(t[a:b + 1])
            raise
