"""Lớp trừu tượng cho embedding. Cho phép đổi backend không sửa retriever.

Ba lựa chọn theo giai đoạn:
- HashingEmbedder: không cần model, chạy offline, đủ để test và cho kho nhỏ.
- LocalEmbedder: sentence-transformers đa ngữ (vd bge-m3), self-host, tiếng Việt tốt.
- APIEmbedder: gọi API embedding, chất lượng cao nhất, tốn tiền.

Với tiếng Việt, ưu tiên model đa ngữ có huấn luyện tiếng Việt. Tránh model chỉ
tiếng Anh — nó embed 'tứ giác nội tiếp' rất kém.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod


def _tokenize(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower(), flags=re.UNICODE)


class Embedder(ABC):
    dim: int

    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]: ...

    def encode_one(self, text: str) -> list[float]:
        return self.encode([text])[0]


class HashingEmbedder(Embedder):
    """Embedding bằng hashing trick — không cần model, tất định, chạy offline.

    Không nắm được ngữ nghĩa sâu, nhưng đủ cho unit test và kho vài trăm tài
    liệu khi kết hợp với BM25 trong hybrid search. Thay bằng LocalEmbedder khi
    lên production.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def encode(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            v = [0.0] * self.dim
            toks = _tokenize(t)
            for tok in toks:
                h = int(hashlib.blake2b(tok.encode(), digest_size=8).hexdigest(), 16)
                v[h % self.dim] += 1.0
                # bigram để bắt cụm 'nội tiếp', 'cố định'
            for a, b in zip(toks, toks[1:]):
                h = int(hashlib.blake2b(f"{a}_{b}".encode(), digest_size=8).hexdigest(), 16)
                v[h % self.dim] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out


class OpenAIEmbedder(Embedder):
    """API embedding tương thích OpenAI. `text-embedding-3-small`: đa ngữ, tiếng Việt ổn, rẻ
    (khoảng 0,02 USD / 1 triệu token — cả kho vài nghìn đề chưa tới 1 cent)."""

    def __init__(self, model: str = "text-embedding-3-small", dim: int = 1536,
                 base_url: str | None = None, api_key: str | None = None, batch: int = 64):
        import os

        self.model, self.dim, self.batch = model, dim, batch
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def encode(self, texts: list[str]) -> list[list[float]]:
        import httpx

        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch):
            chunk = [t[:8000] or " " for t in texts[i:i + self.batch]]      # API từ chối chuỗi rỗng
            r = httpx.post(f"{self.base_url}/embeddings", json={"model": self.model, "input": chunk},
                           headers={"Authorization": f"Bearer {self.api_key}"}, timeout=60)
            if r.status_code >= 400:
                raise RuntimeError(f"Embedding HTTP {r.status_code}: {r.text[:300]}")
            out += [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
        return out


class LocalEmbedder(Embedder):
    """sentence-transformers self-host. Khuyên dùng bge-m3 cho tiếng Việt."""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self._model = None
        self.dim = 1024

    def _lazy(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self.dim = self._model.get_sentence_embedding_dimension()
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self._lazy().encode(texts, normalize_embeddings=True).tolist()
