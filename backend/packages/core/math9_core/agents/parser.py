"""Agent Parser: ảnh chụp đề -> văn bản đề bài (VLM). Chỉ chạy khi đầu vào là ảnh.

Với đầu vào text, Pipeline bỏ qua bước gọi model và dùng thẳng raw_input.

Dùng VLM đa năng thay vì OCR chuyên dụng: đề toán lớp 9 có nhiều ký hiệu và bố
cục nhiều ý, VLM giữ được cấu trúc a), b), c) tốt hơn.
"""

from __future__ import annotations

import logging

from ..state import ProblemState
from .base import Agent

log = logging.getLogger(__name__)


class ImageNotMathError(ValueError):
    """Ảnh không phải đề toán — báo lại người dùng thay vì giải bừa."""


class ParserAgent(Agent):
    role = "parser"
    prompt_file = "parser.md"

    def run(self, state: ProblemState) -> ProblemState:
        if not state.image_path:
            state.latex = state.latex or state.raw_input
            return state

        user = self.render(user_text=state.raw_input.strip() or None)
        data = self.parse_json(self.complete(
            state, user,
            system="Bạn chép lại đề toán từ ảnh. Chỉ trả JSON, không giải bài.",
            max_tokens=6000, temperature=0.0, images=[state.image_path],
        ))

        statement = str(data.get("statement") or "").strip()
        if not data.get("is_math", True) or not statement:
            raise ImageNotMathError(
                data.get("note") or "Không đọc được đề toán trong ảnh. Hãy chụp rõ hơn hoặc gõ đề bằng tay."
            )

        state.latex = statement
        if not state.raw_input.strip():
            state.raw_input = statement
        state.ocr = {
            "statement": statement,
            "has_figure": bool(data.get("has_figure")),
            "figure_note": str(data.get("figure_note") or ""),
            "note": str(data.get("note") or ""),
        }
        log.info("Parser đọc được %d ký tự từ ảnh", len(statement))
        return state
