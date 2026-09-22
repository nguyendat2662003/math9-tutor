"""Schema sổ tay phương pháp.

Sổ tay tổ chức theo MỤC TIÊU CHỨNG MINH (goal_type), không theo dạng bài. Đây
là khác biệt cốt lõi so với các tài liệu tra cứu có sẵn: tài liệu gốc tổ chức
để người tra cứu, sổ tay này tổ chức để máy truy xuất theo goal_type.

Mỗi hướng giải mang hai trường mà không tài liệu nào có sẵn — `when_not` (khi
nào KHÔNG dùng) và `pitfalls` (bẫy) — vì lời giải và tài liệu tra cứu không ghi
lại những ngả cụt và quyết định đã loại bỏ. Đó là phần giáo viên phải bổ sung.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ReviewStatus(StrEnum):
    DRAFT = "draft"              # LLM sinh, chưa ai soát
    NEEDS_TEACHER = "needs_teacher"  # cần giáo viên bổ sung when_not / pitfalls
    REVIEWED = "reviewed"        # giáo viên đã soát và duyệt


class Approach(BaseModel):
    """Một hướng giải cho một mục tiêu."""

    title: str                                  # "Tổng hai góc đối bằng 180 độ"
    tools: list[str] = Field(default_factory=list)   # id công cụ trong allowed_tools
    when_to_use: str = ""                       # dấu hiệu nhận biết nên dùng
    when_not: str = ""                          # GIÁO VIÊN ĐIỀN — tài liệu gốc không có
    steps_outline: list[str] = Field(default_factory=list)
    pitfalls: list[str] = Field(default_factory=list)  # GIÁO VIÊN ĐIỀN
    example_ids: list[str] = Field(default_factory=list)  # bài minh họa từ kho đề
    source_refs: list[str] = Field(default_factory=list)  # trang/mục tài liệu gốc


class MethodDoc(BaseModel):
    """Sổ tay cho một goal_type."""

    goal_type: str
    title_vi: str
    topics: list[str] = Field(default_factory=list)
    modes: list[str] = Field(default_factory=lambda: ["basic", "exam10"])
    approaches: list[Approach] = Field(default_factory=list)
    status: ReviewStatus = ReviewStatus.DRAFT
    provenance: str | None = None               # nguồn tài liệu đã rút ra

    def coverage_gaps(self) -> list[str]:
        """Liệt kê chỗ giáo viên cần bổ sung. Dùng để tạo checklist soát."""
        gaps: list[str] = []
        if not self.approaches:
            return ["Chưa có hướng giải nào"]
        for a in self.approaches:
            if not a.when_not.strip():
                gaps.append(f"'{a.title}': thiếu 'khi nào KHÔNG dùng'")
            if not a.pitfalls:
                gaps.append(f"'{a.title}': thiếu 'bẫy thường gặp'")
            if not a.example_ids:
                gaps.append(f"'{a.title}': chưa gắn bài minh họa nào")
        return gaps

    def to_markdown(self) -> str:
        """Xuất ra định dạng data/methods/*.md mà retrieval đọc được."""
        fm = [
            "---",
            f"goal_type: {self.goal_type}",
            f"title_vi: {self.title_vi}",
            f"topics: [{', '.join(self.topics)}]",
            f"modes: [{', '.join(self.modes)}]",
            f"status: {self.status}",
        ]
        if self.provenance:
            fm.append(f"provenance: {self.provenance}")
        fm.append("---\n")

        body = [f"# {self.title_vi}\n"]
        for i, a in enumerate(self.approaches, 1):
            body.append(f"## Hướng {i} — {a.title}")
            if a.when_to_use:
                body.append(f"**Khi nào dùng:** {a.when_to_use}")
            if a.when_not:
                body.append(f"**Khi nào KHÔNG dùng:** {a.when_not}")
            elif self.status != ReviewStatus.REVIEWED:
                body.append("**Khi nào KHÔNG dùng:** _(giáo viên bổ sung)_")
            if a.steps_outline:
                body.append("**Các bước:**")
                body += [f"{j}. {s}" for j, s in enumerate(a.steps_outline, 1)]
            if a.pitfalls:
                body.append("**Bẫy thường gặp:**")
                body += [f"- {p}" for p in a.pitfalls]
            elif self.status != ReviewStatus.REVIEWED:
                body.append("**Bẫy thường gặp:** _(giáo viên bổ sung)_")
            if a.tools:
                body.append(f"_Công cụ: {', '.join(a.tools)}_")
            if a.source_refs:
                body.append(f"_Nguồn: {', '.join(a.source_refs)}_")
            body.append("")
        return "\n".join(fm + body)
