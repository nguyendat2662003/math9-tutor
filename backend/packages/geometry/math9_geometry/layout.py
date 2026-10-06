"""Chọn cấu hình 'đẹp' và đặt nhãn tránh chồng lấn.

Engine dựng hình cho tọa độ ĐÚNG, nhưng đúng chưa chắc đã dễ nhìn: tam giác
có thể quá bẹt, hai điểm có thể sát nhau, nhãn có thể đè lên nét vẽ. Module
này thử nhiều seed và chấm điểm để chọn cấu hình dễ nhìn nhất.

Đây là bước rẻ tiền nhưng nâng chất lượng cảm nhận rất nhiều.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

from .construct import Figure, build
from .dsl import Construction
from .primitives import Circle, GeometryError, Line, Point, Segment, dist

CANDIDATE_SEEDS = tuple(range(1, 41))


@dataclass
class Quality:
    score: float
    min_point_gap: float
    min_point_line_gap: float
    aspect: float
    reasons: list[str]


def _bbox(pts: list[Point]) -> tuple[float, float, float, float]:
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def score_figure(fig: Figure) -> Quality:
    """Điểm càng cao càng dễ nhìn. Trả về 0 nếu hình suy biến."""
    pts = list(fig.points().values())
    if len(pts) < 2:
        return Quality(0.0, 0.0, 0.0, 1.0, ["ít hơn 2 điểm"])

    x0, y0, x1, y1 = _bbox(pts)
    w, h = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    diag = math.hypot(w, h)
    reasons: list[str] = []

    gap = min(dist(a, b) for a, b in combinations(pts, 2)) / diag
    if gap < 0.06:
        reasons.append("hai điểm quá sát nhau")

    pl_gap = 1.0
    for name, obj in fig.objects.items():
        if isinstance(obj, Segment):
            line = obj.to_line()
        elif isinstance(obj, Line):
            line = obj
        else:
            continue
        for p in pts:
            d = abs(
                (p.x - line.p.x) * line.d.y - (p.y - line.p.y) * line.d.x
            ) / diag
            if 1e-6 < d < pl_gap:
                pl_gap = d
    if pl_gap < 0.04:
        reasons.append("có điểm nằm gần sát một đường thẳng khác")

    aspect = max(w / h, h / w)
    if aspect > 3.0:
        reasons.append("hình quá dẹt")

    # Đường tròn quá lớn so với khung cũng gây khó nhìn
    for obj in fig.objects.values():
        if isinstance(obj, Circle) and obj.radius > diag * 1.2:
            reasons.append("đường tròn lớn hơn nhiều so với phần còn lại")
            break

    score = (
        min(gap / 0.12, 1.0) * 0.45
        + min(pl_gap / 0.08, 1.0) * 0.35
        + max(0.0, 1.0 - (aspect - 1.0) / 2.5) * 0.20
    )
    return Quality(score, gap, pl_gap, aspect, reasons)


def best_figure(
    construction: Construction, seeds: tuple[int, ...] = CANDIDATE_SEEDS, tries: int = 12
) -> tuple[Figure, Quality]:
    """Thử nhiều seed, trả về cấu hình dễ nhìn nhất."""
    best: tuple[Figure, Quality] | None = None
    tried = 0
    for s in seeds:
        if tried >= tries and best and best[1].score > 0.75:
            break
        try:
            fig = build(construction, seed=s)
        except GeometryError:
            continue
        tried += 1
        q = score_figure(fig)
        if best is None or q.score > best[1].score:
            best = (fig, q)
    if best is None:
        raise GeometryError("Không dựng được hình ở bất kỳ cấu hình nào")
    return best


def label_offsets(fig: Figure, radius: float = 14.0) -> dict[str, tuple[float, float]]:
    """Đặt nhãn theo hướng ra xa trọng tâm, tránh đè lên các điểm lân cận."""
    pts = fig.points()
    if not pts:
        return {}
    cx = sum(p.x for p in pts.values()) / len(pts)
    cy = sum(p.y for p in pts.values()) / len(pts)

    out: dict[str, tuple[float, float]] = {}
    for name, p in pts.items():
        dx, dy = p.x - cx, p.y - cy
        n = math.hypot(dx, dy)
        if n < 1e-9:
            dx, dy, n = 1.0, 1.0, math.sqrt(2)
        base = (dx / n, dy / n)

        # Nếu hướng mặc định đâm vào điểm khác, quay dần tìm hướng trống
        best_dir, best_clear = base, -1.0
        for k in range(12):
            ang = math.atan2(base[1], base[0]) + k * math.pi / 6
            cand = (math.cos(ang), math.sin(ang))
            probe = Point(p.x + cand[0] * 0.4, p.y + cand[1] * 0.4)
            clear = min(
                (dist(probe, q) for m, q in pts.items() if m != name), default=9.9
            )
            if clear > best_clear:
                best_dir, best_clear = cand, clear
            if clear > 0.9:
                break
        out[name] = (best_dir[0] * radius, -best_dir[1] * radius)
    return out
