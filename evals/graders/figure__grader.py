"""Chấm hình vẽ: hình có đúng quan hệ hình học của đề không.

Không chấm bằng mắt và không chấm bằng LLM. Dựng lại hình từ kịch bản rồi
kiểm tra các vị từ trong đề bằng số — cùng cơ chế với Verifier.

Có hai nguồn kịch bản:
- Sản phẩm thật: Draftsman sinh ra khi Pipeline chạy — dùng `grade()` trực tiếp.
- Bộ eval: `data/eval/constructions.jsonl` chứa kịch bản THAM CHIẾU do người viết
  và đã kiểm chứng, khóa theo `context_id` (nhiều ý của một bài dùng chung một
  hình). Dùng `grade_eval_file()` để chấm cả `figure.jsonl` một lượt — đây là kịch
  bản đúng để đối chiếu, không phải kịch bản Draftsman cần sinh ra.
"""

from __future__ import annotations

import json
from pathlib import Path

from math9_geometry.dsl import Construction
from math9_verifier.geometry import verify
from math9_verifier.predicates import Predicate

CONSTRUCTIONS_PATH = Path("data/eval/constructions.jsonl")
FIGURE_PATH = Path("data/eval/figure.jsonl")


def grade(construction: Construction, given_predicates: list[dict]) -> tuple[bool, dict]:
    claims = [Predicate(**p) for p in given_predicates]
    v = verify(construction, claims)
    return v.ok, {
        "n_configs": v.n_configs,
        "failures": [repr(f.predicate) for f in v.failures()],
        "build_errors": v.build_errors,
    }


def load_constructions(path: Path = CONSTRUCTIONS_PATH) -> dict[str, Construction]:
    """context_id -> Construction đã kiểm chứng, dùng làm hình tham chiếu."""
    if not path.exists():
        raise SystemExit(
            f"Chưa có {path}. Chạy evals/build_constructions.py để dựng, hoặc bổ sung "
            "kịch bản cho bài hình mới trong data/eval/eval-seed.jsonl."
        )
    out: dict[str, Construction] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        out[r["context_id"]] = Construction.model_validate(r["construction"])
    return out


def grade_eval_file(
    figure_path: Path = FIGURE_PATH, constructions_path: Path = CONSTRUCTIONS_PATH
) -> list[dict]:
    """Chấm toàn bộ data/eval/figure.jsonl bằng các kịch bản tham chiếu.

    Trả về một bản ghi kết quả mỗi bài — id, đạt/không, chi tiết. Bài nào không
    có kịch bản tham chiếu (context_id không có trong constructions.jsonl) được
    báo riêng, không tính là fail.
    """
    constructions = load_constructions(constructions_path)
    rows = [json.loads(l) for l in figure_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    results = []
    for r in rows:
        key = r.get("context_id") or r["id"]
        preds = r["gold"].get("predicates") or []
        if key not in constructions:
            results.append({"id": r["id"], "status": "missing_construction", "ok": None})
            continue
        ok, detail = grade(constructions[key], preds)
        results.append({"id": r["id"], "status": "graded", "ok": ok, **detail})
    return results


def _summarize(results: list[dict]) -> str:
    graded = [r for r in results if r["status"] == "graded"]
    missing = [r for r in results if r["status"] == "missing_construction"]
    passed = sum(1 for r in graded if r["ok"])
    lines = [f"Đã chấm {len(graded)}/{len(results)} bài, đạt {passed}/{len(graded) or 1}"]
    if missing:
        lines.append(f"Thiếu kịch bản tham chiếu ({len(missing)}): " + ", ".join(r["id"] for r in missing))
    for r in graded:
        if not r["ok"]:
            lines.append(f"  SAI {r['id']}: {r['failures']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_summarize(grade_eval_file()))
