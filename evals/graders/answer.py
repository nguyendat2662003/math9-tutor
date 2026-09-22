"""Chấm đáp án tự động bằng SymPy — không dùng so khớp chuỗi.

'x = 2 hoặc x = 3' và 'S = {2; 3}' là cùng một đáp án. So khớp chuỗi sẽ
báo sai và làm hỏng toàn bộ số liệu eval.
"""

from __future__ import annotations

import re

import sympy as sp


def extract_numbers(text: str) -> set:
    out = set()
    for tok in re.findall(r"-?\d+(?:[.,]\d+)?(?:/\d+)?|\\sqrt\{[^}]+\}", text):
        try:
            out.add(sp.nsimplify(tok.replace(",", ".")))
        except Exception:
            continue
    return out


def grade(predicted: str, expected: str) -> bool:
    if predicted.strip() == expected.strip():
        return True
    return extract_numbers(predicted) == extract_numbers(expected) != set()
