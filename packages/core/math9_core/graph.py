"""Orchestrator: đồ thị CỐ ĐỊNH, không ủy quyền động.

Luồng biết trước, không agent nào tự quyết gọi agent khác. Toán lớp 9 là miền
đóng, quy trình xử lý một bài luôn giống nhau — không cần agent "suy nghĩ xem
tiếp theo làm gì", và tránh được rủi ro cùng chi phí của ủy quyền động.

    Parser -> Router -> {Solver ∥ Draftsman} -> Verifier -> [Critic] -> Render

Vòng lặp Solver <-> Verifier giới hạn CỨNG 2 lần. Sau đó trả lời một phần
kèm nhãn độ tin cậy, không cố nữa.
"""

from __future__ import annotations

import contextvars
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from math9_curriculum.guardrail import check as guardrail_check
from math9_curriculum.guardrail import feedback_message
from math9_curriculum.loader import curriculum
from math9_geometry.layout import best_figure
from math9_geometry.primitives import GeometryError
from math9_geometry.render_svg import render
from math9_verifier.geometry import cross_check_solution, verify
from math9_verifier.lemma_finder import find_lemmas, format_for_prompt
from math9_verifier.predicates import Predicate

from . import tracing
from .agents.critic import CriticAgent
from .agents.draftsman import DraftsmanAgent
from .agents.parser import ParserAgent
from .agents.pedagogue import PedagogueAgent
from .agents.router import RouterAgent
from .agents.solver import SolverAgent
from .enums import Confidence
from .state import ProblemState

if TYPE_CHECKING:
    from math9_retrieval.service import RagService

    from .llm.client import LLMClient

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
    #: Gọi ở mỗi giai đoạn: on_stage(tên, payload). API dùng để stream SSE.
    on_stage: "Callable[[str, dict], None] | None" = None

    def _emit(self, stage: str, **payload) -> None:
        if self.on_stage:
            self.on_stage(stage, payload)

    # -- luồng chính ------------------------------------------------------

    def run(self, state: ProblemState) -> ProblemState:
        """Một lượt giải = một trace trên Langfuse (nếu bật)."""
        mode = state.mode.value if hasattr(state.mode, "value") else state.mode
        with tracing.attributes(trace_name="giai-bai", tags=[mode]), \
                tracing.observe("giai-bai", kind="chain",
                                input={"de": state.raw_input, "co_anh": bool(state.image_path), "mode": mode}) as root:
            root.set_trace_io(input=state.raw_input or "(ảnh đề)")
            try:
                state = self._run(state)
            finally:
                summary = {
                    "topic": state.topic, "difficulty": state.difficulty, "attempts": state.attempts,
                    "confidence": state.confidence().value,
                    "answers": {sp.label: sp.answer for sp in state.subproblems if sp.answer},
                }
                root.update(output=summary)
                root.set_trace_io(output=summary)
                # Chuyên đề + độ tin cậy chỉ biết lúc cuối: gắn tag lên observation gốc để lọc trên Langfuse
                with tracing.attributes(tags=[t for t in (mode, state.topic, summary["confidence"]) if t]):
                    pass
                url = tracing.trace_url()           # phải lấy khi trace còn mở
        if url:
            log.info("Langfuse trace: %s", url)
        return state

    def _run(self, state: ProblemState) -> ProblemState:
        self._emit("parsing", from_image=bool(state.image_path))
        state = self.parser(state)
        if state.ocr:
            self._emit("parsed", statement=state.latex, note=state.ocr.get("note") or "")
        self._emit("routing")
        state = self.router(state)
        self._emit("routed", topic=state.topic, difficulty=state.difficulty,
                   subproblems=[{"label": sp.label, "goal_type": sp.goal_type} for sp in state.subproblems])
        with tracing.observe("rag", kind="retriever", input={"goal_types": [sp.goal_type for sp in state.subproblems]}) as span:
            self._retrieve(state)      # RAG: nạp chiến lược + bài mẫu vào state
            span.update(output={k: len(v or "") for k, v in (state.retrieved or {}).items()})

        while True:
            self._emit("solving", geometry=state.is_geometry(), attempt=state.attempts)
            state = self._solve_and_draw(state)
            self._emit("verifying")
            with tracing.observe("verifier", kind="evaluator", input={"attempt": state.attempts}) as span:
                state = self._verify(state)
                v = state.verification
                span.update(
                    output={"passed": self._passed(state), "algebra_ok": v.algebra_ok, "geometry_ok": v.geometry_ok,
                            "violations": v.violations, "cross_check": v.cross_check,
                            "geometry": v.detail.get("geometry")},
                    level="DEFAULT" if self._passed(state) else "WARNING",
                )

            if self._passed(state) or state.attempts >= state.max_attempts:
                break

            state.attempts += 1
            log.info("Kiểm chứng thất bại, thử lại lần %d", state.attempts)
            reasons = _short_reasons(state)
            with tracing.observe("giai-lai", input={"lan": state.attempts, "ly_do": reasons}, level="WARNING"):
                pass
            self._emit("retrying", attempt=state.attempts, reasons=reasons)
            state = self.critic(state)
            self._draftsman_feedback(state)
            if state.difficulty >= 3:
                self._attach_lemmas(state)

        self._emit("rendering")
        state = self._render(state)
        if self.enable_hints and state.confidence() != Confidence.LOW:
            self._emit("hinting")
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

        Cả hai chỉ cần đề bài đã chuẩn hóa, không phụ thuộc nhau. Ở lượt giải
        lại, hình đã dựng được và khớp lời giải thì giữ nguyên, chỉ gọi Solver.
        """
        if not state.is_geometry():
            return self.solver(state)
        if state.construction and state.attempts > 0 and not state.verification.cross_check:
            return self.solver(state)

        n0 = len(state.trace)
        # Mỗi luồng một bản sao context để span của Solver/Draftsman nằm dưới trace hiện tại
        with ThreadPoolExecutor(max_workers=2) as ex:
            fs = ex.submit(contextvars.copy_context().run, self.solver, state.model_copy(deep=True))
            fd = ex.submit(contextvars.copy_context().run, self.draftsman, state.model_copy(deep=True))
            solved, drawn = fs.result(), fd.result()

        state.subproblems = solved.subproblems
        state.construction = drawn.construction
        state.entities = drawn.entities or solved.entities
        state.verification.detail.update(solved.verification.detail)
        state.verification.detail.update(drawn.verification.detail)
        state.trace += solved.trace[n0:] + drawn.trace[n0:]
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
                # sai thật khi kiểm bằng số
                "failures": [repr(f.predicate) for f in verdict.failures() if f.error is None],
                # không kiểm được (thường do nhắc tới điểm không có trên hình)
                "unresolved": [f"{f.predicate!r}: {f.error}" for f in verdict.failures() if f.error],
                "build_errors": verdict.build_errors,
            }
            # 4. Đối chiếu chéo lời giải với hình
            v.cross_check = cross_check_solution(
                state.construction, state.referenced_names()
            )
        return state

    def _claims(self, state: ProblemState) -> list[Predicate]:
        """Trích mệnh đề cần kiểm chứng từ trường `predicate` của mỗi bước.

        Predicate sai định dạng (kind lạ, thiếu args) được ghi nhận, không làm
        hỏng cả lượt kiểm chứng.
        """
        out: list[Predicate] = []
        bad: list[str] = []
        for sp in state.subproblems:
            for st in sp.steps:
                if not st.predicate:
                    continue
                try:
                    out.append(Predicate(
                        st.predicate["kind"], [str(a) for a in st.predicate["args"]], _num(st.predicate.get("value")),
                    ))
                except (KeyError, ValueError, TypeError) as e:
                    bad.append(f"{st.id}: {e}")
        if bad:
            state.verification.detail["bad_predicates"] = bad
        return out

    def _draftsman_feedback(self, state: ProblemState) -> None:
        """Lời giải dùng điểm phụ mà hình chưa có -> bảo Draftsman dựng thêm, kèm
        các câu trong lời giải định nghĩa điểm đó."""
        missing = [m.split("'")[1] for m in state.verification.cross_check if "nhắc tới '" in m]
        if not missing or not state.construction:
            state.verification.detail.pop("draftsman_feedback", None)
            return
        lines = [f"Lời giải cần thêm các điểm chưa có trên hình: {', '.join(missing)}. "
                 "Hãy giữ nguyên kịch bản cũ và DỰNG THÊM các điểm này theo mô tả sau:"]
        for sp in state.subproblems:
            for st in sp.steps:
                if any(m in st.refs or m in st.highlight or f" {m} " in f" {st.claim} " for m in missing):
                    lines.append(f"- {st.claim} ({st.justification})")
        lines.append("Kịch bản cũ:\n" + state.construction.model_dump_json())
        state.verification.detail["draftsman_feedback"] = "\n".join(lines)

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
        if state.is_geometry() and state.construction is None:
            return False
        return (
            not v.violations
            and not v.cross_check
            and v.algebra_ok is not False
            and v.geometry_ok is not False
        )


def _short_reasons(state: ProblemState) -> list[str]:
    v = state.verification
    out = [x["detail"] for x in v.violations]
    out += v.detail.get("geometry", {}).get("failures", [])
    out += v.cross_check
    if v.algebra_ok is False:
        out.append("SymPy giải lại không khớp đáp án")
    return out[:6]


def _num(v) -> float | None:
    """value của predicate: số, hoặc biểu thức như 'sqrt(2)', '1/2' -> float."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    import sympy as sp

    return float(sp.sympify(str(v).replace("√", "sqrt").replace("^", "**")))


def build_pipeline(
    llm: "LLMClient | None" = None, model: str | None = None, rag: bool = True,
    require_reviewed: bool = True, enable_hints: bool = True,
    on_stage: "Callable[[str, dict], None] | None" = None,
) -> Pipeline:
    """Dựng Pipeline hoàn chỉnh từ biến môi trường.

    `model` ghi đè MODEL_POLICY cho mọi agent — dùng khi chỉ có một model khả
    dụng (giai đoạn hiện tại). Khi có model local, bỏ tham số này để chính sách
    định tuyến theo độ khó có hiệu lực.
    """
    from .llm.client import client_from_env, default_model

    llm = llm or client_from_env()
    model = model or default_model()
    rag_service = None
    if rag:
        from math9_retrieval.service import RagService

        rag_service = RagService(require_reviewed=require_reviewed)
    return Pipeline(
        parser=ParserAgent(llm, model),
        router=RouterAgent(llm, model),
        solver=SolverAgent(llm, model),
        draftsman=DraftsmanAgent(llm, model),
        critic=CriticAgent(llm, model),
        pedagogue=PedagogueAgent(llm, model),
        rag=rag_service,
        enable_hints=enable_hints,
        on_stage=on_stage,
    )


def retry_prompt(state: ProblemState) -> str:
    """Thông điệp gửi lại Solver ở vòng lặp thứ hai."""
    parts = []
    v = state.verification
    if v.violations:
        parts.append(feedback_message([type("V", (), x)() for x in v.violations]))
    if v.detail.get("algebra", {}).get("results"):
        wrong = [r for r in v.detail["algebra"]["results"] if not r.get("ok")]
        if wrong:
            parts.append("SymPy giải lại không khớp với đáp án của bạn: " + json.dumps(wrong, ensure_ascii=False))
    if v.detail.get("draftsman_error"):
        parts.append("Không dựng được hình từ đề: " + v.detail["draftsman_error"])
    if v.detail.get("geometry", {}).get("failures"):
        parts.append(
            "Các kết luận sau KHÔNG đúng khi kiểm tra bằng số trên nhiều cấu hình: "
            + ", ".join(v.detail["geometry"]["failures"])
        )
    if v.detail.get("geometry", {}).get("unresolved"):
        parts.append(
            "Các kết luận sau KHÔNG kiểm chứng được vì nhắc tới đối tượng không có trên hình "
            "(hình sẽ được dựng lại có thêm các điểm này; nếu vẫn cần, hãy định nghĩa rõ cách dựng "
            "chúng trong claim): " + ", ".join(v.detail["geometry"]["unresolved"])
        )
    if v.cross_check:
        parts.append("Lời giải và hình vẽ không khớp: " + "; ".join(v.cross_check))
    if v.detail.get("lemma_prompt"):
        parts.append(
            "Các mệnh đề sau đã được kiểm chứng đúng, hãy dùng làm mốc trung gian:\n"
            + v.detail["lemma_prompt"]
        )
    return "\n\n".join(parts)
