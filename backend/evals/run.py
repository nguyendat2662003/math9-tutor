"""Chạy bộ đánh giá. ĐÂY LÀ THỨ PHẢI LÀM TRƯỚC KHI VIẾT SẢN PHẨM.

Không có bộ eval, mọi thay đổi prompt sau này đều là đoán mò.

    python evals/run.py --set smoke                      # 30 bài, mỗi commit
    python evals/run.py --set core --workers 4           # 200 bài, mỗi PR
    python evals/run.py --set smoke --limit 5 --ids bn26-1a,hn24-IVa
    python evals/run.py --report evals/reports/2026-09-22_smoke.json   # chỉ in lại báo cáo cũ

Chấm tự động (không dùng LLM):
  - Router: topic và goal_type so với nhãn giáo viên.
  - Đáp án: SymPy so khớp số (graders/answer.py); bài chứng minh chấm bằng Verifier.
  - Hình: dựng lại kịch bản Draftsman, kiểm `gold.predicates` trên 5 cấu hình.
  - Vi phạm chương trình: guardrail.
  - Sai mà tự tin: confidence=high nhưng đáp án/hình sai — chỉ số quan trọng nhất.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))
sys.path.insert(0, str(ROOT))

from evals.graders.answer import grade as grade_answer  # noqa: E402
from evals.graders.figure import grade as grade_figure  # noqa: E402

EVAL_SETS = {
    # (đường dẫn, mục tiêu số bài, mô tả, tần suất chạy)
    "smoke": ("data/eval/smoke.jsonl", 30, "trải đều 3 bài mỗi chuyên đề (10 chuyên đề)", "mỗi commit"),
    "core": ("data/eval/core.jsonl", 200, "bài đề thi vào 10, chương trình GDPT 2018", "mỗi PR"),
    "hard": ("data/eval/hard.jsonl", 80, "độ khó 3 trong đề phổ thông + bài trong-phạm-vi của khối chuyên", "hàng tuần"),
    "figure": ("data/eval/figure.jsonl", 100, "bài hình có predicate — chấm bằng Verifier, không cần mắt người", "hàng tuần"),
}

#: File tham chiếu, KHÔNG dùng cho `--set` — giữ lại phần không thuộc phạm vi lớp 9
#: hiện đang xây (chương trình cũ 2006, hoặc goal_type/chủ đề ngoài 10 chương KNTT).
REFERENCE_SETS = {
    "core_2006": "data/eval/core_2006.jsonl",       # Hà Nội 2024 — chương trình cũ, chưa có thống kê/xác suất
    "out_of_scope": "data/eval/out_of_scope.jsonl",  # số học tổ hợp, đường đối trung... ngoài Toán 9 GDPT2018
    "chuyen_chung": "data/eval/chuyen_chung.jsonl",  # đề toán chung trường chuyên — khó hơn đại trà, không phải chuẩn tối thiểu
}

#: Ngưỡng nghiệm thu. Chỉ số quan trọng nhất là confident_wrong.
THRESHOLDS = {
    "answer_accuracy": {"core": 0.95, "hard": 0.70},
    "figure_valid": {"figure": 0.98},
    "curriculum_violation": {"core": 0.02, "hard": 0.02},   # càng thấp càng tốt
    "router_accuracy": {"core": 0.90},
    "confident_wrong": {"core": 0.01, "hard": 0.01},        # càng thấp càng tốt
}
LOWER_IS_BETTER = {"curriculum_violation", "confident_wrong"}


def load(path: str) -> list[dict]:
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"Chưa có bộ eval {p}. Xem docs/08-bat-dau-tu-dau.md.")
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


# --------------------------------------------------------------------------
# Chấm một bài
# --------------------------------------------------------------------------

_RE_NEEDS_OPTIONS = re.compile(r"nào (?:sau|dưới) đây|khẳng định nào|mệnh đề nào|phát biểu nào", re.I)
_RE_OPTION_A = re.compile(r"(?:^|\s)A[.)]\s")
_RE_OPTION_B = re.compile(r"(?:^|\s)B[.)]\s")


def _needs_options(statement: str) -> bool:
    """'Khẳng định nào sau đây' mà không thấy cả phương án A lẫn B (một chữ 'A.' lẻ
    có thể chỉ là tên điểm: 'vuông tại A.')."""
    has_options = _RE_OPTION_A.search(statement) and _RE_OPTION_B.search(statement)
    return bool(_RE_NEEDS_OPTIONS.search(statement)) and not has_options


def run_item(pipe, item: dict) -> dict:
    from math9_core.state import ProblemState
    from math9_curriculum.schema import Mode

    gold = item["gold"]
    row = {"id": item["id"], "topic_gold": gold.get("topic"), "goal_type_gold": gold.get("goal_type")}
    t0 = time.time()
    try:
        s = pipe.run(ProblemState(raw_input=item["statement"], mode=Mode(item.get("mode", "exam10"))))
    except Exception as e:
        row.update(error=f"{type(e).__name__}: {e}", ms=int((time.time() - t0) * 1000))
        return row
    row["ms"] = int((time.time() - t0) * 1000)
    row["tokens_in"] = sum(t.tokens_in for t in s.trace)
    row["tokens_out"] = sum(t.tokens_out for t in s.trace)
    row["attempts"] = s.attempts
    row["confidence"] = s.confidence().value

    # Router
    row["topic_pred"] = s.topic
    row["goal_types_pred"] = [sp.goal_type for sp in s.subproblems]
    row["router_topic_ok"] = s.topic == gold.get("topic")
    row["router_goal_ok"] = gold.get("goal_type") in row["goal_types_pred"] if gold.get("goal_type") else None

    # Đáp án
    predicted = " ; ".join(sp.answer for sp in s.subproblems if sp.answer)
    row["answer_pred"] = predicted or None
    if _needs_options(item["statement"]):
        # Trắc nghiệm "khẳng định nào sau đây" mà dữ liệu không lưu 4 phương án: không chấm được
        row["answer_ok"] = None
        row["data_issue"] = "trắc nghiệm thiếu phương án"
    elif gold.get("answer"):
        row["answer_ok"] = grade_answer(predicted, gold["answer"]) if predicted else False
    else:
        row["answer_ok"] = None                       # bài chứng minh — chấm qua Verifier

    # Hình: kịch bản Draftsman phải thỏa các vị từ của ĐỀ (không phải của lời giải)
    if gold.get("predicates"):
        if s.construction:
            ok, detail = grade_figure(s.construction, gold["predicates"])
            row["figure_ok"], row["figure_detail"] = ok, detail
        else:
            row["figure_ok"], row["figure_detail"] = False, {"error": "không dựng được hình"}
    else:
        row["figure_ok"] = None

    # Lời giải tự kiểm chứng (Verifier trên predicate của Solver)
    v = s.verification
    row["proof_verified"] = v.geometry_ok if s.is_geometry() else v.algebra_ok
    row["violations"] = [x["detail"] for x in v.violations]
    row["cross_check"] = v.cross_check

    # Sai mà tự tin — chỉ số quan trọng nhất
    wrong = row["answer_ok"] is False or row["figure_ok"] is False
    row["confident_wrong"] = row["confidence"] == "high" and wrong
    return row


# --------------------------------------------------------------------------
# Tổng hợp
# --------------------------------------------------------------------------

def _rate(rows: list[dict], key: str, want=True) -> tuple[float | None, int]:
    xs = [r.get(key) for r in rows if r.get(key) is not None and "error" not in r]
    if not xs:
        return None, 0
    return sum(1 for x in xs if x is want) / len(xs), len(xs)


def summarize(rows: list[dict], set_name: str) -> dict:
    ok_rows = [r for r in rows if "error" not in r]
    m: dict = {"n": len(rows), "n_error": len(rows) - len(ok_rows)}
    m["answer_accuracy"], m["n_answer"] = _rate(rows, "answer_ok")
    m["figure_valid"], m["n_figure"] = _rate(rows, "figure_ok")
    m["proof_verified"], m["n_proof"] = _rate(rows, "proof_verified")
    m["router_accuracy"], _ = _rate(rows, "router_topic_ok")
    m["router_goal_accuracy"], _ = _rate(rows, "router_goal_ok")
    m["curriculum_violation"] = (sum(1 for r in ok_rows if r["violations"]) / len(ok_rows)) if ok_rows else None
    m["confident_wrong"] = (sum(1 for r in ok_rows if r["confident_wrong"]) / len(ok_rows)) if ok_rows else None
    m["confidence_dist"] = {c: sum(1 for r in ok_rows if r["confidence"] == c) for c in ("high", "partial", "low")}
    m["n_data_issue"] = sum(1 for r in rows if r.get("data_issue"))
    if ok_rows:
        ms = sorted(r["ms"] for r in ok_rows)
        m["latency_p50_s"] = round(ms[len(ms) // 2] / 1000, 1)
        m["latency_p95_s"] = round(ms[min(len(ms) - 1, int(len(ms) * 0.95))] / 1000, 1)
        m["tokens_in_avg"] = sum(r["tokens_in"] for r in ok_rows) // len(ok_rows)
        m["tokens_out_avg"] = sum(r["tokens_out"] for r in ok_rows) // len(ok_rows)

    m["thresholds"] = {}
    for metric, per_set in THRESHOLDS.items():
        if set_name in per_set and m.get(metric) is not None:
            th = per_set[set_name]
            passed = m[metric] <= th if metric in LOWER_IS_BETTER else m[metric] >= th
            m["thresholds"][metric] = {"threshold": th, "value": round(m[metric], 3), "pass": passed}
    return m


def print_report(m: dict, set_name: str) -> None:
    def pct(x):
        return "—" if x is None else f"{x * 100:5.1f}%"

    print(f"\n=== Bộ {set_name}: {m['n']} bài, {m['n_error']} lỗi chạy ===")
    print(f"  Đáp án đúng        {pct(m['answer_accuracy'])}  (n={m['n_answer']})")
    print(f"  Hình đúng quan hệ  {pct(m['figure_valid'])}  (n={m['n_figure']})")
    print(f"  Lời giải tự KC     {pct(m['proof_verified'])}  (n={m['n_proof']})")
    print(f"  Router topic       {pct(m['router_accuracy'])}   goal_type {pct(m['router_goal_accuracy'])}")
    print(f"  Vi phạm chương trình {pct(m['curriculum_violation'])}")
    print(f"  SAI MÀ TỰ TIN      {pct(m['confident_wrong'])}")
    print(f"  Độ tin cậy: {m['confidence_dist']}" + (f" · lỗi dữ liệu (không chấm): {m['n_data_issue']}" if m.get("n_data_issue") else ""))
    if "latency_p50_s" in m:
        print(f"  Độ trễ p50/p95: {m['latency_p50_s']}s / {m['latency_p95_s']}s · token TB {m['tokens_in_avg']}→{m['tokens_out_avg']}")
    if m["thresholds"]:
        print("  Ngưỡng nghiệm thu:")
        for k, t in m["thresholds"].items():
            print(f"    {'ĐẠT ' if t['pass'] else 'CHƯA'} {k:22s} {t['value']:.3f} {'≤' if k in LOWER_IS_BETTER else '≥'} {t['threshold']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", choices=list(EVAL_SETS), default="smoke")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids", help="chỉ chạy các id này, cách nhau bằng dấu phẩy")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--model")
    ap.add_argument("--out", default=None, help="mặc định evals/reports/<ngày>_<set>.json")
    ap.add_argument("--report", help="chỉ in lại một báo cáo đã có")
    ap.add_argument("--regrade", help="chấm lại đáp án của báo cáo đã có bằng grader hiện tại (không gọi LLM)")
    args = ap.parse_args()

    if args.report:
        rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
        print_report(rep["metrics"], rep["set"])
        return

    if args.regrade:
        p = Path(args.regrade)
        rep = json.loads(p.read_text(encoding="utf-8"))
        gold = {it["id"]: it["gold"] for it in load(EVAL_SETS[rep["set"]][0])}
        for r in rep["rows"]:
            if "error" in r:
                continue
            g = gold[r["id"]]
            stmt = next(it["statement"] for it in load(EVAL_SETS[rep["set"]][0]) if it["id"] == r["id"])
            if _needs_options(stmt):
                r["answer_ok"], r["data_issue"] = None, "trắc nghiệm thiếu phương án"
            elif g.get("answer"):
                r["answer_ok"] = grade_answer(r["answer_pred"], g["answer"]) if r.get("answer_pred") else False
            wrong = r["answer_ok"] is False or r.get("figure_ok") is False
            r["confident_wrong"] = r["confidence"] == "high" and wrong
        rep["metrics"] = summarize(rep["rows"], rep["set"])
        p.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        print_report(rep["metrics"], rep["set"])
        return

    path, target, desc, freq = EVAL_SETS[args.set]
    items = load(path)
    if args.ids:
        want = set(args.ids.split(","))
        items = [i for i in items if i["id"] in want]
    if args.limit:
        items = items[: args.limit]
    print(f"Bộ {args.set}: chạy {len(items)} bài — {desc} ({freq})")
    if len(load(path)) < target:
        print(f"  ⚠ bộ này mới có {len(load(path))}/{target} bài mục tiêu")

    from math9_core.graph import build_pipeline

    # Không sinh gợi ý khi eval (tốn token, không chấm được tự động); sổ tay chưa soát vẫn nạp ở giai đoạn này
    pipe = build_pipeline(model=args.model, require_reviewed=False, enable_hints=False)

    rows: list[dict] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_item, pipe, it): it for it in items}
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            rows.append(r)
            if "error" in r:
                status = f"LỖI {r['error'][:80]}"
            else:
                bits = [r["confidence"]]
                if r["answer_ok"] is not None:
                    bits.append("đáp án " + ("✓" if r["answer_ok"] else "✗"))
                if r["figure_ok"] is not None:
                    bits.append("hình " + ("✓" if r["figure_ok"] else "✗"))
                if r["confident_wrong"]:
                    bits.append("!! SAI MÀ TỰ TIN")
                status = " · ".join(bits) + f" · {r['ms'] / 1000:.0f}s"
            print(f"  [{i:3d}/{len(items)}] {r['id']:<14} {status}", flush=True)

    rows.sort(key=lambda r: r["id"])
    metrics = summarize(rows, args.set)
    print_report(metrics, args.set)
    print(f"Tổng thời gian: {(time.time() - t0) / 60:.1f} phút")

    out = Path(args.out) if args.out else ROOT / "evals" / "reports" / f"{datetime.now():%Y-%m-%d_%H%M}_{args.set}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"set": args.set, "model": args.model, "when": datetime.now().isoformat(),
                               "metrics": metrics, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Báo cáo: {out}")


if __name__ == "__main__":
    main()
