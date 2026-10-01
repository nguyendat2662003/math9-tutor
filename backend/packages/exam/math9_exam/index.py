"""Kho đề trên Qdrant: lưu bài đã duyệt, tìm bài tương tự, lọc theo chuyên đề/dạng/độ khó.

Cấu hình (.env):
  QDRANT_URL + QDRANT_API_KEY   Qdrant Cloud (hoặc server riêng)
  QDRANT_PATH                   chế độ nhúng, lưu ra thư mục — dùng khi chưa có Cloud.
                                Chỉ MỘT tiến trình mở được thư mục này cùng lúc.
  (không đặt gì)                tắt — kho luyện đề chỉ dùng bài có sẵn trong data/eval/

Tên collection gắn với model embedding: đổi model thì dùng collection mới, không trộn
vector khác chiều vào nhau.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
BASE_COLLECTION = "de_thi"
UPSERT_BATCH = 32
_NS = uuid.UUID("8f0c7d1e-6a4b-4c2f-9d3e-5b7a1c9e2f40")    # uuid5 cố định: cùng id bài -> cùng point
INDEXED_FIELDS = {"topic": "keyword", "format": "keyword", "difficulty": "integer",
                  "status": "keyword", "origin": "keyword", "hash": "keyword"}


def text_hash(text: str) -> str:
    """Băm đề đã chuẩn hóa (bỏ khoảng trắng, dấu câu, hoa/thường) — bắt trùng lặp y hệt."""
    norm = re.sub(r"[\s\W_]+", "", text.lower())
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


def point_id(item_id: str) -> str:
    return str(uuid.uuid5(_NS, item_id))


def embed_text(p: dict) -> str:
    """Văn bản đem đi embed: đề chung + đề ý + phương án (không kèm đáp án)."""
    parts = [p.get("lead") or "", p.get("statement") or ""]
    if p.get("options"):
        parts.append(" ; ".join(p["options"]))
    return "\n".join(x for x in parts if x).strip()


class ProblemIndex:
    def __init__(self, client: Any, embedder: Any, name: str = BASE_COLLECTION):
        self.client, self.embedder = client, embedder
        model = getattr(embedder, "model", type(embedder).__name__)
        self.collection = f"{name}__{re.sub(r'[^A-Za-z0-9]+', '-', str(model)).strip('-').lower()}"
        self._lock = threading.Lock()
        self._ensure()

    # -- tạo từ .env -------------------------------------------------------

    @classmethod
    def from_env(cls) -> ProblemIndex | None:
        from math9_core.llm.client import load_env

        load_env()
        if os.environ.get("QDRANT_DISABLED") == "1":
            return None
        url, path = os.environ.get("QDRANT_URL"), os.environ.get("QDRANT_PATH")
        if not (url or path):
            return None
        from qdrant_client import QdrantClient

        if url:
            client = QdrantClient(url=url, api_key=os.environ.get("QDRANT_API_KEY") or None, timeout=90)
        else:
            p = Path(path)
            client = QdrantClient(path=str(p if p.is_absolute() else ROOT / p))
        return cls(client, _embedder_from_env())

    @property
    def mode(self) -> str:
        return "cloud" if os.environ.get("QDRANT_URL") else "local"

    def _ensure(self) -> None:
        from qdrant_client import models

        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=models.VectorParams(size=self.embedder.dim, distance=models.Distance.COSINE),
            )
            import warnings

            for field, kind in INDEXED_FIELDS.items():
                schema = models.PayloadSchemaType.INTEGER if kind == "integer" else models.PayloadSchemaType.KEYWORD
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")        # chế độ nhúng: index payload không có tác dụng, vô hại
                    try:
                        self.client.create_payload_index(self.collection, field, field_schema=schema)
                    except Exception:
                        pass
            log.info("Tạo collection Qdrant %s (%d chiều)", self.collection, self.embedder.dim)

    # -- ghi -------------------------------------------------------------

    def upsert(self, problems: list[dict]) -> int:
        """Ghi (hoặc ghi đè) bài theo `id`. Mỗi bài là payload đầy đủ, cần có id + statement."""
        from qdrant_client import models

        if not problems:
            return 0
        vecs = self.embedder.encode([embed_text(p) for p in problems])
        now = datetime.now(UTC).isoformat()
        points = []
        for p, v in zip(problems, vecs):
            payload = {**p, "hash": p.get("hash") or text_hash((p.get("lead") or "") + (p.get("statement") or "")),
                       "indexed_at": now}
            points.append(models.PointStruct(id=point_id(p["id"]), vector=v, payload=payload))
        # Gửi theo lô nhỏ: mỗi điểm kèm vector 1536 số (~30 KB JSON) — 200 bài một lần là vài MB,
        # mạng upload chậm sẽ quá thời gian. Lỗi mạng tạm thời thì thử lại.
        with self._lock:
            for i in range(0, len(points), UPSERT_BATCH):
                chunk = points[i:i + UPSERT_BATCH]
                for attempt in range(1, 4):
                    try:
                        self.client.upsert(self.collection, points=chunk, wait=True)
                        break
                    except Exception as e:
                        if attempt == 3:
                            raise RuntimeError(f"Ghi Qdrant thất bại ở bài {i + 1}–{i + len(chunk)} "
                                               f"sau 3 lần thử: {e}") from e
                        log.warning("Ghi Qdrant lỗi (%s), thử lại lần %d", type(e).__name__, attempt + 1)
                        time.sleep(2 * attempt)
        return len(points)

    def delete(self, ids: list[str]) -> None:
        from qdrant_client import models

        with self._lock:
            self.client.delete(self.collection, points_selector=models.PointIdsList(points=[point_id(i) for i in ids]))

    # -- đọc -------------------------------------------------------------

    def _filter(self, **must: Any):
        from qdrant_client import models

        conds = []
        for k, v in must.items():
            if v is None:
                continue
            if isinstance(v, (list, tuple, set)):
                conds.append(models.FieldCondition(key=k, match=models.MatchAny(any=list(v))))
            else:
                conds.append(models.FieldCondition(key=k, match=models.MatchValue(value=v)))
        return models.Filter(must=conds) if conds else None

    def similar(self, text: str, k: int = 5, *, topic: str | None = None, exclude_hash: str | None = None,
                min_score: float = 0.0) -> list[dict]:
        """Bài gần nghĩa nhất với `text`. Bỏ bài trùng y hệt (cùng hash) — không gợi ý lại chính nó."""
        from qdrant_client import models

        flt = self._filter(topic=topic, status="approved")
        if exclude_hash:
            not_same = models.FieldCondition(key="hash", match=models.MatchValue(value=exclude_hash))
            flt = models.Filter(must=(flt.must if flt else []), must_not=[not_same])
        res = self.client.query_points(self.collection, query=self.embedder.encode_one(text), limit=k,
                                       query_filter=flt, with_payload=True)
        return [{**p.payload, "score": round(p.score, 4)} for p in res.points if p.score >= min_score]

    def find_hash(self, h: str) -> dict | None:
        pts, _ = self.client.scroll(self.collection, scroll_filter=self._filter(hash=h), limit=1, with_payload=True)
        return pts[0].payload if pts else None

    def all(self, **must: Any) -> list[dict]:
        out, offset = [], None
        while True:
            pts, offset = self.client.scroll(self.collection, scroll_filter=self._filter(**must), limit=256,
                                             offset=offset, with_payload=True)
            out += [p.payload for p in pts]
            if offset is None:
                return out

    def count(self, **must: Any) -> int:
        return self.client.count(self.collection, count_filter=self._filter(**must), exact=True).count


def _embedder_from_env():
    from math9_retrieval.embedder import HashingEmbedder, OpenAIEmbedder

    if os.environ.get("EMBEDDER", "openai") == "hashing" or not os.environ.get("OPENAI_API_KEY"):
        log.warning("Kho đề dùng HashingEmbedder (không có OPENAI_API_KEY) — tìm bài tương tự sẽ kém")
        return HashingEmbedder()
    return OpenAIEmbedder(model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))


_index: ProblemIndex | None = None
_index_ready = False
_index_lock = threading.Lock()


def get_index() -> ProblemIndex | None:
    """Kho Qdrant dùng chung cho cả tiến trình; None nếu chưa cấu hình hoặc không kết nối được."""
    global _index, _index_ready
    with _index_lock:
        if not _index_ready:
            _index_ready = True
            try:
                _index = ProblemIndex.from_env()
            except Exception as e:
                log.warning("Không mở được kho đề Qdrant: %s — luyện đề chỉ dùng kho có sẵn", e)
                _index = None
        return _index


def set_index(index: ProblemIndex | None) -> None:
    """Cho test gắn kho trong bộ nhớ."""
    global _index, _index_ready
    with _index_lock:
        _index, _index_ready = index, True
