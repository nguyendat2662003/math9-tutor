"""Vẽ hình cho các bài trong kho mà đề nói "như hình vẽ", "biểu đồ...".

Đề gốc có hình; khi chép vào kho chỉ còn chữ. Không có hình thì học sinh không
làm được (vd vị trí điểm A quyết định góc BAC là 45° hay 135°). Mỗi bài như vậy
có một mục trong `data/exam/figures.yaml`; bài nào nhắc tới hình mà không có mục
thì bị loại khỏi đề (xem `needs_figure`).
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from html import escape
from pathlib import Path

import yaml

FIGURES = Path(__file__).resolve().parents[3] / "data" / "exam" / "figures.yaml"

# "hình chữ nhật", "hình trụ" không phải tham chiếu tới hình vẽ — chỉ bắt các cụm chỉ hình minh họa
_RE_NEEDS = re.compile(
    r"như hình|hình vẽ|hình bên|hình dưới|\(hình|Hình \d|biểu đồ|bảng bên|bảng dưới", re.I)

INK, MUTED, GRID = "#1f2937", "#6b7280", "#e7e5e4"
SERIES = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#0891b2"]
W, H = 480, 300
FONT = 'font-family="inherit" font-size="12"'


def needs_figure(text: str) -> bool:
    return bool(_RE_NEEDS.search(text))


@lru_cache(maxsize=1)
def load_figures(path: Path = FIGURES) -> dict[str, str]:
    """id bài / context_id -> SVG."""
    if not path.exists():
        return {}
    specs = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {key: _unique_ids(render_spec(spec), key) for key, spec in specs.items()}


def _unique_ids(svg: str, key: str) -> str:
    """Nhiều SVG nhúng cùng một trang dùng chung không gian id: id="vp" của hình này
    sẽ bị hình kia dùng nhầm. Gắn hậu tố theo bài để id không trùng."""
    suffix = re.sub(r"\W", "", key)
    for i in set(re.findall(r'id="([^"]+)"', svg)):
        svg = svg.replace(f'id="{i}"', f'id="{i}-{suffix}"').replace(f"url(#{i})", f"url(#{i}-{suffix})")
    return svg


def figure_for(item_id: str, group: str | None) -> str | None:
    figs = load_figures()
    return figs.get(item_id) or (figs.get(group) if group else None)


def render_spec(spec: dict) -> str:
    kind = spec["kind"]
    if kind == "svg":
        return spec["svg"].strip()
    if kind in ("bar", "line", "hist"):
        return _xy_chart(spec)
    if kind == "pie":
        return _pie(spec)
    if kind == "parabola":
        return _parabola(spec)
    if kind == "construction":
        return _construction(spec)
    raise ValueError(f"Loại hình không hỗ trợ: {kind}")


# ---------- biểu đồ cột / đoạn thẳng / tần số ghép nhóm ----------

def _nice_step(vmax: float) -> float:
    raw = vmax / 5
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    return next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)


def _fmt(v: float) -> str:
    return (f"{v:g}").replace(".", ",")


def _xy_chart(spec: dict) -> str:
    cats, vals, kind = spec["categories"], [float(v) for v in spec["values"]], spec["kind"]
    unit = spec.get("unit", "")
    left, right, top, bottom = 56, 16, 34, 58
    pw, ph = W - left - right, H - top - bottom
    step = _nice_step(max(vals))
    # chừa khoảng trên cột cao nhất cho nhãn số, không đè lên tiêu đề
    ymax = step * math.ceil(max(vals) * 1.1 / step)
    y = lambda v: top + ph - v / ymax * ph          # noqa: E731
    n = len(cats)
    slot = pw / n
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" {FONT} role="img">']
    if spec.get("title"):
        out.append(f'<text x="{W / 2}" y="18" text-anchor="middle" font-weight="600" fill="{INK}">{escape(spec["title"])}</text>')
    t = 0.0
    while t <= ymax + 1e-9:
        out.append(f'<line x1="{left}" y1="{y(t):.1f}" x2="{W - right}" y2="{y(t):.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{left - 6}" y="{y(t) + 4:.1f}" text-anchor="end" fill="{MUTED}">{_fmt(t)}</text>')
        t += step
    pts = []
    for i, (c, v) in enumerate(zip(cats, vals)):
        cx = left + slot * (i + 0.5)
        if kind == "line":
            pts.append((cx, y(v)))
        else:
            bw = slot if kind == "hist" else slot * 0.56
            out.append(f'<rect x="{cx - bw / 2:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{y(0) - y(v):.1f}" '
                       f'fill="{SERIES[0]}" fill-opacity="0.85" stroke="#fff"/>')
        out.append(f'<text x="{cx:.1f}" y="{y(v) - 6:.1f}" text-anchor="middle" fill="{INK}">{_fmt(v)}{escape(unit)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{top + ph + 18}" text-anchor="middle" fill="{INK}">{escape(str(c))}</text>')
    if pts:
        out.append('<polyline fill="none" stroke="{}" stroke-width="2" points="{}"/>'.format(
            SERIES[0], " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)))
        out += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4" fill="{SERIES[0]}"/>' for a, b in pts]
    out.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + ph}" stroke="{INK}"/>')
    out.append(f'<line x1="{left}" y1="{top + ph}" x2="{W - right}" y2="{top + ph}" stroke="{INK}"/>')
    if spec.get("y_label"):
        out.append(f'<text x="14" y="{top + ph / 2}" text-anchor="middle" fill="{MUTED}" '
                   f'transform="rotate(-90 14 {top + ph / 2})">{escape(spec["y_label"])}</text>')
    if spec.get("x_label"):
        out.append(f'<text x="{left + pw / 2}" y="{H - 10}" text-anchor="middle" fill="{MUTED}">{escape(spec["x_label"])}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------- biểu đồ quạt ----------

def _pie(spec: dict) -> str:
    labels, raw = spec["labels"], spec["values"]
    known = sum(v for v in raw if v is not None)
    # null = phần "còn lại": vẽ đúng tỉ lệ nhưng KHÔNG ghi số, vì đề không cho
    vals = [v if v is not None else (100 - known) / max(1, sum(1 for x in raw if x is None)) for v in raw]
    cx, cy, r = 150, 162, 110
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" {FONT} role="img">']
    if spec.get("title"):
        out.append(f'<text x="{W / 2}" y="18" text-anchor="middle" font-weight="600" fill="{INK}">{escape(spec["title"])}</text>')
    a0 = -math.pi / 2
    for i, (lab, v, shown) in enumerate(zip(labels, vals, raw)):
        a1 = a0 + 2 * math.pi * v / 100
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        large = 1 if a1 - a0 > math.pi else 0
        out.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" '
                   f'fill="{SERIES[i % len(SERIES)]}" stroke="#fff" stroke-width="2"/>')
        if shown is not None:
            am = (a0 + a1) / 2
            out.append(f'<text x="{cx + r * 0.62 * math.cos(am):.1f}" y="{cy + r * 0.62 * math.sin(am) + 4:.1f}" '
                       f'text-anchor="middle" fill="#fff" font-weight="600">{_fmt(v)}%</text>')
        ly = 80 + i * 26
        out.append(f'<rect x="300" y="{ly - 11}" width="14" height="14" rx="3" fill="{SERIES[i % len(SERIES)]}"/>')
        out.append(f'<text x="322" y="{ly}" fill="{INK}">{escape(lab)}</text>')
        a0 = a1
    out.append("</svg>")
    return "".join(out)


# ---------- đồ thị parabol y = ax² ----------

def _parabola(spec: dict) -> str:
    a = float(spec["a"])
    pts = [tuple(map(float, p)) for p in spec.get("points", [])]
    xmax = max([abs(p[0]) for p in pts] + [2]) + 0.8
    ys = [a * xmax * xmax, 0.0] + [p[1] for p in pts]
    ylo, yhi = min(ys) - 0.6, max(ys) + 0.8
    s = min((W - 60) / (2 * xmax), (H - 40) / (yhi - ylo))
    vw = round(2 * xmax * s + 60)                    # cùng tỉ lệ hai trục; khung vừa khít đồ thị
    ox, oy = vw / 2, 20 + yhi * s
    X = lambda x: ox + x * s                         # noqa: E731
    Y = lambda y: oy - y * s                         # noqa: E731
    out = [f'<svg viewBox="0 0 {vw} {H}" xmlns="http://www.w3.org/2000/svg" {FONT} role="img" '
           f'style="max-width:{vw}px;margin:0 auto">',
           f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>',
           f'<line x1="{X(-xmax):.1f}" y1="{oy:.1f}" x2="{X(xmax):.1f}" y2="{oy:.1f}" stroke="{INK}" marker-end="url(#ar)"/>',
           f'<line x1="{ox:.1f}" y1="{Y(ylo):.1f}" x2="{ox:.1f}" y2="{Y(yhi):.1f}" stroke="{INK}" marker-end="url(#ar)"/>',
           f'<text x="{X(xmax) - 4:.1f}" y="{oy - 8:.1f}" fill="{INK}">x</text>',
           f'<text x="{ox + 8:.1f}" y="{Y(yhi) + 12:.1f}" fill="{INK}">y</text>',
           f'<text x="{ox - 12:.1f}" y="{oy + 14:.1f}" fill="{INK}">O</text>']
    curve = []
    x = -xmax
    while x <= xmax + 1e-9:
        yv = a * x * x
        if ylo <= yv <= yhi:
            curve.append(f"{X(x):.1f},{Y(yv):.1f}")
        x += xmax / 60
    out.append(f'<polyline fill="none" stroke="{SERIES[0]}" stroke-width="2" points="{" ".join(curve)}"/>')
    for px, py in pts:
        out.append(f'<line x1="{X(px):.1f}" y1="{oy:.1f}" x2="{X(px):.1f}" y2="{Y(py):.1f}" stroke="{MUTED}" stroke-dasharray="3 3"/>')
        out.append(f'<line x1="{ox:.1f}" y1="{Y(py):.1f}" x2="{X(px):.1f}" y2="{Y(py):.1f}" stroke="{MUTED}" stroke-dasharray="3 3"/>')
        out.append(f'<circle cx="{X(px):.1f}" cy="{Y(py):.1f}" r="3.5" fill="{INK}"/>')
        # nhãn hoành độ nằm phía trục đối diện với điểm, không đè lên đường gióng
        out.append(f'<text x="{X(px):.1f}" y="{oy + (-6 if py < 0 else 14):.1f}" text-anchor="middle" fill="{INK}">{_fmt(px).replace("-", "−")}</text>')
        out.append(f'<text x="{ox + (8 if px < 0 else -6):.1f}" y="{Y(py) + 4:.1f}" text-anchor="{"start" if px < 0 else "end"}" '
                   f'fill="{INK}">{_fmt(py).replace("-", "−")}</text>')
    out.append(f'<text x="{X(-xmax * 0.75):.1f}" y="{Y(a * (xmax * 0.75) ** 2) + (14 if a < 0 else -8):.1f}" fill="{SERIES[0]}">(P)</text>')
    out.append("</svg>")
    return "".join(out)


# ---------- hình học: dùng engine dựng hình của dự án ----------

def _construction(spec: dict) -> str:
    from math9_geometry.construct import build
    from math9_geometry.dsl import Construction
    from math9_geometry.render_svg import render

    return render(build(Construction.model_validate({"ops": spec["ops"]}), seed=0))
