"""Nạp bản đồ chương trình từ thư mục YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .schema import CurriculumMap, Topic

DEFAULT_DIR = Path(__file__).resolve().parents[3] / "data" / "curriculum"


def load_dir(path: Path | str = DEFAULT_DIR) -> CurriculumMap:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục chương trình: {p}")
    topics: dict[str, Topic] = {}
    for f in sorted(p.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        t = Topic.model_validate(data)
        topics[t.id] = t
    if not topics:
        raise ValueError(f"Thư mục {p} không có file chuyên đề nào")
    return CurriculumMap(topics=topics)


@lru_cache(maxsize=1)
def curriculum() -> CurriculumMap:
    return load_dir()
