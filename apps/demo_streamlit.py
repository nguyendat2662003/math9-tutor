"""Demo dựng hình trên Streamlit: đề bài -> LLM sinh kịch bản -> engine -> SVG.

    streamlit run apps/demo_streamlit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))
sys.path.insert(0, str(ROOT / "tools"))

from demo_draw import MAX_ATTEMPTS, draw, try_build  # noqa: E402
from math9_core.graph import build_pipeline  # noqa: E402
from math9_core.state import ProblemState  # noqa: E402
from math9_curriculum.schema import Mode  # noqa: E402
from math9_core.llm.client import client_from_env, default_model  # noqa: E402
from math9_geometry.layout import best_figure  # noqa: E402
from math9_geometry.render_svg import render  # noqa: E402
from math9_verifier.geometry import verify  # noqa: E402
from math9_verifier.predicates import PredKind, Predicate  # noqa: E402

SAMPLES = {
    "Hai tiếp tuyến + đường kính": (ROOT / "demo" / "de.txt").read_text(encoding="utf-8").strip(),
    "Tam giác nội tiếp, ba đường cao": (
        "Cho tam giác ABC nhọn (AB < AC) nội tiếp đường tròn (O). Ba đường cao AD, BE, CF cắt nhau tại H. "
        "Gọi M là trung điểm của BC, K là điểm đối xứng với H qua M.\n"
        "a) Chứng minh tứ giác AEHF nội tiếp.\nb) Chứng minh K thuộc đường tròn (O).\n"
        "c) Chứng minh AK là đường kính của (O)."
    ),
    "Tam giác vuông, đường tròn đường kính": (
        "Cho tam giác ABC vuông tại A (AB < AC), đường cao AH. Vẽ đường tròn tâm O đường kính BC. "
        "Gọi M là trung điểm của AC, đường thẳng MH cắt đường tròn (O) tại điểm thứ hai D.\n"
        "a) Chứng minh tứ giác AHOM nội tiếp.\nb) Chứng minh MA² = MH·MD."
    ),
}

st.set_page_config(page_title="Math9 — Demo dựng hình", page_icon="📐", layout="wide")
st.title("Math9 Tutor — demo")
tab_solve, tab_draw = st.tabs(["Giải toán (pipeline đầy đủ)", "Dựng hình"])

with st.sidebar:
    st.header("Cấu hình")
    model = st.text_input("Model", value=default_model())
    st.caption("Đọc từ `.env`: OPENAI_API_KEY (hoặc LOCAL_LLM_URL) và MODEL_NAME / MODEL_API_KEY.")
    st.markdown("---")
    st.markdown(f"Tối đa **{MAX_ATTEMPTS}** lượt gọi LLM; lỗi kịch bản được gửi lại để LLM tự sửa.")


ALG_SAMPLE = (
    "Cho phương trình x^2 - 2(m+1)x + m^2 + 2 = 0 (m là tham số).\n"
    "a) Giải phương trình khi m = 1.\n"
    "b) Tìm m để phương trình có hai nghiệm phân biệt x1, x2 thỏa mãn x1^2 + x2^2 = 10."
)

with tab_solve:
    st.caption("Router → RAG → Solver ∥ Draftsman → Verifier (SymPy / dựng hình 5 cấu hình) → Critic → Pedagogue. "
               "Kiểm chứng bằng code, không bằng LLM.")
    s_sample = st.selectbox("Bài mẫu", ["(tự nhập)", "Đại số: tham số + Viète"] + list(SAMPLES), key="s_sample")
    s_default = ALG_SAMPLE if s_sample == "Đại số: tham số + Viète" else SAMPLES.get(s_sample, "")
    s_text = st.text_area("Đề bài", value=s_default, height=140, key="s_text")
    c1, c2, c3 = st.columns([1, 1, 2])
    s_mode = c1.selectbox("Chế độ", [m.value for m in Mode], index=1, key="s_mode",
                          help="basic: đúng SGK · exam10: + kỹ thuật thi vào 10 · advanced: + phương tích, Ptolemy")
    s_hints = c2.toggle("Sinh gợi ý", value=True, key="s_hints")
    s_run = c3.button("Giải", type="primary", width="stretch", disabled=not s_text.strip(), key="s_run")

    if s_run:
        st.session_state.pop("solve", None)
        with st.status("Đang giải...", expanded=True) as status:
            try:
                status.write("Dựng pipeline (RAG nạp sổ tay chưa soát ở chế độ phát triển)...")
                pipe = build_pipeline(model=model.strip(), require_reviewed=False, enable_hints=s_hints)
                status.write("Router → Solver ∥ Draftsman → Verifier → (Critic → giải lại) → Pedagogue. "
                             "Bài hình mất 1–3 phút.")
                res = pipe.run(ProblemState(raw_input=s_text.strip(), mode=Mode(s_mode)))
                st.session_state["solve"] = res
                status.update(label=f"Xong — độ tin cậy {res.confidence().value.upper()}", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Thất bại", state="error")
                st.exception(e)

    if "solve" in st.session_state:
        res: ProblemState = st.session_state["solve"]
        conf = res.confidence().value
        badge = {"high": st.success, "partial": st.warning, "low": st.error}[conf]
        badge(f"Độ tin cậy: **{conf.upper()}** · chuyên đề {res.topic} (Router tin cậy {res.router_confidence:.2f}) · "
              f"độ khó {res.difficulty} · giải lại {res.attempts} lần")

        show_solution = st.toggle("Hiện lời giải (mặc định chỉ hiện gợi ý)", value=False, key="show_sol")
        if res.hints and not show_solution:
            st.subheader("Gợi ý")
            for h in res.hints:
                st.markdown(f"- {h}")

        col_l, col_r = st.columns([3, 2]) if res.figure_svg else (st.container(), None)
        with col_l:
            if show_solution or not res.hints:
                for sp in res.subproblems:
                    st.markdown(f"**{sp.label}) {sp.statement}** &nbsp; `{sp.goal_type}`")
                    for st_ in sp.steps:
                        pred = f" `⟨{st_.predicate['kind']}⟩`" if st_.predicate else ""
                        st.markdown(f"{st_.id}. {st_.claim} &nbsp; *({st_.justification})*{pred}")
                    if sp.answer:
                        st.markdown(f"→ **{sp.answer}**")
        if col_r is not None:
            with col_r:
                st.markdown(res.figure_svg, unsafe_allow_html=True)
                st.caption(f"Độ dễ nhìn {res.figure_quality:.2f} · seed {res.figure_seed}")

        v = res.verification
        with st.expander("Kết quả kiểm chứng", expanded=conf != "high"):
            st.write({"algebra_ok": v.algebra_ok, "geometry_ok": v.geometry_ok,
                      "violations": v.violations, "cross_check": v.cross_check})
            g = v.detail.get("geometry")
            if g:
                st.write(f"Hình: {g['n_configs']}/5 cấu hình · sai: {g['failures']} · không kiểm được: {g.get('unresolved', [])}")
            al = v.detail.get("algebra", {}).get("results")
            if al:
                st.dataframe([{"ok": r["ok"], **{k: str(val) for k, val in r["check"].items()}} for r in al],
                             hide_index=True, width="stretch")
        with st.expander("Nhật ký (agent, model, token, thời gian)"):
            tin, tout = sum(t.tokens_in for t in res.trace), sum(t.tokens_out for t in res.trace)
            st.caption(f"Tổng token: {tin} vào / {tout} ra")
            st.dataframe([t.model_dump() for t in res.trace], hide_index=True, width="stretch")
        st.download_button("Tải state.json", res.model_dump_json(indent=2, exclude={"figure_svg"}),
                           file_name="state.json", mime="application/json")

with tab_draw:
    st.caption("Đề bài → LLM sinh kịch bản dựng hình (DSL) → engine tính tọa độ → SVG. LLM không bao giờ sinh tọa độ.")
    sample = st.selectbox("Bài mẫu", ["(tự nhập)"] + list(SAMPLES))
    default_text = SAMPLES.get(sample, "")
    statement = st.text_area("Đề bài", value=default_text, height=160, placeholder="Dán đề bài hình học lớp 9 vào đây...")

    col_run, col_pred = st.columns([1, 3])
    run = col_run.button("Dựng hình", type="primary", width="stretch", disabled=not statement.strip())
    preds_text = col_pred.text_input(
        "Vị từ cần kiểm chứng (tùy chọn, JSON)",
        placeholder='[{"kind":"concyclic","args":["A","B","O","C"]}, {"kind":"perpendicular","args":["O","A","B","C"]}]',
        help="Các loại: " + ", ".join(k.value for k in PredKind),
    )

    if run:
        st.session_state.pop("result", None)
        status = st.status("Đang dựng hình...", expanded=True)
        events: list[str] = []

        def on_event(kind: str, p: dict) -> None:
            if kind == "calling":
                status.write(f"Lượt {p['attempt']}/{MAX_ATTEMPTS}: gọi LLM sinh kịch bản...")
            elif kind == "received":
                m = p["meta"]
                status.write(f"Nhận {len(p['raw'].get('ops', []))} phép dựng — {m['ms']} ms, {m['tokens_in']}→{m['tokens_out']} token")
            elif kind == "error":
                status.write(f"Kịch bản lỗi, gửi lại cho LLM sửa: `{p['error'].splitlines()[0]}`")
            elif kind == "built":
                status.write(f"Engine dựng xong — chọn cấu hình seed {p['seed']}, độ dễ nhìn {p['quality']:.2f}")

        try:
            r = draw(statement.strip(), client_from_env(), model.strip(), on_event)
            st.session_state["result"] = r
            st.session_state["statement"] = statement.strip()
            status.update(label="Dựng hình thành công", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Thất bại", state="error")
            st.error(str(e))

    if "result" in st.session_state:
        r = st.session_state["result"]
        c = r.construction

        left, right = st.columns([3, 2])
        with left:
            st.markdown(r.svg, unsafe_allow_html=True)
            reasons = f" — {'; '.join(r.quality.reasons)}" if r.quality.reasons else ""
            st.caption(f"{len(c.ops)} phép dựng · {r.n_points} điểm · độ dễ nhìn {r.quality.score:.2f} (seed {r.seed}){reasons}")
            st.download_button("Tải SVG", r.svg, file_name="figure.svg", mime="image/svg+xml")

        with right:
            st.subheader("Kịch bản dựng hình")
            rows = [
                {"#": i, "op": o.op.value, "name": o.name or "", "args": ", ".join(o.args),
                 "params": json.dumps(o.params, ensure_ascii=False) if o.params else "", "style": o.style if o.style != "solid" else ""}
                for i, o in enumerate(c.ops, 1)
            ]
            st.dataframe(rows, hide_index=True, width="stretch", height=min(40 + 35 * len(rows), 520))
            st.download_button("Tải construction.json", c.model_dump_json(indent=2), file_name="construction.json", mime="application/json")

            with st.expander("Nhật ký các lượt gọi"):
                st.json(r.log)

        # --- kiểm chứng bằng Verifier (không dùng LLM) ---
        if preds_text.strip():
            st.subheader("Kiểm chứng bằng số trên 5 cấu hình ngẫu nhiên")
            try:
                claims = [Predicate(p["kind"], p["args"], p.get("value")) for p in json.loads(preds_text)]
                v = verify(c, claims)
                for res in v.results:
                    if res.holds:
                        st.success(f"ĐÚNG · {res.predicate!r}  (sai lệch lớn nhất {res.max_residual:.1e})")
                    else:
                        st.error(f"SAI · {res.predicate!r}  ({res.error or f'sai lệch {res.max_residual:.2e}'})")
                if v.build_errors:
                    st.warning("Không dựng được ở một số cấu hình: " + "; ".join(v.build_errors))
            except Exception as e:
                st.warning(f"Không đọc được vị từ: {e}")

        # --- sửa tay kịch bản và dựng lại, không gọi LLM ---
        with st.expander("Sửa kịch bản và dựng lại (không gọi LLM)"):
            edited = st.text_area("construction.json", value=c.model_dump_json(indent=2), height=300, key="edit_json")
            if st.button("Dựng lại từ JSON"):
                c2, err = try_build(json.loads(edited))
                if not c2:
                    st.error(err)
                else:
                    fig, q = best_figure(c2)
                    r.construction, r.svg, r.quality, r.seed, r.n_points = c2, render(fig), q, fig.seed, len(fig.points())
                    st.rerun()
