"""Chấm đáp án cho eval. Logic cốt lõi nằm ở `math9_verifier.answer` (dùng chung với phần chấm đề);
đây chỉ thêm cách chấm theo từng dòng dữ liệu (`accept`, `grading: "context"`)."""

from math9_verifier.answer import _delatex, _ineq_signs, _strip_conditions, extract_numbers, grade, normalize  # noqa: F401


def _in_context(predicted: str, expected, statement: str) -> bool:
    """Đáp án gốc nằm TRỌN trong câu trả lời, số thừa chỉ được là số đã có trong đề.

    Cứu các câu đúng mà model nhắc lại đề ("Có 14 xe 7 chỗ", "chiếm 70% … từ 3 giờ"). Số thừa không có
    trong đề (một nghiệm khác, một kết quả trung gian) thì vẫn bị chấm sai.
    """
    text = expected["value"] if isinstance(expected, dict) else str(expected)
    gold = extract_numbers(_strip_conditions(text))
    if not gold:
        return False
    need = _ineq_signs(_strip_conditions(text))
    if need and not need <= _ineq_signs(_delatex(predicted)):
        return False
    pred = extract_numbers(predicted)
    return gold <= pred and (pred - gold) <= extract_numbers(statement)


def grade_item(predicted: str, item: dict) -> bool:
    """Chấm một dòng dữ liệu: đáp án gốc, các đáp án chấp nhận thêm (`gold.accept`: cách viết khác như
    32π/3 và 33,51), rồi — nếu dòng bật `"grading": "context"` — luật nhắc lại số trong đề."""
    gold = item["gold"]
    if grade(predicted, gold["answer"]):
        return True
    if any(grade(predicted, alt) for alt in gold.get("accept", [])):
        return True
    return item.get("grading") == "context" and _in_context(predicted, gold["answer"], item["statement"])
