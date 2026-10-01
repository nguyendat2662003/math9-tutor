"""Hybrid retriever: goal_type filter + BM25 + vector, gộp bằng RRF.

Nguyên tắc cốt lõi cho dự án này: với sổ tay, TRUY THEO goal_type LÀ CHÍNH.
Bạn không tìm 'bài giống', bạn tìm 'chiến lược phù hợp'. Vector và BM25 chỉ để
xếp hạng trong số các sổ tay cùng goal_type, hoặc để cứu vãn khi Router phân
loại sai.

Với bài giải mẫu thì ngược lại: độ tương đồng là chính (để bắt chước văn phong),
goal_type là phụ.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .embedder import Embedder, HashingEmbedder
from .store import Collection, Doc


def _tokenize(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower(), flags=re.UNICODE)


@dataclass
class Hit:
    doc: Doc
    score: float
    how: str          # "goal_type" | "bm25" | "vector" | "hybrid"


class BM25:
    def __init__(self, docs: list[Doc], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tf = [Counter(_tokenize(d.body)) for d in docs]
        self.df: Counter[str] = Counter()
        for t in self.tf:
            self.df.update(t.keys())
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.len) / len(docs)) if docs else 0.0
        self.n = len(docs)

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        q = _tokenize(query)
        scores = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for term in q:
                f = tf.get(term, 0)
                if not f:
                    continue
                idf = math.log(1 + (self.n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                denom = f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1))
                s += idf * f * (self.k1 + 1) / denom
            if s > 0:
                scores.append((i, s))
        return sorted(scores, key=lambda t: -t[1])[:k]


class VectorIndex:
    def __init__(self, docs: list[Doc], embedder: Embedder):
        self.docs = docs
        self.embedder = embedder
        self.vecs = embedder.encode([d.body for d in docs]) if docs else []

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        if not self.vecs:
            return []
        q = self.embedder.encode_one(query)
        sims = [(i, sum(a * b for a, b in zip(q, v))) for i, v in enumerate(self.vecs)]
        return sorted(sims, key=lambda t: -t[1])[:k]


def _rrf(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion — gộp nhiều bảng xếp hạng không cần chuẩn hóa điểm."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return fused


class Retriever:
    """Một retriever cho một collection."""

    def __init__(self, docs: list[Doc], embedder: Embedder | None = None):
        self.docs = docs
        self.bm25 = BM25(docs)
        self.vec = VectorIndex(docs, embedder or HashingEmbedder())

    def search_methods(
        self, query: str, goal_type: str | None, mode: str, k: int = 3
    ) -> list[Hit]:
        """Cho sổ tay: goal_type là chính, hybrid là phụ."""
        # 1. Ưu tiên tuyệt đối: sổ tay đúng goal_type và đúng mode
        exact = [
            i for i, d in enumerate(self.docs)
            if d.goal_type == goal_type and (mode in d.modes)
        ]
        if exact:
            return [Hit(self.docs[i], 1.0, "goal_type") for i in exact[:k]]

        # 2. Router có thể sai -> hybrid cứu vãn
        return self._hybrid(query, k)

    def search_similar(self, query: str, k: int = 3) -> list[Hit]:
        """Cho bài giải mẫu: độ tương đồng là chính."""
        return self._hybrid(query, k)

    def _hybrid(self, query: str, k: int) -> list[Hit]:
        bm = self.bm25.search(query, k * 3)
        ve = self.vec.search(query, k * 3)
        fused = _rrf([[i for i, _ in bm], [i for i, _ in ve]])
        top = sorted(fused.items(), key=lambda t: -t[1])[:k]
        return [Hit(self.docs[i], s, "hybrid") for i, s in top]
