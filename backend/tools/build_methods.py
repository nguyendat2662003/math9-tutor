"""Xây bộ khung sổ tay từ một tài liệu tra cứu.

    # 1. Đã có text trích (qua ingest + OCR) tại data/raw/cam-nang.txt
    python tools/build_methods.py --source-text data/raw/cam-nang.txt \
        --map cam_nang_toanmath --out data/methods_draft

    # 2. Xem tài liệu phủ được goal_type nào
    python tools/build_methods.py --map cam_nang_toanmath --coverage-only

Đầu ra là bản DRAFT (status: needs_teacher). Phải qua giáo viên soát rồi
`gate_for_rag` mới cho vào RAG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from math9_core.enums import GOAL_TYPE_VI
from math9_methods.reorganize import Reorganizer, write_methods
from math9_methods.section_map import CAM_NANG_TOANMATH, coverage_report
from math9_methods.split_source import report_coverage, split_source

MAPS = {"cam_nang_toanmath": CAM_NANG_TOANMATH}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-text", type=Path, help="text đã trích (sau OCR)")
    ap.add_argument("--map", choices=list(MAPS), default="cam_nang_toanmath")
    ap.add_argument("--out", type=Path, default=Path("data/methods_draft"))
    ap.add_argument("--coverage-only", action="store_true")
    ap.add_argument("--use-llm", action="store_true", help="dùng LLM soạn nháp (cần API)")
    args = ap.parse_args()

    sections = MAPS[args.map]

    if args.coverage_only:
        rep = coverage_report(sections, list(GOAL_TYPE_VI))
        print(f"Phủ {len(rep['covered'])}/{len(GOAL_TYPE_VI)} goal_type")
        print("Giàu nhất:", ", ".join(rep["richest"]))
        print("KHÔNG phủ:", ", ".join(rep["uncovered"]) or "(không)")
        return

    if not args.source_text or not args.source_text.exists():
        raise SystemExit(
            "Cần --source-text trỏ tới text đã trích. Chạy tầng ingest + OCR trước:\n"
            "  công thức trong tài liệu này vỡ khi trích thẳng, phải qua Mathpix."
        )

    full = args.source_text.read_text(encoding="utf-8")
    chunks = split_source(full)

    cov = report_coverage(chunks, [s.ref for s in sections])
    if cov["missing_from_source"]:
        print("⚠ Mục có trong bản đồ nhưng KHÔNG cắt được từ text:",
              ", ".join(cov["missing_from_source"]))
    if cov["empty_or_too_short"]:
        print("⚠ Mục cắt được nhưng quá ngắn (nghi trích hỏng):",
              ", ".join(cov["empty_or_too_short"]))

    llm = None
    if args.use_llm:
        from math9_core.llm.client import client_from_env
        llm = client_from_env()

    r = Reorganizer(llm=llm, provenance=f"{args.map} ({len(sections)} mục)")
    result = r.run(sections, chunks)
    write_methods(result, args.out)

    print(f"\nĐã tạo {len(result.docs)} sổ tay draft tại {args.out}")
    print(f"Checklist soát: {args.out}/_review_checklist.json")
    if result.uncovered_goal_types:
        print("Cần nguồn khác cho:", ", ".join(result.uncovered_goal_types))


if __name__ == "__main__":
    main()
