"""Hỏi đáp sau khi giải: học sinh hỏi thêm về bài vừa giải, trợ lý trả lời thẳng dựa trên
đúng lời giải đó (các bước, căn cứ, kết quả kiểm chứng) và chương trình Toán 9.

Câu trả lời hỏi đáp KHÔNG qua Verifier như lời giải chính — giao diện luôn ghi rõ điều đó.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from jinja2 import Template

from . import tracing
from .llm.client import LLMClient

PROMPT = Path(__file__).resolve().parents[3] / "prompts" / "tutor.md"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
MAX_HISTORY = 12                 # số lượt hỏi-đáp cũ gửi kèm (giữ ngữ cảnh mà không phình prompt)
_template: Template | None = None


def chapter_of(topic: str | None) -> str | None:
    """'GEO-9' -> 'Chương IX' (mã chuyên đề đặt theo đúng số chương sách KNTT)."""
    m = re.search(r"-(\d+)$", topic or "")
    return f"Chương {ROMAN.get(int(m.group(1)), m.group(1))}" if m else None


def system_prompt(state: dict) -> str:
    """Ngữ cảnh cho trợ lý: bài đã giải (dạng ProblemState công khai) + công cụ được dùng."""
    global _template
    if _template is None:
        _template = Template(PROMPT.read_text(encoding="utf-8"), trim_blocks=True, lstrip_blocks=True)
    from math9_curriculum.loader import curriculum
    from math9_curriculum.schema import Mode

    cm = curriculum()
    topic_id = state.get("topic")
    mode = state.get("mode") or "exam10"
    topic = cm.topics.get(topic_id) if topic_id else None
    chap = chapter_of(topic_id)
    topic_line = f"{topic_id} · {chap} — {topic.name}" if topic and chap else (topic_id or "chưa xác định")
    # Toàn bộ công cụ của chương trình (~112 dòng, vài nghìn token), MỖI DÒNG GHI SẴN CHƯƠNG CỦA NÓ.
    # Chỉ đưa chương của bài thì model gán nhầm chương của bài cho định lí (bài tiếp tuyến ở Chương V
    # nhưng "tứ giác nội tiếp" là Chương IX) — dẫn chứng sai còn tệ hơn không dẫn.
    tools: list[str] = []
    for tid, t in cm.topics.items():
        tools += [f"[{chapter_of(tid)}] {x.statement}" for x in t.toolkit(Mode(mode))]
    if topic and topic.forbidden_keywords:
        tools.append("KHÔNG dùng (ngoài chương trình): " + ", ".join(topic.forbidden_keywords))
    v = state.get("verification") or {}
    verification = {"high": "đã kiểm chứng đầy đủ", "partial": "kiểm chứng một phần",
                    "low": "chưa kiểm chứng được"}.get(state.get("confidence") or "", "không rõ")
    if v.get("algebra_ok") is True:
        verification += " (SymPy giải lại khớp đáp án)"
    if v.get("geometry_ok") is True:
        verification += " (hình dựng lại đúng quan hệ trên nhiều cấu hình)"
    return _template.render(
        mode_note={"basic": "(mức cơ bản SGK)", "exam10": "(mức ôn thi vào 10)", "advanced": "(mức nâng cao)"}.get(mode, ""),
        low_confidence=state.get("confidence") == "low",
        topic_line=topic_line,
        statement=state.get("latex") or state.get("raw_input") or "",
        subproblems=state.get("subproblems") or [],
        verification=verification,
        tools=tools,
    )


def answer_stream(llm: LLMClient, model: str, state: dict, history: list[dict], question: str,
                  usage: dict | None = None) -> Iterator[str]:
    """Trả lời từng đoạn. history: [{"role": "user"|"assistant", "content": ...}] theo thứ tự thời gian."""
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-MAX_HISTORY:]]
    messages.append({"role": "user", "content": question})
    usage = usage if usage is not None else {}
    parts: list[str] = []
    with tracing.observe("hoi-dap", kind="generation", model=model, input=messages,
                         metadata={"topic": state.get("topic")}) as gen:
        for piece in llm.stream(system_prompt(state), messages, model=model, max_tokens=6000, usage=usage):
            parts.append(piece)
            yield piece
        gen.update(output="".join(parts), model=usage.get("model") or model,
                   usage_details={"input": usage.get("input", 0), "output": usage.get("output", 0)})
