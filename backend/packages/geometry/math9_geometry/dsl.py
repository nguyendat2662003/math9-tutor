"""Ngôn ngữ mô tả kịch bản dựng hình.

Đây là hợp đồng giữa LLM và engine hình học. LLM CHỈ sinh ra danh sách các
phép dựng khai báo dưới đây — không bao giờ sinh tọa độ. Engine tính tọa độ.

Nguyên tắc: mọi phép dựng phải xác định duy nhất kết quả từ các đối tượng đã
có trước đó, hoặc khai báo rõ tham số ngẫu nhiên (`free`, `on_object`).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class OpKind(StrEnum):
    # -- điểm --
    FREE = "free"                    # điểm tự do (tọa độ do engine sinh)
    ON_OBJECT = "on_object"          # điểm thuộc một đối tượng đã có
    MIDPOINT = "midpoint"
    DIVIDE_RATIO = "divide_ratio"
    INTERSECT = "intersect"
    FOOT = "foot"                    # chân đường vuông góc
    REFLECT_LINE = "reflect_line"
    REFLECT_POINT = "reflect_point"
    CENTER_OF = "center_of"          # tâm của một đường tròn đã có

    # -- đường --
    LINE = "line"
    SEGMENT = "segment"
    RAY = "ray"
    PERPENDICULAR = "perpendicular"
    PARALLEL = "parallel"
    ANGLE_BISECTOR = "angle_bisector"
    PERP_BISECTOR = "perp_bisector"

    # -- đường tròn --
    CIRCLE_CENTER_RADIUS = "circle_center_radius"
    CIRCLE_THROUGH = "circle_through"       # tâm + 1 điểm trên đường tròn
    CIRCLE_DIAMETER = "circle_diameter"
    CIRCUMCIRCLE = "circumcircle"
    INCIRCLE = "incircle"
    TANGENT_AT = "tangent_at"
    TANGENT_FROM = "tangent_from"

    # -- hình mẫu (macro) --
    TRIANGLE = "triangle"

    # -- điểm đặc biệt của tam giác --
    CENTROID = "centroid"
    ORTHOCENTER = "orthocenter"
    INCENTER = "incenter"
    CIRCUMCENTER = "circumcenter"

    # -- ký hiệu (không sinh đối tượng mới, chỉ để vẽ) --
    RIGHT_ANGLE_MARK = "right_angle_mark"
    EQUAL_SEGMENTS = "equal_segments"
    EQUAL_ANGLES = "equal_angles"
    ARC = "arc"
    LABEL = "label"


#: Các phép dựng chỉ phục vụ hiển thị, không tạo đối tượng hình học mới.
MARK_OPS = {
    OpKind.RIGHT_ANGLE_MARK,
    OpKind.EQUAL_SEGMENTS,
    OpKind.EQUAL_ANGLES,
    OpKind.ARC,
    OpKind.LABEL,
}


class ConstructionOp(BaseModel):
    """Một phép dựng đơn lẻ."""

    op: OpKind
    name: str | None = Field(
        default=None,
        description="Tên đối tượng sinh ra, ví dụ 'H' hoặc 'O'. Bỏ trống với ký hiệu.",
    )
    args: list[str] = Field(
        default_factory=list,
        description="Tên các đối tượng đã dựng trước, ví dụ ['A','B'] hoặc ['line:AB'].",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Tham số phụ: hint, ratio, branch, radius...",
    )
    step_ref: str | None = Field(
        default=None,
        description="ID bước lời giải mà phép dựng này thuộc về (để vẽ theo bước).",
    )
    style: Literal["solid", "dashed", "auxiliary", "highlight"] = "solid"

    model_config = {"use_enum_values": False}


class Construction(BaseModel):
    """Toàn bộ kịch bản dựng hình cho một bài toán."""

    ops: list[ConstructionOp]
    constraints: list["Constraint"] = Field(
        default_factory=list,
        description="Ràng buộc không dựng tuần tự được, giải bằng numeric solver.",
    )
    seed: int | None = None

    def named_ops(self) -> dict[str, ConstructionOp]:
        return {o.name: o for o in self.ops if o.name}


class Constraint(BaseModel):
    """Ràng buộc số cho những cấu hình không dựng được tuần tự.

    Ví dụ: 'lấy M trên cung nhỏ BC sao cho MB = 2MC' -> ON_OBJECT + Constraint
    kiểu RATIO với args ['M','B','M','C'] và value 2.
    """

    kind: Literal[
        "dist_eq", "ratio", "angle_eq", "collinear", "concyclic", "perpendicular"
    ]
    args: list[str]
    value: float | None = None


Construction.model_rebuild()


# --------------------------------------------------------------------------
# Số lượng đối số bắt buộc — dùng để validate kịch bản LLM sinh ra
# --------------------------------------------------------------------------

ARITY: dict[OpKind, tuple[int, int]] = {
    OpKind.FREE: (0, 0),
    OpKind.ON_OBJECT: (1, 1),
    OpKind.MIDPOINT: (2, 2),
    OpKind.DIVIDE_RATIO: (2, 2),
    OpKind.INTERSECT: (2, 2),
    OpKind.FOOT: (2, 2),
    OpKind.REFLECT_LINE: (2, 2),
    OpKind.REFLECT_POINT: (2, 2),
    OpKind.CENTER_OF: (1, 1),
    OpKind.LINE: (2, 2),
    OpKind.SEGMENT: (2, 2),
    OpKind.RAY: (2, 2),
    OpKind.PERPENDICULAR: (2, 2),
    OpKind.PARALLEL: (2, 2),
    OpKind.ANGLE_BISECTOR: (3, 3),
    OpKind.PERP_BISECTOR: (2, 2),
    OpKind.CIRCLE_CENTER_RADIUS: (1, 1),
    OpKind.CIRCLE_THROUGH: (2, 2),
    OpKind.CIRCLE_DIAMETER: (2, 2),
    OpKind.CIRCUMCIRCLE: (3, 3),
    OpKind.INCIRCLE: (3, 3),
    OpKind.TANGENT_AT: (2, 2),
    OpKind.TANGENT_FROM: (2, 2),
    OpKind.TRIANGLE: (3, 3),
    OpKind.CENTROID: (3, 3),
    OpKind.ORTHOCENTER: (3, 3),
    OpKind.INCENTER: (3, 3),
    OpKind.CIRCUMCENTER: (3, 3),
    OpKind.RIGHT_ANGLE_MARK: (3, 3),
    OpKind.EQUAL_SEGMENTS: (2, 8),
    OpKind.EQUAL_ANGLES: (2, 8),
    OpKind.ARC: (3, 3),
    OpKind.LABEL: (1, 1),
}


#: Phép dựng mà `args` là tên các đối tượng ĐƯỢC TẠO RA, không phải tham chiếu.
PRODUCER_OPS = {OpKind.TRIANGLE}


#: Mô tả từng phép dựng cho prompt Draftsman: (args, params, ý nghĩa).
OP_DOC: dict[OpKind, tuple[str, str, str]] = {
    OpKind.FREE: ("[]", "outside=<tên đường tròn> | inside=<tên đường tròn> | min_dist=[<điểm>, d]",
                  "điểm tự do, engine chọn tọa độ"),
    OpKind.ON_OBJECT: ("[<đường tròn | đoạn | đường thẳng>]", "theta_min, theta_max (radian, chỉ cho đường tròn)",
                       "điểm ngẫu nhiên thuộc đối tượng"),
    OpKind.MIDPOINT: ("[A, B]", "", "trung điểm AB"),
    OpKind.DIVIDE_RATIO: ("[A, B]", "t (0→A, 1→B, t>1 nằm ngoài phía B)", "điểm chia AB theo tỉ số"),
    OpKind.INTERSECT: ("[<đối tượng 1>, <đối tượng 2>]", "branch=0|1 hoặc not=<điểm cần tránh>",
                       "giao điểm; với đường tròn có 2 giao, dùng not=<điểm đã biết> để lấy giao còn lại"),
    OpKind.FOOT: ("[P, <đường thẳng>]", "", "chân đường vuông góc hạ từ P"),
    OpKind.REFLECT_LINE: ("[P, <đường thẳng>]", "", "đối xứng của P qua đường thẳng"),
    OpKind.REFLECT_POINT: ("[P, I]", "", "đối xứng của P qua điểm I (I là trung điểm)"),
    OpKind.CENTER_OF: ("[<đường tròn>]", "", "tâm của đường tròn đã có (dùng sau circumcircle)"),
    OpKind.LINE: ("[A, B]", "", "đường thẳng AB (vô hạn)"),
    OpKind.SEGMENT: ("[A, B]", "", "đoạn thẳng AB"),
    OpKind.RAY: ("[A, B]", "", "tia AB"),
    OpKind.PERPENDICULAR: ("[P, <đường thẳng>]", "", "đường thẳng qua P vuông góc đường đã cho"),
    OpKind.PARALLEL: ("[P, <đường thẳng>]", "", "đường thẳng qua P song song đường đã cho"),
    OpKind.ANGLE_BISECTOR: ("[A, V, B]", "", "phân giác trong của góc AVB (đỉnh V ở giữa)"),
    OpKind.PERP_BISECTOR: ("[A, B]", "", "đường trung trực của AB"),
    OpKind.CIRCLE_CENTER_RADIUS: ("[O]", "radius=<số>", "đường tròn tâm O bán kính cho trước"),
    OpKind.CIRCLE_THROUGH: ("[O, A]", "", "đường tròn tâm O đi qua A"),
    OpKind.CIRCLE_DIAMETER: ("[A, B]", "", "đường tròn đường kính AB"),
    OpKind.CIRCUMCIRCLE: ("[A, B, C]", "", "đường tròn ngoại tiếp tam giác ABC"),
    OpKind.INCIRCLE: ("[A, B, C]", "", "đường tròn nội tiếp tam giác ABC"),
    OpKind.TANGENT_AT: ("[<đường tròn>, P]", "", "tiếp tuyến tại điểm P thuộc đường tròn"),
    OpKind.TANGENT_FROM: ("[<đường tròn>, P]", "branch=0|1, touch_point=<tên tiếp điểm>",
                          "tiếp tuyến kẻ từ P ngoài đường tròn; touch_point đặt tên cho tiếp điểm"),
    OpKind.TRIANGLE: ("[A, B, C] (tên 3 đỉnh ĐƯỢC TẠO)", "hint=acute|obtuse|right|isosceles|equilateral|scalene",
                      "tam giác ngẫu nhiên; right → vuông tại đỉnh đầu; isosceles → cân tại đỉnh đầu"),
    OpKind.CENTROID: ("[A, B, C]", "", "trọng tâm"),
    OpKind.ORTHOCENTER: ("[A, B, C]", "", "trực tâm"),
    OpKind.INCENTER: ("[A, B, C]", "", "tâm đường tròn nội tiếp"),
    OpKind.CIRCUMCENTER: ("[A, B, C]", "", "tâm đường tròn ngoại tiếp"),
    OpKind.RIGHT_ANGLE_MARK: ("[A, V, B]", "", "ký hiệu góc vuông tại V (không tạo đối tượng, không cần name)"),
    OpKind.EQUAL_SEGMENTS: ("[A, B, C, D, ...]", "ticks=1|2|3", "ký hiệu các đoạn bằng nhau (từng cặp)"),
    OpKind.EQUAL_ANGLES: ("[A, V, B, C, W, D]", "", "ký hiệu hai góc bằng nhau"),
    OpKind.ARC: ("[<đường tròn>, A, B]", "", "tô đậm cung AB"),
    OpKind.LABEL: ("[<đối tượng>]", "text=<chuỗi>", "nhãn phụ"),
}


def op_catalog() -> str:
    """Danh mục phép dựng dạng văn bản để nạp vào prompt Draftsman."""
    lines = []
    for k, (args, params, desc) in OP_DOC.items():
        need = "không cần name" if k in MARK_OPS else "cần name"
        s = f"- {k.value}: args={args}"
        if params:
            s += f"; params: {params}"
        s += f" — {desc} ({need})"
        lines.append(s)
    return "\n".join(lines)


def validate_ops(ops: list[ConstructionOp]) -> list[str]:
    """Kiểm tra tĩnh kịch bản trước khi chạy engine. Trả về danh sách lỗi."""
    errors: list[str] = []
    defined: set[str] = set()

    for i, op in enumerate(ops):
        lo, hi = ARITY.get(op.op, (0, 99))
        if not (lo <= len(op.args) <= hi):
            errors.append(f"[{i}] {op.op}: cần {lo}-{hi} đối số, nhận {len(op.args)}")

        if op.op in PRODUCER_OPS:
            defined.update(op.args)
            continue

        for a in op.args:
            if ":" in a:
                # Tham chiếu phức hợp: 'line:AB', 'circle:O' -> kiểm tra từng thành phần
                refs = list(a.split(":", 1)[1])
            else:
                refs = [a]
            for r in refs:
                if r not in defined and not r.replace(".", "").isdigit():
                    errors.append(f"[{i}] {op.op}: tham chiếu '{r}' chưa được dựng")

        if op.op not in MARK_OPS:
            if not op.name:
                errors.append(f"[{i}] {op.op}: thiếu tên đối tượng")
            else:
                defined.add(op.name)
        # Một số phép dựng tạo thêm đối tượng phụ qua params
        for extra_key in ("touch_point", "second_point"):
            if op.params.get(extra_key):
                defined.add(op.params[extra_key])

    return errors
