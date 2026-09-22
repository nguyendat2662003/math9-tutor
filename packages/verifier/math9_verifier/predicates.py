"""Vị từ hình học — mệnh đề kiểm tra được bằng số.

Mỗi kết luận của bài toán hình học lớp 9 đều quy về một vị từ ở đây. Verifier
dựng lại hình với nhiều cấu hình ngẫu nhiên và kiểm tra vị từ trên từng cấu
hình; đúng trên mọi cấu hình mới coi là đúng.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Callable

from math9_geometry.construct import Figure
from math9_geometry.primitives import (
    Circle,
    GeometryError,
    Line,
    Point,
    Segment,
    angle_at,
    circumcircle,
    cross,
    dist,
    dot,
    midpoint,
)


class PredKind(StrEnum):
    COLLINEAR = "collinear"
    CONCYCLIC = "concyclic"
    CONCURRENT = "concurrent"
    EQUAL_LENGTH = "equal_length"
    EQUAL_ANGLE = "equal_angle"
    PERPENDICULAR = "perpendicular"
    PARALLEL = "parallel"
    TANGENT = "tangent"
    MIDPOINT = "midpoint"
    ON_OBJECT = "on_object"
    RATIO_EQUAL = "ratio_equal"
    IS_ISOSCELES = "is_isosceles"
    RIGHT_ANGLE = "right_angle"


class Predicate:
    """Một mệnh đề cần kiểm chứng, ví dụ Predicate('concyclic', ['A','B','O','C'])."""

    __slots__ = ("kind", "args", "value")

    def __init__(self, kind: str, args: list[str], value: float | None = None):
        self.kind = PredKind(kind)
        self.args = args
        self.value = value

    def __repr__(self) -> str:
        return f"{self.kind}({', '.join(self.args)})"

    def __hash__(self) -> int:
        return hash((self.kind, tuple(self.args), self.value))

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Predicate) and repr(o) == repr(self)


# --------------------------------------------------------------------------
# Cài đặt — mỗi hàm trả về sai lệch (residual), càng gần 0 càng đúng
# --------------------------------------------------------------------------

def _pts(fig: Figure, names: list[str]) -> list[Point]:
    return [fig.point(n) for n in names]


def _r_collinear(fig: Figure, a: list[str], v: float | None) -> float:
    p = _pts(fig, a)
    scale = max(dist(p[0], p[1]), 1e-9)
    return abs(cross(p[1] - p[0], p[2] - p[0])) / scale


def _r_concyclic(fig: Figure, a: list[str], v: float | None) -> float:
    p = _pts(fig, a)
    c = circumcircle(p[0], p[1], p[2])
    return max(abs(dist(c.center, q) - c.radius) for q in p[3:]) / max(c.radius, 1e-9)


def _r_concurrent(fig: Figure, a: list[str], v: float | None) -> float:
    """Ba đường thẳng đồng quy. Đối số là tên 3 đường hoặc 6 điểm."""
    lines = [_as_line(fig, n) for n in a] if len(a) == 3 else [
        Line.through(fig.point(a[i]), fig.point(a[i + 1])) for i in (0, 2, 4)
    ]
    from math9_geometry.primitives import intersect_line_line

    x = intersect_line_line(lines[0], lines[1])
    return abs(cross(lines[2].d, x - lines[2].p))


def _r_equal_length(fig: Figure, a: list[str], v: float | None) -> float:
    d1 = dist(fig.point(a[0]), fig.point(a[1]))
    d2 = dist(fig.point(a[2]), fig.point(a[3]))
    return abs(d1 - d2) / max(d1, d2, 1e-9)


def _r_ratio_equal(fig: Figure, a: list[str], v: float | None) -> float:
    d1 = dist(fig.point(a[0]), fig.point(a[1]))
    d2 = dist(fig.point(a[2]), fig.point(a[3]))
    return abs(d1 - (v or 1.0) * d2) / max(d1, 1e-9)


def _r_equal_angle(fig: Figure, a: list[str], v: float | None) -> float:
    """args = [A,V1,B, C,V2,D] — góc AV1B bằng góc CV2D."""
    p = _pts(fig, a)
    return abs(angle_at(p[1], p[0], p[2]) - angle_at(p[4], p[3], p[5]))


def _r_perpendicular(fig: Figure, a: list[str], v: float | None) -> float:
    p = _pts(fig, a)
    u, w = p[1] - p[0], p[3] - p[2]
    return abs(dot(u, w)) / max(u.norm() * w.norm(), 1e-9)


def _r_parallel(fig: Figure, a: list[str], v: float | None) -> float:
    p = _pts(fig, a)
    u, w = p[1] - p[0], p[3] - p[2]
    return abs(cross(u, w)) / max(u.norm() * w.norm(), 1e-9)


def _r_right_angle(fig: Figure, a: list[str], v: float | None) -> float:
    """args = [A, V, B] — góc AVB vuông."""
    import math

    p = _pts(fig, a)
    return abs(angle_at(p[1], p[0], p[2]) - math.pi / 2)


def _r_midpoint(fig: Figure, a: list[str], v: float | None) -> float:
    """args = [M, A, B] — M là trung điểm AB."""
    m, x, y = _pts(fig, a)
    return dist(m, midpoint(x, y)) / max(dist(x, y), 1e-9)


def _r_tangent(fig: Figure, a: list[str], v: float | None) -> float:
    """args = [tên đường thẳng, tên đường tròn]."""
    line = _as_line(fig, a[0])
    circ = fig.objects[a[1]]
    if not isinstance(circ, Circle):
        raise GeometryError(f"'{a[1]}' không phải đường tròn")
    from math9_geometry.primitives import foot_of_perpendicular

    d = dist(circ.center, foot_of_perpendicular(circ.center, line))
    return abs(d - circ.radius) / max(circ.radius, 1e-9)


def _r_on_object(fig: Figure, a: list[str], v: float | None) -> float:
    """args = [tên điểm, tên đối tượng]."""
    p = fig.point(a[0])
    o = fig.objects[a[1]]
    if isinstance(o, Circle):
        return abs(dist(o.center, p) - o.radius) / max(o.radius, 1e-9)
    line = _as_line(fig, a[1])
    return abs(cross(line.d, p - line.p))


def _r_is_isosceles(fig: Figure, a: list[str], v: float | None) -> float:
    """args = [A, B, C] — tam giác cân tại A."""
    return _r_equal_length(fig, [a[0], a[1], a[0], a[2]], None)


def _as_line(fig: Figure, ref: str) -> Line:
    o = fig.objects.get(ref)
    if isinstance(o, Line):
        return o
    if isinstance(o, Segment):
        return o.to_line()
    if len(ref) == 2 and all(c in fig.objects for c in ref):
        return Line.through(fig.point(ref[0]), fig.point(ref[1]))
    raise GeometryError(f"'{ref}' không phải đường thẳng")


RESIDUALS: dict[PredKind, Callable[[Figure, list[str], float | None], float]] = {
    PredKind.COLLINEAR: _r_collinear,
    PredKind.CONCYCLIC: _r_concyclic,
    PredKind.CONCURRENT: _r_concurrent,
    PredKind.EQUAL_LENGTH: _r_equal_length,
    PredKind.EQUAL_ANGLE: _r_equal_angle,
    PredKind.PERPENDICULAR: _r_perpendicular,
    PredKind.PARALLEL: _r_parallel,
    PredKind.TANGENT: _r_tangent,
    PredKind.MIDPOINT: _r_midpoint,
    PredKind.ON_OBJECT: _r_on_object,
    PredKind.RATIO_EQUAL: _r_ratio_equal,
    PredKind.IS_ISOSCELES: _r_is_isosceles,
    PredKind.RIGHT_ANGLE: _r_right_angle,
}


def residual(fig: Figure, pred: Predicate) -> float:
    """Sai lệch của vị từ trên một cấu hình cụ thể. 0 nghĩa là đúng."""
    return RESIDUALS[pred.kind](fig, pred.args, pred.value)
