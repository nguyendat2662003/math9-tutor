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
# "khi" chỉ là đuôi điều kiện khi phía sau có biểu thức ("khi x = 2"); "sau khi thả vật cao 1,13 m" thì không
_RE_TAIL = re.compile(
    r"(\s+với\s|\s+khi\s(?=[^.;]*[=<>≤≥])|\s+trong đó\s|≈|xấp xỉ|tức là|đạt được|\(\s*x\s*=|\(\s*[a-z]\s*=)", re.I)
# Ngoặc chứa điều kiện/giải thích: "(x = 250, y = 270)", "(h = 8/3 dm)"
_RE_PAREN_COND = re.compile(r"\((?=[^)]*(?:=|khi|với))[^)]*\)")
# Từ mở đầu phần kết luận
_RE_LEAD = re.compile(r"(?:^|\s)(?:là|bằng|được|vậy|=)\s", re.I)


_RE_FRAC = re.compile(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
_RE_SQRT = re.compile(r"\\sqrt\s*\{([^{}]*)\}")
_LATEX_SYMBOLS = {
    r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥", r"\ne": "≠", r"\neq": "≠", r"\pm": "±",
    r"\cdot": "*", r"\times": "*", r"\infty": "∞", r"\pi": "pi", r"\%": "%", r"\left": "", r"\right": "",
    r"\,": " ", r"\;": " ", r"\!": "", r"\ ": " ", r"\{": "{", r"\}": "}",
}


def _frac_to_text(m: re.Match) -> str:
    r"""\dfrac{60}{17} -> 60/17 (số thuần thì không bọc ngoặc để nhận ra phân số); biểu thức thì bọc."""
    a, b = m.group(1).strip(), m.group(2).strip()
    simple = lambda t: re.fullmatch(r"-?[\d.]+", t) is not None  # noqa: E731
    return f"{a}/{b}" if simple(a) and simple(b) else f"({a})/({b})"


_N = r"[-−–]?[\d.,]+(?:/\d+)?"
_RE_INTERVAL_UP = re.compile(rf"([(\[])\s*({_N})\s*;\s*\+?\s*∞\s*\)")             # (a; +∞)  [a; +∞)
_RE_INTERVAL_DOWN = re.compile(rf"\(\s*[-−–]\s*∞\s*;\s*({_N})\s*([)\]])")        # (-∞; a)  (-∞; a]


def _intervals_to_inequalities(text: str) -> str:
    """Tập nghiệm viết kiểu khoảng: S = (−1; +∞) -> S = > −1, để so được với đáp án "x > −1"."""
    text = _RE_INTERVAL_UP.sub(lambda m: ("> " if m.group(1) == "(" else "≥ ") + m.group(2), text)
    return _RE_INTERVAL_DOWN.sub(lambda m: ("< " if m.group(2) == ")" else "≤ ") + m.group(1), text)


def _delatex(text: str) -> str:
    r"""Model hay viết đáp án bằng LaTeX ($\dfrac{60}{17}$, $x \le 5$): đưa về dạng chữ trước khi đọc số."""
    if "\\" in text or "$" in text:
        for _ in range(3):                                             # phân số lồng nhau
            text = _RE_FRAC.sub(_frac_to_text, text)
        text = _RE_SQRT.sub(r"sqrt(\1)", text)
        for k in sorted(_LATEX_SYMBOLS, key=len, reverse=True):
            text = text.replace(k, _LATEX_SYMBOLS[k])
        text = text.replace("$", "")
    return _intervals_to_inequalities(text)


def normalize(text: str) -> str:
    text = _delatex(text)
    for k, v in _NORMALIZE.items():
        text = text.replace(k, v)
    text = re.sub(r"(?<=\d)[ \u00a0](?=\d{3}(?!\d))", "", text)       # 14 000 -> 14000
    # 2,5 -> 2.5 nhưng "x1, x2" giữ nguyên
    return re.sub(r"(?<=\d),(?=\d)", ".", text)


# "-" chỉ là dấu âm khi không đứng ngay sau chữ/số/ngoặc đóng: "4-2√2" là phép trừ, không phải {4, -2}
_NUM = r"(?:(?<![\w)\]])-)?\d+(?:\.\d+)?(?:/\d+)?"


def extract_numbers(text: str) -> set:
    """Tập các số (kể cả phân số, căn đơn giản) xuất hiện trong chuỗi."""
    out = set()
    for tok in re.findall(_NUM + r"|sqrt\(\d+\)|sqrt\d+", normalize(text)):
        try:
            out.add(sp.nsimplify(tok))
        except Exception:
            continue
    return out


def extract_number_list(text: str) -> list:
    """Các số theo đúng thứ tự xuất hiện — cho đáp án mà thứ tự có nghĩa, vd (x; y) = (8; 3)."""
    out = []
    for tok in re.findall(_NUM, normalize(text)):
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
    text = _RE_PAREN_COND.sub(" ", _delatex(text))
    m = _RE_TAIL.search(text)
    if not m:
        return text
    # "≈ 1139 cm³", "Sxq ≈ 1884", "xác định khi x ≤ 1/2": phần đứng TRƯỚC không có số -> đáp án nằm phía sau
    if m.group(0).strip().lower() in ("≈", "xấp xỉ", "khi") and not re.search(r"\d", text[: m.start()]):
        return text[m.end():]
    return text[: m.start()]


def _candidates(text: str) -> list[str]:
    """Các cách đọc 'phần kết luận' của một câu trả lời."""
    core = _strip_conditions(text)
    cands = [core]
    if "=" in core:
        cands.append(core.rsplit("=", 1)[1])
    leads = list(_RE_LEAD.finditer(core))
    if leads:
        cands.append(core[leads[-1].end():])
    segs = re.findall(r"\$([^$]+)\$", text)                  # "Có $14$ xe 7 chỗ" -> số 7 là nhắc lại đề
    if segs:
        cands += [*segs, " ".join(segs)]
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


_RE_TF_GOLD = re.compile(r"\s*[ĐS](?:\s*[-–;,]\s*[ĐS])+\s*")
_RE_TF_TOKEN = re.compile(r"(?<![\w])(Đúng|Sai|Đ|S)(?![\w])")


def _grade_true_false(predicted: str, expected: str) -> bool:
    toks = lambda t: ["Đ" if x in ("Đúng", "Đ") else "S" for x in _RE_TF_TOKEN.findall(t)]  # noqa: E731
    return toks(predicted) == toks(expected)


def grade(predicted: str, expected) -> bool:
    if isinstance(expected, str) and _RE_TF_GOLD.fullmatch(expected):
        return _grade_true_false(predicted, expected)
    if isinstance(expected, dict):
        letter, value = expected.get("letter"), expected.get("value")
        if value is not None and _grade_str(predicted, str(value)):
            return True
        if letter and re.search(rf"(?<![A-Za-z]){re.escape(letter)}(?![A-Za-z])", predicted):
            return True
        return False
    return _grade_str(predicted, str(expected))
