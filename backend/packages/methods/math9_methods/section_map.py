"""Ánh xạ mục/dạng trong tài liệu tra cứu -> goal_type.

Đây là bản đồ do CON NGƯỜI định nghĩa, một lần, cho mỗi tài liệu nguồn. Nó nói:
mục "Đường tròn" của tài liệu này chứa nguyên liệu cho những goal_type nào, và
một goal_type như prove_concyclic rút nguyên liệu từ những mục nào.

Quan hệ là NHIỀU-NHIỀU: một dạng bài rải nguyên liệu cho nhiều goal_type, và
một goal_type gom nguyên liệu từ nhiều dạng bài. Chính vì quan hệ nhiều-nhiều
này mà không thể dùng thẳng cấu trúc tài liệu gốc làm sổ tay.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceSection:
    """Một mục/dạng trong tài liệu gốc."""

    ref: str                       # "Dạng 29" hoặc "Phụ lục mục 10"
    title: str                     # "Góc với đường tròn"
    page: int | None = None
    goal_types: list[str] = field(default_factory=list)  # goal_type mà mục này nuôi


# Bản đồ cho tài liệu "Cẩm nang tra cứu công thức, dạng toán Toán 9" (toanmath, 59tr).
# Suy ra từ mục lục; con người xác nhận. Các dạng đại số ánh xạ thẳng, các mục
# hình học rải cho nhiều goal_type.
CAM_NANG_TOANMATH: list[SourceSection] = [
    # --- đại số: phần lớn ánh xạ 1-1 ---
    SourceSection("Dạng 1", "Điều kiện xác định biểu thức chứa căn", 3, ["simplify_expression"]),
    SourceSection("Dạng 2", "Tìm x, giải phương trình", 3, ["solve_equation"]),
    SourceSection("Dạng 3", "Các phép toán căn thức", 4, ["simplify_expression"]),
    SourceSection("Dạng 4", "Tìm x nguyên để biểu thức nguyên", 5, ["find_parameter"]),
    SourceSection("Dạng 5", "Giá trị lớn nhất, nhỏ nhất", 5, ["find_max_min"]),
    SourceSection("Dạng 6", "Hàm số bậc nhất và tính chất", 6, ["analyze_function"]),
    SourceSection("Dạng 7", "Vẽ đồ thị hàm số bậc nhất", 6, ["analyze_function"]),
    SourceSection("Dạng 8", "Vị trí tương đối hai đường thẳng", 7, ["analyze_function"]),
    SourceSection("Dạng 9", "Lập phương trình đường thẳng", 7, ["analyze_function"]),
    SourceSection("Dạng 10", "Điểm cố định của họ đường thẳng", 9, ["find_fixed_point"]),
    SourceSection("Dạng 11", "Ba đường thẳng đồng quy", 9, ["prove_concurrent", "find_parameter"]),
    SourceSection("Dạng 12", "Khoảng cách từ gốc đến đường thẳng", 10, ["compute_length"]),
    SourceSection("Dạng 13", "Tính chất hàm số y=ax²", 11, ["analyze_function"]),
    SourceSection("Dạng 14", "Vẽ đồ thị y=ax²", 12, ["analyze_function"]),
    SourceSection("Dạng 15", "Tương giao đường thẳng và parabol", 13, ["find_parameter", "solve_equation"]),
    SourceSection("Dạng 16", "Giải bài toán bằng cách lập phương trình", 14, ["word_problem"]),
    SourceSection("Dạng 17", "Dự đoán số nghiệm của hệ", 19, ["solve_system"]),
    SourceSection("Dạng 18", "Giải hệ bằng cộng, thế", 20, ["solve_system"]),
    SourceSection("Dạng 19", "Tìm hệ số biết nghiệm của hệ", 21, ["find_parameter"]),
    SourceSection("Dạng 20", "Điều kiện hệ có nghiệm duy nhất", 22, ["find_parameter"]),
    SourceSection("Dạng 21", "Giải phương trình bậc hai", 23, ["solve_equation"]),
    SourceSection("Dạng 22", "Tìm m để phương trình có nghiệm cho trước", 24, ["find_parameter"]),
    SourceSection("Dạng 23", "Biện luận nghiệm phương trình bậc hai", 25, ["find_parameter"]),
    SourceSection("Dạng 24", "Hệ thức Vi-ète", 26, ["find_parameter", "prove_inequality", "solve_equation"]),
    SourceSection("Dạng 25", "Phương trình trùng phương", 33, ["solve_equation"]),
    # --- hình học: rải cho nhiều goal_type ---
    SourceSection("Dạng 26", "Hệ thức lượng trong tam giác vuông", 33,
                  ["compute_length", "compute_angle", "prove_equal_length"]),
    SourceSection("Dạng 27", "Tỉ số lượng giác góc nhọn", 35,
                  ["compute_length", "compute_angle"]),
    SourceSection("Dạng 28", "Đường tròn", 36,
                  ["prove_tangent", "compute_length", "prove_equal_length", "prove_perpendicular"]),
    SourceSection("Dạng 29", "Góc với đường tròn", 39,
                  ["prove_concyclic", "prove_equal_angle", "compute_angle", "prove_similar"]),
    SourceSection("Dạng 30", "Các mô hình mẫu trong đề thi vào 10", 42,
                  ["prove_concyclic", "prove_collinear", "prove_concurrent",
                   "find_fixed_point", "prove_perpendicular", "prove_midpoint",
                   "prove_equal_length", "find_max_min"]),
    SourceSection("Dạng 31", "Hình học không gian", 47, ["compute_area"]),
    # --- phụ lục lớp 8: đúng theo goal_type ---
    SourceSection("PL mục 6", "Các trường hợp đồng dạng của tam giác", 53, ["prove_similar"]),
    SourceSection("PL mục 7", "Chứng minh hai góc bằng nhau", 54, ["prove_equal_angle"]),
    SourceSection("PL mục 8", "Chứng minh hai đoạn thẳng bằng nhau", 54, ["prove_equal_length"]),
    SourceSection("PL mục 9", "Chứng minh hai đường thẳng song song", 55, ["prove_parallel"]),
    SourceSection("PL mục 10", "Chứng minh hai đường thẳng vuông góc", 55, ["prove_perpendicular"]),
    SourceSection("PL mục 11", "Chứng minh ba đường thẳng đồng quy", 55, ["prove_concurrent"]),
    SourceSection("PL mục 15", "Chứng minh ba điểm thẳng hàng", 56, ["prove_collinear"]),
]


def invert(sections: list[SourceSection]) -> dict[str, list[SourceSection]]:
    """goal_type -> các mục nguồn nuôi nó. Đây là bước 'tái tổ chức' cốt lõi."""
    out: dict[str, list[SourceSection]] = {}
    for s in sections:
        for g in s.goal_types:
            out.setdefault(g, []).append(s)
    return out


def coverage_report(sections: list[SourceSection], all_goal_types: list[str]) -> dict:
    """goal_type nào có nguồn, goal_type nào tài liệu này không phủ."""
    inv = invert(sections)
    covered = set(inv)
    return {
        "covered": sorted(covered),
        "uncovered": sorted(set(all_goal_types) - covered),
        "richest": sorted(inv, key=lambda g: -len(inv[g]))[:5],
    }
