"""Guardrail hai lớp: chặn kiến thức vượt cấp trong lời giải.

Lớp 1 — quét từ khóa cấm: nhanh, thô, bắt được các trường hợp lộ liễu.
Lớp 2 — đối chiếu căn cứ từng bước với `allowed_tools`: chậm hơn, chính xác hơn.

Guardrail chạy SAU khi Solver sinh lời giải. Vi phạm -> buộc giải lại với
thông báo cụ thể công cụ nào bị cấm.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .schema import Mode, Topic

#: Từ khóa vượt cấp áp dụng cho MỌI chuyên đề, bất kể chế độ nào dưới advanced.
GLOBAL_FORBIDDEN = [
    "đạo hàm", "tích phân", "giới hạn", "vectơ", "véc tơ", "vector",
    "số phức", "ma trận", "quy nạp", "logarit", "lượng giác hóa",
    "menelaus", "ceva", "ptolemy", "phương tích", "trục đẳng phương",
    "nghịch đảo", "hàng điểm điều hòa", "cực và đối cực", "định lý sin",
    "định lý cosin", "tọa độ hóa", "gắn hệ trục",
]

ADVANCED_ALLOWED = {"phương tích", "ptolemy", "định lý sin", "định lý cosin"}


@dataclass
class Violation:
    kind: str          # "forbidden_keyword" | "unlisted_tool" | "missing_justification"
    detail: str
    step_id: str | None = None


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    return re.sub(r"\s+", " ", s)


def check_keywords(text: str, topic: Topic, mode: Mode) -> list[Violation]:
    banned = set(GLOBAL_FORBIDDEN) | {_norm(k) for k in topic.forbidden_keywords}
    if mode == Mode.ADVANCED:
        banned -= ADVANCED_ALLOWED
    body = _norm(text)
    return [
        Violation("forbidden_keyword", f"Dùng kiến thức vượt cấp: '{k}'")
        for k in sorted(banned)
        if k in body
    ]


def check_justifications(
    steps: list[dict], topic: Topic, mode: Mode, strict: bool = False
) -> list[Violation]:
    """Đối chiếu căn cứ mỗi bước với danh sách công cụ được phép."""
    allowed = topic.toolkit(mode)
    vocab = {_norm(t.statement) for t in allowed}
    vocab |= {_norm(a) for t in allowed for a in t.aliases}
    out: list[Violation] = []

    for st in steps:
        j = st.get("justification") or ""
        sid = st.get("id")
        if not j.strip():
            out.append(Violation("missing_justification", "Bước không nêu căn cứ", sid))
            continue
        if strict and not any(v and v in _norm(j) for v in vocab):
            out.append(
                Violation("unlisted_tool", f"Căn cứ không thuộc chương trình: '{j}'", sid)
            )
    return out


def check(
    solution_text: str, steps: list[dict], topic: Topic, mode: Mode, strict: bool = False
) -> list[Violation]:
    return check_keywords(solution_text, topic, mode) + check_justifications(
        steps, topic, mode, strict
    )


def feedback_message(violations: list[Violation]) -> str:
    """Thông điệp gửi lại Solver để giải lại đúng phạm vi."""
    if not violations:
        return ""
    lines = ["Lời giải vi phạm phạm vi chương trình lớp 9. Vui lòng giải lại:"]
    lines += [f"- {v.detail}" for v in violations]
    lines.append("Chỉ dùng các công cụ đã liệt kê trong phần 'Được phép dùng'.")
    return "\n".join(lines)
