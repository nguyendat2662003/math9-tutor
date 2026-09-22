"""Xuất hàng đợi soát cho giáo viên dưới dạng bảng tính.

Giáo viên KHÔNG nên phải đọc JSONL. Công cụ này xuất CSV mở được bằng Excel
hoặc Google Sheets, với đúng các cột cần điền, rồi nhập ngược lại.

    python tools/review_queue.py export --out review.csv
    python tools/review_queue.py import --in review_done.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

COLUMNS = [
    "id", "source", "statement", "flags",
    # --- giáo viên điền từ đây ---
    "statement_fixed",     # sửa lại đề nếu trích sai
    "topic",               # GEO-9
    "goal_type",           # prove_concyclic
    "difficulty",          # 1 | 2 | 3
    "answer",              # đáp án chuẩn
    "predicates",          # JSON: [{"kind":"concyclic","args":["A","B","O","C"]}]
    "eval_set",            # smoke | core | hard | figure | skip
    "notes",
]


def export(src: Path, out: Path, limit: int | None) -> None:
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    if limit:
        rows = rows[:limit]
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({
                "id": r["id"],
                "source": r["source"],
                "statement": r["statement"],
                "flags": "; ".join(r["quality"]["flags"]),
            })
    print(f"Đã xuất {len(rows)} bài ra {out}. Mở bằng Excel, điền từ cột statement_fixed.")


def import_back(src: Path, out: Path) -> None:
    kept = 0
    with src.open(encoding="utf-8-sig") as fh, out.open("w", encoding="utf-8") as o:
        for row in csv.DictReader(fh):
            if not row.get("topic") or row.get("eval_set") == "skip":
                continue
            preds = row.get("predicates", "").strip()
            o.write(json.dumps({
                "id": row["id"],
                "source": row["source"],
                "statement": row.get("statement_fixed") or row["statement"],
                "mode": "exam10",
                "gold": {
                    "topic": row["topic"],
                    "goal_type": row.get("goal_type") or None,
                    "difficulty": int(row.get("difficulty") or 1),
                    "answer": row.get("answer") or None,
                    "predicates": json.loads(preds) if preds else [],
                },
                "eval_set": row.get("eval_set") or "core",
                "teacher_notes": row.get("notes") or None,
            }, ensure_ascii=False) + "\n")
            kept += 1
    print(f"Đã nhập {kept} bài đã soát vào {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--src", type=Path, default=Path("data/raw/review.jsonl"))
    e.add_argument("--out", type=Path, default=Path("data/raw/review.csv"))
    e.add_argument("--limit", type=int)
    i = sub.add_parser("import")
    i.add_argument("--src", type=Path, required=True)
    i.add_argument("--out", type=Path, default=Path("data/eval/reviewed.jsonl"))
    a = ap.parse_args()

    if a.cmd == "export":
        export(a.src, a.out, a.limit)
    else:
        import_back(a.src, a.out)


if __name__ == "__main__":
    main()
