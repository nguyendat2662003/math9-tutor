"""Ghép nối toàn bộ khâu nhập dữ liệu và xuất JSONL.

    discover -> fetch -> extract -> normalize -> segment -> quality -> dedupe -> xuất

Đầu ra KHÔNG phải kho sẵn dùng. Nó gồm hai phần:
  - `accepted.jsonl`  — sạch, vào thẳng bộ eval / kho few-shot
  - `review.jsonl`    — xếp hàng cho giáo viên soát

Tỉ lệ auto-accept thực tế với PDF đề thi khoảng 50-65%. Đừng thiết kế quy trình
giả định 100%.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .adapters.base import DocumentRef, SourceAdapter
from .dedup import Deduper
from .extract.text import extract
from .fetch import Fetcher
from .normalize import normalize
from .quality import Verdict, assess
from .segment import split_answer_key, split_problems

log = logging.getLogger(__name__)


@dataclass
class IngestStats:
    docs_fetched: int = 0
    docs_failed: int = 0
    problems_found: int = 0
    auto_accepted: int = 0
    needs_review: int = 0
    needs_ocr: int = 0
    rejected: int = 0
    duplicates: int = 0
    by_source: dict = field(default_factory=dict)

    def report(self) -> str:
        total = max(self.problems_found, 1)
        return (
            f"Tài liệu: {self.docs_fetched} tải được, {self.docs_failed} lỗi\n"
            f"Bài trích được: {self.problems_found}\n"
            f"  tự động chấp nhận : {self.auto_accepted:4d} ({self.auto_accepted/total:.0%})\n"
            f"  cần giáo viên soát: {self.needs_review:4d} ({self.needs_review/total:.0%})\n"
            f"  cần OCR công thức : {self.needs_ocr:4d} ({self.needs_ocr/total:.0%})\n"
            f"  loại bỏ           : {self.rejected:4d} ({self.rejected/total:.0%})\n"
            f"  trùng lặp         : {self.duplicates:4d}"
        )


class IngestPipeline:
    def __init__(self, out_dir: Path = Path("data/raw"), fetcher: Fetcher | None = None):
        self.out = out_dir
        self.out.mkdir(parents=True, exist_ok=True)
        self.fetcher = fetcher or Fetcher()
        self.deduper = Deduper()
        self.stats = IngestStats()

    def run(self, adapters: list[SourceAdapter]) -> IngestStats:
        accepted, review = [], []

        for ad in adapters:
            if not ad.verified_public:
                log.error(
                    "Bỏ qua adapter '%s': chưa đặt verified_public. "
                    "Xem adapters/README.md để biết checklist.", ad.name
                )
                continue
            for doc, key in ad.pair_answer_key(ad.discover()):
                a, r = self._process(ad, doc, key)
                accepted += a
                review += r

        self._write("accepted.jsonl", accepted)
        self._write("review.jsonl", review)
        return self.stats

    # -- xử lý một tài liệu ---------------------------------------------

    def _process(self, ad, doc: DocumentRef, key: DocumentRef | None):
        f = self.fetcher.fetch(doc.url)
        if not f:
            self.stats.docs_failed += 1
            return [], []
        self.stats.docs_fetched += 1

        raw, diag = extract(f.path, f.content_type)
        if diag.get("likely_scanned"):
            log.warning("PDF có vẻ là bản scan, cần OCR: %s", doc.url)
        text = normalize(raw)

        answers: dict[str, str] = {}
        if key and (fk := self.fetcher.fetch(key.url)):
            araw, _ = extract(fk.path, fk.content_type)
            answers = split_answer_key(normalize(araw))

        accepted, review = [], []
        for p in split_problems(text):
            self.stats.problems_found += 1
            q = assess(p)

            dup = self.deduper.add(self.stats.problems_found, p.statement())
            if dup is not None:
                self.stats.duplicates += 1
                continue

            rec = {
                "id": f"{ad.name}-{doc.year or 'na'}-{doc.province or 'na'}-b{p.number}",
                "source": doc.source_label(),
                "source_url": doc.url,
                "statement": p.statement(),
                "parts": [{"label": x.label, "statement": x.statement} for x in p.parts],
                "answer_raw": answers.get(p.number),
                "score": p.score,
                "likely_geometry": p.likely_geometry,
                "quality": {"verdict": str(q.verdict), "score": q.score, "flags": q.flags},
                "gold": None,          # giáo viên điền: topic, goal_type, difficulty, predicates
                "extract_diag": diag,
            }

            if q.verdict == Verdict.AUTO_ACCEPT:
                self.stats.auto_accepted += 1
                accepted.append(rec)
            elif q.verdict == Verdict.REJECT:
                self.stats.rejected += 1
            else:
                if q.verdict == Verdict.NEEDS_OCR:
                    self.stats.needs_ocr += 1
                else:
                    self.stats.needs_review += 1
                review.append(rec)

        self.stats.by_source[ad.name] = self.stats.by_source.get(ad.name, 0) + 1
        return accepted, review

    def _write(self, name: str, records: list[dict]) -> None:
        p = self.out / name
        with p.open("w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        log.info("Đã ghi %d bản ghi vào %s", len(records), p)
