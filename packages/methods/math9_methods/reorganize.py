"""Pipeline tái tổ chức: tài liệu theo dạng bài -> khung sổ tay theo goal_type.

    trích text -> gán mục vào goal_type (section_map) -> LLM soạn nháp mỗi hướng
    -> đánh dấu chỗ giáo viên phải bổ sung -> xuất data/methods/*.md + checklist soát

Quan trọng: LLM CHỈ soạn nháp phần rút được từ tài liệu (các hướng, dấu hiệu
nhận biết, các bước). Nó KHÔNG bịa 'khi nào không dùng' và 'bẫy' — hai trường
đó để trống cho giáo viên, vì tài liệu gốc không chứa thông tin đó và bịa ra
thì nguy hiểm hơn để trống.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from math9_core.enums import GOAL_TYPE_VI

from .schema import Approach, MethodDoc, ReviewStatus
from .section_map import SourceSection, invert

log = logging.getLogger(__name__)


# Prompt cho LLM soạn nháp một sổ tay. Ràng buộc rõ: chỉ rút, không bịa.
DRAFT_PROMPT = """Bạn đang biên soạn sổ tay phương pháp giải Toán 9 cho mục tiêu:
"{title_vi}" (mã: {goal_type}).

Dưới đây là trích đoạn từ tài liệu tra cứu, thuộc các mục liên quan tới mục tiêu này:

{source_excerpts}

Nhiệm vụ: liệt kê các HƯỚNG giải khác nhau cho mục tiêu này mà trích đoạn đề cập.
Với mỗi hướng, rút ra:
- title: tên ngắn gọn của hướng
- when_to_use: dấu hiệu nhận biết nên dùng hướng này (nếu tài liệu có nêu)
- steps_outline: các bước chính (nếu tài liệu có)
- tools: tên định lý/công thức mà hướng này dùng

TUYỆT ĐỐI KHÔNG bịa "khi nào không dùng" hay "bẫy thường gặp" — nếu tài liệu
không nêu rõ, để trống. Chỉ rút những gì thực sự có trong trích đoạn.

Trả JSON:
{{"approaches": [{{"title": "...", "when_to_use": "...", "steps_outline": ["..."], "tools": ["..."]}}]}}
"""


@dataclass
class ReorganizeResult:
    docs: list[MethodDoc]
    review_checklist: list[dict]
    uncovered_goal_types: list[str]


class Reorganizer:
    """Biến một tài liệu tra cứu thành bộ khung sổ tay."""

    def __init__(self, llm=None, provenance: str = ""):
        self.llm = llm
        self.provenance = provenance

    def run(
        self,
        sections: list[SourceSection],
        section_texts: dict[str, str],
        goal_types: list[str] | None = None,
    ) -> ReorganizeResult:
        """
        sections: bản đồ mục -> goal_type (từ section_map)
        section_texts: {ref -> text đã trích}, ví dụ {"Dạng 29": "..."}
        """
        inv = invert(sections)
        targets = goal_types or list(inv)
        docs, checklist = [], []

        for g in targets:
            secs = inv.get(g, [])
            if not secs:
                continue
            excerpts = self._gather_excerpts(secs, section_texts)
            approaches = self._draft_approaches(g, excerpts)

            doc = MethodDoc(
                goal_type=g,
                title_vi=GOAL_TYPE_VI.get(g, g),
                topics=self._infer_topics(secs),
                approaches=approaches,
                status=ReviewStatus.NEEDS_TEACHER,
                provenance=self.provenance,
            )
            for a in approaches:
                a.source_refs = [s.ref for s in secs]
            docs.append(doc)
            checklist.append({
                "goal_type": g,
                "title": doc.title_vi,
                "n_approaches": len(approaches),
                "source_sections": [f"{s.ref} ({s.title})" for s in secs],
                "gaps": doc.coverage_gaps(),
            })

        all_gt = goal_types or list(GOAL_TYPE_VI)
        uncovered = sorted(set(all_gt) - set(inv))
        return ReorganizeResult(docs, checklist, uncovered)

    def _gather_excerpts(self, secs: list[SourceSection], texts: dict[str, str]) -> str:
        parts = []
        for s in secs:
            body = texts.get(s.ref, "").strip()
            if body:
                parts.append(f"[{s.ref} — {s.title}]\n{body}")
            else:
                parts.append(f"[{s.ref} — {s.title}] (chưa có text trích)")
        return "\n\n".join(parts)

    def _draft_approaches(self, goal_type: str, excerpts: str) -> list[Approach]:
        if not self.llm:
            # Không có LLM: tạo khung rỗng để giáo viên điền tay hoàn toàn
            return [Approach(title="(chưa soạn — cần LLM hoặc giáo viên)")]

        prompt = DRAFT_PROMPT.format(
            title_vi=GOAL_TYPE_VI.get(goal_type, goal_type),
            goal_type=goal_type,
            source_excerpts=excerpts[:8000],
        )
        try:
            resp = self.llm.complete(
                system="Bạn là giáo viên Toán THCS giàu kinh nghiệm.",
                user=prompt, model="api:strong", max_tokens=2000,
            )
            data = resp.json()
            return [Approach(**a) for a in data.get("approaches", [])]
        except Exception as e:
            log.error("Soạn nháp %s thất bại: %s", goal_type, e)
            return [Approach(title=f"(soạn nháp lỗi: {e})")]

    def _infer_topics(self, secs: list[SourceSection]) -> list[str]:
        """Suy chuyên đề từ trang: ánh xạ thô, giáo viên chỉnh lại khi soát."""
        topics = set()
        for s in secs:
            p = s.page or 0
            if "căn" in s.title.lower() or p < 6:
                topics.add("ALG-3")
            elif "vi-ète" in s.title.lower() or "bậc hai" in s.title.lower():
                topics.add("ALG-6")
            elif "đường tròn" in s.title.lower() or "góc" in s.title.lower():
                topics.add("GEO-9")
            elif "tam giác vuông" in s.title.lower() or "lượng giác" in s.title.lower():
                topics.add("GEO-4")
        return sorted(topics)


def write_methods(result: ReorganizeResult, out_dir: Path) -> None:
    """Xuất ra data/methods/*.md và checklist soát."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for doc in result.docs:
        (out_dir / f"{doc.goal_type}.md").write_text(doc.to_markdown(), encoding="utf-8")

    checklist_path = out_dir / "_review_checklist.json"
    checklist_path.write_text(
        json.dumps({
            "documents": result.review_checklist,
            "uncovered_goal_types": result.uncovered_goal_types,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("Đã xuất %d sổ tay + checklist vào %s", len(result.docs), out_dir)
