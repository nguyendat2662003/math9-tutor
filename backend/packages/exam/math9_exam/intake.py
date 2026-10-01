"""Nhập tài liệu đề mới: file -> LLM tách bài (chép đáp án có sẵn, KHÔNG tự giải) -> lô chờ duyệt.

Mỗi lần tải lên là một LÔ lưu ở `data/inbox/<id>.json`. Bài chỉ vào kho Qdrant (và từ đó
vào đề luyện, gợi ý bài tương tự) khi người duyệt bấm duyệt. Chưa duyệt thì không ai thấy.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bank import load_bank, parse_options, parse_true_false
from .figures import needs_figure
from .index import ProblemIndex, text_hash

log = logging.getLogger(__name__)

INBOX_DIR = Path(__file__).resolve().parents[3] / "data" / "inbox"
FORMATS = {"trac_nghiem", "dung_sai", "tra_loi_ngan", "tu_luan"}
MAX_CHARS = 60_000                   # tài liệu dài hơn: cắt, báo cho người duyệt
_RE_ID = re.compile(r"^[0-9a-f]{32}$")
_lock = threading.Lock()


# ---------- lưu lô ----------

def _path(batch_id: str) -> Path:
    if not _RE_ID.fullmatch(batch_id or ""):
        raise ValueError("batch_id không hợp lệ")
    return INBOX_DIR / f"{batch_id}.json"


def save_batch(batch: dict) -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        tmp = _path(batch["id"]).with_suffix(".tmp")
        tmp.write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(_path(batch["id"]))


def load_batch(batch_id: str) -> dict:
    p = _path(batch_id)
    if not p.exists():
        raise KeyError(batch_id)
    return json.loads(p.read_text(encoding="utf-8"))


def list_batches() -> list[dict]:
    if not INBOX_DIR.exists():
        return []
    out = []
    for p in INBOX_DIR.glob("*.json"):
        b = json.loads(p.read_text(encoding="utf-8"))
        probs = b.get("problems", [])
        out.append({k: b.get(k) for k in ("id", "filename", "source", "status", "error", "created_at")}
                   | {"counts": {s: sum(1 for x in probs if x["status"] == s) for s in ("pending", "approved", "rejected")}})
    return sorted(out, key=lambda b: b["created_at"] or "", reverse=True)


def new_batch(filename: str) -> dict:
    return {"id": uuid.uuid4().hex, "filename": filename, "source": None, "status": "processing",
            "error": None, "created_at": datetime.now(UTC).isoformat(), "notes": [], "problems": []}


# ---------- đọc tài liệu ----------

def read_document(path: Path) -> tuple[str, list[str]]:
    """-> (văn bản, danh sách ảnh). PDF/Word lấy chữ; ảnh để VLM đọc."""
    ext = path.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        return "", [str(path)]
    from math9_ingest.extract.text import extract

    text, _meta = extract(path)
    if not text.strip():
        raise ValueError("Không trích được chữ từ tài liệu (có thể là PDF scan) — hãy chụp ảnh từng trang rồi tải ảnh lên")
    return text, []


# ---------- LLM tách bài ----------

def _extractor(llm, model: str | None):
    from math9_core.agents.base import Agent

    class ExtractorAgent(Agent):
        role = "extractor"
        prompt_file = "extractor.md"

        def run(self, state):                        # không dùng trong pipeline giải bài
            return state

    return ExtractorAgent(llm=llm, model=model)


def extract_problems(path: Path, llm, model: str | None = None) -> tuple[dict, list[str]]:
    """Gọi LLM tách bài. -> (JSON thô của LLM, ghi chú cho người duyệt)."""
    from math9_core.enums import GOAL_TYPE_VI
    from math9_core.state import ProblemState
    from math9_curriculum.loader import curriculum

    notes: list[str] = []
    text, images = read_document(path)
    if len(text) > MAX_CHARS:
        notes.append(f"Tài liệu dài {len(text):,} ký tự — chỉ đọc {MAX_CHARS:,} ký tự đầu. Nên tách thành nhiều file.")
        text = text[:MAX_CHARS]
    agent = _extractor(llm, model)
    prompt = agent.render(text=text, topic_catalog=curriculum().label_catalog(), goal_types=", ".join(GOAL_TYPE_VI))
    resp = agent.complete(
        ProblemState(raw_input=f"[tài liệu] {path.name}"), prompt,
        system="Bạn tách đề thi Toán thành từng bài, chép nguyên văn, không tự giải. Chỉ trả JSON.",
        max_tokens=32000, temperature=0.0, images=images or None,
    )
    if resp.finish_reason == "length":
        notes.append("Model dừng vì hết độ dài đầu ra — có thể thiếu các bài cuối. Nên tách tài liệu nhỏ hơn.")
    return agent.parse_json(resp), notes


# ---------- chuẩn hóa + kiểm tra ----------

def normalize(raw: dict, batch_id: str, filename: str) -> list[dict]:
    """JSON của LLM -> danh sách bài theo đúng schema kho, kèm cảnh báo cho người duyệt."""
    source = raw.get("source") or Path(filename).stem
    out = []
    for i, p in enumerate(raw.get("problems") or [], 1):
        fmt = p.get("format") if p.get("format") in FORMATS else "tu_luan"
        statement = str(p.get("statement") or "").strip()
        lead = (str(p.get("lead")).strip() or None) if p.get("lead") else None
        if not statement:
            continue
        item: dict[str, Any] = {
            "id": f"up-{batch_id[:8]}-{i:03d}", "batch": batch_id, "filename": filename, "source": source,
            "number": str(p.get("number") or f"Bài {i}"),
            "group": f"{batch_id[:8]}:{p['group']}" if p.get("group") and lead else None,
            "lead": lead, "statement": statement, "format": fmt,
            "answer": p.get("answer"), "answer_evidence": p.get("answer_evidence"),
            "topic": p.get("topic"), "goal_type": p.get("goal_type") or "",
            "difficulty": p.get("difficulty"), "needs_figure": bool(p.get("needs_figure")),
            "status": "pending", "origin": "upload",
            "options": p.get("options"), "claims": p.get("claims"),
        }
        out.append(validate(item))
    return out


def validate(item: dict) -> dict:
    """Chuẩn hóa kiểu dữ liệu theo dạng câu và tính lại cảnh báo. Gọi lại sau mỗi lần sửa bài."""
    from math9_curriculum.loader import curriculum

    w: list[str] = []
    fmt = item["format"] if item.get("format") in FORMATS else "tu_luan"
    item["format"] = fmt
    if item.get("topic") not in curriculum().topics:
        item["topic"] = None
        w.append("Chưa xác định được chuyên đề — chọn chuyên đề trước khi duyệt.")
    item["difficulty"] = min(3, max(1, int(item.get("difficulty") or 1)))
    ans = item.get("answer")
    if fmt == "trac_nghiem":
        opts = item.get("options")
        opts = parse_options(opts) if isinstance(opts, str) else [str(o).strip() for o in (opts or [])]
        item["options"], item["claims"] = opts, None
        a = ans if isinstance(ans, dict) else ({"letter": ans.strip()[:1]} if isinstance(ans, str) and ans.strip() else None)
        if len(opts) != 4:
            w.append(f"Trắc nghiệm có {len(opts)} phương án (cần 4).")
        letter = str((a or {}).get("letter", "")).upper()
        if letter not in ("A", "B", "C", "D"):
            w.append("Trắc nghiệm chưa có đáp án (chữ cái A–D).")
            item["answer"] = None
        else:
            idx = "ABCD".index(letter)
            item["answer"] = {"letter": letter, "value": (a or {}).get("value") or (opts[idx] if idx < len(opts) else "")}
    elif fmt == "dung_sai":
        item["claims"], item["options"] = [str(c).strip() for c in (item.get("claims") or [])], None
        tf = parse_true_false(ans) if ans else []
        if not tf or len(tf) != len(item["claims"]):
            w.append("Đúng/Sai: số đáp án không khớp số ý.")
    else:
        item["options"] = item["claims"] = None
        item["answer"] = str(ans).strip() if ans not in (None, "") and not isinstance(ans, dict) else None
        if not item["answer"] and not re.search(r"chứng minh|chứng tỏ", item["statement"], re.I):
            w.append("Chưa có đáp số trong tài liệu — học sinh sẽ phải tự chấm câu này.")
    if item["answer"] and not item.get("answer_evidence"):
        w.append("Có đáp án nhưng không trích được nguồn trong tài liệu — kiểm tra kỹ.")
    item["needs_figure"] = bool(item.get("needs_figure")) or needs_figure((item.get("lead") or "") + " " + item["statement"])
    if item["needs_figure"]:
        w.append("Đề cần hình/biểu đồ — chưa hỗ trợ đính kèm hình, bài sẽ KHÔNG được đưa vào đề luyện.")
    item["hash"] = text_hash((item.get("lead") or "") + item["statement"])
    item["warnings"] = w
    item.pop("duplicate_of", None)             # mark_duplicates tính lại
    return item


def mark_duplicates(problems: list[dict], index: ProblemIndex | None, near: float = 0.95) -> None:
    """Đánh dấu bài trùng với kho có sẵn (data/eval), với Qdrant, hoặc với bài khác cùng lô."""
    eval_hashes = {text_hash(x.statement): x.id for x in load_bank(include_uploads=False).items}
    seen: dict[str, str] = {}
    for p in problems:
        dup = eval_hashes.get(p["hash"]) or seen.get(p["hash"])
        if not dup and index is not None:
            hit = index.find_hash(p["hash"])
            dup = hit["id"] if hit and hit["id"] != p["id"] else None
            if not dup:
                try:
                    near_hits = [h for h in index.similar((p["lead"] or "") + "\n" + p["statement"], k=2, min_score=near)
                                 if h["id"] != p["id"]]
                    if near_hits:
                        p["warnings"].append(f"Rất giống bài {near_hits[0]['id']} đã có trong kho "
                                             f"(độ giống {near_hits[0]['score']:.2f}) — xem có phải trùng không.")
                except Exception as e:
                    log.warning("Không so được độ giống: %s", e)
        if dup:
            p["duplicate_of"] = dup
            p["warnings"].append(f"Trùng với bài {dup} đã có — sẽ không thêm lại.")
        seen.setdefault(p["hash"], p["id"])


def process_upload(batch: dict, path: Path, llm, model: str | None, index: ProblemIndex | None) -> dict:
    """Chạy nền sau khi nhận file: tách bài, chuẩn hóa, đánh dấu trùng. Lỗi thì ghi vào lô."""
    try:
        raw, notes = extract_problems(path, llm, model)
        problems = normalize(raw, batch["id"], batch["filename"])
        mark_duplicates(problems, index)
        batch.update(source=raw.get("source"), problems=problems, notes=notes,
                     status="ready" if problems else "error",
                     error=None if problems else "Không tách được bài nào từ tài liệu")
    except Exception as e:
        log.exception("Xử lý tài liệu %s lỗi", batch["filename"])
        batch.update(status="error", error=f"{type(e).__name__}: {e}"[:500])
    save_batch(batch)
    return batch


# ---------- duyệt ----------

EDITABLE = {"statement", "lead", "format", "options", "claims", "answer", "topic", "goal_type", "difficulty", "number"}


def approve(batch: dict, ids: list[str], index: ProblemIndex) -> tuple[int, list[str]]:
    """Đưa các bài đã chọn vào Qdrant. Bỏ qua bài trùng hoặc thiếu chuyên đề. -> (số bài ghi, lý do bỏ)."""
    chosen = [p for p in batch["problems"] if p["id"] in set(ids) and p["status"] != "approved"]
    ok, skipped = [], []
    for p in chosen:
        if p.get("duplicate_of"):
            skipped.append(f"{p['number']}: trùng {p['duplicate_of']}")
        elif not p.get("topic"):
            skipped.append(f"{p['number']}: chưa chọn chuyên đề")
        elif p["format"] == "trac_nghiem" and (len(p.get("options") or []) != 4 or not p.get("answer")):
            skipped.append(f"{p['number']}: trắc nghiệm thiếu phương án/đáp án")
        else:
            ok.append(p)
    payloads = [{k: v for k, v in p.items() if k != "warnings"} | {"status": "approved"} for p in ok]
    n = index.upsert(payloads) if payloads else 0
    for p in ok:
        p["status"] = "approved"
        p["approved_at"] = datetime.now(UTC).isoformat()
    save_batch(batch)
    return n, skipped
