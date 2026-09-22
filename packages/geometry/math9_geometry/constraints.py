"""Giải ràng buộc số cho cấu hình không dựng tuần tự được.

Ví dụ: "lấy M trên cung nhỏ BC sao cho MB = 2MC". Không có phép dựng thước
compa trực tiếp, nên ta đặt M tự do trên cung rồi tối ưu vị trí.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares

from .dsl import Constraint
from .primitives import Circle, GeometryError, Point, angle_at, dist


def _residual(kind: str, pts: list[Point], value: float | None) -> float:
    if kind == "dist_eq":
        return dist(pts[0], pts[1]) - dist(pts[2], pts[3])
    if kind == "ratio":
        return dist(pts[0], pts[1]) - (value or 1.0) * dist(pts[2], pts[3])
    if kind == "angle_eq":
        return angle_at(pts[1], pts[0], pts[2]) - angle_at(pts[4], pts[3], pts[5])
    if kind == "collinear":
        ux, uy = pts[1].x - pts[0].x, pts[1].y - pts[0].y
        vx, vy = pts[2].x - pts[0].x, pts[2].y - pts[0].y
        return ux * vy - uy * vx
    if kind == "perpendicular":
        u = (pts[1].x - pts[0].x, pts[1].y - pts[0].y)
        v = (pts[3].x - pts[2].x, pts[3].y - pts[2].y)
        return u[0] * v[0] + u[1] * v[1]
    if kind == "concyclic":
        c = _circum(pts[0], pts[1], pts[2])
        return dist(c.center, pts[3]) - c.radius
    raise GeometryError(f"Chưa hỗ trợ ràng buộc '{kind}'")


def _circum(a: Point, b: Point, c: Point) -> Circle:
    from .primitives import circumcircle

    return circumcircle(a, b, c)


def solve_constraints(ctor, constraints: list[Constraint], max_iter: int = 200) -> None:
    """Tinh chỉnh vị trí các điểm tự do để thỏa mãn ràng buộc.

    Chỉ di chuyển những điểm được sinh bởi FREE/ON_OBJECT — các điểm dựng
    được giữ nguyên quan hệ vì chúng sẽ được tính lại sau.
    """
    movable = [
        n for n in ctor.order
        if isinstance(ctor.objects.get(n), Point) and ctor.styles.get(n) != "locked"
    ]
    involved = {a for c in constraints for a in c.args}
    movable = [n for n in movable if n in involved]
    if not movable:
        raise GeometryError("Không có điểm nào có thể di chuyển để thỏa ràng buộc")

    x0 = np.array([v for n in movable for v in ctor.objects[n].as_tuple()])

    def f(x: np.ndarray) -> list[float]:
        for i, n in enumerate(movable):
            ctor.objects[n] = Point(float(x[2 * i]), float(x[2 * i + 1]))
        out = []
        for c in constraints:
            try:
                out.append(_residual(c.kind, [ctor._pt(a) for a in c.args], c.value))
            except GeometryError:
                out.append(1e3)
        return out

    res = least_squares(f, x0, max_nfev=max_iter)
    f(res.x)
    if max(abs(r) for r in f(res.x)) > 1e-6:
        raise GeometryError("Không tìm được cấu hình thỏa mãn mọi ràng buộc")
