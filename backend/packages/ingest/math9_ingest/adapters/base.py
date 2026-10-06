"""Giao diện adapter cho từng nguồn.

Mỗi site có cấu trúc riêng: nơi liệt kê đề, cách đặt tên file, đáp án nằm cùng
file hay file riêng. Toàn bộ khác biệt đó gói vào adapter; phần còn lại của
pipeline không cần biết.

Khi có link nguồn mới, chỉ cần thêm một file trong thư mục này.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DocumentRef:
    """Một tài liệu cần tải: đề thi, đáp án, hoặc cả hai trong một file."""

    url: str
    title: str
    kind: str = "exam"                    # exam | answer_key | combined
    year: int | None = None
    province: str | None = None
    grade: int = 9
    meta: dict = field(default_factory=dict)

    def source_label(self) -> str:
        bits = [b for b in (self.province, str(self.year) if self.year else None) if b]
        return " ".join(bits) or self.title


class SourceAdapter(ABC):
    """Adapter cho một site cụ thể."""

    name: str = "unnamed"
    base_url: str = ""
    #: Đặt True chỉ khi đã xác nhận nguồn công khai, không tường phí, không SGK.
    verified_public: bool = False

    @abstractmethod
    def discover(self) -> list[DocumentRef]:
        """Duyệt trang danh sách, trả về các tài liệu cần tải."""

    def pair_answer_key(self, docs: list[DocumentRef]) -> list[tuple[DocumentRef, DocumentRef | None]]:
        """Ghép mỗi đề với đáp án tương ứng. Mặc định ghép theo (tỉnh, năm)."""
        exams = [d for d in docs if d.kind in ("exam", "combined")]
        keys = {(d.province, d.year): d for d in docs if d.kind == "answer_key"}
        return [(e, keys.get((e.province, e.year))) for e in exams]
