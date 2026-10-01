"""Đưa kho đề có sẵn (data/eval, GDPT 2018) lên Qdrant để "gợi ý bài tương tự" tìm được cả trên kho cũ.

    python tools/index_bank.py            # ghi/ghi đè toàn bộ (chạy lại bao nhiêu lần cũng được)
    python tools/index_bank.py --dry-run  # chỉ đếm
    python tools/index_bank.py --uploads  # kèm bài tải lên đã duyệt (khi chuyển kho, vd cục bộ -> Cloud)

Bình thường bài tải lên qua trang quản trị vào Qdrant ngay lúc được duyệt; `--uploads` chỉ để
dựng lại kho. Bài có sẵn ghi KHÔNG kèm đáp án (gợi ý tương tự chỉ cần đề; luyện đề đọc đáp án
từ data/eval). Bài tải lên giữ đáp án vì luyện đề cần để chấm; API gợi ý không bao giờ trả đáp án.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval", "exam", "ingest"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from math9_exam.bank import load_bank  # noqa: E402
from math9_exam.index import get_index  # noqa: E402


def payloads() -> list[dict]:
    out = []
    for x in load_bank(include_uploads=False).items:
        out.append({
            "id": x.id, "source": x.source, "number": x.id.split("-", 1)[-1],
            "group": x.group, "lead": x.lead, "statement": x.part if x.lead else x.statement,
            "format": x.format, "options": x.options, "claims": x.claims,
            "topic": x.topic, "goal_type": x.goal_type, "difficulty": x.difficulty,
            "needs_figure": x.needs_figure and not x.figure, "origin": "eval", "status": "approved",
        })
    return out


def approved_uploads() -> list[dict]:
    """Bài đã duyệt trong các lô ở data/inbox — nguồn gốc để dựng lại kho khi đổi Qdrant."""
    from math9_exam import intake

    out = []
    for b in intake.list_batches():
        for p in intake.load_batch(b["id"])["problems"]:
            if p["status"] == "approved":
                out.append({k: v for k, v in p.items() if k != "warnings"})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uploads", action="store_true",
                    help="ghi lại cả bài tải lên ĐÃ DUYỆT (lấy từ data/inbox) — dùng khi chuyển kho, vd cục bộ -> Cloud")
    a = ap.parse_args()
    items = payloads()
    print(f"Kho có sẵn: {len(items)} bài")
    if a.uploads:
        ups = approved_uploads()
        print(f"Bài tải lên đã duyệt: {len(ups)} bài")
        items += ups
    if a.dry_run:
        return
    idx = get_index()
    if idx is None:
        import os

        if os.environ.get("QDRANT_PATH") and not os.environ.get("QDRANT_URL"):
            raise SystemExit("Không mở được Qdrant cục bộ — thường do API đang chạy và giữ thư mục này. "
                             "Tắt API rồi chạy lại (hoặc chuyển sang Qdrant Cloud).")
        raise SystemExit("Chưa cấu hình Qdrant: đặt QDRANT_URL + QDRANT_API_KEY (Cloud) hoặc QDRANT_PATH trong .env")
    n = idx.upsert(items)
    print(f"Đã ghi {n} bài vào {idx.mode} · {idx.collection}; kho hiện có {idx.count()} bài")
    idx.client.close()           # đóng chủ động — để Python tự đóng lúc thoát thì Qdrant cục bộ báo lỗi


if __name__ == "__main__":
    main()
