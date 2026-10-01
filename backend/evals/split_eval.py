"""Tách data/eval/eval-seed.jsonl thành các file mà evals/run.py đọc.

`eval-seed.jsonl` là kho THÔ — mọi bài trích được từ đề thi, gồm cả những bài
ngoài phạm vi (chương trình cũ, đề chuyên, goal_type ngoài 10 chương KNTT).
Script này lọc và chia lại theo đúng bốn tệp mà pipeline eval cần, cộng vài
tệp tham chiếu để không mất dữ liệu.

Chạy lại script này mỗi khi eval-seed.jsonl có thêm đề mới:

    python evals/split_eval.py

Kết quả GHI ĐÈ toàn bộ file trong data/eval/ (trừ chính eval-seed.jsonl và
README.md) — không chỉnh tay các file đó, mọi chỉnh sửa phải làm ở eval-seed.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

SEED_PATH = Path("data/eval/eval-seed.jsonl")
OUT_DIR = Path("data/eval")

#: Bao nhiêu bài mỗi chuyên đề lấy vào smoke — 10 chuyên đề x 3 = 30, đúng mục
#: tiêu "30 bài trải đều" của evals/run.py.
SMOKE_PER_TOPIC = 3
#: Cố định để lần tách nào cũng ra cùng một bộ smoke — không đổi ngẫu nhiên
#: giữa các lần chạy, tiện khi so sánh báo cáo eval qua thời gian.
RANDOM_SEED = 9


def load(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Không thấy {path}. Đây là kho thô, cần có trước khi tách.")
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write(name: str, rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda r: r["id"])
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"{name}: có id trùng — {[i for i in ids if ids.count(i) > 1]}"
    with (OUT_DIR / f"{name}.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  {name}.jsonl: {len(rows)} bài")


def in_scope(r: dict) -> bool:
    """Trong phạm vi Toán 9 GDPT2018 hiện đang xây — loại nền lớp 8 và nội
    dung ngoài chương trình (số học tổ hợp bậc cao, đường đối trung...)."""
    return r["gold"]["topic"] != "NEN" and r["gold"]["goal_type"] != "out_of_scope"


def build_smoke(core: list[dict]) -> list[dict]:
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for r in core:
        by_topic[r["gold"]["topic"]].append(r)
    rnd = random.Random(RANDOM_SEED)
    for v in by_topic.values():
        rnd.shuffle(v)

    topics = sorted(by_topic)
    out: list[dict] = []
    counts = Counter()
    i = 0
    # Vòng lấy round-robin qua các chuyên đề để phân bố đều, thay vì lấy hết
    # một chuyên đề rồi mới sang chuyên đề khác.
    while len(out) < SMOKE_PER_TOPIC * len(topics) and any(by_topic.values()):
        t = topics[i % len(topics)]
        if by_topic[t] and counts[t] < SMOKE_PER_TOPIC:
            out.append(by_topic[t].pop())
            counts[t] += 1
        i += 1
        if i > 10_000:  # an toàn: tránh vòng lặp vô hạn nếu một chuyên đề rỗng
            break
    return out


def build_hard(core: list[dict], chuyen_chung: list[dict], chuyen: list[dict]) -> list[dict]:
    out = [r for r in core if r["gold"]["difficulty"] == 3]
    # Bài khối chuyên khó vừa trở lên NHƯNG vẫn trong phạm vi chương trình —
    # đây là nguồn "câu cuối / HSG" tốt hơn vì đã được kiểm chứng, không phải
    # tự bịa thêm bài khó.
    out += [r for r in chuyen_chung + chuyen if in_scope(r) and r["gold"]["difficulty"] >= 2]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="chỉ in thống kê, không ghi file")
    args = ap.parse_args()

    rows = load(SEED_PATH)
    by_set = defaultdict(list)
    for r in rows:
        by_set[r["eval_set"]].append(r)

    core = by_set["core"]
    core_2006 = by_set["core_2006"]
    chuyen_chung = by_set["chuyen_chung"]
    chuyen = by_set["chuyen"]

    smoke = build_smoke(list(core))
    hard = build_hard(core, chuyen_chung, chuyen)
    figure = [r for r in rows if r["gold"].get("predicates")]
    out_of_scope = [r for r in chuyen_chung + chuyen if not in_scope(r)]

    print(f"Kho thô: {len(rows)} bài  ({dict(Counter(r['eval_set'] for r in rows))})")
    print("Tách ra:")
    plan = {
        "smoke": smoke, "core": core, "hard": hard, "figure": figure,
        "core_2006": core_2006, "out_of_scope": out_of_scope, "chuyen_chung": chuyen_chung,
    }
    for name, data in plan.items():
        print(f"  {name}.jsonl: {len(data)} bài" + (" (dry-run)" if args.dry_run else ""))
    if args.dry_run:
        return
    for name, data in plan.items():
        write(name, data)

    print("\nKiểm tra chồng lấn giữa các file bắt buộc (smoke/core/hard/figure):")
    print("  smoke ⊆ core:", {r["id"] for r in smoke} <= {r["id"] for r in core})
    print("  hard có bài ngoài core (khối chuyên):", sum(1 for r in hard if r["eval_set"] != "core"))


if __name__ == "__main__":
    main()
