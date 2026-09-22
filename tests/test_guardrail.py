"""Kiểm thử guardrail chương trình — cũng không cần LLM."""

import pytest
from math9_curriculum.guardrail import check_justifications, check_keywords
from math9_curriculum.loader import load_dir
from math9_curriculum.schema import Mode


@pytest.fixture(scope="module")
def geo9():
    return load_dir("data/curriculum").get("GEO-9")


def test_power_of_point_blocked_in_exam10(geo9):
    text = "Áp dụng phương tích của điểm A đối với (O), ta có AB² = AH·AO"
    assert check_keywords(text, geo9, Mode.EXAM10)


def test_power_of_point_allowed_in_advanced(geo9):
    text = "Áp dụng phương tích của điểm A đối với (O)"
    assert not check_keywords(text, geo9, Mode.ADVANCED)


def test_derivative_blocked_everywhere(geo9):
    text = "Lấy đạo hàm hai vế ta được"
    assert check_keywords(text, geo9, Mode.ADVANCED)


def test_missing_justification_flagged(geo9):
    steps = [{"id": "s1", "claim": "ABOC nội tiếp", "justification": ""}]
    v = check_justifications(steps, geo9, Mode.EXAM10)
    assert any(x.kind == "missing_justification" for x in v)


def test_valid_solution_passes(geo9):
    text = "Xét tứ giác ABOC có góc ABO + góc ACO = 180 độ nên ABOC nội tiếp"
    steps = [{"id": "s1", "claim": "ABOC nội tiếp",
              "justification": "tổng hai góc đối bằng 180 độ"}]
    assert not check_keywords(text, geo9, Mode.EXAM10)
    assert not check_justifications(steps, geo9, Mode.EXAM10, strict=True)


def test_all_topics_load_and_cover_handbook_tools():
    """Mọi mã công cụ mà sổ tay tham chiếu phải tồn tại trong bản đồ chương trình."""
    import re
    from pathlib import Path

    cm = load_dir("data/curriculum")
    assert len(cm.topics) == 10
    known = {t.id for topic in cm.topics.values() for t in topic.allowed_tools}
    referenced = set()
    for f in Path("data/methods").glob("*.md"):
        referenced |= set(re.findall(r"T-[A-Z0-9-]+", f.read_text(encoding="utf-8")))
    assert referenced <= known, referenced - known


def test_tangent_chord_angle_blocked_below_advanced():
    """KNTT 9 không có bài riêng — chỉ được dùng ở advanced cho tới khi giáo viên xác nhận."""
    geo9 = load_dir("data/curriculum").get("GEO-9")
    ids = {t.id for t in geo9.toolkit(Mode.EXAM10)}
    assert "T-TANGENT-CHORD-ANGLE" not in ids
    assert "T-TANGENT-CHORD-ANGLE" in {t.id for t in geo9.toolkit(Mode.ADVANCED)}
