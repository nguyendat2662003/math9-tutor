"""Tách tài liệu tra cứu thành từng mục theo mục lục.

Tài liệu kiểu 'Cẩm nang' đánh số Dạng 1..31 + Phụ lục. Ta cắt theo các mốc đó
để lấy text của từng mục, khớp với ref trong section_map.

Lưu ý: công thức trong PDF loại này gần như luôn vỡ (mục lục đã cho thấy
'2 ax bx c 0' thay vì 'ax²+bx+c=0'). Bước này chỉ lo CẮT ĐÚNG MỤC; việc phục
hồi công thức là của OCR (Mathpix) ở tầng ingest, chạy trước bước này.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# "Dạng 29.", "Dạng 29:", "+ Dạng 29"
RE_DANG = re.compile(r"(?:^|\n)\s*\+?\s*Dạng\s+(\d{1,2})\s*[.:]", re.IGNORECASE)
# Phụ lục đánh số "10. Chứng minh..."
RE_PHULUC = re.compile(r"(?:^|\n)\s*(\d{1,2})\.\s+(?=[A-ZĐÀ-Ỹ])")


@dataclass
class SourceChunk:
    ref: str
    title_line: str
    body: str


def split_dang(text: str) -> dict[str, str]:
    """Trả về {"Dạng 29": text, ...}."""
    out: dict[str, str] = {}
    marks = list(RE_DANG.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        num = m.group(1)
        out[f"Dạng {num}"] = text[m.start(): end].strip()
    return out


def split_phuluc(text: str, offset: int = 0) -> dict[str, str]:
    """Phụ lục lớp 8: {"PL mục 10": text, ...}. offset để tách khỏi phần chính."""
    out: dict[str, str] = {}
    marks = list(RE_PHULUC.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[f"PL mục {m.group(1)}"] = text[m.start(): end].strip()
    return out


def split_source(full_text: str, phuluc_marker: str = "PHỤ LỤC") -> dict[str, str]:
    """Cắt cả tài liệu. Tách phần chính (Dạng) và phụ lục (PL mục)."""
    idx = full_text.upper().find(phuluc_marker)
    main = full_text[:idx] if idx > 0 else full_text
    appendix = full_text[idx:] if idx > 0 else ""
    chunks = split_dang(main)
    chunks.update(split_phuluc(appendix))
    return chunks


def report_coverage(chunks: dict[str, str], expected_refs: list[str]) -> dict:
    """Đối chiếu mục cắt được với section_map: thiếu mục nào, mục nào rỗng."""
    found = set(chunks)
    expected = set(expected_refs)
    empty = [r for r in expected & found if len(chunks.get(r, "")) < 50]
    return {
        "matched": sorted(expected & found),
        "missing_from_source": sorted(expected - found),
        "empty_or_too_short": sorted(empty),
        "extra_in_source": sorted(found - expected),
    }
