"""Agent Pedagogue: lời giải đã kiểm chứng -> chuỗi gợi ý từng bước kiểu Socratic.

Chế độ gợi ý là MẶC ĐỊNH của sản phẩm: học sinh thấy gợi ý trước, bấm mới thấy
lời giải. Model nhỏ là đủ — đây là diễn đạt lại, không phải suy luận.
"""

from __future__ import annotations

from ..state import ProblemState
from .base import Agent


class PedagogueAgent(Agent):
    role = "pedagogue"
    prompt_file = "pedagogue.md"

    def run(self, state: ProblemState) -> ProblemState:
        steps_txt = []
        for sp in state.subproblems:
            steps_txt.append(f"Ý {sp.label}) {sp.statement}")
            steps_txt += [f"  - {s.claim} ({s.justification})" for s in sp.steps]
        if not any(sp.steps for sp in state.subproblems):
            return state
        user = self.render(latex=state.latex or state.raw_input, solution="\n".join(steps_txt))
        data = self.parse_json(self.complete(
            state, user, system="Bạn là giáo viên Toán THCS, dạy bằng cách gợi mở. Chỉ trả JSON.", max_tokens=2000,
        ))
        state.hints = [str(h) for h in data.get("hints", []) if str(h).strip()]
        return state
