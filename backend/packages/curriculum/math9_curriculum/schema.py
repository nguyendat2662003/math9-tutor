"""Schema bản đồ chương trình Toán 9.

Đây KHÔNG phải dữ liệu cho vector search. Nó được nạp trực tiếp vào prompt
theo `topic` mà Router xác định, và được code đối chiếu ở khâu hậu kiểm.
Tra cứu chính xác, không xác suất.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Mode(StrEnum):
    BASIC = "basic"        # đúng theo SGK, không hơn
    EXAM10 = "exam10"      # SGK + kỹ thuật thường gặp trong đề thi vào 10
    ADVANCED = "advanced"  # thêm phương tích, Ptolemy, BĐT nâng cao


class Tool(BaseModel):
    """Một định lý, công thức hoặc kỹ thuật được phép dùng."""

    id: str
    statement: str
    modes: list[Mode]
    aliases: list[str] = Field(default_factory=list)

    def allowed_in(self, mode: Mode) -> bool:
        return mode in self.modes


class Topic(BaseModel):
    id: str                       # "GEO-9" — mã theo số chương sách KNTT
    name: str
    prerequisites: list[str] = Field(default_factory=list)
    allowed_tools: list[Tool] = Field(default_factory=list)
    forbidden_keywords: list[str] = Field(default_factory=list)
    notation: dict[str, str] = Field(default_factory=dict)
    presentation_template: str | None = None
    goal_types: list[str] = Field(default_factory=list)

    def toolkit(self, mode: Mode) -> list[Tool]:
        return [t for t in self.allowed_tools if t.allowed_in(mode)]

    def prompt_block(self, mode: Mode) -> str:
        """Khối văn bản nạp vào prompt của Solver."""
        lines = [f"Chuyên đề: {self.id} — {self.name}", "", "Được phép dùng:"]
        lines += [f"- {t.statement}" for t in self.toolkit(mode)]
        if self.forbidden_keywords:
            lines += ["", "Tuyệt đối KHÔNG dùng: " + ", ".join(self.forbidden_keywords)]
        if self.presentation_template:
            lines += ["", "Mẫu trình bày:", self.presentation_template.strip()]
        return "\n".join(lines)


class CurriculumMap(BaseModel):
    topics: dict[str, Topic]

    def get(self, topic_id: str) -> Topic:
        if topic_id not in self.topics:
            raise KeyError(f"Không có chuyên đề '{topic_id}' trong bản đồ chương trình")
        return self.topics[topic_id]

    def label_catalog(self) -> str:
        """Danh mục nhãn cho prompt của Router — khoảng 600 token, không phải cả SGK."""
        return "\n".join(f"{t.id} {t.name}" for t in self.topics.values())

    def all_goal_types(self) -> list[str]:
        return sorted({g for t in self.topics.values() for g in t.goal_types})
