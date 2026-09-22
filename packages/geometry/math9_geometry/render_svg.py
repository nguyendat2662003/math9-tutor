"""Render hình ra SVG theo chuẩn ký hiệu SGK Việt Nam.

Hỗ trợ vẽ theo từng bước lời giải: mỗi đối tượng mang `step_ref`, renderer
nhận `up_to_step` để chỉ vẽ tới bước đó và tô sáng đối tượng của bước hiện tại.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .construct import Figure
from .layout import label_offsets
from .primitives import Circle, Line, Point, Segment, dist, dot

PALETTE = {
    "solid": "#1f2937",
    "dashed": "#6b7280",
    "auxiliary": "#9ca3af",
    "highlight": "#dc2626",
    "point": "#111827",
    "label": "#111827",
    "mark": "#2563eb",
}


@dataclass
class Viewport:
    width: int = 520
    height: int = 400
    padding: int = 36


class SvgRenderer:
    def __init__(self, fig: Figure, vp: Viewport | None = None):
        self.fig = fig
        self.vp = vp or Viewport()
        self._fit()

    # -- ánh xạ tọa độ ----------------------------------------------------

    def _fit(self) -> None:
        pts = list(self.fig.points().values())
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        for o in self.fig.objects.values():
            if isinstance(o, Circle):
                xs += [o.center.x - o.radius, o.center.x + o.radius]
                ys += [o.center.y - o.radius, o.center.y + o.radius]
        if not xs:
            xs, ys = [0, 1], [0, 1]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)
        pad = self.vp.padding
        self.k = min(
            (self.vp.width - 2 * pad) / w, (self.vp.height - 2 * pad) / h
        )
        self.ox = pad + (self.vp.width - 2 * pad - w * self.k) / 2 - x0 * self.k
        self.oy = self.vp.height - pad - (
            self.vp.height - 2 * pad - h * self.k
        ) / 2 + y0 * self.k

    def T(self, p: Point) -> tuple[float, float]:
        return (self.ox + p.x * self.k, self.oy - p.y * self.k)

    # -- vẽ ----------------------------------------------------------------

    def render(self, up_to_step: str | None = None, highlight_step: str | None = None) -> str:
        allowed = self._allowed_names(up_to_step)
        body: list[str] = []

        # Thứ tự vẽ: đường tròn -> đường thẳng -> đoạn -> ký hiệu -> điểm -> nhãn
        for name in self.fig.order:
            if name not in allowed:
                continue
            obj = self.fig.objects[name]
            style = self.fig.styles.get(name, "solid")
            if highlight_step and self.fig.step_refs.get(name) == highlight_step:
                style = "highlight"
            if isinstance(obj, Circle):
                body.append(self._wrap(name, "circle", self._circle(obj, style), self._pts_on(obj)))
        for name in self.fig.order:
            if name not in allowed:
                continue
            obj = self.fig.objects[name]
            style = self.fig.styles.get(name, "solid")
            if highlight_step and self.fig.step_refs.get(name) == highlight_step:
                style = "highlight"
            if isinstance(obj, Segment):
                body.append(self._wrap(name, "segment", self._seg(obj.a, obj.b, style), self._pts_on(obj)))
            elif isinstance(obj, Line):
                body.append(self._wrap(name, "line", self._infinite_line(obj, style), self._pts_on(obj)))

        body += self._marks(allowed)

        offs = label_offsets(self.fig)
        for name, p in self.fig.points().items():
            if name not in allowed:
                continue
            x, y = self.T(p)
            dx, dy = offs.get(name, (12, -12))
            body.append(self._wrap(name, "point", (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{PALETTE["point"]}"/>'
                f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" font-size="15" '
                f'font-family="Georgia, serif" font-style="italic" '
                f'fill="{PALETTE["label"]}" text-anchor="middle" '
                f'dominant-baseline="central">{name}</text>'
            ), [name]))

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '
            f'{self.vp.width} {self.vp.height}" width="100%">'
            f'<defs><clipPath id="vp"><rect x="0" y="0" width="{self.vp.width}" '
            f'height="{self.vp.height}"/></clipPath></defs>'
            + "".join(body)
            + "</svg>"
        )

    @staticmethod
    def _wrap(name: str, kind: str, inner: str, pts: list[str]) -> str:
        """Bọc mỗi đối tượng trong <g data-name data-kind data-pts> để frontend tô sáng theo bước."""
        return f'<g data-name="{name}" data-kind="{kind}" data-pts="{",".join(pts)}">{inner}</g>'

    def _pts_on(self, obj) -> list[str]:
        """Tên các điểm nằm trên đối tượng (đầu mút đoạn, điểm trên đường/đường tròn)."""
        out = []
        for n, p in self.fig.points().items():
            if isinstance(obj, Segment):
                if dist(p, obj.a) < 1e-7 or dist(p, obj.b) < 1e-7:
                    out.append(n)
            elif isinstance(obj, (Line, Circle)) and obj.contains(p, tol=1e-6):
                out.append(n)
        return out

    def _allowed_names(self, up_to_step: str | None) -> set[str]:
        if up_to_step is None:
            return set(self.fig.objects)
        allowed, reached = set(), False
        for name in self.fig.order:
            allowed.add(name)
            if self.fig.step_refs.get(name) == up_to_step:
                reached = True
            elif reached and self.fig.step_refs.get(name) not in (None, up_to_step):
                allowed.discard(name)
        return allowed

    # -- nguyên thủy SVG ---------------------------------------------------

    def _stroke(self, style: str) -> str:
        color = PALETTE.get(style, PALETTE["solid"])
        w = 2.0 if style == "highlight" else 1.4
        dash = ' stroke-dasharray="5 4"' if style in ("dashed", "auxiliary") else ""
        return f'stroke="{color}" stroke-width="{w}" fill="none"{dash}'

    def _seg(self, a: Point, b: Point, style: str) -> str:
        x1, y1 = self.T(a)
        x2, y2 = self.T(b)
        return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {self._stroke(style)}/>'

    def _circle(self, c: Circle, style: str) -> str:
        cx, cy = self.T(c.center)
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{c.radius * self.k:.1f}" {self._stroke(style)}/>'

    def _infinite_line(self, line: Line, style: str) -> str:
        """Vẽ đường thẳng theo chuẩn SGK: chỉ qua các điểm có tên nằm trên nó, kéo
        thêm một đoạn ngắn ở hai đầu — không kéo dài hết khung như đường vô hạn."""
        ts = [
            dot(p - line.p, line.d)
            for p in self.fig.points().values()
            if line.contains(p, tol=1e-6)
        ]
        ext = self._extent() * 0.08
        if len(ts) >= 2:
            lo, hi = min(ts) - ext, max(ts) + ext
        else:
            t0 = ts[0] if ts else 0.0
            lo, hi = t0 - ext * 3, t0 + ext * 3
        a = Point(line.p.x + line.d.x * lo, line.p.y + line.d.y * lo)
        b = Point(line.p.x + line.d.x * hi, line.p.y + line.d.y * hi)
        x1, y1 = self.T(a)
        x2, y2 = self.T(b)
        return (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'{self._stroke(style)} clip-path="url(#vp)"/>'
        )

    def _extent(self) -> float:
        """Đường chéo hộp bao các điểm, đơn vị tọa độ hình."""
        pts = list(self.fig.points().values())
        if len(pts) < 2:
            return 1.0
        xs, ys = [p.x for p in pts], [p.y for p in pts]
        return math.hypot(max(xs) - min(xs), max(ys) - min(ys)) or 1.0

    # -- ký hiệu -----------------------------------------------------------

    def _marks(self, allowed: set[str]) -> list[str]:
        out: list[str] = []
        for m in self.fig.marks:
            kind = m.kind.split(".")[-1]
            try:
                if kind == "RIGHT_ANGLE_MARK" or kind == "right_angle_mark":
                    out.append(self._right_angle(*[self.fig.point(n) for n in m.args]))
                elif kind in ("EQUAL_SEGMENTS", "equal_segments"):
                    n = int(m.params.get("ticks", 1))
                    for i in range(0, len(m.args) - 1, 2):
                        out.append(
                            self._ticks(
                                self.fig.point(m.args[i]),
                                self.fig.point(m.args[i + 1]),
                                n,
                            )
                        )
            except Exception:  # ký hiệu lỗi không được làm hỏng cả hình
                continue
        return out

    def _right_angle(self, a: Point, v: Point, b: Point) -> str:
        """Ô vuông ký hiệu góc vuông tại đỉnh V — chuẩn trình bày Việt Nam."""
        s = 12.0
        ua = _unit_screen(self.T(v), self.T(a))
        ub = _unit_screen(self.T(v), self.T(b))
        vx, vy = self.T(v)
        p1 = (vx + ua[0] * s, vy + ua[1] * s)
        p3 = (vx + ub[0] * s, vy + ub[1] * s)
        p2 = (p1[0] + ub[0] * s, p1[1] + ub[1] * s)
        pts = f"{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}"
        return f'<polyline points="{pts}" stroke="{PALETTE["mark"]}" stroke-width="1.2" fill="none"/>'

    def _ticks(self, a: Point, b: Point, n: int) -> str:
        """Gạch chéo ký hiệu hai đoạn bằng nhau."""
        x1, y1 = self.T(a)
        x2, y2 = self.T(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ang = math.atan2(y2 - y1, x2 - x1)
        px, py = -math.sin(ang), math.cos(ang)
        dx, dy = math.cos(ang), math.sin(ang)
        parts = []
        for i in range(n):
            off = (i - (n - 1) / 2) * 5
            cx, cy = mx + dx * off, my + dy * off
            parts.append(
                f'<line x1="{cx - px * 5:.1f}" y1="{cy - py * 5:.1f}" '
                f'x2="{cx + px * 5:.1f}" y2="{cy + py * 5:.1f}" '
                f'stroke="{PALETTE["mark"]}" stroke-width="1.2"/>'
            )
        return "".join(parts)


def _unit_screen(o: tuple[float, float], p: tuple[float, float]) -> tuple[float, float]:
    dx, dy = p[0] - o[0], p[1] - o[1]
    n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n)


def render(fig: Figure, **kw) -> str:
    return SvgRenderer(fig).render(**kw)
