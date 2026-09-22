"""Chấm đáp án tự động bằng SymPy — không dùng so khớp chuỗi.

'x = 2 hoặc x = 3' và 'S = {2; 3}' là cùng một đáp án. So khớp chuỗi sẽ
báo sai và làm hỏng toàn bộ số liệu eval.

Gold có hai dạng:
  - chuỗi:  "x = 4; x = −2"
  - dict (trắc nghiệm): {"letter": "B", "value": "14"} — chấp nhận đúng giá trị
    hoặc nêu đúng chữ cái.
"""

from __future__ import annotations

import re

import sympy as sp

# Ký tự toán Unicode hay gặp trong đề Việt Nam -> dạng máy đọc được
_NORMALIZE = {
    "−": "-", "–": "-", "—": "-",   # − – —
    "×": "*", "·": "*", "⋅": "*",   # × · ⋅
    "÷": "/", "√": "sqrt", "π": "pi",
    "²": "^2", "³": "^3",
    ",": ".",
}


def normalize(text: str) -> str:
    for k, v in _NORMALIZE.items():
        text = text.replace(k, v)
    return text


def extract_numbers(text: str) -> set:
    """Tập các số (kể cả phân số, căn đơn giản) xuất hiện trong chuỗi."""
    text = normalize(text)
    out = set()
    for tok in re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?|sqrt\(?\d+\)?|\\sqrt\{[^}]+\}", text):
        try:
            tok = tok.replace("\\sqrt{", "sqrt(").replace("}", ")")
            out.add(sp.nsimplify(tok))
        except Exception:
            continue
    return out


def _grade_str(predicted: str, expected: str) -> bool:
    if normalize(predicted).strip().lower() == normalize(expected).strip().lower():
        return True
    return extract_numbers(predicted) == extract_numbers(expected) != set()


def grade(predicted: str, expected) -> bool:
    if isinstance(expected, dict):
        letter, value = expected.get("letter"), expected.get("value")
        if value is not None and _grade_str(predicted, str(value)):
            return True
        if letter and re.search(rf"(?<![A-Za-z]){re.escape(letter)}(?![A-Za-z])", predicted):
            return True
        return False
    return _grade_str(predicted, str(expected))
