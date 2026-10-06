"""Kiểm thử pipeline tái tổ chức sổ tay — chạy offline, không cần LLM."""

import pytest
from math9_core.enums import GOAL_TYPE_VI
from math9_methods.reorganize import Reorganizer, write_methods
from math9_methods.review_export import gate_for_rag, make_review_packet, validate_reviewed
from math9_methods.schema import Approach, MethodDoc, ReviewStatus
from math9_methods.section_map import (
    CAM_NANG_TOANMATH,
    coverage_report,
    invert,
)
from math9_methods.split_source import report_coverage, split_source


def test_inversion_is_many_to_many():
    """prove_concyclic phải rút từ nhiều mục; Dạng 30 phải nuôi nhiều goal_type."""
    inv = invert(CAM_NANG_TOANMATH)
    assert len(inv["prove_concyclic"]) >= 2       # Dạng 29 + Dạng 30
    dang30 = [s for s in CAM_NANG_TOANMATH if s.ref == "Dạng 30"][0]
    assert len(dang30.goal_types) >= 6            # mô hình mẫu nuôi nhiều mục tiêu


def test_coverage_report_flags_uncovered():
    rep = coverage_report(CAM_NANG_TOANMATH, list(GOAL_TYPE_VI))
    assert "prove_concyclic" in rep["covered"]
    # Tài liệu này không có quỹ tích và xác suất -> phải báo thiếu
    assert "find_locus" in rep["uncovered"]
    assert "compute_probability" in rep["uncovered"]
    assert "find_fixed_point" in rep["richest"] or len(rep["richest"]) == 5


def test_split_source_cuts_by_dang():
    text = """
Dạng 28. Đường tròn
Nội dung về tiếp tuyến và dây cung ở đây.
Dạng 29. Góc với đường tròn
Góc nội tiếp bằng nửa góc ở tâm cùng chắn một cung.
Dạng 30: Các mô hình mẫu trong đề thi
Mô hình hai tiếp tuyến, mô hình đường cao.
PHẦN 2: PHỤ LỤC
10. Chứng minh hai đường thẳng vuông góc
Dùng định lý Pythagore đảo hoặc tích vô hướng.
"""
    chunks = split_source(text)
    assert "Dạng 29" in chunks
    assert "Góc nội tiếp" in chunks["Dạng 29"]
    assert "PL mục 10" in chunks
    assert "vuông góc" in chunks["PL mục 10"]


def test_reorganize_without_llm_makes_scaffold():
    """Không có LLM vẫn tạo được khung để giáo viên điền tay."""
    r = Reorganizer(llm=None, provenance="Cẩm nang toanmath 59tr")
    section_texts = {"Dạng 29": "Góc nội tiếp...", "Dạng 30": "Mô hình mẫu..."}
    result = r.run(CAM_NANG_TOANMATH, section_texts, goal_types=["prove_concyclic"])
    assert len(result.docs) == 1
    doc = result.docs[0]
    assert doc.goal_type == "prove_concyclic"
    assert doc.status == ReviewStatus.NEEDS_TEACHER
    assert doc.provenance == "Cẩm nang toanmath 59tr"


def test_draft_doc_has_gaps_for_teacher():
    """Sổ tay draft phải liệt kê rõ chỗ giáo viên cần bổ sung."""
    doc = MethodDoc(
        goal_type="prove_concyclic",
        title_vi="Chứng minh đồng viên",
        approaches=[Approach(title="Tổng hai góc đối", when_to_use="có góc vuông")],
        status=ReviewStatus.NEEDS_TEACHER,
    )
    gaps = doc.coverage_gaps()
    assert any("khi nào KHÔNG dùng" in g for g in gaps)
    assert any("bẫy" in g for g in gaps)


def test_markdown_shows_placeholder_before_review():
    doc = MethodDoc(
        goal_type="prove_tangent", title_vi="Chứng minh tiếp tuyến",
        approaches=[Approach(title="Bán kính vuông góc tại tiếp điểm")],
        status=ReviewStatus.NEEDS_TEACHER,
    )
    md = doc.to_markdown()
    assert "_(giáo viên bổ sung)_" in md      # chỗ trống hiện rõ


def test_rag_gate_blocks_unreviewed(tmp_path):
    """Sổ tay chưa soát KHÔNG được vào RAG."""
    draft = MethodDoc(goal_type="prove_concyclic", title_vi="X",
                      approaches=[Approach(title="A")], status=ReviewStatus.NEEDS_TEACHER)
    reviewed = MethodDoc(
        goal_type="prove_tangent", title_vi="Y",
        approaches=[Approach(title="B", when_not="khi chưa có tiếp điểm",
                             pitfalls=["quên điều kiện"], example_ids=["hn-2024-c4"])],
        status=ReviewStatus.REVIEWED,
    )
    (tmp_path / "prove_concyclic.md").write_text(draft.to_markdown(), encoding="utf-8")
    (tmp_path / "prove_tangent.md").write_text(reviewed.to_markdown(), encoding="utf-8")

    gate = gate_for_rag(tmp_path)
    assert "prove_tangent" in gate["ready_for_rag"]
    assert "prove_concyclic" in gate["pending_review"]


def test_validate_reviewed_catches_incomplete(tmp_path):
    doc = MethodDoc(goal_type="x", title_vi="X",
                    approaches=[Approach(title="A")], status=ReviewStatus.NEEDS_TEACHER)
    p = tmp_path / "x.md"
    p.write_text(doc.to_markdown(), encoding="utf-8")
    ok, issues = validate_reviewed(p)
    assert not ok
    assert len(issues) >= 2                    # còn placeholder + chưa reviewed
