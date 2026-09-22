"""Kiểm thử engine dựng hình và verifier — chạy được KHÔNG cần LLM.

Đây là lý do nên tách phần hình học ra khỏi tầng agent: nó kiểm thử được
tất định, nhanh, và bắt lỗi hồi quy ngay lập tức.
"""

import math

import pytest
from math9_geometry.construct import build
from math9_geometry.dsl import Construction, ConstructionOp as Op
from math9_geometry.layout import best_figure, score_figure
from math9_geometry.primitives import GeometryError, dist
from math9_geometry.render_svg import render
from math9_verifier.geometry import verify
from math9_verifier.lemma_finder import find_lemmas
from math9_verifier.predicates import Predicate


@pytest.fixture
def two_tangents() -> Construction:
    """Cho (O) và A nằm ngoài. Kẻ hai tiếp tuyến AB, AC. H = BC ∩ OA."""
    return Construction(ops=[
        Op(op="free", name="O"),
        Op(op="circle_center_radius", name="w", args=["O"], params={"radius": 2.0}),
        Op(op="free", name="A", params={"outside": "w"}),
        Op(op="tangent_from", name="t1", args=["w", "A"],
           params={"branch": 0, "touch_point": "B"}),
        Op(op="tangent_from", name="t2", args=["w", "A"],
           params={"branch": 1, "touch_point": "C"}),
        Op(op="segment", name="BC", args=["B", "C"]),
        Op(op="segment", name="OA", args=["O", "A"]),
        Op(op="intersect", name="H", args=["line:BC", "line:OA"]),
    ])


def test_true_claims_hold(two_tangents):
    v = verify(two_tangents, [
        Predicate("concyclic", ["A", "B", "O", "C"]),
        Predicate("perpendicular", ["O", "A", "B", "C"]),
        Predicate("equal_length", ["A", "B", "A", "C"]),
        Predicate("midpoint", ["H", "B", "C"]),
    ])
    assert v.ok, [repr(f.predicate) for f in v.failures()]
    assert v.n_configs >= 4


def test_false_claim_is_caught(two_tangents):
    """Verifier phải BẮT được mệnh đề sai — đây là giá trị cốt lõi của nó."""
    v = verify(two_tangents, [Predicate("collinear", ["A", "B", "C"])])
    assert not v.ok


def test_tangent_is_actually_tangent(two_tangents):
    """Hình do engine dựng phải đúng quan hệ, không 'gần đúng'."""
    fig = build(two_tangents, seed=7)
    assert abs(dist(fig.point("O"), fig.point("B")) - 2.0) < 1e-9


def test_thales_right_angle():
    """Góc nội tiếp chắn nửa đường tròn là góc vuông."""
    c = Construction(ops=[
        Op(op="free", name="B"),
        Op(op="free", name="C", params={"min_dist": ["B", 3.0]}),
        Op(op="circle_diameter", name="w", args=["B", "C"]),
        Op(op="on_object", name="A", args=["w"]),
    ])
    assert verify(c, [Predicate("right_angle", ["B", "A", "C"])]).ok


def test_triangle_hint_respected():
    c = Construction(ops=[Op(op="triangle", args=["A", "B", "C"],
                             params={"hint": "right"})])
    fig = build(c, seed=3)
    from math9_geometry.primitives import angle_at
    angs = [angle_at(fig.point("A"), fig.point("B"), fig.point("C"))]
    assert any(abs(a - math.pi / 2) < 1e-9 for a in angs)


def test_degenerate_construction_raises():
    c = Construction(ops=[
        Op(op="free", name="A"),
        Op(op="line", name="l1", args=["A", "A"]),
    ])
    with pytest.raises(GeometryError):
        build(c, seed=1)


def test_layout_picks_readable_figure(two_tangents):
    fig, q = best_figure(two_tangents)
    assert q.score > 0.5
    assert q.min_point_gap > 0.05


def test_render_produces_svg(two_tangents):
    svg = render(build(two_tangents, seed=4))
    assert svg.startswith("<svg") and "</svg>" in svg
    assert svg.count("<circle") >= 4        # 1 đường tròn + các điểm


def test_lemma_finder_discovers_midpoint(two_tangents):
    """Bộ dò bổ đề phải tìm ra H là trung điểm BC mà không được mách trước."""
    lemmas = find_lemmas(two_tangents, limit=20)
    assert any(str(p.kind) == "midpoint" and p.args[0] == "H" for p in lemmas)
