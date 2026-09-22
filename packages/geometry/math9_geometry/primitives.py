"""Phép toán hình học phẳng cơ bản.

Tầng thấp nhất của engine dựng hình. Không phụ thuộc LLM, không phụ thuộc DSL.
Mọi hàm ở đây đều thuần toán học và kiểm thử được độc lập.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

EPS = 1e-9


class GeometryError(Exception):
    """Phép dựng không thực hiện được (suy biến, không có giao điểm...)."""


# --------------------------------------------------------------------------
# Kiểu dữ liệu
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, o: "Point") -> "Point":
        return Point(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Point") -> "Point":
        return Point(self.x - o.x, self.y - o.y)

    def __mul__(self, k: float) -> "Point":
        return Point(self.x * k, self.y * k)

    __rmul__ = __mul__

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def unit(self) -> "Point":
        n = self.norm()
        if n < EPS:
            raise GeometryError("Vector không xác định phương")
        return Point(self.x / n, self.y / n)

    def perp(self) -> "Point":
        """Quay 90 độ ngược chiều kim đồng hồ."""
        return Point(-self.y, self.x)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass(frozen=True)
class Line:
    """Đường thẳng qua `p` với vector chỉ phương `d` (đã chuẩn hóa)."""

    p: Point
    d: Point

    @staticmethod
    def through(a: Point, b: Point) -> "Line":
        if dist(a, b) < EPS:
            raise GeometryError("Hai điểm trùng nhau, không xác định đường thẳng")
        return Line(a, (b - a).unit())

    def normal(self) -> Point:
        return self.d.perp()

    def contains(self, q: Point, tol: float = 1e-7) -> bool:
        return abs(cross(self.d, q - self.p)) < tol


@dataclass(frozen=True)
class Circle:
    center: Point
    radius: float

    @staticmethod
    def through(center: Point, on: Point) -> "Circle":
        return Circle(center, dist(center, on))

    def contains(self, q: Point, tol: float = 1e-7) -> bool:
        return abs(dist(self.center, q) - self.radius) < tol

    def point_at(self, theta: float) -> Point:
        return Point(
            self.center.x + self.radius * math.cos(theta),
            self.center.y + self.radius * math.sin(theta),
        )


@dataclass(frozen=True)
class Segment:
    a: Point
    b: Point

    def to_line(self) -> Line:
        return Line.through(self.a, self.b)

    def length(self) -> float:
        return dist(self.a, self.b)


# --------------------------------------------------------------------------
# Hàm tiện ích
# --------------------------------------------------------------------------

def dist(a: Point, b: Point) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def dot(a: Point, b: Point) -> float:
    return a.x * b.x + a.y * b.y


def cross(a: Point, b: Point) -> float:
    return a.x * b.y - a.y * b.x


def midpoint(a: Point, b: Point) -> Point:
    return Point((a.x + b.x) / 2, (a.y + b.y) / 2)


def divide_ratio(a: Point, b: Point, t: float) -> Point:
    """Điểm chia đoạn AB theo tỉ lệ t (t=0 -> A, t=1 -> B)."""
    return Point(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)


def angle_at(vertex: Point, a: Point, b: Point) -> float:
    """Góc AVB theo radian, luôn thuộc [0, pi]."""
    u, v = a - vertex, b - vertex
    if u.norm() < EPS or v.norm() < EPS:
        raise GeometryError("Không xác định được góc: điểm trùng đỉnh")
    c = max(-1.0, min(1.0, dot(u, v) / (u.norm() * v.norm())))
    return math.acos(c)


def signed_area(a: Point, b: Point, c: Point) -> float:
    return cross(b - a, c - a) / 2


# --------------------------------------------------------------------------
# Giao điểm
# --------------------------------------------------------------------------

def intersect_line_line(l1: Line, l2: Line) -> Point:
    den = cross(l1.d, l2.d)
    if abs(den) < EPS:
        raise GeometryError("Hai đường thẳng song song hoặc trùng nhau")
    t = cross(l2.p - l1.p, l2.d) / den
    return Point(l1.p.x + l1.d.x * t, l1.p.y + l1.d.y * t)


def intersect_line_circle(line: Line, circle: Circle) -> list[Point]:
    """Trả về 0, 1 hoặc 2 giao điểm, sắp theo tham số tăng dần trên đường thẳng."""
    f = line.p - circle.center
    b = dot(f, line.d)
    c = dot(f, f) - circle.radius**2
    disc = b * b - c
    if disc < -EPS:
        return []
    disc = max(disc, 0.0)
    r = math.sqrt(disc)
    ts = sorted({-b - r, -b + r})
    return [Point(line.p.x + line.d.x * t, line.p.y + line.d.y * t) for t in ts]


def intersect_circle_circle(c1: Circle, c2: Circle) -> list[Point]:
    d = dist(c1.center, c2.center)
    if d < EPS:
        return []
    if d > c1.radius + c2.radius + EPS or d < abs(c1.radius - c2.radius) - EPS:
        return []
    a = (c1.radius**2 - c2.radius**2 + d * d) / (2 * d)
    h2 = c1.radius**2 - a * a
    h = math.sqrt(max(h2, 0.0))
    base = divide_ratio(c1.center, c2.center, a / d)
    if h < EPS:
        return [base]
    u = (c2.center - c1.center).unit().perp()
    return [base - u * h, base + u * h]


# --------------------------------------------------------------------------
# Phép dựng
# --------------------------------------------------------------------------

def perpendicular_through(p: Point, line: Line) -> Line:
    return Line(p, line.d.perp())


def parallel_through(p: Point, line: Line) -> Line:
    return Line(p, line.d)


def foot_of_perpendicular(p: Point, line: Line) -> Point:
    t = dot(p - line.p, line.d)
    return Point(line.p.x + line.d.x * t, line.p.y + line.d.y * t)


def reflect_over_line(p: Point, line: Line) -> Point:
    f = foot_of_perpendicular(p, line)
    return Point(2 * f.x - p.x, 2 * f.y - p.y)


def reflect_over_point(p: Point, center: Point) -> Point:
    return Point(2 * center.x - p.x, 2 * center.y - p.y)


def perpendicular_bisector(a: Point, b: Point) -> Line:
    return Line(midpoint(a, b), (b - a).unit().perp())


def angle_bisector(vertex: Point, a: Point, b: Point) -> Line:
    """Phân giác trong của góc AVB."""
    u = (a - vertex).unit()
    v = (b - vertex).unit()
    d = u + v
    if d.norm() < EPS:
        raise GeometryError("Góc bẹt, không xác định phân giác")
    return Line(vertex, d.unit())


def circumcenter(a: Point, b: Point, c: Point) -> Point:
    if abs(signed_area(a, b, c)) < EPS:
        raise GeometryError("Ba điểm thẳng hàng, không có đường tròn ngoại tiếp")
    return intersect_line_line(
        perpendicular_bisector(a, b), perpendicular_bisector(b, c)
    )


def circumcircle(a: Point, b: Point, c: Point) -> Circle:
    o = circumcenter(a, b, c)
    return Circle(o, dist(o, a))


def incenter(a: Point, b: Point, c: Point) -> Point:
    la, lb, lc = dist(b, c), dist(c, a), dist(a, b)
    s = la + lb + lc
    return Point(
        (la * a.x + lb * b.x + lc * c.x) / s,
        (la * a.y + lb * b.y + lc * c.y) / s,
    )


def incircle(a: Point, b: Point, c: Point) -> Circle:
    i = incenter(a, b, c)
    return Circle(i, dist(i, foot_of_perpendicular(i, Line.through(b, c))))


def centroid(a: Point, b: Point, c: Point) -> Point:
    return Point((a.x + b.x + c.x) / 3, (a.y + b.y + c.y) / 3)


def orthocenter(a: Point, b: Point, c: Point) -> Point:
    return intersect_line_line(
        perpendicular_through(a, Line.through(b, c)),
        perpendicular_through(b, Line.through(a, c)),
    )


def tangent_at(circle: Circle, p: Point) -> Line:
    """Tiếp tuyến của đường tròn tại điểm P nằm trên đường tròn."""
    if abs(dist(circle.center, p) - circle.radius) > 1e-6:
        raise GeometryError("Điểm không nằm trên đường tròn")
    return Line(p, (p - circle.center).unit().perp())


def tangent_points_from(circle: Circle, p: Point) -> list[Point]:
    """Hai tiếp điểm của tiếp tuyến kẻ từ điểm P nằm ngoài đường tròn."""
    d = dist(circle.center, p)
    if d < circle.radius - EPS:
        raise GeometryError("Điểm nằm trong đường tròn, không kẻ được tiếp tuyến")
    if abs(d - circle.radius) < EPS:
        return [p]
    # Tiếp điểm nằm trên đường tròn đường kính OP (định lý góc nội tiếp chắn nửa đường tròn)
    mid = midpoint(circle.center, p)
    return intersect_circle_circle(circle, Circle(mid, d / 2))
