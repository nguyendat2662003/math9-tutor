"""Danh mục nhãn dùng chung. Router chỉ cần danh mục này, không cần SGK."""

from enum import StrEnum


class GoalType(StrEnum):
    """Dạng mục tiêu — khóa để truy xuất sổ tay phương pháp.

    Chuyên đề cho biết ĐƯỢC DÙNG GÌ; goal_type cho biết NÊN ĐI HƯỚNG NÀO.
    """

    # hình học
    PROVE_CONCYCLIC = "prove_concyclic"
    PROVE_TANGENT = "prove_tangent"
    PROVE_EQUAL_LENGTH = "prove_equal_length"
    PROVE_EQUAL_ANGLE = "prove_equal_angle"
    PROVE_PERPENDICULAR = "prove_perpendicular"
    PROVE_PARALLEL = "prove_parallel"
    PROVE_COLLINEAR = "prove_collinear"
    PROVE_CONCURRENT = "prove_concurrent"
    PROVE_SIMILAR = "prove_similar"
    PROVE_MIDPOINT = "prove_midpoint"
    FIND_FIXED_POINT = "find_fixed_point"
    FIND_LOCUS = "find_locus"
    FIND_MAX_MIN = "find_max_min"
    COMPUTE_LENGTH = "compute_length"
    COMPUTE_AREA = "compute_area"
    COMPUTE_ANGLE = "compute_angle"
    # đại số
    SOLVE_EQUATION = "solve_equation"
    SOLVE_SYSTEM = "solve_system"
    SIMPLIFY_EXPRESSION = "simplify_expression"
    EVALUATE_ROOT_EXPRESSION = "evaluate_root_expression"
    FIND_PARAMETER = "find_parameter"
    WORD_PROBLEM = "word_problem"
    PROVE_INEQUALITY = "prove_inequality"
    ANALYZE_FUNCTION = "analyze_function"
    COMPUTE_PROBABILITY = "compute_probability"
    ANALYZE_STATISTICS = "analyze_statistics"


class Confidence(StrEnum):
    HIGH = "high"
    PARTIAL = "partial"
    LOW = "low"


#: Nhãn tiếng Việt cho từng goal_type — dùng trong sổ tay và giao diện.
GOAL_TYPE_VI: dict[str, str] = {
    "prove_concyclic": "Chứng minh các điểm cùng thuộc một đường tròn",
    "prove_tangent": "Chứng minh đường thẳng là tiếp tuyến",
    "prove_equal_length": "Chứng minh hai đoạn thẳng bằng nhau",
    "prove_equal_angle": "Chứng minh hai góc bằng nhau",
    "prove_perpendicular": "Chứng minh hai đường thẳng vuông góc",
    "prove_parallel": "Chứng minh hai đường thẳng song song",
    "prove_collinear": "Chứng minh ba điểm thẳng hàng",
    "prove_concurrent": "Chứng minh ba đường thẳng đồng quy",
    "prove_similar": "Chứng minh hai tam giác đồng dạng",
    "prove_midpoint": "Chứng minh một điểm là trung điểm",
    "find_fixed_point": "Chứng minh đi qua điểm cố định, tìm điểm cố định",
    "find_locus": "Tìm quỹ tích, tập hợp điểm",
    "find_max_min": "Tìm giá trị lớn nhất, nhỏ nhất",
    "compute_length": "Tính độ dài đoạn thẳng",
    "compute_area": "Tính diện tích, chu vi",
    "compute_angle": "Tính số đo góc",
    "solve_equation": "Giải phương trình",
    "solve_system": "Giải hệ phương trình",
    "simplify_expression": "Rút gọn biểu thức",
    "evaluate_root_expression": "Tính giá trị biểu thức chứa căn, chứng minh đẳng thức căn",
    "find_parameter": "Tìm tham số thỏa điều kiện",
    "word_problem": "Giải bài toán bằng cách lập phương trình, hệ phương trình",
    "prove_inequality": "Chứng minh bất đẳng thức",
    "analyze_function": "Khảo sát hàm số, đồ thị",
    "compute_probability": "Tính xác suất",
    "analyze_statistics": "Thống kê, tần số",
}
