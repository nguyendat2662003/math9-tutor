"""Engine dựng hình: kịch bản DSL -> tọa độ chính xác.

Đây là lý do LLM không bao giờ cần sinh tọa độ. Mỗi phép dựng được thực thi
bằng công thức toán học, nên quan hệ hình học đúng tuyệt đối (sai số máy).

Engine nhận `seed` để sinh lại cùng một hình với cấu hình khác nhau — cơ chế
này chính là nền tảng của Verifier hình học (xem packages/verifier).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

from .dsl import MARK_OPS, Construction, ConstructionOp, OpKind, validate_ops
from .primitives import (
    Circle,
    GeometryError,
    Line,
    Point,
    Segment,
    angle_bisector,
    centroid,
    circumcenter,
    circumcircle,
    dist,
    divide_ratio,
    foot_of_perpendicular,
    incenter,
    incircle,
    intersect_circle_circle,
    intersect_line_circle,
    intersect_line_line,
    midpoint,
    orthocenter,
    parallel_through,
    perpendicular_bisector,
    perpendicular_through,
    reflect_over_line,
    reflect_over_point,
    tangent_at,
    tangent_points_from,
)

GeoObject = Point | Line | Circle | Segment


@dataclass
class Mark:
    """Ký hiệu hình học để renderer vẽ (góc vuông, cạnh bằng nhau...)."""

    kind: str
    args: list[str]
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Figure:
    """Kết quả dựng hình."""

    objects: dict[str, GeoObject]
    marks: list[Mark]
    order: list[str]
    styles: dict[str, str]
    step_refs: dict[str, str | None]
    seed: int

    def points(self) -> dict[str, Point]:
        return {k: v for k, v in self.objects.items() if isinstance(v, Point)}

    def point(self, name: str) -> Point:
        o = self.objects.get(name)
        if not isinstance(o, Point):
            raise GeometryError(f"'{name}' không phải là điểm")
        return o


class Constructor:
    """Thực thi tuần tự các phép dựng."""

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.seed = seed
        self.objects: dict[str, GeoObject] = {}
        self.marks: list[Mark] = []
        self.order: list[str] = []
        self.styles: dict[str, str] = {}
        self.step_refs: dict[str, str | None] = {}
        #: Tham số ghi đè cho điểm tự do (FREE: (x, y); ON_OBJECT: (t,)) — bộ giải ràng buộc dùng.
        self.overrides: dict[str, tuple[float, ...]] = {}

    # -- truy xuất -------------------------------------------------------

    def _get(self, ref: str) -> GeoObject:
        """Giải tham chiếu. Hỗ trợ 'A', 'line:AB', 'circle:O', 'seg:AB'."""
        if ref in self.objects:
            return self.objects[ref]
        if ":" in ref:
            kind, body = ref.split(":", 1)
            if body in self.objects:
                obj = self.objects[body]
                if kind == "line" and isinstance(obj, Segment):
                    return obj.to_line()
                return obj
            if kind in ("line", "seg", "ray") and len(body) == 2:
                a, b = self._pt(body[0]), self._pt(body[1])
                return Line.through(a, b) if kind != "seg" else Segment(a, b)
        raise GeometryError(f"Chưa dựng đối tượng '{ref}'")

    def _pt(self, ref: str) -> Point:
        o = self._get(ref)
        if not isinstance(o, Point):
            raise GeometryError(f"'{ref}' không phải là điểm")
        return o

    def _line(self, ref: str) -> Line:
        o = self._get(ref)
        if isinstance(o, Line):
            return o
        if isinstance(o, Segment):
            return o.to_line()
        raise GeometryError(f"'{ref}' không phải là đường thẳng")

    def _circle(self, ref: str) -> Circle:
        o = self._get(ref)
        if not isinstance(o, Circle):
            raise GeometryError(f"'{ref}' không phải là đường tròn")
        return o

    def _put(self, name: str, obj: GeoObject, op: ConstructionOp) -> None:
        self.objects[name] = obj
        self.order.append(name)
        self.styles[name] = op.style
        self.step_refs[name] = op.step_ref

    # -- lựa chọn nhánh --------------------------------------------------

    def _pick(self, cands: list[Point], op: ConstructionOp) -> Point:
        """Chọn một trong nhiều giao điểm.

        `branch` = 0/1 chọn theo chỉ số; `not` = tên điểm cần tránh (dùng khi
        một giao điểm đã biết, ví dụ 'giao điểm thứ hai của AH với (O)').
        """
        if not cands:
            raise GeometryError("Không có giao điểm")
        avoid = op.params.get("not")
        if avoid:
            p0 = self._pt(avoid)
            far = [c for c in cands if dist(c, p0) > 1e-6]
            if far:
                return far[0]
        idx = int(op.params.get("branch", 0))
        return cands[min(idx, len(cands) - 1)]

    # -- thực thi --------------------------------------------------------

    def run(self, construction: Construction) -> Figure:
        errs = validate_ops(construction.ops)
        if errs:
            raise GeometryError("Kịch bản không hợp lệ: " + "; ".join(errs[:5]))
        self.rebuild(construction.ops)
        if construction.constraints:
            from .constraints import solve_constraints

            solve_constraints(self, construction)
        return Figure(
            objects=dict(self.objects),
            marks=list(self.marks),
            order=list(self.order),
            styles=dict(self.styles),
            step_refs=dict(self.step_refs),
            seed=self.seed,
        )

    def rebuild(self, ops: list[ConstructionOp]) -> None:
        """Dựng lại toàn bộ từ đầu với cùng seed. Điểm tự do có trong `overrides`
        nhận tham số ghi đè; các điểm khác ra đúng như lần trước (rng cùng seed)."""
        self.rng = random.Random(self.seed)
        self.objects, self.marks, self.order = {}, [], []
        self.styles, self.step_refs = {}, {}
        for op in ops:
            self._exec(op)

    def _exec(self, op: ConstructionOp) -> None:  # noqa: C901
        k, a, p = op.op, op.args, op.params

        if k in MARK_OPS:
            self.marks.append(Mark(kind=str(k), args=a, params=p))
            return

        name = op.name or ""

        # --- hình mẫu -----------------------------------------------------
        if k == OpKind.TRIANGLE:
            for n, pt in zip(a, self._random_triangle(p.get("hint", "scalene"))):
                self._put(n, pt, op)
            return

        # --- điểm ---------------------------------------------------------
        if k == OpKind.FREE:
            pt = self._random_point(p)               # luôn gọi để rng tiêu thụ như nhau
            if name in self.overrides:
                pt = Point(*self.overrides[name])
            self._put(name, pt, op)

        elif k == OpKind.ON_OBJECT:
            obj = self._get(a[0])
            pt = self._random_on(obj, p)
            if name in self.overrides:
                pt = self.point_on(obj, self.overrides[name][0])
            self._put(name, pt, op)

        elif k == OpKind.MIDPOINT:
            self._put(name, midpoint(self._pt(a[0]), self._pt(a[1])), op)

        elif k == OpKind.DIVIDE_RATIO:
            t = float(p.get("t", 0.5))
            self._put(name, divide_ratio(self._pt(a[0]), self._pt(a[1]), t), op)

        elif k == OpKind.INTERSECT:
            self._put(name, self._intersect(a[0], a[1], op), op)

        elif k == OpKind.FOOT:
            self._put(name, foot_of_perpendicular(self._pt(a[0]), self._line(a[1])), op)

        elif k == OpKind.REFLECT_LINE:
            self._put(name, reflect_over_line(self._pt(a[0]), self._line(a[1])), op)

        elif k == OpKind.REFLECT_POINT:
            self._put(name, reflect_over_point(self._pt(a[0]), self._pt(a[1])), op)

        elif k == OpKind.CENTER_OF:
            self._put(name, self._circle(a[0]).center, op)

        # --- đường --------------------------------------------------------
        elif k in (OpKind.LINE, OpKind.RAY):
            self._put(name, Line.through(self._pt(a[0]), self._pt(a[1])), op)

        elif k == OpKind.SEGMENT:
            self._put(name, Segment(self._pt(a[0]), self._pt(a[1])), op)

        elif k == OpKind.PERPENDICULAR:
            self._put(name, perpendicular_through(self._pt(a[0]), self._line(a[1])), op)

        elif k == OpKind.PARALLEL:
            self._put(name, parallel_through(self._pt(a[0]), self._line(a[1])), op)

        elif k == OpKind.ANGLE_BISECTOR:
            self._put(
                name,
                angle_bisector(self._pt(a[1]), self._pt(a[0]), self._pt(a[2])),
                op,
            )

        elif k == OpKind.PERP_BISECTOR:
            self._put(name, perpendicular_bisector(self._pt(a[0]), self._pt(a[1])), op)

        # --- đường tròn ----------------------------------------------------
        elif k == OpKind.CIRCLE_CENTER_RADIUS:
            self._put(name, Circle(self._pt(a[0]), float(p.get("radius", 1.0))), op)

        elif k == OpKind.CIRCLE_THROUGH:
            c = self._pt(a[0])
            self._put(name, Circle(c, dist(c, self._pt(a[1]))), op)

        elif k == OpKind.CIRCLE_DIAMETER:
            u, v = self._pt(a[0]), self._pt(a[1])
            self._put(name, Circle(midpoint(u, v), dist(u, v) / 2), op)

        elif k == OpKind.CIRCUMCIRCLE:
            self._put(name, circumcircle(*[self._pt(x) for x in a]), op)

        elif k == OpKind.INCIRCLE:
            self._put(name, incircle(*[self._pt(x) for x in a]), op)

        elif k == OpKind.TANGENT_AT:
            self._put(name, tangent_at(self._circle(a[0]), self._pt(a[1])), op)

        elif k == OpKind.TANGENT_FROM:
            pts = tangent_points_from(self._circle(a[0]), self._pt(a[1]))
            tp = self._pick(pts, op)
            tp_name = p.get("touch_point")
            if tp_name:
                self._put(tp_name, tp, op)
            self._put(name, Line.through(self._pt(a[1]), tp), op)

        # --- điểm đặc biệt --------------------------------------------------
        elif k == OpKind.CENTROID:
            self._put(name, centroid(*[self._pt(x) for x in a]), op)
        elif k == OpKind.ORTHOCENTER:
            self._put(name, orthocenter(*[self._pt(x) for x in a]), op)
        elif k == OpKind.INCENTER:
            self._put(name, incenter(*[self._pt(x) for x in a]), op)
        elif k == OpKind.CIRCUMCENTER:
            self._put(name, circumcenter(*[self._pt(x) for x in a]), op)

        else:
            raise GeometryError(f"Chưa hỗ trợ phép dựng '{k}'")

    # -- giao điểm giữa hai đối tượng bất kỳ ------------------------------

    def _intersect(self, r1: str, r2: str, op: ConstructionOp) -> Point:
        o1, o2 = self._get(r1), self._get(r2)
        if isinstance(o1, Segment):
            o1 = o1.to_line()
        if isinstance(o2, Segment):
            o2 = o2.to_line()

        if isinstance(o1, Line) and isinstance(o2, Line):
            return intersect_line_line(o1, o2)
        if isinstance(o1, Line) and isinstance(o2, Circle):
            return self._pick(intersect_line_circle(o1, o2), op)
        if isinstance(o1, Circle) and isinstance(o2, Line):
            return self._pick(intersect_line_circle(o2, o1), op)
        if isinstance(o1, Circle) and isinstance(o2, Circle):
            return self._pick(intersect_circle_circle(o1, o2), op)
        raise GeometryError(f"Không lấy được giao của {r1} và {r2}")

    # -- sinh tọa độ ngẫu nhiên -------------------------------------------

    def _random_point(self, params: dict | None = None) -> Point:
        """Sinh điểm tự do, tôn trọng ràng buộc vị trí nếu có.

        params hỗ trợ: outside=<tên đường tròn>, inside=<tên đường tròn>,
        min_dist=[<tên điểm>, khoảng cách tối thiểu].
        """
        params = params or {}
        for _ in range(300):
            q = Point(self.rng.uniform(-5, 5), self.rng.uniform(-4, 4))
            if (c := params.get("outside")) is not None:
                circ = self._circle(c)
                if dist(q, circ.center) < circ.radius * 1.35:
                    continue
            if (c := params.get("inside")) is not None:
                circ = self._circle(c)
                if dist(q, circ.center) > circ.radius * 0.7:
                    continue
            if (md := params.get("min_dist")) is not None:
                if dist(q, self._pt(md[0])) < float(md[1]):
                    continue
            return q
        raise GeometryError("Không sinh được điểm tự do thỏa ràng buộc vị trí")

    @staticmethod
    def point_on(obj: GeoObject, t: float) -> Point:
        """Điểm trên đối tượng theo một tham số: góc (đường tròn) hoặc t (đoạn/đường)."""
        if isinstance(obj, Circle):
            return obj.point_at(t)
        if isinstance(obj, Segment):
            return divide_ratio(obj.a, obj.b, t)
        if isinstance(obj, Line):
            return Point(obj.p.x + obj.d.x * t, obj.p.y + obj.d.y * t)
        raise GeometryError("Không đặt được điểm trên đối tượng này")

    @staticmethod
    def param_of(obj: GeoObject, q: Point) -> float:
        """Nghịch đảo của point_on: tham số của điểm q đang nằm trên obj."""
        if isinstance(obj, Circle):
            return math.atan2(q.y - obj.center.y, q.x - obj.center.x)
        if isinstance(obj, Segment):
            d = obj.b - obj.a
            return ((q - obj.a).x * d.x + (q - obj.a).y * d.y) / max(d.norm() ** 2, 1e-12)
        if isinstance(obj, Line):
            return (q - obj.p).x * obj.d.x + (q - obj.p).y * obj.d.y
        raise GeometryError("Không đặt được điểm trên đối tượng này")

    def _random_on(self, obj: GeoObject, params: dict) -> Point:
        if isinstance(obj, Circle):
            lo = float(params.get("theta_min", 0.0))
            hi = float(params.get("theta_max", 2 * math.pi))
            return obj.point_at(self.rng.uniform(lo, hi))
        if isinstance(obj, Segment):
            return divide_ratio(obj.a, obj.b, self.rng.uniform(0.2, 0.8))
        if isinstance(obj, Line):
            t = self.rng.uniform(-3, 3)
            return Point(obj.p.x + obj.d.x * t, obj.p.y + obj.d.y * t)
        raise GeometryError("Không đặt được điểm trên đối tượng này")

    def _random_triangle(self, hint: str) -> list[Point]:
        """Sinh tam giác theo gợi ý hình dạng, đảm bảo không suy biến."""
        r = self.rng
        for _ in range(200):
            if hint == "right":
                a = Point(0, 0)
                b = Point(r.uniform(2.5, 5), 0)
                c = Point(0, r.uniform(2.5, 5))
            elif hint == "isosceles":
                h = r.uniform(3, 5)
                w = r.uniform(1.5, 3)
                a, b, c = Point(0, h), Point(-w, 0), Point(w, 0)
            elif hint == "equilateral":
                s = r.uniform(3, 5)
                a = Point(0, s * math.sqrt(3) / 2)
                b, c = Point(-s / 2, 0), Point(s / 2, 0)
            else:
                angs = sorted(r.uniform(0, 2 * math.pi) for _ in range(3))
                rad = r.uniform(2.5, 3.5)
                a, b, c = (Point(rad * math.cos(t), rad * math.sin(t)) for t in angs)

            angles = _triangle_angles(a, b, c)
            if hint == "acute" and max(angles) > math.radians(85):
                continue
            if hint == "obtuse" and max(angles) < math.radians(100):
                continue
            if min(angles) < math.radians(28):
                continue
            # Chuẩn hóa chiều: luôn ngược chiều kim đồng hồ cho nhãn ổn định
            if (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x) < 0:
                b, c = c, b
            return [a, b, c]
        raise GeometryError(f"Không sinh được tam giác dạng '{hint}'")


def _triangle_angles(a: Point, b: Point, c: Point) -> list[float]:
    from .primitives import angle_at

    return [angle_at(a, b, c), angle_at(b, a, c), angle_at(c, a, b)]


def build(construction: Construction, seed: int = 0) -> Figure:
    """Hàm tiện lợi: dựng hình một lần với seed cho trước."""
    return Constructor(seed=seed).run(construction)
