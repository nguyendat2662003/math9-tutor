"""Điểm vào RAG mà Solver gọi. Gói cả ba collection sau một giao diện.

Solver không cần biết BM25, vector hay RRF. Nó hỏi: 'cho tôi chiến lược và bài
mẫu cho goal_type này' -> service trả về khối văn bản nạp thẳng vào prompt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .embedder import Embedder, HashingEmbedder
from .retriever import Hit, Retriever
from .store import Collection, load_methods, load_worked_examples

log = logging.getLogger(__name__)

DATA = Path(__file__).resolve().parents[3] / "data"


@dataclass
class RetrievedContext:
    """Kết quả truy xuất, sẵn sàng nạp vào prompt Solver."""

    method_notes: str = ""
    worked_examples: str = ""
    method_hits: list[Hit] = field(default_factory=list)
    example_hits: list[Hit] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.method_notes or self.worked_examples)


class RagService:
    def __init__(
        self,
        methods_dir: Path = DATA / "methods",
        problems_dir: Path = DATA / "problems",
        embedder: Embedder | None = None,
        require_reviewed: bool = True,
    ):
        emb = embedder or HashingEmbedder()
        methods = load_methods(methods_dir, require_reviewed) if methods_dir.exists() else []
        worked = load_worked_examples(problems_dir, require_reviewed) if problems_dir.exists() else []

        self.methods = Retriever(methods, emb) if methods else None
        self.worked = Retriever(worked, emb) if worked else None
        log.info("RAG: %d sổ tay (reviewed), %d bài mẫu", len(methods), len(worked))

    def retrieve(
        self, query: str, goal_type: str | None, mode: str = "exam10",
        n_methods: int = 2, n_examples: int = 2,
    ) -> RetrievedContext:
        ctx = RetrievedContext()

        if self.methods:
            ctx.method_hits = self.methods.search_methods(query, goal_type, mode, n_methods)
            ctx.method_notes = "\n\n---\n\n".join(h.doc.body for h in ctx.method_hits)

        if self.worked:
            ctx.example_hits = self.worked.search_similar(query, n_examples)
            ctx.worked_examples = "\n\n---\n\n".join(h.doc.body for h in ctx.example_hits)

        return ctx
