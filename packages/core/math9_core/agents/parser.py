"""Agent Parser: ảnh -> latex (OCR/VLM). Chỉ chạy khi đầu vào là ảnh.

Với đầu vào text, Pipeline bỏ qua agent này và dùng thẳng raw_input.
"""

from __future__ import annotations

from ..state import ProblemState
from .base import Agent


class ParserAgent(Agent):
    role = "parser"

    def run(self, state: ProblemState) -> ProblemState:
        if not state.image_path:
            state.latex = state.latex or state.raw_input
            return state
        raise NotImplementedError("Đầu vào ảnh: nối Mathpix (math9_ingest.extract.ocr) hoặc VLM tại đây")
