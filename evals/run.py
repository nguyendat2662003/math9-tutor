"""Chạy bộ đánh giá. ĐÂY LÀ THỨ PHẢI LÀM TRƯỚC KHI VIẾT SẢN PHẨM.

Không có bộ eval, mọi thay đổi prompt sau này đều là đoán mò.

Cách dùng:
    python evals/run.py --set core --out evals/reports/2026-08-08.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def load(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(
            f"Chưa có bộ eval {p}. Chạy `python evals/split_eval.py` để tách từ "
            "data/eval/eval-seed.jsonl, hoặc xem docs/08-bat-dau-tu-dau.md."
        )
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=list(EVAL_SETS), default="smoke")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    path, target, desc, freq = EVAL_SETS[args.set]
    items = load(path)
    print(f"Bộ {args.set}: {len(items)} bài — {desc} ({freq})")
    if len(items) < target:
        print(
            f"  ⚠ chưa đủ mục tiêu {target} bài (đang có {len(items)}, thiếu "
            f"{target - len(items)}). Xem docs/du-lieu-de-thi/PHAN-TICH-DOT-2.md "
            "mục 'Còn mỏng và nên làm tiếp' để biết ưu tiên tìm thêm đề nào."
        )
    # TODO: chạy Pipeline trên từng bài, chấm bằng evals/graders/*
    raise NotImplementedError("Nối Pipeline vào đây sau Sprint 2")


if __name__ == "__main__":
    main()
