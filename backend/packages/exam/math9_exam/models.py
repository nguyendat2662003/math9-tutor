"""Cấu trúc câu hỏi và đề thi.

Đáp án và lời giải là dữ liệu RIÊNG của server: `public()` bỏ chúng đi trước khi
gửi cho trình duyệt, không thì học sinh mở DevTools là thấy đáp án.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Format = Literal["trac_nghiem", "tra_loi_ngan", "dung_sai", "tu_luan"]
FORMAT_VI = {
    "trac_nghiem": "Trắc nghiệm",
    "tra_loi_ngan": "Trả lời ngắn",
    "dung_sai": "Đúng/Sai",
    "tu_luan": "Tự luận",
}
PRIVATE = {"answer", "solution", "bank_id", "template", "check"}


class Question(BaseModel):
    qid: str                                  # khóa nội bộ: q1, q2...
    number: str                               # nhãn hiển thị: "Câu 3", "Bài IV.2b"
    section: str = ""
    format: Format
    statement: str
    context: str | None = None                # phần đề chung của một bài nhiều ý
    group: str | None = None
    options: list[str] | None = None          # trắc nghiệm: nội dung A–D (không kèm chữ cái)
    claims: list[str] | None = None           # đúng/sai: các ý a, b, c, d
    points: float
    topic: str
    difficulty: int
    source: str
    origin: Literal["bank", "variant"]
    auto: bool                                # chấm tự động được; False = học sinh tự chấm theo lời giải
    hint: str | None = None                   # cách nhập đáp án, ví dụ "(x; y)"
    figure_svg: str | None = None             # hình/biểu đồ của đề (bài nhiều ý: hình chung của cả bài)
    # --- riêng của server ---
    answer: Any = None                        # str | {"letter","value"} | list[bool] | None
    check: Literal["set", "ordered"] = "set"  # ordered: số phải đúng thứ tự, vd nghiệm (x; y)
    solution: list[str] = Field(default_factory=list)
    bank_id: str | None = None
    template: str | None = None

    def public(self) -> dict:
        return self.model_dump(exclude=PRIVATE)


class Exam(BaseModel):
    id: str
    title: str
    minutes: int
    blueprint: str
    seed: int
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    questions: list[Question]
    warnings: list[str] = Field(default_factory=list)

    @property
    def total_points(self) -> float:
        return round(sum(q.points for q in self.questions), 2)

    def public(self) -> dict:
        return {
            "id": self.id, "title": self.title, "minutes": self.minutes, "blueprint": self.blueprint,
            "seed": self.seed, "created_at": self.created_at, "total_points": self.total_points,
            "warnings": self.warnings, "questions": [q.public() for q in self.questions],
        }
