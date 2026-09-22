"""Phát hiện trùng lặp gần.

Đề thi được đăng lại rất nhiều nơi với khác biệt nhỏ (khoảng trắng, cách đánh
số, watermark). Không lọc thì bộ eval sẽ nghiêng nặng về vài bài phổ biến và
cho ra con số accuracy sai lệch.

Dùng MinHash trên shingle ký tự — bền với khác biệt định dạng, không cần thư
viện ngoài.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

SHINGLE = 5
NUM_HASHES = 64


def _canon(s: str) -> str:
    """Rút về dạng chuẩn: bỏ dấu câu, khoảng trắng, số thứ tự bài."""
    s = re.sub(r"(?i)^\s*(?:bài|câu)\s+[0-9IVX]+\s*[.:)\-]", "", s)
    s = re.sub(r"[^\w]", "", s.lower())
    return s


def minhash(text: str, num: int = NUM_HASHES) -> tuple[int, ...]:
    c = _canon(text)
    if len(c) < SHINGLE:
        c = c.ljust(SHINGLE, "_")
    shingles = {c[i: i + SHINGLE] for i in range(len(c) - SHINGLE + 1)}
    sig = []
    for i in range(num):
        best = min(
            int(hashlib.blake2b(f"{i}:{sh}".encode(), digest_size=8).hexdigest(), 16)
            for sh in shingles
        )
        sig.append(best)
    return tuple(sig)


def similarity(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a)


@dataclass
class DedupResult:
    kept: list[int]
    duplicates: dict[int, int]   # chỉ số bị loại -> chỉ số bản gốc giữ lại


class Deduper:
    def __init__(self, threshold: float = 0.82):
        self.threshold = threshold
        self._sigs: list[tuple[int, ...]] = []
        self._ids: list[int] = []

    def add(self, idx: int, text: str) -> int | None:
        """Trả về chỉ số bản gốc nếu trùng, None nếu là bản mới."""
        sig = minhash(text)
        for kept_sig, kept_id in zip(self._sigs, self._ids):
            if similarity(sig, kept_sig) >= self.threshold:
                return kept_id
        self._sigs.append(sig)
        self._ids.append(idx)
        return None


def dedupe(texts: list[str], threshold: float = 0.82) -> DedupResult:
    d = Deduper(threshold)
    kept, dups = [], {}
    for i, t in enumerate(texts):
        orig = d.add(i, t)
        if orig is None:
            kept.append(i)
        else:
            dups[i] = orig
    return DedupResult(kept, dups)
