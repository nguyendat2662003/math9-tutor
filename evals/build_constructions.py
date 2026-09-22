"""Dựng và kiểm chứng lại kịch bản dựng hình cho các bài hình trong bộ eval.

data/eval/constructions.jsonl là kho THAM CHIẾU: mỗi bài hình cần một kịch bản
dựng hình đúng để `evals/graders/figure.py` chấm tự động. Không viết tay từng
lần — chạy script này, nó kiểm chứng lại MỌI kịch bản trước khi ghi ra file,
nên không thể lỡ tay ghi một kịch bản kiểm chứng thất bại.

Khi thêm bài hình mới vào eval-seed.jsonl (đề mới hoặc sổ tay mới cần ví dụ
dựng được), thêm một hàm builder ở đây rồi chạy lại:

    python evals/build_constructions.py

Đối chiếu tên điểm: `name=` trong ConstructionOp PHẢI khớp tuyệt đối với tên
điểm trong trường `predicates` đã lưu ở eval-seed.jsonl — đây là lỗi từng xảy
ra thật (na26-4c dùng "Pp"/"Qq" trong code nhưng đề gốc và predicate ghi
"P"/"Q", vì "P" đã dùng làm bí danh cho lớp Predicate trong script build eval).
"""

from __future__ import annotations

import json
from pathlib import Path

from math9_geometry.dsl import Construction, ConstructionOp as Op
from math9_verifier.geometry import verify
from math9_verifier.predicates import Predicate

OUT_PATH = Path("data/eval/constructions.jsonl")

CIRC = [
    Op(op="free", name="O"),
    Op(op="circle_center_radius", name="w", args=["O"], params={"radius": 2.0}),
]


def two_tangents(X: str, T1: str, T2: str, P1: str, P2: str, H: str, I: str, J: str) -> Construction:
    """Điểm ngoài + hai tiếp tuyến, cát tuyến qua tâm, trung điểm, giao với đường tròn.

    Dùng chung cho hai mã đề Hà Tĩnh 2026 và câu Đúng/Sai Hưng Yên 2026 — cùng
    một cấu hình hình học, chỉ đổi tên điểm theo từng đề.
    """
    return Construction(ops=CIRC + [
        Op(op="free", name=X, params={"outside": "w"}),
        Op(op="tangent_from", name="t1", args=["w", X], params={"branch": 0, "touch_point": T1}),
        Op(op="tangent_from", name="t2", args=["w", X], params={"branch": 1, "touch_point": T2}),
        Op(op="intersect", name=P1, args=[f"line:{X}O", "w"], params={"branch": 0}),
        Op(op="intersect", name=P2, args=[f"line:{X}O", "w"], params={"branch": 1}),
        Op(op="intersect", name=H, args=[f"line:{T1}{T2}", f"line:{X}O"]),
        Op(op="midpoint", name=I, args=[X, H]),
        Op(op="intersect", name=J, args=[f"line:{T1}{I}", "w"], params={"not": T1}),
    ])


def acute_altitudes() -> list[Op]:
    """Tam giác nhọn nội tiếp, ba đường cao, trực tâm — bộ khung dùng cho
    Nghệ An câu 4 và TP.HCM bài 7."""
    return [
        Op(op="triangle", args=["A", "B", "C"], params={"hint": "acute"}),
        Op(op="circumcircle", name="w", args=["A", "B", "C"]),
        Op(op="center_of", name="O", args=["w"]),
        Op(op="foot", name="D", args=["A", "line:BC"]),
        Op(op="foot", name="E", args=["B", "line:AC"]),
        Op(op="foot", name="F", args=["C", "line:AB"]),
        Op(op="orthocenter", name="H", args=["A", "B", "C"]),
    ]


#: context_id -> (Construction, [predicate dict, ...]).
#: predicate dict PHẢI đúng y hệt trường `predicates` đã lưu cho context_id đó
#: trong data/eval/eval-seed.jsonl (script này không đọc ngược từ eval-seed —
#: nếu sửa đề bài, sửa predicate ở CẢ HAI nơi).
BUILDERS: dict[str, tuple[Construction, list[dict]]] = {}

BUILDERS["ht26m1-13"] = (
    two_tangents("A", "M", "N", "P", "Q", "H", "I", "J"),
    [
        {"kind": "concyclic", "args": ["A", "M", "O", "N"]},
        {"kind": "product_equal", "args": ["A", "P", "A", "Q", "A", "M", "A", "M"]},
        {"kind": "perpendicular", "args": ["H", "J", "M", "I"]},
    ],
)

BUILDERS["ht26m2-13"] = (
    two_tangents("M", "A", "B", "C", "D", "H", "I", "E"),
    [
        {"kind": "concyclic", "args": ["M", "A", "O", "B"]},
        {"kind": "product_equal", "args": ["M", "C", "M", "D", "M", "A", "M", "A"]},
        {"kind": "perpendicular", "args": ["H", "E", "A", "I"]},
    ],
)

BUILDERS["hy26-DS1"] = (
    Construction(ops=CIRC + [
        Op(op="free", name="I", params={"outside": "w"}),
        Op(op="tangent_from", name="t1", args=["w", "I"], params={"branch": 0, "touch_point": "A"}),
        Op(op="tangent_from", name="t2", args=["w", "I"], params={"branch": 1, "touch_point": "B"}),
        Op(op="on_object", name="N", args=["w"]),
        Op(op="intersect", name="M", args=["line:IN", "w"], params={"not": "N"}),
    ]),
    [
        {"kind": "perpendicular", "args": ["A", "B", "O", "I"]},
        {"kind": "concyclic", "args": ["A", "B", "O", "I"]},
        {"kind": "product_equal", "args": ["I", "A", "I", "A", "I", "M", "I", "N"]},
    ],
)

BUILDERS["bn26-4"] = (
    Construction(ops=CIRC + [
        Op(op="on_object", name="A", args=["w"]),
        Op(op="reflect_point", name="B", args=["A", "O"]),
        Op(op="on_object", name="C", args=["w"]),
        Op(op="foot", name="H", args=["C", "line:AB"]),
        Op(op="divide_ratio", name="D", args=["C", "H"], params={"t": 0.45}),
        Op(op="intersect", name="E", args=["line:AD", "w"], params={"not": "A"}),
    ]),
    [
        {"kind": "concyclic", "args": ["B", "H", "D", "E"]},
        {"kind": "equal_angle", "args": ["A", "D", "H", "A", "B", "E"]},
    ],
)

BUILDERS["hcm26-7"] = (
    Construction(ops=acute_altitudes() + [
        Op(op="reflect_point", name="K", args=["A", "O"]),
        Op(op="intersect", name="I", args=["line:EF", "line:AH"]),
        Op(op="intersect", name="J", args=["line:AK", "line:BC"]),
    ]),
    [
        {"kind": "concyclic", "args": ["B", "F", "E", "C"]},
        {"kind": "equal_angle", "args": ["A", "B", "D", "A", "K", "C"]},
        {"kind": "product_equal", "args": ["A", "F", "A", "K", "A", "H", "A", "C"]},
        {"kind": "parallel", "args": ["H", "K", "I", "J"]},
    ],
)

BUILDERS["na26-4"] = (
    Construction(ops=acute_altitudes() + [
        Op(op="midpoint", name="M", args=["B", "C"]),
        Op(op="reflect_point", name="L", args=["A", "O"]),
        Op(op="intersect", name="N", args=["line:AL", "line:ME"]),
        Op(op="intersect", name="K", args=["line:AM", "line:EF"]),
        Op(op="foot", name="I", args=["K", "line:BC"]),
        Op(op="circumcircle", name="wADI", args=["A", "D", "I"]),
        # Tên điểm PHẢI là "P", "Q" — đúng như đề bài gốc và predicate đã lưu.
        Op(op="intersect", name="P", args=["line:AB", "wADI"], params={"not": "A"}),
        Op(op="intersect", name="Q", args=["line:AC", "wADI"], params={"not": "A"}),
    ]),
    [
        {"kind": "concyclic", "args": ["A", "E", "H", "F"]},
        {"kind": "equal_angle", "args": ["B", "A", "D", "L", "A", "C"]},
        {"kind": "product_equal", "args": ["A", "E", "A", "B", "A", "N", "O", "M"], "value": 2.0},
        {"kind": "perpendicular", "args": ["P", "K", "A", "C"]},
        {"kind": "perpendicular", "args": ["Q", "K", "A", "B"]},
    ],
)

BUILDERS["nbc26-3"] = (
    Construction(ops=[
        Op(op="triangle", args=["A", "B", "C"], params={"hint": "right"}),
        Op(op="midpoint", name="O", args=["B", "C"]),
        Op(op="circle_through", name="w", args=["O", "B"]),
        Op(op="divide_ratio", name="H", args=["O", "C"], params={"t": 0.4}),
        Op(op="perpendicular", name="dH", args=["H", "line:BC"]),
        Op(op="intersect", name="E", args=["dH", "line:AC"]),
        Op(op="intersect", name="F", args=["dH", "line:AB"]),
        Op(op="intersect", name="D", args=["line:BE", "w"], params={"not": "B"}),
        Op(op="intersect", name="I", args=["line:AD", "line:BC"]),
        Op(op="tangent_at", name="tA", args=["w", "A"]),
        Op(op="intersect", name="G", args=["tA", "line:EF"]),
        Op(op="parallel", name="pB", args=["B", "line:FC"]),
        Op(op="intersect", name="S", args=["pB", "line:CA"]),
        Op(op="intersect", name="K", args=["dH", "line:AD"]),
    ]),
    [
        {"kind": "collinear", "args": ["F", "D", "C"]},
        {"kind": "equal_angle", "args": ["F", "D", "A", "F", "B", "C"]},
        {"kind": "midpoint", "args": ["G", "E", "F"]},
        {"kind": "product_equal", "args": ["O", "H", "O", "I", "O", "A", "O", "A"]},
        {"kind": "parallel", "args": ["O", "S", "C", "K"]},
    ],
)

BUILDERS["qn26-TL6"] = (
    Construction(ops=CIRC + [
        Op(op="free", name="M", params={"outside": "w"}),
        Op(op="tangent_from", name="t1", args=["w", "M"], params={"branch": 0, "touch_point": "A"}),
        Op(op="tangent_from", name="t2", args=["w", "M"], params={"branch": 1, "touch_point": "B"}),
        Op(op="reflect_point", name="C", args=["B", "O"]),
        Op(op="intersect", name="D", args=["line:MC", "w"], params={"not": "C"}),
        Op(op="intersect", name="H", args=["line:AB", "line:MO"]),
        Op(op="parallel", name="pC", args=["C", "line:DH"]),
        Op(op="intersect", name="E", args=["pC", "line:AB"]),
    ]),
    [
        {"kind": "parallel", "args": ["A", "C", "M", "O"]},
        {"kind": "concyclic", "args": ["M", "D", "H", "B"]},
        {"kind": "equal_angle", "args": ["D", "H", "M", "M", "C", "O"]},
        {"kind": "midpoint", "args": ["A", "E", "H"]},
    ],
)

BUILDERS["th26-14"] = (
    Construction(ops=CIRC + [
        Op(op="free", name="M", params={"outside": "w"}),
        Op(op="tangent_from", name="t1", args=["w", "M"], params={"branch": 0, "touch_point": "A"}),
        Op(op="tangent_from", name="t2", args=["w", "M"], params={"branch": 1, "touch_point": "B"}),
        Op(op="intersect", name="I", args=["line:OM", "line:AB"]),
        Op(op="divide_ratio", name="K", args=["B", "I"], params={"t": 0.4}),
        Op(op="foot", name="H", args=["M", "line:OK"]),
        Op(op="reflect_point", name="D", args=["B", "O"]),
        Op(op="intersect", name="C", args=["line:MD", "w"], params={"not": "D"}),
        Op(op="midpoint", name="E", args=["M", "I"]),
    ]),
    [
        {"kind": "concyclic", "args": ["A", "O", "B", "M"]},
        {"kind": "product_equal", "args": ["O", "K", "O", "H", "O", "A", "O", "A"]},
        {"kind": "collinear", "args": ["A", "C", "E"]},
    ],
)

BUILDERS["hn24-IV"] = (
    Construction(ops=CIRC + [
        Op(op="free", name="A", params={"outside": "w"}),
        Op(op="tangent_from", name="t1", args=["w", "A"], params={"branch": 0, "touch_point": "B"}),
        Op(op="tangent_from", name="t2", args=["w", "A"], params={"branch": 1, "touch_point": "C"}),
        Op(op="reflect_point", name="D", args=["B", "O"]),
        Op(op="intersect", name="E", args=["line:AD", "w"], params={"not": "D"}),
        Op(op="intersect", name="H", args=["line:BC", "line:AO"]),
        Op(op="divide_ratio", name="M", args=["B", "C"], params={"t": 1.6}),
        Op(op="foot", name="N", args=["M", "line:AB"]),
        Op(op="midpoint", name="K", args=["M", "N"]),
    ]),
    [
        {"kind": "concyclic", "args": ["A", "B", "O", "C"]},
        {"kind": "product_equal", "args": ["A", "B", "A", "B", "A", "E", "A", "D"]},
        {"kind": "product_equal", "args": ["A", "B", "A", "B", "A", "H", "A", "O"]},
        {"kind": "equal_angle", "args": ["H", "D", "O", "H", "B", "E"]},
        {"kind": "collinear", "args": ["B", "E", "K"]},
    ],
)

BUILDERS["hn26-IV2"] = (
    Construction(ops=[
        Op(op="triangle", args=["A", "B", "C"], params={"hint": "right"}),
        Op(op="midpoint", name="O", args=["B", "C"]),
        Op(op="circle_through", name="w", args=["O", "B"]),
        Op(op="divide_ratio", name="H", args=["A", "B"], params={"t": 0.3}),
        Op(op="foot", name="D", args=["H", "line:BC"]),
        Op(op="perpendicular", name="dH", args=["H", "line:BC"]),
        Op(op="intersect", name="E", args=["dH", "line:AC"]),
        Op(op="intersect", name="F", args=["line:CH", "w"], params={"not": "C"}),
        Op(op="perpendicular", name="dA", args=["A", "line:ED"]),
        Op(op="intersect", name="M", args=["dA", "line:DF"]),
        Op(op="intersect", name="K", args=["line:BM", "w"], params={"not": "B"}),
    ]),
    [
        {"kind": "concyclic", "args": ["A", "H", "D", "C"]},
        {"kind": "right_angle", "args": ["E", "M", "H"]},
        {"kind": "product_equal", "args": ["A", "E", "B", "C", "E", "H", "A", "B"]},
        {"kind": "equal_length", "args": ["H", "K", "H", "M"]},
    ],
)


def main() -> None:
    out = []
    all_ok = True
    for cid, (construction, preds) in BUILDERS.items():
        claims = [Predicate(p["kind"], p["args"], p.get("value")) for p in preds]
        v = verify(construction, claims)
        all_ok &= v.ok
        status = "OK " if v.ok else "SAI"
        print(f"{status}  {cid:<14} {v.n_configs}/5 cấu hình  {len(preds)} vị từ")
        if not v.ok:
            for f in v.failures():
                print(f"        lỗi: {f.predicate!r}  sai lệch {f.max_residual:.2e}")
        out.append({"context_id": cid, "construction": json.loads(construction.model_dump_json())})

    if not all_ok:
        raise SystemExit(
            "\nCó kịch bản kiểm chứng THẤT BẠI — không ghi file. Xem lỗi ở trên: "
            "thường là tên điểm trong Construction lệch với tên điểm trong predicate "
            "(đối chiếu lại với eval-seed.jsonl), hoặc phép dựng chưa đúng quan hệ đề bài."
        )

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nĐã ghi {len(out)} kịch bản vào {OUT_PATH}")


if __name__ == "__main__":
    main()
