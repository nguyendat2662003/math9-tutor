"""Tạo bài giải mẫu (data/problems/*.json) bán tự động từ Pipeline.

    python tools/make_example.py --id mau-hai-tiep-tuyen --file de.txt --source "Tự soạn"
    python tools/make_example.py --id mau-viete --from-state solve_alg/state.json

Quy trình (xem data/problems/QUY-CACH.md, mục "Cách làm bán tự động"):
  1. Pipeline giải + Verifier kiểm chứng.
  2. CHỈ ghi file khi độ tin cậy HIGH — lời giải chưa kiểm chứng không được làm mẫu.
  3. File ghi ra mang `status: needs_teacher`; giáo viên soát `justification`
     (Verifier kiểm được kết luận đúng/sai, không kiểm được căn cứ có thuộc lớp 9)
     rồi đổi thành `reviewed`. RAG chỉ nạp bản reviewed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from math9_core.state import ProblemState  # noqa: E402

OUT_DIR = ROOT / "data" / "problems"


def to_example(s: ProblemState, ex_id: str, source: str) -> dict:
    subs = []
    for sp in s.subproblems:
        subs.append({
            "label": sp.label,
            "statement": sp.statement,
            "topic": s.topic,
            "goal_type": sp.goal_type,
            "difficulty": sp.difficulty,
            "approach_ref": None,               # giáo viên gắn: "prove_concyclic#huong-1"
            "steps": [
                {k: v for k, v in st.model_dump().items() if v not in (None, [], "")}
                for st in sp.steps
            ],
            "answer": sp.answer,
        })
    doc = {
        "id": ex_id,
        "source": source,
        "mode": s.mode.value,
        "solution_type": "detailed",
        "status": "needs_teacher",
        "statement": s.raw_input,
        "subproblems": subs,
        "verification": {
            "algebra_ok": s.verification.algebra_ok,
            "geometry_ok": s.verification.geometry_ok,
            "n_configs": s.verification.detail.get("geometry", {}).get("n_configs"),
        },
    }
    if s.construction:
        doc["construction"] = json.loads(s.construction.model_dump_json())
    return doc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True, help="tên file, ví dụ mau-hai-tiep-tuyen")
    ap.add_argument("--file", type=Path, help="đề bài")
    ap.add_argument("--statement")
    ap.add_argument("--from-state", type=Path, help="dùng state.json đã có, không gọi LLM")
    ap.add_argument("--source", default="Tự soạn")
    ap.add_argument("--force", action="store_true", help="ghi cả khi chưa HIGH (không khuyến khích)")
    a = ap.parse_args()

    if a.from_state:
        s = ProblemState.model_validate_json(a.from_state.read_text(encoding="utf-8"))
    else:
        text = a.statement or (a.file.read_text(encoding="utf-8").strip() if a.file else "")
        if not text:
            raise SystemExit("Cần --file / --statement / --from-state")
        from math9_core.graph import build_pipeline

        s = build_pipeline(require_reviewed=False, enable_hints=False).run(ProblemState(raw_input=text))

    conf = s.confidence().value
    if conf != "high" and not a.force:
        raise SystemExit(f"Độ tin cậy {conf.upper()} — không ghi làm mẫu. Xem verification: "
                         f"{json.dumps(s.verification.model_dump(exclude={'detail'}), ensure_ascii=False)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{a.id}.json"
    out.write_text(json.dumps(to_example(s, a.id, a.source), ensure_ascii=False, indent=2), encoding="utf-8")
    n_steps = sum(len(sp.steps) for sp in s.subproblems)
    print(f"Đã ghi {out} — {len(s.subproblems)} ý, {n_steps} bước, độ tin cậy {conf.upper()}, status: needs_teacher")
    print("Giáo viên soát: justification từng bước có thuộc lớp 9 không, gắn approach_ref, đổi status -> reviewed.")


if __name__ == "__main__":
    main()
