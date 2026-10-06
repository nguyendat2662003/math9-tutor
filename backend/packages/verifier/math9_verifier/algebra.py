"""Kiểm chứng đại số bằng SymPy — giải lại độc lập rồi so khớp.

Solver xuất kèm một biểu thức/phương trình dạng SymPy cho mỗi kết luận số.
Ta giải lại bằng SymPy và đối chiếu. Cách này bắt được phần lớn lỗi tính toán,
vì SymPy không "sai giống" LLM.
"""

from __future__ import annotations

from typing import Any

import sympy as sp


def _parse(expr: str) -> Any:
    return sp.sympify(expr, rational=True)


def check_equation(equation: str, var: str, claimed: list[str]) -> tuple[bool, dict]:
    """So khớp tập nghiệm LLM đưa ra với tập nghiệm SymPy tính được."""
    x = sp.Symbol(var)
    lhs, rhs = equation.split("=") if "=" in equation else (equation, "0")
    real = sp.solveset(sp.Eq(_parse(lhs), _parse(rhs)), x, domain=sp.S.Reals)
    try:
        real_set = {sp.nsimplify(s) for s in real}
    except TypeError:
        return False, {"reason": "tập nghiệm không hữu hạn", "sympy": str(real)}
    claim_set = {sp.nsimplify(_parse(c)) for c in claimed}
    ok = real_set == claim_set
    return ok, {"sympy": sorted(map(str, real_set)), "claimed": sorted(map(str, claim_set))}


def check_identity(lhs: str, rhs: str, assumptions: dict | None = None) -> tuple[bool, dict]:
    """Kiểm tra hai biểu thức bằng nhau (dùng cho bài rút gọn căn thức)."""
    diff = sp.simplify(_parse(lhs) - _parse(rhs))
    ok = diff == 0
    return ok, {"difference": str(diff)}


def check_value(expr: str, claimed: str) -> tuple[bool, dict]:
    diff = sp.simplify(_parse(expr) - _parse(claimed))
    return diff == 0, {"difference": str(diff)}


def verify_algebra(state) -> tuple[bool | None, dict]:
    """Điểm vào dùng trong Pipeline._verify.

    Solver nên xuất `state.verification.detail['algebra_checks']` dạng:
        [{"kind": "equation", "equation": "x**2-5*x+6", "var": "x",
          "claimed": ["2","3"]}, ...]
    """
    checks = state.verification.detail.get("algebra_checks") or []
    if not checks:
        return None, {"reason": "Solver không xuất phép kiểm tra nào"}

    results, all_ok = [], True
    for c in checks:
        try:
            if c["kind"] == "equation":
                ok, d = check_equation(c["equation"], c["var"], c["claimed"])
            elif c["kind"] == "identity":
                ok, d = check_identity(c["lhs"], c["rhs"])
            else:
                ok, d = check_value(c["expr"], c["claimed"])
        except Exception as e:
            ok, d = False, {"error": str(e)}
        all_ok &= ok
        results.append({"check": c, "ok": ok, **d})
    return all_ok, {"results": results}
