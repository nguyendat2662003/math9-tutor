"""Kiểm chứng kết luận hình học bằng số trên nhiều cấu hình ngẫu nhiên.

Nguyên tắc: một mệnh đề hình học đúng thì đúng với MỌI cấu hình thỏa mãn giả
thiết. Ta dựng lại hình với N seed khác nhau và kiểm tra vị từ trên từng cấu
hình. Đúng cả N lần -> gần như chắc chắn đúng. Sai dù chỉ một lần -> sai.

Đây là cơ chế độc lập với LLM, nên nó bắt được lỗi mà LLM tự kiểm tra sẽ bỏ sót.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from math9_geometry.construct import Figure, build
from math9_geometry.dsl import Construction
from math9_geometry.primitives import GeometryError

from .predicates import Predicate, residual

DEFAULT_SEEDS = (11, 29, 47, 83, 131)
TOLERANCE = 1e-7


@dataclass
class PredicateResult:
    predicate: Predicate
    holds: bool
    max_residual: float
    n_configs: int
    error: str | None = None


@dataclass
class GeometryVerdict:
    ok: bool
    results: list[PredicateResult] = field(default_factory=list)
    build_errors: list[str] = field(default_factory=list)
    n_configs: int = 0

    def failures(self) -> list[PredicateResult]:
        return [r for r in self.results if not r.holds]


def build_many(
    construction: Construction, seeds: tuple[int, ...] = DEFAULT_SEEDS
) -> tuple[list[Figure], list[str]]:
    """Dựng lại cùng một hình với nhiều cấu hình ngẫu nhiên."""
    figs: list[Figure] = []
    errors: list[str] = []
    for s in seeds:
        try:
            figs.append(build(construction, seed=s))
        except GeometryError as e:
            errors.append(f"seed={s}: {e}")
    return figs, errors


def verify(
    construction: Construction,
    claims: list[Predicate],
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    tol: float = TOLERANCE,
) -> GeometryVerdict:
    """Kiểm chứng danh sách kết luận.

    Nếu không dựng được hình ở đa số cấu hình, coi như kịch bản sai — thường
    là dấu hiệu Draftsman hiểu sai đề hoặc đề có mâu thuẫn.
    """
    figs, build_errors = build_many(construction, seeds)
    if len(figs) < max(2, len(seeds) // 2):
        return GeometryVerdict(
            ok=False, build_errors=build_errors, n_configs=len(figs)
        )

    results: list[PredicateResult] = []
    for c in claims:
        worst, err = 0.0, None
        try:
            worst = max(residual(f, c) for f in figs)
        except (GeometryError, KeyError, IndexError, TypeError, ValueError, ZeroDivisionError) as e:
            err = f"{type(e).__name__}: {e}"
        results.append(
            PredicateResult(
                predicate=c,
                holds=err is None and worst < tol,
                max_residual=worst,
                n_configs=len(figs),
                error=err,
            )
        )

    return GeometryVerdict(
        ok=all(r.holds for r in results),
        results=results,
        build_errors=build_errors,
        n_configs=len(figs),
    )


def cross_check_solution(construction: Construction, referenced: set[str]) -> list[str]:
    """Đối chiếu chéo lời giải với kịch bản dựng hình.

    Nếu lời giải nhắc tới điểm K mà kịch bản không dựng K, một trong hai agent
    đã hiểu sai đề. Đây là tín hiệu cảnh báo sớm rất rẻ.
    """
    try:
        fig = build(construction, seed=DEFAULT_SEEDS[0])
    except GeometryError as e:
        return [f"Không dựng được hình: {e}"]
    known = set(fig.objects) | {c for n in fig.objects for c in n}
    missing = sorted(referenced - known)
    return [f"Lời giải nhắc tới '{m}' nhưng hình không có" for m in missing]
