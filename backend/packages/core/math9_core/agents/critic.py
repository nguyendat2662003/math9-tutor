"""Agent Critic: chuyển kết quả Verifier thành thông điệp sửa lỗi cho Solver.

Phiên bản này KHÔNG gọi LLM: Verifier đã nói chính xác sai ở đâu (vị từ nào
sai, từ khóa nào vượt cấp, điểm nào không có trên hình). Diễn đạt lại bằng LLM
chỉ thêm chi phí mà không thêm thông tin. Nâng cấp lên LLM khi cần phân tích
lỗi lập luận mà Verifier không bắt được.
"""

from __future__ import annotations

from ..state import ProblemState
from .base import Agent


class CriticAgent(Agent):
    role = "critic"

    def run(self, state: ProblemState) -> ProblemState:
        from ..graph import retry_prompt

        state.verification.detail["retry_feedback"] = retry_prompt(state)
        return state
