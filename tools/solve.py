"""Giải một bài bằng Pipeline đầy đủ với LLM thật, in kết quả và ghi state ra file.

    python tools/solve.py "Giải phương trình x^2 - 5x + 6 = 0."
    python tools/solve.py --file demo/de.txt --out demo/solve_out --mode exam10
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from math9_core.graph import build_pipeline  # noqa: E402
from math9_core.state import ProblemState  # noqa: E402
from math9_curriculum.schema import Mode  # noqa: E402


def print_state(s: ProblemState) -> None:
    print(f"\nChuyên đề: {s.topic} (tin cậy {s.router_confidence:.2f}) · độ khó {s.difficulty} · lượt giải lại {s.attempts}")
    for sp in s.subproblems:
        print(f"\n{sp.label}) {sp.statement}   [{sp.goal_type}]")
        for st in sp.steps:
            mark = f"  ⟨{st.predicate['kind']}⟩" if st.predicate else ""
            print(f"   {st.id}. {st.claim}  ({st.justification}){mark}")
        if sp.answer:
            print(f"   → {sp.answer}")
    v = s.verification
    print(f"\nKiểm chứng: đại số={v.algebra_ok} · hình={v.geometry_ok} · vi phạm={len(v.violations)} · "
          f"lệch hình-lời giải={len(v.cross_check)} → ĐỘ TIN CẬY: {s.confidence().value.upper()}")
    for f in v.detail.get("geometry", {}).get("failures", []):
        print(f"   vị từ SAI: {f}")
    for x in v.violations:
        print(f"   vi phạm: {x['detail']}")
    for x in v.cross_check:
        print(f"   {x}")
    if s.hints:
        print("\nGợi ý:")
        for h in s.hints:
            print(f"   • {h}")
    tot_in = sum(t.tokens_in for t in s.trace)
    tot_out = sum(t.tokens_out for t in s.trace)
    print(f"\nToken: {tot_in} vào / {tot_out} ra · các bước: " + ", ".join(f"{t.agent}({t.ms}ms)" for t in s.trace if t.ms))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("statement", nargs="?")
    ap.add_argument("--file", type=Path)
    ap.add_argument("--mode", choices=[m.value for m in Mode], default="exam10")
    ap.add_argument("--model")
    ap.add_argument("--no-rag", action="store_true")
    ap.add_argument("--no-hints", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO if a.v else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    text = a.statement or (a.file.read_text(encoding="utf-8").strip() if a.file else "")
    if not text:
        raise SystemExit("Cần đề bài")

    # Sổ tay chưa soát vẫn nạp được ở giai đoạn phát triển; production dùng require_reviewed=True
    pipe = build_pipeline(model=a.model, rag=not a.no_rag, require_reviewed=False, enable_hints=not a.no_hints)
    t0 = time.time()
    s = pipe.run(ProblemState(raw_input=text, mode=Mode(a.mode)))
    print_state(s)
    print(f"Tổng thời gian: {time.time() - t0:.1f}s")

    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        (a.out / "state.json").write_text(s.model_dump_json(indent=2, exclude={"figure_svg"}), encoding="utf-8")
        if s.figure_svg:
            (a.out / "figure.svg").write_text(s.figure_svg, encoding="utf-8")
        print(f"Đã ghi {a.out}/state.json" + (" + figure.svg" if s.figure_svg else ""))


if __name__ == "__main__":
    main()
