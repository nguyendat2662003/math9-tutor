"""Giao diện chung cho mọi agent. Agent đọc và ghi ProblemState, không trả text thô."""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Template

from .. import tracing
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
        with tracing.observe(self.role, kind="agent", input={"attempt": state.attempts, "topic": state.topic}) as span:
            out = self.run(state)
            span.update(output=self.trace_summary(out))
        out.log(
            agent=self.role,
            model=self.model_for(state),
            ms=int((time.time() - t0) * 1000),
        )
        return out

    def trace_summary(self, state: ProblemState) -> dict:
        """Tóm tắt hiện trên span của agent. Prompt/kết quả đầy đủ nằm ở generation con."""
        return {
            "topic": state.topic, "difficulty": state.difficulty,
            "subproblems": [
                {"label": sp.label, "goal_type": sp.goal_type, "steps": len(sp.steps), "answer": sp.answer}
                for sp in state.subproblems
            ],
        }

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
                 temperature: float = 0.2, images: list[str] | None = None) -> LLMResponse:
        if self.llm is None:
            raise RuntimeError(f"Agent {self.role} chưa được gắn LLM client")
        model = self.model_for(state)
        messages: list[dict] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        if images:
            # Không đẩy ảnh base64 lên Langfuse — chỉ ghi ảnh nào, nặng bao nhiêu
            messages.append({"role": "user", "content": [_image_note(i) for i in images]})
        with tracing.observe(f"{self.role}.llm", kind="generation", model=model, input=messages,
                             model_parameters={"max_tokens": max_tokens, "temperature": temperature}) as gen:
            resp = self.llm.complete(system=system, user=user, model=model,
                                     max_tokens=max_tokens, temperature=temperature, images=images)
            gen.update(model=resp.model or model, output=resp.text,
                       usage_details={"input": resp.tokens_in, "output": resp.tokens_out},
                       metadata={"finish_reason": resp.finish_reason})
        state.log(agent=f"{self.role}.llm", model=resp.model, tokens_in=resp.tokens_in, tokens_out=resp.tokens_out)
        return resp

    @staticmethod
    def parse_json(resp: LLMResponse) -> dict:
        """Bóc JSON kể cả khi model bọc trong ```json, kèm text thừa, hoặc viết
        LaTeX với backslash không hợp lệ (\\sqrt, \\frac...) trong chuỗi."""
        t = resp.text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1].rsplit("```", 1)[0]
        a, b = t.find("{"), t.rfind("}")
        if a >= 0 and b > a:
            t = t[a:b + 1]
        t = _RE_AMBIG.sub(r"\\\\\1", t)
        try:
            return json.loads(t, strict=False)
        except json.JSONDecodeError:
            try:
                return json.loads(_repair_latex_escapes(t), strict=False)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"LLM không trả JSON hợp lệ ({e.msg}); {len(resp.text)} ký tự, "
                    f"đầu: {resp.text[:120]!r} ... cuối: {resp.text[-80:]!r}"
                ) from e


#: Lệnh LaTeX bắt đầu bằng ký tự trùng escape JSON (\b \f \n \r \t \u) — nếu không
#: nhận diện, "\frac" thành form-feed + "rac". Lệnh khác (\sqrt, \cdot...) bắt bằng regex chung.
_LATEX_AMBIGUOUS = (
    "frac", "tfrac", "dfrac", "times", "theta", "tan", "text", "triangle", "to", "top",
    "beta", "bar", "bigcap", "bigcup", "binom", "boldsymbol", "backsim",
    "neq", "ne", "nabla", "not", "nu", "notin",
    "right", "rho", "rightarrow", "Rightarrow",
    "underline", "underbrace", "upsilon",
)
_RE_AMBIG = re.compile(r"\\(" + "|".join(sorted(_LATEX_AMBIGUOUS, key=len, reverse=True)) + r")(?![A-Za-z])")


def _image_note(image: str) -> str:
    s = str(image)
    if s.startswith("data:"):
        return f"[ảnh data URL, {len(s) // 1024} KB]"
    p = Path(s)
    return f"[ảnh {p.name}, {p.stat().st_size // 1024} KB]" if p.exists() else f"[ảnh {p.name}]"


def _repair_latex_escapes(t: str) -> str:
    """\\ theo sau không phải escape JSON hợp lệ -> nhân đôi."""
    return re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", t)
