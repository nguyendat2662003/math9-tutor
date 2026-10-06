"""Sinh đề từ cấu trúc: điền từng ô bằng bài thật trong kho hoặc biến thể đổi số.

Tất định theo `seed`: cùng cấu trúc + cùng seed -> cùng đề (để "làm lại đề này").
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from random import Random
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from .bank import Bank, BankItem, load_bank, parse_true_false
from .models import Exam, Question
from .variants import TEMPLATES, Template

BLUEPRINTS = Path(__file__).resolve().parents[3] / "data" / "exam" / "blueprints.yaml"
LETTERS = "ABCD"
# Chuyên đề có bài chứng minh hình: tự luận chỉ lấy từ đề thật, không biến thể
PROOF_TOPICS = {"GEO-5", "GEO-9"}
DIFFICULTY = {"de": [1], "vua": [2], "kho": [3], "tron": [1, 1, 2, 2, 3]}


@dataclass
class Slot:
    section: str
    format: str | None = None
    topic: str | None = None
    difficulty: int = 1
    points: float = 0.0
    group: str | None = None
    group_points: list[float] = field(default_factory=list)


@dataclass
class Blueprint:
    id: str
    name: str
    style: str
    minutes: int
    based_on: str
    slots: list[Slot]

    @property
    def total_points(self) -> float:
        return round(sum(s.points if not s.group else sum(s.group_points) for s in self.slots), 2)


class CustomSpec(BaseModel):
    """Đề tự chọn."""

    topics: list[str] = Field(min_length=1)
    n_trac_nghiem: int = Field(8, ge=0, le=40)
    n_tra_loi_ngan: int = Field(0, ge=0, le=20)
    n_tu_luan: int = Field(4, ge=0, le=15)
    level: Literal["de", "vua", "kho", "tron"] = "tron"
    minutes: int = Field(60, ge=5, le=180)


@lru_cache(maxsize=1)
def load_blueprints(path: Path = BLUEPRINTS) -> dict[str, Blueprint]:
    out: dict[str, Blueprint] = {}
    for raw in yaml.safe_load(path.read_text(encoding="utf-8")):
        slots: list[Slot] = []
        for sec in raw["sections"]:
            for s in sec["slots"]:
                if "group" in s:
                    slots.append(Slot(sec["title"], group=s["group"], group_points=[float(p) for p in s["points"]]))
                    continue
                for t in s.get("topics") or [s["topic"]]:
                    slots.append(Slot(sec["title"], s["format"], t, int(s.get("difficulty", 1)), float(s["points"])))
        out[raw["id"]] = Blueprint(raw["id"], raw["name"], raw["style"], int(raw["minutes"]), raw["based_on"], slots)
    return out


def custom_blueprint(spec: CustomSpec, rng: Random) -> Blueprint:
    """Chia đều chuyên đề đã chọn cho các câu; điểm theo trọng số rồi quy về thang 10."""
    levels = DIFFICULTY[spec.level]
    plan = ([("trac_nghiem", 1.0)] * spec.n_trac_nghiem + [("tra_loi_ngan", 1.5)] * spec.n_tra_loi_ngan
            + [("tu_luan", 3.0)] * spec.n_tu_luan)
    if not plan:
        raise ValueError("Đề cần ít nhất một câu")
    total_w = sum(w for _, w in plan)
    topics = list(spec.topics)
    rng.shuffle(topics)
    slots: list[Slot] = []
    for i, (fmt, w) in enumerate(plan):
        title = {"trac_nghiem": "Phần I. Trắc nghiệm", "tra_loi_ngan": "Phần II. Trả lời ngắn", "tu_luan": "Phần III. Tự luận"}[fmt]
        slots.append(Slot(title, fmt, topics[i % len(topics)], rng.choice(levels), round(10 * w / total_w, 2)))
    slots[-1].points = round(slots[-1].points + 10 - sum(s.points for s in slots), 2)   # bù sai số làm tròn
    return Blueprint("tu-chon", "Đề tự chọn", "Tự chọn", spec.minutes, "", slots)


# ---------- điền ô ----------

class _Filler:
    def __init__(self, bank: Bank, rng: Random, variant_ratio: float):
        self.bank, self.rng, self.ratio = bank, rng, variant_ratio
        self.used_items: set[str] = set()
        self.used_groups: set[str] = set()
        self.used_templates: dict[str, int] = {}
        self.warnings: list[str] = []

    def _bank_candidates(self, fmt: str, topic: str, ok_d) -> list[BankItem]:
        return [x for x in self.bank.items
                if x.format == fmt and x.topic == topic and ok_d(x.difficulty) and x.standalone and x.usable
                and x.id not in self.used_items and (not x.group or x.group not in self.used_groups)]

    def _template_candidates(self, fmt: str, topic: str, ok_d) -> list[Template]:
        if fmt == "tu_luan" and topic in PROOF_TOPICS:
            return []
        return [t for t in TEMPLATES if t.topic == topic and fmt in t.formats and ok_d(t.difficulty)]

    def single(self, slot: Slot) -> Question | None:
        d = slot.difficulty
        for ok_d in (lambda x: x == d, lambda x: abs(x - d) <= 1, lambda x: True):
            items = self._bank_candidates(slot.format, slot.topic, ok_d)
            temps = self._template_candidates(slot.format, slot.topic, ok_d)
            if items or temps:
                break
        else:
            self.warnings.append(f"Không có câu {slot.format} chuyên đề {slot.topic} — bỏ trống ô này.")
            return None
        least = min((self.used_templates.get(t.id, 0) for t in temps), default=0)
        # Mẫu nào cũng đã dùng trong đề này mà kho còn bài thật -> lấy bài thật, tránh hai câu na ná nhau
        if temps and (not items or (least == 0 and self.rng.random() < self.ratio)):
            t = self.rng.choice([t for t in temps if self.used_templates.get(t.id, 0) == least])
            self.used_templates[t.id] = least + 1
            return from_variant(t, slot.format, self.rng, slot)
        x = self.rng.choice(items)
        self.used_items.add(x.id)
        if x.group:
            self.used_groups.add(x.group)       # không lấy ý khác của cùng bài ở ô sau
        return from_bank(x, slot)

    def group(self, slot: Slot) -> list[Question]:
        want = len(slot.group_points)
        cands = [(gid, parts) for gid, parts in self.bank.groups.items()
                 if gid not in self.used_groups and _main_topic(parts) == slot.group
                 and all(p.usable for p in parts) and not any(p.id in self.used_items for p in parts)]
        exact = [c for c in cands if len(c[1]) >= want]
        if not (exact or cands):
            self.warnings.append(f"Không còn bài nhiều ý chuyên đề {slot.group} — bỏ trống ô này.")
            return []
        gid, parts = self.rng.choice(exact or cands)
        self.used_groups.add(gid)
        parts = parts[:want]                     # ý sau phụ thuộc ý trước, nên cắt từ cuối là an toàn
        pts = slot.group_points
        if len(parts) < want:                    # bài ít ý hơn cấu trúc: dồn điểm cho đủ
            pts = [round(sum(pts) / len(parts), 2)] * len(parts)
        out = []
        for x, p in zip(parts, pts):
            self.used_items.add(x.id)
            out.append(from_bank(x, Slot(slot.section, x.format, x.topic, x.difficulty, p), grouped=True))
        return out


def _main_topic(parts: list[BankItem]) -> str:
    topics = [p.topic for p in parts]
    return max(set(topics), key=topics.count)


def from_bank(x: BankItem, slot: Slot, grouped: bool = False) -> Question:
    q = Question(
        qid="", number="", section=slot.section, format=x.format,
        statement=(x.part or x.statement) if grouped else x.statement,
        context=x.lead if grouped else None, group=x.group if grouped else None,
        points=slot.points, topic=x.topic, difficulty=x.difficulty, source=x.source,
        origin="bank", auto=x.auto, answer=x.answer, bank_id=x.id, figure_svg=x.figure,
    )
    if x.format == "trac_nghiem":
        q.options = list(x.options or [])
    if x.format == "dung_sai":
        q.claims = list(x.claims or [])
        q.answer = parse_true_false(x.answer)
    return q


def from_variant(t: Template, fmt: str, rng: Random, slot: Slot) -> Question:
    v = t.instantiate(rng)
    q = Question(
        qid="", number="", section=slot.section, format=fmt, statement=v.statement,
        points=slot.points, topic=t.topic, difficulty=t.difficulty, source="Biến thể tự sinh (đáp án tính bằng máy)",
        origin="variant", auto=True, answer=v.answer, solution=v.solution, template=t.id,
        check=v.check, hint=v.hint,
    )
    if fmt == "trac_nghiem":
        order = list(range(4))
        rng.shuffle(order)
        q.statement = v.stem
        q.options = [v.choices[i] for i in order]
        q.answer = {"letter": LETTERS[order.index(0)], "value": v.choices[0]}
        q.check, q.hint = "set", None
    return q


def build_exam(blueprint: Blueprint, seed: int | None = None, variant_ratio: float = 0.5,
               bank: Bank | None = None) -> Exam:
    seed = seed if seed is not None else Random().randrange(1, 10**9)
    rng = Random(seed)
    f = _Filler(bank or load_bank(), rng, variant_ratio)
    questions: list[Question] = []
    for slot in blueprint.slots:
        if slot.group:
            questions += f.group(slot)
        else:
            q = f.single(slot)
            if q:
                questions.append(q)
    _number(questions)
    return Exam(id=uuid.uuid4().hex, title=blueprint.name if blueprint.id == "tu-chon" else f"Đề luyện thi vào 10 — {blueprint.name}",
                minutes=blueprint.minutes, blueprint=blueprint.id, seed=seed, questions=questions, warnings=f.warnings)


def _number(questions: list[Question]) -> None:
    """Đánh số lại từ 1 trong mỗi phần/bài; các ý của cùng một bài nhiều ý thêm a, b, c."""
    n = 0
    section: str | None = None
    last_group: str | None = None
    letter = 0
    for i, q in enumerate(questions, 1):
        q.qid = f"q{i}"
        if q.section != section:
            section, n, last_group = q.section, 0, None
        if q.group and q.group == last_group:
            letter += 1
            q.number = f"Câu {n}{'abcdefgh'[letter]}"
            continue
        n += 1
        letter = 0
        last_group = q.group
        q.number = f"Câu {n}a" if q.group else f"Câu {n}"
