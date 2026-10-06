"""OCR công thức cho trang scan hoặc công thức vỡ.

Dùng khi `extract.text` báo `likely_scanned` hoặc `quality.assess` trả về
NEEDS_OCR. Đây là bước TỐN TIỀN — chỉ chạy trên phần thực sự cần, không chạy
đại trà.

Mathpix cho chất lượng LaTeX tốt nhất với công thức in. Với trang hỗn hợp
chữ-hình, một VLM thường cho kết quả tổng thể tốt hơn.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

MATHPIX_URL = "https://api.mathpix.com/v3/text"


def page_to_image(pdf_path: Path, page_no: int, dpi: int = 200) -> bytes:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        return pdf.pages[page_no].to_image(resolution=dpi).original.tobytes()


def mathpix_ocr(image_bytes: bytes) -> str:
    """Trả về Markdown có công thức LaTeX. Cần MATHPIX_APP_ID/KEY."""
    import httpx

    app_id, app_key = os.environ.get("MATHPIX_APP_ID"), os.environ.get("MATHPIX_APP_KEY")
    if not (app_id and app_key):
        raise RuntimeError("Thiếu MATHPIX_APP_ID / MATHPIX_APP_KEY trong .env")

    b64 = base64.b64encode(image_bytes).decode()
    r = httpx.post(
        MATHPIX_URL,
        headers={"app_id": app_id, "app_key": app_key},
        json={
            "src": f"data:image/png;base64,{b64}",
            "formats": ["text"],
            "math_inline_delimiters": ["$", "$"],
            "rm_spaces": True,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("text", "")
