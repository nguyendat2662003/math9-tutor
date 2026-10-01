"""Chấm đáp án tự động bằng SymPy — không dùng so khớp chuỗi.

'x = 2 hoặc x = 3' và 'S = {2; 3}' là cùng một đáp án. So khớp chuỗi sẽ
báo sai và làm hỏng toàn bộ số liệu eval.

Gold có hai dạng:
  - chuỗi:  "x = 4; x = −2", "1040 m (x = 250, y = 270)"
  - dict (trắc nghiệm): {"letter": "B", "value": "14"} — chấp nhận đúng giá trị
    hoặc nêu đúng chữ cái.

Lời giải thường kèm điều kiện, xấp xỉ, hoặc nhắc lại đề ("∛(−27) = −3") — các
số đó không phải đáp án. Ta cắt bỏ phần đuôi điều kiện rồi thử vài cách lấy
"phần kết luận" của câu; khớp một cách là đủ.
"""

from __future__ import annotations

import re

import sympy as sp

# Ký tự toán Unicode hay gặp trong đề Việt Nam -> dạng máy đọc được
_NORMALIZE = {
    "−": "-", "–": "-", "—": "-",   # − – —
    "×": "*", "·": "*", "⋅": "*",   # × · ⋅
    "÷": "/", "√": "sqrt", "π": "pi",
    "²": "", "³": "",                    # ² ³ — bỏ, tránh sinh số giả (cm² -> 2)
}

# Đuôi điều kiện / xấp xỉ / diễn giải — không chứa đáp án
_RE_TAIL = re.compile(r"(\s+với\s|\s+khi\s|\s+trong đó\s|≈|xấp xỉ|tức là|đạt được|\(\s*x\s*=|\(\s*[a-z]\s*=)", re.I)
# Ngoặc chứa điều kiện/giải thích: "(x = 250, y = 270)", "(h = 8/3 dm)"
_RE_PAREN_COND = re.compile(r"\((?=[^)]*(?:=|khi|với))[^)]*\)")
# Từ mở đầu phần kết luận
_RE_LEAD = re.compile(r"(?:^|\s)(?:là|bằng|được|vậy|=)\s", re.I)


def normalize(text: str) -> str:
    for k, v in _NORMALIZE.items():
        text = text.replace(k, v)
    # 2,5 -> 2.5 nhưng "x1, x2" giữ nguyên
    return re.sub(r"(?<=\d),(?=\d)", ".", text)


def extract_numbers(text: str) -> set:
    """Tập các số (kể cả phân số, căn đơn giản) xuất hiện trong chuỗi."""
    out = set()
    for tok in re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?|sqrt\(?\d+\)?", normalize(text)):
        try:
            out.add(sp.nsimplify(tok))
        except Exception:
            continue
    return out


def extract_number_list(text: str) -> list:
    """Các số theo đúng thứ tự xuất hiện — cho đáp án mà thứ tự có nghĩa, vd (x; y) = (8; 3)."""
    out = []
    for tok in re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?", normalize(text)):
        try:
            out.append(sp.nsimplify(tok))
        except Exception:
            continue
    return out


def grade_ordered(predicted: str, expected: str) -> bool:
    """Như `grade` nhưng các số phải khớp cả thứ tự: (3; 8) ≠ (8; 3)."""
    gold = extract_number_list(_strip_conditions(expected))
    return bool(gold) and any(extract_number_list(c) == gold for c in [predicted, *_candidates(predicted)])


def _strip_conditions(text: str) -> str:
    text = _RE_PAREN_COND.sub(" ", text)
    m = _RE_TAIL.search(text)
    return text[: m.start()] if m else text


def _candidates(text: str) -> list[str]:
    """Các cách đọc 'phần kết luận' của một câu trả lời."""
    core = _strip_conditions(text)
    cands = [core]
    if "=" in core:
        cands.append(core.rsplit("=", 1)[1])
    leads = list(_RE_LEAD.finditer(core))
    if leads:
        cands.append(core[leads[-1].end():])
    return cands


def _ineq_signs(text: str) -> set[str]:
    """Dấu bất đẳng thức trong chuỗi: 'x <= 4' và 'x ≤ 4' cùng cho {'≤'}."""
    t = text.replace("<=", "≤").replace(">=", "≥")
    return {c for c in t if c in "≤≥<>"}


def _grade_str(predicted: str, expected: str) -> bool:
    if normalize(predicted).strip().lower() == normalize(expected).strip().lower():
        return True
    # Chỉ so số thì 'x ≥ 4' sẽ khớp với 'x ≤ 4' — với bất phương trình, dấu cũng là đáp án
    need = _ineq_signs(_strip_conditions(expected))
    if need and not need <= _ineq_signs(_strip_conditions(predicted)):
        return False
    gold = extract_numbers(_strip_conditions(expected))
    if not gold:
        # Gold không có số (ví dụ "sin B = AC/BC"): so chuỗi sau chuẩn hóa khoảng trắng
        g = re.sub(r"\s+", "", normalize(expected)).lower()
        return g in re.sub(r"\s+", "", normalize(predicted)).lower()
    return any(extract_numbers(c) == gold for c in _candidates(predicted))


def grade(predicted: str, expected) -> bool:
    if isinstance(expected, dict):
        letter, value = expected.get("letter"), expected.get("value")
        if value is not None and _grade_str(predicted, str(value)):
            return True
        if letter and re.search(rf"(?<![A-Za-z]){re.escape(letter)}(?![A-Za-z])", predicted):
            return True
        return False
    return _grade_str(predicted, str(expected))
