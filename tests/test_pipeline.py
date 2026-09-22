"""Kiểm thử Pipeline end-to-end với LLM giả — không cần mạng, tất định.

LLM giả trả JSON đóng sẵn theo vai trò (nhận diện qua nội dung prompt). Mục
đích: chứng minh đồ thị Router → RAG → Solver ∥ Draftsman → Verifier → Critic →
Render → Pedagogue chạy đúng và vòng lặp giải lại hoạt động.
"""

import json

import pytest
from math9_core.agents.critic import CriticAgent
from math9_core.agents.draftsman import DraftsmanAgent
from math9_core.agents.parser import ParserAgent
from math9_core.agents.pedagogue import PedagogueAgent
from math9_core.agents.router import RouterAgent
from math9_core.agents.solver import SolverAgent
from math9_core.enums import Confidence
from math9_core.graph import Pipeline
from math9_core.llm.client import LLMClient, LLMResponse
from math9_core.state import ProblemState

STATEMENT = (
    "Cho đường tròn (O) và điểm A nằm ngoài đường tròn. Kẻ hai tiếp tuyến AB, AC (B, C là tiếp điểm). "
    "Gọi H là giao điểm của OA và BC. a) Chứng minh ABOC nội tiếp. b) Chứng minh OA vuông góc BC."
)

ROUTER = {
    "topic": "GEO-9", "subtopics": ["GEO-5"], "confidence": 0.9, "alternatives": [],
    "subproblems": [
        {"label": "a", "statement": "Chứng minh ABOC nội tiếp", "goal_type": "prove_concyclic", "difficulty": 1},
        {"label": "b", "statement": "Chứng minh OA vuông góc BC", "goal_type": "prove_perpendicular", "difficulty": 1},
    ],
}

DRAFT = {"ops": [
    {"op": "free", "name": "O"},
    {"op": "circle_center_radius", "name": "w", "args": ["O"], "params": {"radius": 2}},
    {"op": "free", "name": "A", "params": {"outside": "w"}},
    {"op": "tangent_from", "name": "t1", "args": ["w", "A"], "params": {"branch": 0, "touch_point": "B"}},
    {"op": "tangent_from", "name": "t2", "args": ["w", "A"], "params": {"branch": 1, "touch_point": "C"}},
    {"op": "intersect", "name": "H", "args": ["line:OA", "line:BC"]},
]}


def solver_output(wrong: bool) -> dict:
    return {"subproblems": [
        {"label": "a", "steps": [{"id": "a1", "claim": "ABOC nội tiếp", "justification": "tổng hai góc đối bằng 180 độ",
                                  "refs": ["A", "B", "O", "C"], "highlight": ["A", "B", "O", "C"],
                                  "predicate": {"kind": "concyclic", "args": ["A", "B", "O", "C"]}}]},
        {"label": "b", "steps": [{"id": "b1", "claim": "OA vuông góc BC" if not wrong else "A, B, C thẳng hàng",
                                  "justification": "OA là trung trực của BC",
                                  "refs": ["O", "A", "B", "C"],
                                  "predicate": ({"kind": "collinear", "args": ["A", "B", "C"]} if wrong
                                                else {"kind": "perpendicular", "args": ["O", "A", "B", "C"]})}]},
    ], "algebra_checks": []}


class FakeLLM(LLMClient):
    """Trả lời theo vai trò; Solver sai ở lượt đầu, đúng ở lượt hai."""

    def __init__(self):
        self.calls: list[str] = []
        self.solver_calls = 0

    def complete(self, system, user, *, model, max_tokens=4000, temperature=0.2, thinking=False):
        if "phân loại" in system:
            role, out = "router", ROUTER
        elif "dựng hình" in system:
            role, out = "draftsman", DRAFT
        elif "gợi mở" in system:
            role, out = "pedagogue", {"hints": ["Em nhìn vào hai góc ABO và ACO xem?"]}
        else:
            role = "solver"
            self.solver_calls += 1
            out = solver_output(wrong=self.solver_calls == 1)
            assert ("Lần giải trước có lỗi" in user) == (self.solver_calls > 1)
        self.calls.append(role)
        return LLMResponse(text=json.dumps(out, ensure_ascii=False), model=model)


@pytest.fixture
def pipeline():
    llm = FakeLLM()
    p = Pipeline(
        parser=ParserAgent(llm, "fake"), router=RouterAgent(llm, "fake"), solver=SolverAgent(llm, "fake"),
        draftsman=DraftsmanAgent(llm, "fake"), critic=CriticAgent(llm, "fake"), pedagogue=PedagogueAgent(llm, "fake"),
        rag=None,
    )
    return p, llm


def test_pipeline_retries_and_verifies(pipeline):
    p, llm = pipeline
    s = p.run(ProblemState(raw_input=STATEMENT))

    assert s.topic == "GEO-9"
    assert [sp.goal_type for sp in s.subproblems] == ["prove_concyclic", "prove_perpendicular"]
    # Lượt 1 Verifier bắt được vị từ sai -> Critic -> giải lại -> lượt 2 đúng
    assert llm.solver_calls == 2
    assert s.attempts == 1
    assert s.verification.geometry_ok is True
    assert s.verification.detail["geometry"]["n_configs"] == 5
    # Hình chỉ dựng một lần (lượt 2 giữ nguyên vì lời giải và hình khớp)
    assert llm.calls.count("draftsman") == 1
    assert s.figure_svg and s.figure_svg.startswith("<svg")
    assert s.confidence() == Confidence.HIGH
    assert s.hints == ["Em nhìn vào hai góc ABO và ACO xem?"]
    assert any(t.agent == "solver.llm" for t in s.trace)


def test_pipeline_gives_up_after_max_attempts():
    class AlwaysWrong(FakeLLM):
        def complete(self, system, user, **kw):
            if "gợi mở" not in system and "phân loại" not in system and "dựng hình" not in system:
                self.solver_calls += 1
                return LLMResponse(text=json.dumps(solver_output(wrong=True)), model="fake")
            return super().complete(system, user, **kw)

    llm = AlwaysWrong()
    p = Pipeline(parser=ParserAgent(llm), router=RouterAgent(llm), solver=SolverAgent(llm),
                 draftsman=DraftsmanAgent(llm), critic=CriticAgent(llm), pedagogue=PedagogueAgent(llm), rag=None)
    s = p.run(ProblemState(raw_input=STATEMENT))
    assert llm.solver_calls == 3            # lượt đầu + 2 lần giải lại
    assert s.attempts == 2
    assert s.confidence() == Confidence.PARTIAL
    assert "collinear(A, B, C)" in s.verification.detail["geometry"]["failures"]
