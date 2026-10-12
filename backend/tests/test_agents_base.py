"""parse_json phải chịu được các kiểu JSON 'gần đúng' mà LLM hay trả về."""

from math9_core.agents.base import Agent
from math9_core.llm.client import LLMResponse


def _p(text: str) -> dict:
    return Agent.parse_json(LLMResponse(text=text))


def test_plain_json():
    assert _p('{"a": 1}') == {"a": 1}


def test_fenced_with_prose():
    assert _p('Kết quả:\n```json\n{"a": [1, 2]}\n```\nHết.') == {"a": [1, 2]}


def test_latex_backslashes_repaired():
    raw = r'{"claim": "x = \sqrt{2}", "tex": "\(x\)", "frac": "\frac{1}{2}"}'
    out = _p(raw)
    assert out["claim"] == r"x = \sqrt{2}"
    assert out["tex"] == r"\(x\)"
    assert out["frac"] == r"\frac{1}{2}"


def test_ambiguous_latex_commands():
    out = _p(r'{"a": "\times", "b": "\theta", "c": "\neq", "d": "\right)", "e": "\beta"}')
    assert out == {"a": r"\times", "b": r"\theta", "c": r"\neq", "d": r"\right)", "e": r"\beta"}


def test_valid_escapes_untouched():
    out = _p(r'{"s": "dòng 1\ndòng 2", "q": "nói \"a\""}')
    assert out["s"] == "dòng 1\ndòng 2" and out["q"] == 'nói "a"'


def test_raw_newline_inside_string_tolerated():
    assert _p('{"s": "a\nb"}')["s"] == "a\nb"


def test_double_escaped_latex_kept():
    # model viết đúng chuẩn JSON: "\frac" — không được biến thành form-feed + "rac"
    out = _p(r'{"a": "\frac{1}{3}", "b": "\dfrac{60}{17}"}')
    assert out == {"a": r"\frac{1}{3}", "b": r"\dfrac{60}{17}"}


def test_mixed_escaped_and_single_backslash_in_one_json():
    # trước đây: một "\le" đơn làm hỏng cả "\sqrt" hợp lệ cùng JSON -> "Invalid \escape"
    out = _p(r'{"a": "\sqrt{5}", "b": "x \le 5", "c": "\{1; 2\}", "d": "\frac{1}{2} \cdot \frac{1}{3}", "e": "50\%"}')
    assert out == {"a": r"\sqrt{5}", "b": r"x \le 5", "c": r"\{1; 2\}",
                   "d": r"\frac{1}{2} \cdot \frac{1}{3}", "e": r"50\%"}


def test_unicode_escape_and_latex_u_commands():
    out = _p(r'{"a": "é", "b": "\underline{x}", "c": "\upsilon"}')
    assert out == {"a": "é", "b": r"\underline{x}", "c": r"\upsilon"}
