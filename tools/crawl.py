"""Chạy khâu nhập dữ liệu.

    python tools/crawl.py --list                 # xem adapter đã đăng ký
    python tools/crawl.py --source sogd-hanoi    # chạy một nguồn
    python tools/crawl.py --all --dry-run        # duyệt link, không tải
"""

from __future__ import annotations

import argparse
import logging

from math9_ingest.fetch import FetchConfig, Fetcher
from math9_ingest.pipeline import IngestPipeline

#: Đăng ký adapter ở đây. Mỗi nguồn một file trong math9_ingest/adapters/.
ADAPTERS: dict[str, type] = {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="tên adapter")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="chỉ duyệt link, không tải")
    ap.add_argument("--delay", type=float, default=2.0, help="giây giữa 2 request cùng domain")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.list or not ADAPTERS:
        print("Adapter đã đăng ký:", ", ".join(ADAPTERS) or "(chưa có)")
        if not ADAPTERS:
            print(
                "\nChưa có adapter nào. Gửi link nguồn để viết adapter tương ứng —\n"
                "xem packages/ingest/math9_ingest/adapters/README.md."
            )
        return

    names = list(ADAPTERS) if args.all else [args.source]
    adapters = [ADAPTERS[n]() for n in names if n in ADAPTERS]

    if args.dry_run:
        for ad in adapters:
            docs = ad.discover()
            print(f"{ad.name}: tìm thấy {len(docs)} tài liệu")
            for d in docs[:5]:
                print(f"  - [{d.kind}] {d.title}  {d.url}")
        return

    pipe = IngestPipeline(fetcher=Fetcher(FetchConfig(delay_per_domain=args.delay)))
    stats = pipe.run(adapters)
    print("\n" + stats.report())


if __name__ == "__main__":
    main()
