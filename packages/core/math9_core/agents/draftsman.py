"""Agent Draftsman: latex -> kịch bản dựng hình (DSL). Không bao giờ sinh tọa độ.

Kịch bản sai (tham chiếu chưa dựng, suy biến...) được gửi lại cho LLM sửa,
tối đa MAX_ATTEMPTS lượt — vòng lặp nội bộ, độc lập với vòng Solver↔Verifier.
"""

from __future__ import annotations

import json
import logging

from math9_geometry.construct import Figure, build
from math9_geometry.dsl import Construction, op_catalog, validate_ops
from math9_geometry.primitives import Circle, GeometryError, Line, Point, Segment

from ..state import Entity, ProblemState
from .base import Agent

log = logging.getLogger(__name__)
MAX_ATTEMPTS = 2


def try_build(raw: dict) -> tuple[Construction | None, str]:
    """(construction, lỗi). Lỗi rỗng nghĩa là dựng được ít nhất một cấu hình."""
    try:
        c = Construction.model_validate(raw)
    except Exception as e:
        return None, f"JSON không đúng schema: {e}"
    errs = validate_ops(c.ops)
    if errs:
        return None, "Kịch bản không hợp lệ:\n" + "\n".join(f"- {x}" for x in errs)
    try:
        build(c, seed=1)
    except GeometryError as e:
        return None, f"Engine không dựng được: {e}"
    except Exception as e:              # tham số lạ (branch không phải số, ratio thiếu value...)
        return None, f"Engine lỗi khi dựng ({type(e).__name__}): {e}"
    return c, ""


def entities_from(fig: Figure) -> list[Entity]:
    kind = {Point: "point", Line: "line", Segment: "segment", Circle: "circle"}
    return [Entity(name=n, kind=kind[type(o)], role="constructed") for n, o in fig.objects.items() if type(o) in kind]


class DraftsmanAgent(Agent):
    role = "draftsman"
    prompt_file = "draftsman.md"

    def run(self, state: ProblemState) -> ProblemState:
        feedback, raw = state.verification.detail.get("draftsman_feedback", ""), {}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            user = self.render(op_catalog=op_catalog(), latex=state.latex or state.raw_input, retry_feedback=feedback)
            try:
                raw = self.parse_json(self.complete(
                    state, user, system="Bạn là kỹ sư dựng hình cho phần mềm hình học. Chỉ trả JSON hợp lệ.",
                    max_tokens=12000,
                ))
            except Exception as e:      # LLM rỗng, JSON hỏng, lỗi mạng: tính là một lượt hỏng
                raw, err = {}, f"Không nhận được kịch bản hợp lệ: {e}"
            else:
                c, err = try_build(raw)
                if c:
                    state.construction = c
                    state.entities = entities_from(build(c, seed=1))
                    state.verification.detail.pop("draftsman_error", None)
                    return state
            log.info("Draftsman lượt %d lỗi: %s", attempt, err.splitlines()[0])
            feedback = err + "\n\nKịch bản đã gửi:\n" + json.dumps(raw, ensure_ascii=False)

        state.verification.detail["draftsman_error"] = feedback.split("\n\nKịch bản")[0]
        return state
