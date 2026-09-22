"""Trích văn bản từ PDF / DOCX / HTML.

Đây là nút thắt thật của pipeline, không phải khâu tải. Công thức toán trong
PDF thường vỡ vụn thành ký tự rời; tỉ lệ trích sạch thực tế khoảng 60-70%.
Phần còn lại phải qua OCR công thức (xem ocr.py) hoặc soát tay.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)


def from_pdf(path: Path) -> tuple[str, dict]:
    """Trả về (văn bản, thông tin chẩn đoán). Cần pdfplumber."""
    import pdfplumber

    pages, images, chars = [], 0, 0
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages.append(t)
            chars += len(t)
            images += len(page.images)
    text = "\n\n".join(pages)
    diag = {
        "n_pages": len(pages),
        "n_images": images,
        "chars_per_page": chars / max(len(pages), 1),
        # Ít chữ + nhiều ảnh = PDF scan, phải OCR toàn trang
        "likely_scanned": chars / max(len(pages), 1) < 200 and images > 0,
    }
    return text, diag


def from_docx(path: Path) -> tuple[str, dict]:
    """DOCX giữ công thức trong OMML — trích tốt hơn PDF nhiều. Ưu tiên nguồn DOCX."""
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    text = "\n".join(parts)
    omml = text.count("\u0000")  # chỗ giữ công thức OMML nếu có
    return text, {"n_paragraphs": len(doc.paragraphs), "omml_placeholders": omml}


def from_html(path: Path) -> tuple[str, dict]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # MathJax/KaTeX nhúng LaTeX trong annotation — lấy được là quý
    for ann in soup.select('annotation[encoding="application/x-tex"]'):
        ann.replace_with(f" ${ann.get_text()}$ ")

    text = soup.get_text("\n")
    return text, {"n_mathml": len(soup.select("math"))}


EXTRACTORS = {
    ".pdf": from_pdf,
    ".docx": from_docx,
    ".doc": from_docx,
    ".html": from_html,
    ".htm": from_html,
}


def extract(path: Path, content_type: str = "") -> tuple[str, dict]:
    suffix = path.suffix.lower()
    if not suffix and content_type:
        suffix = {"application/pdf": ".pdf", "text/html": ".html"}.get(content_type, "")
    fn = EXTRACTORS.get(suffix)
    if not fn:
        raise ValueError(f"Chưa hỗ trợ định dạng '{suffix}'")
    try:
        return fn(path)
    except Exception as e:
        log.error("Trích xuất hỏng %s: %s", path, e)
        return "", {"error": str(e)}
