"""Dò bổ đề trung gian bằng cách quét vị từ trên hình đã dựng.

Dùng cho bài mức 3 (rất khó). Sau khi Solver giải tự do và Draftsman dựng
được hình, ta quét thử một loạt mệnh đề trên nhiều cấu hình. Mệnh đề nào đúng
trên MỌI cấu hình gần như chắc chắn là bổ đề thật, và trở thành mục tiêu trung
gian cho pha hạ cấp về công cụ lớp 9.

Một bài khó thường bị bẻ thành ba bài dễ nhờ bước này.
"""

from __future__ import annotations

from itertools import combinations

from math9_geometry.construct import Figure
from math9_geometry.dsl import Construction
from math9_geometry.primitives import Circle, GeometryError, Point

from .geometry import DEFAULT_SEEDS, TOLERANCE, build_many
from .predicates import Predicate, residual

#: Trần số tổ hợp mỗi loại, tránh bùng nổ tổ hợp trên hình nhiều điểm.
MAX_PER_KIND = 400


def _point_names(fig: Figure) -> list[str]:
    return sorted(n for n, o in fig.objects.items() if isinstance(o, Point))


def _circle_names(fig: Figure) -> list[str]:
    return sorted(n for n, o in fig.objects.items() if isinstance(o, Circle))


def candidate_predicates(fig: Figure, given: set[str] | None = None) -> list[Predicate]:
    """Sinh tập mệnh đề ứng viên để thử. `given` là các vị từ đã biết từ đề."""
    pts = _point_names(fig)
    out: list[Predicate] = []

    for combo in list(combinations(pts, 3))[:MAX_PER_KIND]:
        out.append(Predicate("collinear", list(combo)))

    for combo in list(combinations(pts, 4))[:MAX_PER_KIND]:
        out.append(Predicate("concyclic", list(combo)))

    for (a, b), (c, d) in list(
        combinations(list(combinations(pts, 2)), 2)
    )[:MAX_PER_KIND]:
        out.append(Predicate("equal_length", [a, b, c, d]))
        out.append(Predicate("perpendicular", [a, b, c, d]))
        out.append(Predicate("parallel", [a, b, c, d]))

    for m in pts:
        for a, b in combinations([p for p in pts if p != m], 2):
            out.append(Predicate("midpoint", [m, a, b]))
    out = out[: MAX_PER_KIND * 6]

    for cn in _circle_names(fig):
        for p in pts:
            out.append(Predicate("on_object", [p, cn]))

    out = [p for p in out if not is_trivial(p)]
    if given:
        out = [p for p in out if repr(p) not in given]
    return out


def is_trivial(p: Predicate) -> bool:
    """Loại bổ đề vô nghĩa: hai đoạn chung điểm mà 'song song' chỉ nghĩa là thẳng hàng."""
    k, a = str(p.kind), p.args
    if k in ("parallel", "perpendicular", "equal_length"):
        if len({a[0], a[1]} & {a[2], a[3]}) >= 1 and k != "equal_length":
            return True
        if {a[0], a[1]} == {a[2], a[3]}:
            return True
    if k == "collinear" and len(set(a)) < 3:
        return True
    return False


def find_lemmas(
    construction: Construction,
    given: set[str] | None = None,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    tol: float = TOLERANCE,
    limit: int = 25,
) -> list[Predicate]:
    """Trả về các bổ đề đúng trên mọi cấu hình, sắp theo độ 'chặt'."""
    figs, _ = build_many(construction, seeds)
    if len(figs) < 2:
        return []

    scored: list[tuple[float, Predicate]] = []
    for cand in candidate_predicates(figs[0], given):
        try:
            worst = max(residual(f, cand) for f in figs)
        except (GeometryError, KeyError, IndexError):
            continue
        if worst < tol:
            scored.append((worst, cand))

    scored.sort(key=lambda t: t[0])
    return [p for _, p in scored[:limit]]


def format_for_prompt(lemmas: list[Predicate]) -> str:
    """Diễn đạt bổ đề bằng tiếng Việt để nạp vào prompt pha hạ cấp."""
    vi = {
        "collinear": "{0}, {1}, {2} thẳng hàng",
        "concyclic": "{0}, {1}, {2}, {3} cùng thuộc một đường tròn",
        "equal_length": "{0}{1} = {2}{3}",
        "perpendicular": "{0}{1} vuông góc {2}{3}",
        "parallel": "{0}{1} song song {2}{3}",
        "midpoint": "{0} là trung điểm của {1}{2}",
        "on_object": "{0} thuộc {1}",
        "concurrent": "{0}, {1}, {2} đồng quy",
        "right_angle": "góc {0}{1}{2} vuông",
        "product_equal": "{0}{1}·{2}{3} = {4}{5}·{6}{7}",
        "is_isosceles": "tam giác {0}{1}{2} cân tại {0}",
    }
    lines = []
    for p in lemmas:
        tmpl = vi.get(str(p.kind))
        lines.append("- " + (tmpl.format(*p.args) if tmpl else repr(p)))
    return "\n".join(lines)
