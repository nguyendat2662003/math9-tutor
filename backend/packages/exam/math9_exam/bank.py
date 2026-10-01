"""Kho bài thật: đề tuyển sinh vào 10 đã có đáp án trong `data/eval/`.

Kho dùng chung dữ liệu với bộ eval nhưng CHỈ để hiện cho học sinh. Không bao giờ
nạp bài trong kho (hay lời giải sinh ra khi học sinh bấm "xem lời giải") vào RAG:
Solver sẽ thuộc đáp án và số liệu eval mất ý nghĩa.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .figures import figure_for, needs_figure

EVAL_DIR = Path(__file__).resolve().parents[3] / "data" / "eval"
# out_of_scope: vượt chương trình; core_2006: chương trình cũ; smoke là tập con của core
BANK_FILES = ("core", "hard", "figure", "chuyen_chung")

_RE_OPT = re.compile(r"(?:^|;\s*)([A-D])\.\s")
_RE_CLAIM = re.compile(r"(?:^|\s)([a-d])\)\s")


@dataclass
class BankItem:
    id: str
    source: str
    format: str
    statement: str
    answer: object
    topic: str
    goal_type: str
    difficulty: int
    group: str | None = None
    options: list[str] | None = None
    claims: list[str] | None = None
    lead: str | None = None          # phần đề chung (chỉ có khi thuộc bài nhiều ý)
    part: str | None = None          # phần riêng của ý này
    figure: str | None = None        # SVG, cho bài mà đề nói "như hình vẽ", "biểu đồ"...
    needs_figure: bool = False

    @property
    def usable(self) -> bool:
        """Đề nhắc tới hình mà kho chưa có hình -> không đưa vào đề (học sinh không làm được)."""
        return self.figure is not None or not self.needs_figure

    @property
    def standalone(self) -> bool:
        """Tách ra làm câu lẻ được: đề đủ ý, không phụ thuộc ý trước."""
        return "tiếp ý" not in self.statement

    @property
    def auto(self) -> bool:
        """Chấm tự động được hay học sinh phải tự chấm theo lời giải."""
        if self.format == "trac_nghiem":
            return isinstance(self.answer, dict) and bool(self.answer.get("letter"))
        if self.format == "dung_sai":
            return bool(self.claims) and len(parse_true_false(self.answer)) == len(self.claims)
        if self.format == "tra_loi_ngan":
            return bool(self.answer)
        # tự luận: bài chứng minh, vẽ đồ thị -> tự chấm; bài tính ra đáp số -> chấm được.
        # Dựa vào lời đề, không dựa goal_type: eval gắn "Giải bất phương trình" là prove_inequality.
        if not isinstance(self.answer, str) or not self.answer.strip():
            return False
        text = self.part or self.statement
        if re.search(r"chứng minh|chứng tỏ", text, re.I) or re.match(r"\s*Vẽ", text):
            return False
        return not (self.topic.startswith("GEO") and self.goal_type.startswith("prove"))


@dataclass
class Bank:
    items: list[BankItem]
    groups: dict[str, list[BankItem]] = field(default_factory=dict)

    def by_id(self, item_id: str) -> BankItem | None:
        return next((x for x in self.items if x.id == item_id), None)


def parse_options(text: str) -> list[str]:
    """'A. −8; B. −5; C. 5; D. 8' -> ['−8', '−5', '5', '8']."""
    marks = list(_RE_OPT.finditer(text))
    return [text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)].strip(" ;")
            for i, m in enumerate(marks)]


def parse_true_false(answer: object) -> list[bool]:
    """'Đ - S - S - Đ' -> [True, False, False, True]."""
    if isinstance(answer, list):
        return [bool(x) for x in answer]
    return [t.strip().upper().startswith("Đ") for t in re.split(r"[-–,;]", str(answer or "")) if t.strip()]


def _split_claims(statement: str) -> tuple[str, list[str]]:
    """Tách đề đúng/sai thành phần dẫn và các ý a) b) c) d)."""
    head = statement.split("Mỗi ý chọn Đúng/Sai:")[0].strip()
    marks = list(_RE_CLAIM.finditer(statement))
    if len(marks) < 2:
        return statement, []
    head = head if "Mỗi ý chọn" in statement else statement[: marks[0].start()].strip()
    claims = [statement[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(statement)].strip()
              for i, m in enumerate(marks)]
    return head, claims


def _common_lead(statements: list[str]) -> str:
    """Phần đề chung của các ý: tiền tố chung, cắt lùi về hết câu gần nhất."""
    a, b = min(statements), max(statements)
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    cut = a[:n].rfind(". ")
    return a[: cut + 1].strip() if cut > 0 else ""


@lru_cache(maxsize=2)
def load_bank(eval_dir: Path = EVAL_DIR, include_uploads: bool = True) -> Bank:
    """Kho = bài có sẵn trong data/eval + bài tải lên đã duyệt trên Qdrant (nếu cấu hình)."""
    items: list[BankItem] = []
    # Bài vượt chương trình có thể nằm cả trong tập khác (chuyen_chung) — loại theo id
    oos = eval_dir / "out_of_scope.jsonl"
    seen_ids: set[str] = {json.loads(ln)["id"] for ln in oos.read_text(encoding="utf-8").splitlines() if ln.strip()} \
        if oos.exists() else set()
    seen_text: set[str] = set()
    for name in BANK_FILES:
        path = eval_dir / f"{name}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("curriculum") != "GDPT2018" or r["id"] in seen_ids:
                continue
            # Hai mã đề của cùng một kỳ thi trùng phần tự luận — giữ một bản
            key = re.sub(r"\s+", " ", r["statement"]).strip()
            if key in seen_text:
                continue
            seen_ids.add(r["id"])
            seen_text.add(key)

            g = r["gold"]
            fmt = r["format"]
            item = BankItem(
                id=r["id"], source=r["source"], format="tu_luan" if fmt == "ve_do_thi" else fmt,
                statement=r["statement"], answer=g.get("answer"), topic=g["topic"],
                goal_type=g.get("goal_type", ""), difficulty=int(g.get("difficulty", 1)),
                group=r.get("context_id"),
                figure=figure_for(r["id"], r.get("context_id")),
                needs_figure=needs_figure(r["statement"] + " " + (r.get("options") or "")),
            )
            if fmt == "trac_nghiem":
                item.options = parse_options(r.get("options") or "")
                if len(item.options) != 4:
                    continue                      # thiếu phương án -> không dùng làm trắc nghiệm
            if fmt == "dung_sai":
                item.statement, item.claims = _split_claims(r["statement"])
            items.append(item)

    if include_uploads:
        for p in _approved_uploads():
            full = f"{p['lead']} {p['statement']}" if p.get("lead") else p["statement"]
            key = re.sub(r"\s+", " ", full).strip()
            if key in seen_text or p["id"] in seen_ids or not p.get("topic"):
                continue
            seen_ids.add(p["id"])
            seen_text.add(key)
            items.append(BankItem(
                id=p["id"], source=p.get("source") or "Đề tải lên", format=p["format"], statement=full,
                answer=p.get("answer"), topic=p["topic"], goal_type=p.get("goal_type") or "",
                difficulty=int(p.get("difficulty") or 1), group=p.get("group"),
                options=p.get("options"), claims=p.get("claims"),
                lead=p.get("lead"), part=p["statement"] if p.get("lead") else None,
                needs_figure=bool(p.get("needs_figure")) or needs_figure(full + " " + " ".join(p.get("options") or [])),
            ))

    groups: dict[str, list[BankItem]] = {}
    for x in items:
        if x.group:
            groups.setdefault(x.group, []).append(x)
    for gid, parts in list(groups.items()):
        if len(parts) < 2:
            del groups[gid]
            parts[0].group = None
            continue
        parts.sort(key=lambda x: x.id)
        if all(p.lead and p.part for p in parts):
            continue                             # bài tải lên: đề chung đã tách sẵn
        lead = _common_lead([p.statement for p in parts])
        for p in parts:
            p.lead = lead or None
            p.part = p.statement[len(lead):].strip() if lead else p.statement
    return Bank(items=items, groups=groups)


def _approved_uploads() -> list[dict]:
    """Bài tải lên đã duyệt trên Qdrant. Qdrant lỗi -> bỏ qua, kho vẫn chạy với bài có sẵn."""
    from .index import get_index

    idx = get_index()
    if idx is None:
        return []
    try:
        return idx.all(status="approved", origin="upload")
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning("Không đọc được bài tải lên từ Qdrant: %s", e)
        return []


def refresh_bank() -> None:
    """Gọi sau khi duyệt bài mới để đề sinh ra lần sau có bài đó."""
    load_bank.cache_clear()
