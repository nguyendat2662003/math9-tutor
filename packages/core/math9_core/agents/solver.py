"""Agent Solver: latex + guardrail + sổ tay -> steps có căn cứ và predicate cho từng ý.

Chạy song song với Draftsman: cả hai chỉ cần đề đã chuẩn hóa.
"""

from __future__ import annotations

import logging

from math9_curriculum.loader import curriculum

from ..state import ProblemState, Step, SubProblem
from .base import Agent

log = logging.getLogger(__name__)


class SolverAgent(Agent):
    role = "solver"
    prompt_file = "solver.md"

    def run(self, state: ProblemState) -> ProblemState:
        topic = curriculum().get(state.topic) if state.topic else None
        user = self.render(
            curriculum_block=topic.prompt_block(state.mode) if topic else "(chưa xác định chuyên đề)",
            method_notes=state.retrieved.get("method_notes") or "(không có)",
            worked_examples=state.retrieved.get("worked_examples") or "(không có)",
            lemmas=state.verification.detail.get("lemma_prompt"),
            retry_feedback=state.verification.detail.get("retry_feedback"),
            subproblems="\n".join(
                f"{sp.label}) {sp.statement}  [mục tiêu: {sp.goal_type or '?'}]" for sp in state.subproblems
            ),
            latex=state.latex or state.raw_input,
        )
        data = self.parse_json(self.complete(
            state, user, system="Bạn là giáo viên Toán THCS giàu kinh nghiệm luyện thi vào 10. Chỉ trả JSON.",
            max_tokens=6000,
        ))

        by_label = {sp.label: sp for sp in state.subproblems}
        for i, item in enumerate(data.get("subproblems") or []):
            label = str(item.get("label") or chr(ord("a") + i))
            sp = by_label.get(label)
            if sp is None:
                sp = SubProblem(label=label, statement=item.get("statement", ""))
                state.subproblems.append(sp)
                by_label[label] = sp
            sp.steps = [
                Step(
                    id=str(s.get("id") or f"{label}{j + 1}"),
                    claim=str(s.get("claim", "")),
                    justification=str(s.get("justification", "")),
                    refs=[str(r) for r in s.get("refs", [])],
                    highlight=[str(h) for h in s.get("highlight", [])],
                    predicate=s.get("predicate") or None,
                )
                for j, s in enumerate(item.get("steps") or [])
            ]
            sp.answer = item.get("answer")

        state.verification.detail["algebra_checks"] = data.get("algebra_checks") or []
        return state
