"""ProblemState — object trạng thái duy nhất chảy qua toàn bộ đồ thị agent.

Điểm chết của multi-agent là mất ngữ cảnh khi truyền qua lại. Cách chữa: mọi
agent đọc và ghi vào ĐÂY, không nhận text thô từ agent trước.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from math9_curriculum.schema import Mode
from math9_geometry.dsl import Construction
from pydantic import BaseModel, Field

from .enums import Confidence, GoalType


class Entity(BaseModel):
    name: str
    kind: Literal["point", "line", "segment", "circle", "angle", "arc", "polygon"]
    role: Literal["given", "constructed", "variable", "target"] = "given"
    note: str | None = None


class Step(BaseModel):
    id: str
    claim: str                                  # điều được khẳng định
    justification: str                          # căn cứ — guardrail đối chiếu trường này
    refs: list[str] = Field(default_factory=list)
    highlight: list[str] = Field(default_factory=list)  # đối tượng cần tô sáng trên hình
    predicate: dict[str, Any] | None = None     # {kind, args, value?} — Verifier kiểm bằng số


class SubProblem(BaseModel):
    """Một ý của đề bài (a, b, c...). Mỗi ý có goal_type và độ khó riêng."""

    label: str
    statement: str
    goal_type: GoalType | None = None
    difficulty: int = 1
    steps: list[Step] = Field(default_factory=list)
    answer: str | None = None
    confidence: Confidence = Confidence.LOW


class Verification(BaseModel):
    algebra_ok: bool | None = None
    geometry_ok: bool | None = None
    violations: list[dict[str, Any]] = Field(default_factory=list)
    lemmas_found: list[str] = Field(default_factory=list)
    cross_check: list[str] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)


class TraceEntry(BaseModel):
    agent: str
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    ms: int = 0
    note: str | None = None


class ProblemState(BaseModel):
    # --- đầu vào ---
    raw_input: str
    image_path: str | None = None
    latex: str | None = None
    mode: Mode = Mode.EXAM10
    #: Kết quả đọc ảnh của Parser: {statement, has_figure, figure_note, note}
    ocr: dict[str, Any] | None = None

    # --- phân loại ---
    topic: str | None = None
    subtopics: list[str] = Field(default_factory=list)
    difficulty: int = 1
    router_confidence: float = 0.0
    router_alternatives: list[str] = Field(default_factory=list)

    # --- cấu trúc bài ---
    entities: list[Entity] = Field(default_factory=list)
    subproblems: list[SubProblem] = Field(default_factory=list)

    # --- hình ---
    construction: Construction | None = None
    figure_svg: str | None = None
    figure_quality: float | None = None
    figure_seed: int | None = None

    # --- kiểm chứng ---
    verification: Verification = Field(default_factory=Verification)

    # --- RAG ---
    retrieved: dict[str, str] = Field(default_factory=dict)

    # --- sư phạm ---
    hints: list[str] = Field(default_factory=list)

    # --- điều khiển ---
    attempts: int = 0
    max_attempts: int = 2
    trace: list[TraceEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def confidence(self) -> Confidence:
        v = self.verification
        if v.violations:
            return Confidence.PARTIAL
        if v.algebra_ok is False or v.geometry_ok is False:
            return Confidence.PARTIAL
        if v.algebra_ok is None and v.geometry_ok is None:
            return Confidence.LOW
        return Confidence.HIGH

    def is_geometry(self) -> bool:
        return bool(self.topic and self.topic.startswith("GEO"))

    def referenced_names(self) -> set[str]:
        out: set[str] = set()
        for sp in self.subproblems:
            for st in sp.steps:
                out |= set(st.refs) | set(st.highlight)
        return out

    def log(self, **kw) -> None:
        self.trace.append(TraceEntry(**kw))
