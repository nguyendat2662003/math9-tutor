"""Kho tài liệu cho RAG. Hai collection TÁCH BIỆT, không trộn.

Vì sao tách: sổ tay phương pháp và bài giải mẫu phục vụ hai việc khác nhau.
Sổ tay trả lời 'nên đi hướng nào' (truy theo goal_type); bài mẫu trả lời 'trình
bày thế nào' (truy theo độ tương đồng). Trộn chung thì truy xuất trả về hổ lốn.

SGK KHÔNG nằm ở đây. Xem README gốc, mục 'Vì sao không đưa nguyên SGK vào RAG'.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import yaml


class Collection(StrEnum):
    METHODS = "methods"           # sổ tay phương pháp — truy theo goal_type
    WORKED = "worked_examples"    # bài giải mẫu — truy theo độ tương đồng
    CONCEPTS = "concepts"         # định nghĩa/kiến thức SGK — collection RIÊNG cho câu hỏi lý thuyết


@dataclass
class Doc:
    id: str
    collection: Collection
    body: str
    goal_type: str | None = None
    topics: list[str] = field(default_factory=list)
    modes: list[str] = field(default_factory=lambda: ["basic", "exam10", "advanced"])
    status: str = "reviewed"          # chỉ 'reviewed' mới được truy xuất
    meta: dict = field(default_factory=dict)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    try:
        _, fm, body = text.split("---", 2)
        return yaml.safe_load(fm) or {}, body.strip()
    except ValueError:
        return {}, text


def load_methods(path: Path, require_reviewed: bool = True) -> list[Doc]:
    """Nạp sổ tay. Mặc định CHỈ nạp bản đã soát (status: reviewed).

    Đây là cổng chặn RAG: sổ tay draft thiếu 'khi nào không dùng' và 'bẫy',
    nạp vào có thể đẩy Solver sai hướng.
    """
    docs, skipped = [], []
    for f in sorted(path.glob("*.md")):
        if f.name.startswith("_"):
            continue
        meta, body = _parse_frontmatter(f.read_text(encoding="utf-8"))
        status = meta.get("status", "draft")
        if require_reviewed and status != "reviewed":
            skipped.append(f.stem)
            continue
        docs.append(Doc(
            id=f.stem,
            collection=Collection.METHODS,
            body=body,
            goal_type=meta.get("goal_type"),
            topics=meta.get("topics", []),
            modes=meta.get("modes", ["basic", "exam10"]),
            status=status,
            meta={"provenance": meta.get("provenance")},
        ))
    if skipped:
        import logging
        logging.getLogger(__name__).warning(
            "Bỏ qua %d sổ tay chưa soát: %s", len(skipped), ", ".join(skipped))
    return docs


def _step_prose(steps: list[dict]) -> str:
    """Dựng văn xuôi từ các bước có cấu trúc, khi bài mẫu chưa có solution_prose.

    Mỗi bước là {claim, justification, ...} — ghép lại thành một câu có căn cứ
    trong ngoặc, đúng văn phong trình bày mà few-shot cần dạy Solver."""
    lines = []
    for s in steps:
        claim, why = s.get("claim", "").strip(), s.get("justification", "").strip()
        lines.append(f"{claim} ({why})." if why else f"{claim}.")
    return " ".join(lines)


def load_worked_examples(path: Path) -> list[Doc]:
    """Nạp bài giải mẫu: mỗi file `*.json` trong `path` là MỘT bài, theo định
    dạng chia từng bước ở `data/problems/QUY-CACH.md` (không phải JSONL một
    dòng một bài — bài mẫu để giáo viên đọc và sửa tay, một file riêng dễ soát
    hơn nhiều bài dồn trong một file).

    Một bản ghi Doc ứng với MỘT Ý (subproblem), vì mỗi ý mang goal_type riêng —
    đây là đơn vị mà RAG cần truy xuất, không phải cả bài. Chỉ nhận lời giải
    chi tiết (`solution_type: detailed`); hướng dẫn chấm (`answer_key`) bị loại
    vì viết cụt lủn, không nêu căn cứ — nạp vào sẽ dạy Solver bỏ qua căn cứ.
    """
    import json
    import logging

    docs, skipped = [], []
    for f in sorted(path.glob("*.json")):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            skipped.append(f"{f.name} (JSON lỗi: {e})")
            continue
        if r.get("solution_type") == "answer_key":
            skipped.append(f"{f.name} (hướng dẫn chấm, không dùng làm mẫu)")
            continue

        statement = r.get("statement", "")
        subs = r.get("subproblems") or [{
            "label": None, "topic": r.get("topic"), "goal_type": r.get("goal_type"),
            "difficulty": r.get("difficulty"), "approach_ref": r.get("approach_ref"),
            "solution_prose": r.get("solution_prose"), "steps": r.get("steps", []),
            "answer": r.get("answer"),
        }]

        for sub in subs:
            body_parts = [statement]
            if sub.get("label"):
                body_parts.append(f"Ý {sub['label']}.")
            body_parts.append(sub.get("solution_prose") or _step_prose(sub.get("steps", [])))
            if sub.get("answer"):
                body_parts.append(f"Đáp số: {sub['answer']}.")

            doc_id = f"{r['id']}-{sub['label']}" if sub.get("label") else r["id"]
            docs.append(Doc(
                id=doc_id,
                collection=Collection.WORKED,
                body="\n\n".join(p for p in body_parts if p),
                goal_type=sub.get("goal_type"),
                topics=[sub["topic"]] if sub.get("topic") else [],
                modes=[r.get("mode", "exam10")],
                meta={
                    "source": r.get("source"),
                    "approach_ref": sub.get("approach_ref"),
                    "difficulty": sub.get("difficulty"),
                    "steps": sub.get("steps"),          # giữ dạng có cấu trúc để dựng few-shot JSON nếu cần
                    "construction": r.get("construction"),  # kịch bản dựng hình dùng chung cho cả bài, nếu có
                },
            ))

    if skipped:
        logging.getLogger(__name__).warning(
            "Bỏ qua %d file bài mẫu: %s", len(skipped), "; ".join(skipped))
    return docs
