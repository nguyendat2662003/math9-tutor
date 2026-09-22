"""Giải ràng buộc số cho cấu hình không dựng tuần tự được.

Ví dụ: "lấy M trên cung nhỏ BC sao cho MB = 2MC". Không có phép dựng thước
compa trực tiếp, nên ta đặt M tự do trên cung rồi tối ưu vị trí.

Biến số là tham số của MỌI điểm tự do (FREE: x, y; ON_OBJECT: một tham số trên
đối tượng). Mỗi lần thử một bộ tham số, TOÀN BỘ hình được dựng lại từ đầu, nên
các điểm phụ thuộc (giao điểm, chân đường cao...) luôn đúng quan hệ — và ràng
buộc có thể nhắc tới cả những điểm phụ thuộc đó.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares

from .dsl import Construction, OpKind
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


def solve_constraints(ctor, construction: Construction, max_iter: int = 300) -> None:
    """Tinh chỉnh tham số các điểm tự do để thỏa mãn ràng buộc, rồi dựng lại hình."""
    ops = construction.ops
    free_ops = [o for o in ops if o.op in (OpKind.FREE, OpKind.ON_OBJECT) and o.name]
    if not free_ops:
        raise GeometryError("Không có điểm tự do nào để thỏa ràng buộc")

    # Tham số ban đầu lấy từ hình vừa dựng
    x0: list[float] = []
    layout: list[tuple[str, int]] = []          # (tên, số tham số)
    for o in free_ops:
        p = ctor.objects[o.name]
        if o.op == OpKind.FREE:
            x0 += [p.x, p.y]
            layout.append((o.name, 2))
        else:
            x0.append(ctor.param_of(ctor._get(o.args[0]), p))
            layout.append((o.name, 1))

    def apply(x: np.ndarray) -> None:
        i = 0
        for name, n in layout:
            ctor.overrides[name] = tuple(float(v) for v in x[i:i + n])
            i += n
        ctor.rebuild(ops)

    def f(x: np.ndarray) -> list[float]:
        try:
            apply(x)
        except GeometryError:
            return [1e3] * len(construction.constraints)
        out = []
        for c in construction.constraints:
            try:
                out.append(_residual(c.kind, [ctor._pt(a) for a in c.args], c.value))
            except GeometryError:
                out.append(1e3)
        return out

    res = least_squares(f, np.array(x0), max_nfev=max_iter)
    worst = max(abs(r) for r in f(res.x))
    if worst > 1e-6:
        raise GeometryError(f"Không tìm được cấu hình thỏa mãn mọi ràng buộc (sai lệch {worst:.2e})")
