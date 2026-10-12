"""Bộ golden (data/eval/golden.jsonl): đáp án đã kiểm chứng độc lập. Test này giữ cho bộ dữ liệu sạch — thêm
bài mới mà thiếu bằng chứng kiểm chứng, trùng id, hoặc đáp án không tự chấm đúng chính nó thì hỏng ngay."""

import json
from pathlib import Path

import pytest
from evals.graders.answer import grade_item

DATA = Path(__file__).resolve().parents[1] / "data" / "eval"
ROWS = [json.loads(line) for line in (DATA / "golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
EXCLUDED = json.loads((DATA / "golden_excluded.json").read_text(encoding="utf-8"))
SOURCES = {}
for name in ("core", "hard", "figure", "smoke"):
    for line in (DATA / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            SOURCES.setdefault(r["id"], r)


def test_ids_unique_and_traceable():
    ids = [r["id"] for r in ROWS]
    assert len(ids) == len(set(ids))
    for r in ROWS:
        assert r["id"] in SOURCES, f"{r['id']} không có trong bộ nguồn"
        assert r["statement"] == SOURCES[r["id"]]["statement"], f"{r['id']}: đề khác bộ nguồn"


def test_every_row_is_verified_and_tiered():
    for r in ROWS:
        v = r["verification"]
        assert v["tier"] in ("A", "B") and v["checked"]
        assert (v["tier"] == "A") == (r["answer_source"] == "hdc_so"), f"{r['id']}: bậc A chỉ dành cho hướng dẫn chấm của Sở"
        assert r["grading"] == "context"


def test_excluded_rows_stay_out_with_reasons():
    ids = {r["id"] for r in ROWS}
    for i, why in EXCLUDED.items():
        assert i not in ids and len(why) > 20


def test_enough_coverage():
    assert len(ROWS) >= 100
    assert sum(r["verification"]["tier"] == "A" for r in ROWS) >= 20
    topics = {r["gold"]["topic"] for r in ROWS}
    assert len(topics) >= 10          # đủ 10 chuyên đề của chương trình


@pytest.mark.parametrize("row", [r for r in ROWS if r["gold"].get("answer")], ids=lambda r: r["id"])
def test_gold_answer_grades_itself(row):
    """Đáp án gốc (và từng cách viết chấp nhận thêm) phải được bộ chấm công nhận là đúng."""
    g = row["gold"]
    text = g["answer"]["value"] if isinstance(g["answer"], dict) else g["answer"]
    assert grade_item(text, row), f"{row['id']}: bộ chấm không nhận chính đáp án gốc {text!r}"
    for alt in g.get("accept", []):
        assert grade_item(alt, row)
