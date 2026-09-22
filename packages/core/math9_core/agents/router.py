"""Agent Router: latex -> topic, difficulty, goal_type cho từng ý.

Chỉ cần danh mục nhãn (~600 token), không cần SGK. Tách riêng từng ý vì ý sau
thường khó hơn hẳn ý trước.
"""

from __future__ import annotations

import logging

from math9_curriculum.loader import curriculum

from ..enums import GOAL_TYPE_VI
from ..state import ProblemState, SubProblem
from .base import Agent

log = logging.getLogger(__name__)


class RouterAgent(Agent):
    role = "router"
    prompt_file = "router.md"

    def run(self, state: ProblemState) -> ProblemState:
        cm = curriculum()
        user = self.render(
            topic_catalog=cm.label_catalog(),
            goal_types="\n".join(f"{k}: {v}" for k, v in GOAL_TYPE_VI.items()),
            latex=state.latex or state.raw_input,
        )
        data = self.parse_json(self.complete(
            state, user, system="Bạn phân loại bài toán Toán 9. Chỉ trả JSON.", max_tokens=6000, temperature=0.0,
        ))

        topic = str(data.get("topic", "")).strip()
        if topic not in cm.topics:
            # Router có thể sai mã — thử alternatives, cuối cùng mới đoán theo tiền tố
            alts = [a for a in data.get("alternatives", []) if a in cm.topics]
            topic = alts[0] if alts else next((t for t in cm.topics if t.startswith(topic[:3])), "GEO-9")
            log.warning("Router trả topic không hợp lệ %r -> dùng %s", data.get("topic"), topic)

        state.topic = topic
        state.subtopics = [s for s in data.get("subtopics", []) if s in cm.topics]
        state.router_confidence = float(data.get("confidence", 0.0))
        state.router_alternatives = [a for a in data.get("alternatives", []) if a in cm.topics and a != topic]

        valid_gt = set(GOAL_TYPE_VI)
        subs = []
        for i, sp in enumerate(data.get("subproblems") or []):
            gt = sp.get("goal_type")
            subs.append(SubProblem(
                label=str(sp.get("label") or chr(ord("a") + i)),
                statement=str(sp.get("statement") or ""),
                goal_type=gt if gt in valid_gt else None,
                difficulty=max(1, min(3, int(sp.get("difficulty") or 1))),
            ))
        if not subs:
            subs = [SubProblem(label="a", statement=state.latex or state.raw_input)]
        state.subproblems = subs
        state.difficulty = max(s.difficulty for s in subs)
        return state
