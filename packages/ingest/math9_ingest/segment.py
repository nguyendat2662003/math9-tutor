"""Tách văn bản đề thi thành từng bài -> từng ý (a, b, c).

Router phải phân loại RIÊNG từng ý vì ý sau thường khó hơn hẳn ý trước. Nếu
gán cả bài một nhãn theo ý khó nhất, hệ thống sẽ chạy chiến lược mức 3 tốn kém
cho cả những ý đơn giản. Việc tách phải làm ngay từ khâu nhập dữ liệu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# "Bài 1.", "Câu 2:", "Câu I.", "Bài IV -"
RE_PROBLEM = re.compile(
    r"^\s*(?:Bài|Câu)\s+([0-9]{1,2}|[IVX]{1,5})\s*[.:)\-–]",
    re.IGNORECASE | re.MULTILINE,
)
# "a)", "b.", "1)", "c/"
RE_PART = re.compile(r"^\s*([a-hA-H1-9])\s*[).\/]\s+", re.MULTILINE)
# "(2,0 điểm)" — mốc điểm cũng là tín hiệu ranh giới bài
RE_SCORE = re.compile(r"\(\s*(\d+(?:[.,]\d+)?)\s*(?:điểm|đ)\s*\)", re.IGNORECASE)
# Tín hiệu bài có hình
RE_FIGURE_HINT = re.compile(
    r"(?i)\b(hình\s+vẽ|như\s+hình|hình\s+\d|xem\s+hình|đường\s+tròn|tam\s+giác|"
    r"tứ\s+giác|tiếp\s+tuyến|đường\s+cao|trung\s+tuyến)\b"
)


@dataclass
class Part:
    label: str
    statement: str


@dataclass
class Problem:
    number: str
    stem: str                      # phần dẫn chung trước các ý
    parts: list[Part] = field(default_factory=list)
    score: float | None = None
    likely_geometry: bool = False
    raw: str = ""

    def statement(self) -> str:
        body = "\n".join(f"{p.label}) {p.statement}" for p in self.parts)
        return f"{self.stem}\n{body}".strip()


def split_problems(text: str) -> list[Problem]:
    marks = list(RE_PROBLEM.finditer(text))
    if not marks:
        return [_build("1", text)]

    out: list[Problem] = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append(_build(m.group(1), text[m.end(): end]))
    return out


def _build(number: str, body: str) -> Problem:
    body = body.strip()
    score = None
    if (sm := RE_SCORE.search(body)):
        score = float(sm.group(1).replace(",", "."))
        body = body[: sm.start()] + body[sm.end():]

    parts_marks = list(RE_PART.finditer(body))
    if parts_marks:
        stem = body[: parts_marks[0].start()].strip()
        parts = []
        for i, pm in enumerate(parts_marks):
            end = parts_marks[i + 1].start() if i + 1 < len(parts_marks) else len(body)
            parts.append(Part(pm.group(1).lower(), body[pm.end(): end].strip()))
    else:
        stem, parts = body, [Part("a", body)]

    return Problem(
        number=str(number),
        stem=stem,
        parts=parts,
        score=score,
        likely_geometry=bool(RE_FIGURE_HINT.search(body)),
        raw=body,
    )


def split_answer_key(text: str) -> dict[str, str]:
    """Ghép đáp án vào đúng bài. Đáp án thường ở cuối file hoặc file riêng."""
    out: dict[str, str] = {}
    marks = list(RE_PROBLEM.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[str(m.group(1))] = text[m.end(): end].strip()
    return out
