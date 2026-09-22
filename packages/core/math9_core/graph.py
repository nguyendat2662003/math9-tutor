"""Orchestrator: đồ thị CỐ ĐỊNH, không ủy quyền động.

Luồng biết trước, không agent nào tự quyết gọi agent khác. Toán lớp 9 là miền
đóng, quy trình xử lý một bài luôn giống nhau — không cần agent "suy nghĩ xem
tiếp theo làm gì", và tránh được rủi ro cùng chi phí của ủy quyền động.

    Parser -> Router -> {Solver ∥ Draftsman} -> Verifier -> [Critic] -> Render

Vòng lặp Solver <-> Verifier giới hạn CỨNG 2 lần. Sau đó trả lời một phần
kèm nhãn độ tin cậy, không cố nữa.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from math9_curriculum.guardrail import check as guardrail_check
from math9_curriculum.guardrail import feedback_message
from math9_curriculum.loader import curriculum
from math9_geometry.layout import best_figure
from math9_geometry.primitives import GeometryError
from math9_geometry.render_svg import render
from math9_verifier.geometry import cross_check_solution, verify
from math9_verifier.lemma_finder import find_lemmas, format_for_prompt
from math9_verifier.predicates import Predicate

from .agents.critic import CriticAgent
from .agents.draftsman import DraftsmanAgent
from .agents.parser import ParserAgent
from .agents.pedagogue import PedagogueAgent
from .agents.router import RouterAgent
from .agents.solver import SolverAgent
from .enums import Confidence
from .state import ProblemState

log = logging.getLogger(__name__)


@dataclass
class Pipeline:
    parser: ParserAgent
    router: RouterAgent
    solver: SolverAgent
    draftsman: DraftsmanAgent
    critic: CriticAgent
    pedagogue: PedagogueAgent
    rag: "RagService | None" = None
    enable_hints: bool = True

    # -- luồng chính ------------------------------------------------------

    def run(self, state: ProblemState) -> ProblemState:
        state = self.parser(state) if state.image_path else state
        state = self.router(state)
        self._retrieve(state)          # RAG: nạp chiến lược + bài mẫu vào state

        while True:
            state = self._solve_and_draw(state)
            state = self._verify(state)

            if self._passed(state) or state.attempts >= state.max_attempts:
                break

            state.attempts += 1
            log.info("Kiểm chứng thất bại, thử lại lần %d", state.attempts)
            state = self.critic(state)
            if state.difficulty >= 3:
                self._attach_lemmas(state)

        state = self._render(state)
        if self.enable_hints and state.confidence() != Confidence.LOW:
            state = self.pedagogue(state)
        return state

    # -- các khối ---------------------------------------------------------

    def _retrieve(self, state: ProblemState) -> None:
        """RAG: nạp sổ tay chiến lược (theo goal_type) và bài giải mẫu vào state.

        Đây là chỗ RAG được dùng thật. Sổ tay truy theo goal_type là chính; bài
        mẫu truy theo độ tương đồng để bắt chước văn phong. Kết quả đi vào prompt
        Solver qua state.retrieved.
        """
        if not self.rag:
            return
        query = state.latex or state.raw_input
        # Gom goal_type của các ý — bài nhiều ý có thể cần nhiều sổ tay
        goal_types = [
            sp.goal_type for sp in state.subproblems if sp.goal_type
        ] or [None]
        merged_notes, merged_examples = [], []
        for gt in dict.fromkeys(goal_types):        # khử trùng, giữ thứ tự
            ctx = self.rag.retrieve(query, gt, state.mode.value if hasattr(state.mode, "value") else state.mode)
            if ctx.method_notes:
                merged_notes.append(ctx.method_notes)
            if ctx.worked_examples:
                merged_examples.append(ctx.worked_examples)
        state.retrieved = {
            "method_notes": "\n\n===\n\n".join(dict.fromkeys(merged_notes)),
            "worked_examples": "\n\n===\n\n".join(dict.fromkeys(merged_examples)),
        }

    def _solve_and_draw(self, state: ProblemState) -> ProblemState:
        """Solver và Draftsman chạy SONG SONG — tiết kiệm khoảng 40% độ trễ.

        Cả hai chỉ cần đề bài đã chuẩn hóa, không phụ thuộc nhau.
        """
        if not state.is_geometry():
            return self.solver(state)

        with ThreadPoolExecutor(max_workers=2) as ex:
            fs = ex.submit(self.solver, state.model_copy(deep=True))
            fd = ex.submit(self.draftsman, state.model_copy(deep=True))
            solved, drawn = fs.result(), fd.result()

        state.subproblems = solved.subproblems
        state.construction = drawn.construction
        state.entities = drawn.entities or solved.entities
        state.trace += solved.trace + drawn.trace
        return state

    def _verify(self, state: ProblemState) -> ProblemState:
        """Kiểm chứng bằng CODE, không bằng LLM.

        Nếu để một LLM kiểm tra lời giải của LLM khác, hai bên sẽ sai giống
        nhau. Giá trị nằm ở chỗ dùng cơ chế hoàn toàn khác.
        """
        v = state.verification
        topic = curriculum().get(state.topic) if state.topic else None

        # 1. Guardrail chương trình
        if topic:
            text = "\n".join(
                f"{s.claim} {s.justification}"
                for sp in state.subproblems for s in sp.steps
            )
            steps = [s.model_dump() for sp in state.subproblems for s in sp.steps]
            v.violations = [
                x.__dict__ for x in guardrail_check(text, steps, topic, state.mode)
            ]

        # 2. Đại số — SymPy giải lại độc lập
        if not state.is_geometry():
            from math9_verifier.algebra import verify_algebra

            v.algebra_ok, v.detail["algebra"] = verify_algebra(state)

        # 3. Hình học — dựng lại nhiều cấu hình, kiểm tra vị từ bằng số
        if state.is_geometry() and state.construction:
            claims = self._claims(state)
            verdict = verify(state.construction, claims)
            v.geometry_ok = verdict.ok
            v.detail["geometry"] = {
                "n_configs": verdict.n_configs,
                "failures": [repr(f.predicate) for f in verdict.failures()],
                "build_errors": verdict.build_errors,
            }
            # 4. Đối chiếu chéo lời giải với hình
            v.cross_check = cross_check_solution(
                state.construction, state.referenced_names()
            )
        return state

    def _claims(self, state: ProblemState) -> list[Predicate]:
        """Trích mệnh đề cần kiểm chứng từ lời giải.

        Trong bản đầy đủ, Solver xuất kèm trường `predicate` cho mỗi kết luận.
        """
        out: list[Predicate] = []
        for sp in state.subproblems:
            for st in sp.steps:
                p = getattr(st, "predicate", None)
                if p:
                    out.append(Predicate(**p))
        return out

    def _attach_lemmas(self, state: ProblemState) -> None:
        """Bài mức 3: dò bổ đề bằng tọa độ để bẻ bài khó thành chuỗi bài dễ."""
        if not state.construction:
            return
        try:
            lemmas = find_lemmas(state.construction, limit=15)
        except GeometryError:
            return
        state.verification.lemmas_found = [repr(x) for x in lemmas]
        state.verification.detail["lemma_prompt"] = format_for_prompt(lemmas)

    def _render(self, state: ProblemState) -> ProblemState:
        if not state.construction:
            return state
        try:
            fig, q = best_figure(state.construction)
        except GeometryError as e:
            state.verification.detail["render_error"] = str(e)
            return state
        state.figure_svg = render(fig)
        state.figure_quality = q.score
        state.figure_seed = fig.seed
        return state

    @staticmethod
    def _passed(state: ProblemState) -> bool:
        v = state.verification
        return (
            not v.violations
            and not v.cross_check
            and v.algebra_ok is not False
            and v.geometry_ok is not False
        )


def retry_prompt(state: ProblemState) -> str:
    """Thông điệp gửi lại Solver ở vòng lặp thứ hai."""
    parts = []
    v = state.verification
    if v.violations:
        parts.append(feedback_message([type("V", (), x)() for x in v.violations]))
    if v.detail.get("geometry", {}).get("failures"):
        parts.append(
            "Các kết luận sau KHÔNG đúng khi kiểm tra bằng số trên nhiều cấu hình: "
            + ", ".join(v.detail["geometry"]["failures"])
        )
    if v.cross_check:
        parts.append("Lời giải và hình vẽ không khớp: " + "; ".join(v.cross_check))
    if v.detail.get("lemma_prompt"):
        parts.append(
            "Các mệnh đề sau đã được kiểm chứng đúng, hãy dùng làm mốc trung gian:\n"
            + v.detail["lemma_prompt"]
        )
    return "\n\n".join(parts)
