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
