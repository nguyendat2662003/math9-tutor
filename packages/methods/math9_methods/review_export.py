"""Xuất khung sổ tay cho giáo viên soát, và nhập bản đã soát ngược lại.

Giáo viên làm việc trên bản Markdown có sẵn phần LLM rút được, chỉ điền hai mục
để trống: 'khi nào KHÔNG dùng' và 'bẫy thường gặp', cộng với gắn bài minh họa.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schema import MethodDoc, ReviewStatus


def make_review_packet(docs: list[MethodDoc], out_dir: Path) -> Path:
    """Gộp toàn bộ sổ tay draft + checklist thành một gói cho giáo viên."""
    out_dir.mkdir(parents=True, exist_ok=True)
    index_lines = ["# Gói soát sổ tay phương pháp\n",
                   "Với mỗi file, điền hai mục để trống và gắn bài minh họa.\n",
                   "| Sổ tay | Số hướng | Chỗ cần bổ sung |",
                   "|---|---|---|"]
    for doc in sorted(docs, key=lambda d: d.goal_type):
        gaps = len(doc.coverage_gaps())
        index_lines.append(f"| `{doc.goal_type}.md` | {len(doc.approaches)} | {gaps} mục |")
        (out_dir / f"{doc.goal_type}.md").write_text(doc.to_markdown(), encoding="utf-8")

    idx = out_dir / "_index.md"
    idx.write_text("\n".join(index_lines), encoding="utf-8")
    return idx


def validate_reviewed(path: Path) -> tuple[bool, list[str]]:
    """Kiểm tra một sổ tay đã soát: hai mục bắt buộc đã điền chưa."""
    text = path.read_text(encoding="utf-8")
    issues = []
    if "_(giáo viên bổ sung)_" in text:
        issues.append("còn chỗ '_(giáo viên bổ sung)_' chưa điền")
    if "status: reviewed" not in text:
        issues.append("chưa đổi status thành 'reviewed'")
    if "(chưa soạn" in text or "soạn nháp lỗi" in text:
        issues.append("có hướng chưa soạn được")
    return (not issues, issues)


def gate_for_rag(methods_dir: Path) -> dict:
    """Chỉ cho sổ tay đã soát vào RAG. Draft chưa soát KHÔNG được dùng.

    Lý do: sổ tay draft thiếu 'khi nào không dùng' và 'bẫy' — nạp vào có thể
    đẩy Solver đi sai hướng, đúng cái sổ tay sinh ra để tránh.
    """
    ready, pending = [], []
    for f in sorted(methods_dir.glob("*.md")):
        if f.name.startswith("_"):
            continue
        ok, issues = validate_reviewed(f)
        (ready if ok else pending).append(f.stem)
    return {"ready_for_rag": ready, "pending_review": pending}
