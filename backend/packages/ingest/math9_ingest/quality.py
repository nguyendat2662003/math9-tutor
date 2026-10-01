"""Chấm điểm chất lượng bản trích xuất và định tuyến vào hàng đợi soát.

Nguyên tắc: KHÔNG tự động tin bản trích xuất. Toán trong PDF vỡ vụn thường
xuyên, và một đề bài sai một dấu là cả mục eval thành vô nghĩa. Pipeline chỉ
tự động chấp nhận những bản sạch rõ ràng; phần còn lại xếp hàng cho giáo viên.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from .segment import Problem


class Verdict(StrEnum):
    AUTO_ACCEPT = "auto_accept"    # sạch, vào thẳng kho
    NEEDS_REVIEW = "needs_review"  # giáo viên soát
    NEEDS_OCR = "needs_ocr"        # công thức vỡ, cần Mathpix/VLM
    REJECT = "reject"              # rác, bỏ


@dataclass
class QualityReport:
    verdict: Verdict
    score: float
    flags: list[str]


# Dấu hiệu công thức bị vỡ khi trích từ PDF
RE_BROKEN_MATH = [
    (r"[a-zA-Z]\s{2,}[=<>]\s{2,}", "khoảng trắng bất thường quanh dấu so sánh"),
    (r"\b\d\s+\d\s+\d\b", "chữ số bị tách rời"),
    (r"[\u0000-\u0008\u000e-\u001f]", "ký tự điều khiển"),
    (r"(?:cid:\d+)", "font không nhúng (cid:)"),
    (r"[A-Za-z]{1}\s(?:[A-Za-z]{1}\s){4,}", "chữ cái rời rạc"),
]

RE_MATH_SIGNAL = re.compile(
    r"(?:[=<>+\-*/^]|\bsqrt\b|\bx\s*\^|\d+\s*[a-z]|phương trình|đường tròn|"
    r"tam giác|chứng minh|tính|rút gọn|giải)",
    re.IGNORECASE,
)

RE_TRUNCATED = re.compile(r"[,;:\-+=]\s*$|\b(?:và|của|với|thì|nên|suy ra)\s*$", re.I)


def assess(p: Problem) -> QualityReport:
    text = p.statement()
    flags: list[str] = []
    score = 1.0

    if len(text) < 40:
        return QualityReport(Verdict.REJECT, 0.0, ["quá ngắn"])
    if not RE_MATH_SIGNAL.search(text):
        return QualityReport(Verdict.REJECT, 0.0, ["không có dấu hiệu nội dung toán"])

    for pat, msg in RE_BROKEN_MATH:
        if re.search(pat, text):
            flags.append(msg)
            score -= 0.3

    if RE_TRUNCATED.search(text):
        flags.append("có vẻ bị cắt giữa chừng")
        score -= 0.25

    if p.likely_geometry:
        flags.append("bài hình — hình gốc là ảnh, phải dựng lại bằng Draftsman")
        score -= 0.1

    if len(p.parts) == 1 and len(text) > 400:
        flags.append("dài nhưng không tách được ý — kiểm tra lại bộ tách")
        score -= 0.15

    # Tỉ lệ ký tự không phải chữ/số quá cao => trích hỏng
    junk = sum(1 for c in text if not (c.isalnum() or c.isspace() or c in ".,;:()[]{}=<>+-*/^%'\"√°"))
    if junk / max(len(text), 1) > 0.06:
        flags.append("nhiều ký tự lạ — nghi lỗi font")
        score -= 0.3

    score = max(0.0, score)
    if score >= 0.85 and not flags:
        v = Verdict.AUTO_ACCEPT
    elif any("font" in f or "vỡ" in f or "rời" in f for f in flags):
        v = Verdict.NEEDS_OCR
    elif score < 0.3:
        v = Verdict.REJECT
    else:
        v = Verdict.NEEDS_REVIEW
    return QualityReport(v, round(score, 2), flags)
