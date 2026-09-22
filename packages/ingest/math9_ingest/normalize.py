"""Chuẩn hóa văn bản đề toán tiếng Việt.

Đây là nơi dữ liệu crawl hay hỏng nhất. Ba cạm bẫy chính:

1. Dấu phẩy thập phân: tiếng Việt viết 2,5 nhưng SymPy/LaTeX cần 2.5.
   Nhưng 'x1, x2' cũng có dấu phẩy — không được đổi bừa.
2. Dấu tiếng Việt: NFC vs NFD, và các bộ gõ cũ dùng ký tự tổ hợp khác nhau.
3. Rác trang: watermark, header/footer, 'Trang 1/2', tên website.
"""

from __future__ import annotations

import re
import unicodedata

# Rác thường gặp trong PDF/DOC đề thi
NOISE_PATTERNS = [
    r"Trang\s*\d+\s*/\s*\d+",
    r"^\s*-+\s*HẾT\s*-+\s*$",
    r"(?i)\b(?:https?://)?(?:www\.)?[\w-]+\.(?:com|vn|net|org)(?:/\S*)?",
    r"(?i)^\s*(?:sở|phòng)\s+giáo\s+dục.{0,60}$",
    r"(?i)^\s*đề\s+(?:chính\s+thức|dự\s+bị)\s*$",
    r"(?i)^\s*\(?\s*đề\s+thi\s+gồm\s+\d+\s+trang\s*\)?\s*$",
    r"(?i)họ\s+và\s+tên\s+thí\s+sinh.{0,80}",
    r"(?i)số\s+báo\s+danh.{0,40}",
    r"(?i)cán\s+bộ\s+coi\s+thi.{0,60}",
]

# Ký hiệu toán hay bị lỗi font khi trích từ PDF
GLYPH_FIXES = {
    "\u2212": "-",   # minus dài
    "\u2013": "-",
    "\u2014": "-",
    "\u00d7": "*",
    "\u00f7": "/",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u221a": "sqrt",
    "\u0394": "Delta",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u2220": "goc",
    "\u22a5": "vuonggoc",
    "\u2225": "songsong",
    "\u2248": "~=",
    "\u00b0": " do",
    "\ufeff": "",
    "\u00a0": " ",
}


def to_nfc(s: str) -> str:
    """Bộ gõ cũ sinh ký tự tổ hợp (NFD); chuẩn hóa về NFC để so khớp được."""
    return unicodedata.normalize("NFC", s)


def strip_noise(s: str) -> str:
    for pat in NOISE_PATTERNS:
        s = re.sub(pat, "", s, flags=re.MULTILINE)
    return s


def fix_glyphs(s: str) -> str:
    for bad, good in GLYPH_FIXES.items():
        s = s.replace(bad, good)
    return s


def fix_decimal_comma(s: str) -> str:
    """Đổi 2,5 -> 2.5 nhưng KHÔNG đụng tới 'x1, x2' hay '(2,0 điểm)'.

    Quy tắc: chỉ đổi khi cả hai bên dấu phẩy là chữ số và không có khoảng trắng,
    và cụm đó không nằm ngay trước từ 'điểm'.
    """
    def repl(m: re.Match) -> str:
        after = s[m.end(): m.end() + 12].lower()
        if re.match(r"\s*(điểm|đ\b)", after):
            return m.group(0)
        return f"{m.group(1)}.{m.group(2)}"

    return re.sub(r"(?<![\w.])(\d+),(\d+)(?![\w,])", repl, s)


def collapse_whitespace(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return "\n".join(line.strip() for line in s.split("\n")).strip()


def dehyphenate(s: str) -> str:
    """Nối từ bị ngắt dòng bằng gạch nối trong PDF."""
    return re.sub(r"(\w)-\n(\w)", r"\1\2", s)


def normalize(s: str) -> str:
    for f in (to_nfc, fix_glyphs, dehyphenate, strip_noise,
              fix_decimal_comma, collapse_whitespace):
        s = f(s)
    return s
