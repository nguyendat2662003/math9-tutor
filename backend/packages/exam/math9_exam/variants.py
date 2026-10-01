"""Biến thể đổi số cho các dạng bài tính toán.

Mỗi mẫu chọn số ngẫu nhiên (có hạt giống) sao cho đáp án "đẹp", rồi TÍNH đáp án
bằng số học chính xác (Fraction/SymPy) — không để LLM viết đáp án. Test kiểm
lại từng mẫu bằng SymPy theo cách độc lập (giải lại phương trình, thế nghiệm...).

Chỉ làm biến thể cho bài TÍNH RA ĐÁP SỐ. Bài hình chứng minh luôn lấy từ kho đề
thật — đổi số không tạo ra bài hình mới, và bài hình sinh tự động dễ sai đề.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction
from random import Random

SUP = {2: "²", 3: "³"}
FLIP = {"≤": "≥", "≥": "≤", "<": ">", ">": "<"}


class Reject(Exception):
    """Bộ số vừa chọn cho đề xấu (trùng phương án, số lẻ...) — chọn lại."""


@dataclass
class Variant:
    statement: str                 # đề tự luận / trả lời ngắn
    stem: str                      # câu dẫn trắc nghiệm
    answer: str                    # đáp án chuẩn, chấm bằng math9_verifier.answer
    choices: list[str]             # [đúng, nhiễu, nhiễu, nhiễu] — nội dung phương án
    solution: list[str]
    check: str = "set"             # "set": tập số khớp · "ordered": đúng thứ tự, vd (x; y)
    hint: str | None = None        # gợi ý cách nhập đáp án
    data: dict = field(default_factory=dict)   # tham số gốc, để test kiểm lại độc lập


@dataclass(frozen=True)
class Template:
    id: str
    topic: str
    goal_type: str
    difficulty: int
    formats: tuple[str, ...]
    make: Callable[[Random], Variant]

    def instantiate(self, rng: Random, tries: int = 50) -> Variant:
        for _ in range(tries):
            try:
                v = self.make(rng)
            except (Reject, ZeroDivisionError):
                continue
            if not v.choices or len(set(v.choices)) == len(v.choices) == 4:
                return v
        raise RuntimeError(f"Mẫu {self.id} không sinh được đề hợp lệ")


# ---------- định dạng số và biểu thức kiểu SGK ----------

def num(x: Fraction | int) -> str:
    """-3/4 -> '−3/4', 2.5 -> không dùng; phân số tối giản, dấu trừ Unicode."""
    x = Fraction(x)
    s = str(abs(x.numerator)) if x.denominator == 1 else f"{abs(x.numerator)}/{x.denominator}"
    return f"−{s}" if x < 0 else s


def dec(x: Fraction) -> str:
    """Số thập phân kiểu Việt Nam: 12.5 -> '12,5'."""
    s = f"{float(x):.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",").replace("-", "−")


def poly(coeffs: list, var: str = "x") -> str:
    """[2, -3, 1] -> '2x² − 3x + 1'."""
    deg = len(coeffs) - 1
    out = ""
    for i, c in enumerate(coeffs):
        c = Fraction(c)
        p = deg - i
        if c == 0:
            continue
        mono = "" if p == 0 else var if p == 1 else f"{var}{SUP[p]}"
        mag = abs(c)
        if not mono:
            body = num(mag)
        elif mag == 1:
            body = mono
        elif mag.denominator != 1:
            body = f"({num(mag)}){mono}"
        else:
            body = f"{num(mag)}{mono}"
        if not out:
            out = f"−{body}" if c < 0 else body
        else:
            out += f" − {body}" if c < 0 else f" + {body}"
    return out or "0"


def lin2(a: int, b: int) -> str:
    """a x + b y."""
    return poly([a, 0], "x").replace(" + 0", "") + (f" + {poly([b, 0], 'y')}" if b > 0 else f" − {poly([-b, 0], 'y')}")


def pick(rng: Random, lo: int, hi: int, exclude: tuple = (0,)) -> int:
    while True:
        v = rng.randint(lo, hi)
        if v not in exclude:
            return v


# ---------- các mẫu ----------

def _bpt(rng: Random) -> Variant:
    a = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5, 6])
    k = pick(rng, -6, 9, ())
    b = pick(rng, -9, 9)
    op = rng.choice(list(FLIP))
    c = a * k + b                                  # ax + b op c  <=>  x op' k
    op2 = FLIP[op] if a < 0 else op
    lhs = poly([a, b])
    ans = f"x {op2} {num(k)}"
    wrong_k = Fraction(c + b, a)
    if wrong_k == k:
        raise Reject
    sol = [
        f"{lhs} {op} {num(c)} ⇔ {poly([a, 0])} {op} {num(c)} − ({num(b)}) ⇔ {poly([a, 0])} {op} {num(c - b)}.",
        f"Chia hai vế cho {num(a)}" + (" (số âm nên đổi chiều bất đẳng thức)" if a < 0 else "") + f": x {op2} {num(k)}.",
        f"Vậy nghiệm của bất phương trình là {ans}.",
    ]
    return Variant(
        statement=f"Giải bất phương trình {lhs} {op} {num(c)}.",
        stem=f"Nghiệm của bất phương trình {lhs} {op} {num(c)} là",
        answer=ans,
        choices=[ans, f"x {FLIP[op2]} {num(k)}", f"x {op2} {num(-k)}" if k else f"x {op2} 1", f"x {op2} {num(wrong_k)}"],
        solution=sol, hint="Ví dụ: x ≤ 4 (gõ <= hoặc >= cũng được)",
        data={"a": a, "b": b, "c": c, "op": op, "k": k},
    )


def _pt_bac_hai(rng: Random) -> Variant:
    r1, r2 = sorted(rng.sample([v for v in range(-7, 8) if v], 2))
    a = rng.choice([1, 1, 1, 2, -1, 3])
    co = [a, -a * (r1 + r2), a * r1 * r2]
    delta = co[1] ** 2 - 4 * co[0] * co[2]
    sq = math.isqrt(delta)
    eq = f"{poly(co)} = 0"
    sol = [
        f"Δ = b² − 4ac = ({num(co[1])})² − 4·({num(co[0])})·({num(co[2])}) = {delta} > 0, √Δ = {sq}.",
        f"Phương trình có hai nghiệm phân biệt: x₁ = ({num(-co[1])} + {sq})/(2·{num(a)}) = {num(Fraction(-co[1] + sq, 2 * a))}; "
        f"x₂ = ({num(-co[1])} − {sq})/(2·{num(a)}) = {num(Fraction(-co[1] - sq, 2 * a))}.",
        f"Vậy tập nghiệm S = {{{num(r1)}; {num(r2)}}}.",
    ]
    return Variant(
        statement=f"Giải phương trình {eq}.",
        stem=f"Tập nghiệm của phương trình {eq} là",
        answer=f"x = {num(r1)}; x = {num(r2)}",
        choices=[f"S = {{{num(r1)}; {num(r2)}}}", f"S = {{{num(-r2)}; {num(-r1)}}}",
                 f"S = {{{num(r1)}; {num(-r2)}}}", f"S = {{{num(r1 + r2)}; {num(r1 * r2)}}}"],
        solution=sol, hint="Liệt kê các nghiệm, ví dụ: x = 2; x = −3",
        data={"coeffs": co, "roots": [r1, r2]},
    )


def _he_pt(rng: Random) -> Variant:
    x0, y0 = pick(rng, -5, 9, ()), pick(rng, -5, 9, ())
    while True:
        a1, b1, a2, b2 = (pick(rng, -5, 5) for _ in range(4))
        if a1 * b2 - a2 * b1 != 0:
            break
    c1, c2 = a1 * x0 + b1 * y0, a2 * x0 + b2 * y0
    e1, e2 = f"{lin2(a1, b1)} = {num(c1)}", f"{lin2(a2, b2)} = {num(c2)}"
    det = a1 * b2 - a2 * b1
    sol = [
        f"Nhân phương trình thứ nhất với {num(b2)}, phương trình thứ hai với {num(b1)} rồi trừ vế theo vế để khử y:",
        f"({num(a1 * b2)} − ({num(a2 * b1)}))x = {num(c1 * b2)} − ({num(c2 * b1)}) ⇔ {num(det)}x = {num(c1 * b2 - c2 * b1)} ⇔ x = {num(x0)}.",
        f"Thay x = {num(x0)} vào {e1} ta được y = {num(y0)}.",
        f"Vậy hệ có nghiệm duy nhất (x; y) = ({num(x0)}; {num(y0)}).",
    ]
    if (y0, x0) == (x0, y0) or (-x0, -y0) == (x0, y0):
        raise Reject
    return Variant(
        statement=f"Giải hệ phương trình:\n  {e1}\n  {e2}",
        stem=f"Nghiệm của hệ phương trình {{ {e1} ; {e2} }} là",
        answer=f"(x; y) = ({num(x0)}; {num(y0)})",
        choices=[f"({num(x0)}; {num(y0)})", f"({num(y0)}; {num(x0)})", f"({num(-x0)}; {num(-y0)})", f"({num(x0)}; {num(-y0)})"],
        solution=sol, check="ordered", hint="Nhập theo dạng (x; y), ví dụ (2; −1)",
        data={"a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2, "x": x0, "y": y0},
    )


_VIETE = [
    # (biểu thức, hàm của S, P, cách biến đổi, độ khó)
    ("x₁ + x₂", lambda s, p: s, "x₁ + x₂ = S", 1),
    ("x₁x₂", lambda s, p: p, "x₁x₂ = P", 1),
    ("x₁² + x₂²", lambda s, p: s * s - 2 * p, "x₁² + x₂² = (x₁ + x₂)² − 2x₁x₂ = S² − 2P", 1),
    ("1/x₁ + 1/x₂", lambda s, p: s / p, "1/x₁ + 1/x₂ = (x₁ + x₂)/(x₁x₂) = S/P", 2),
    ("(x₁ − x₂)²", lambda s, p: s * s - 4 * p, "(x₁ − x₂)² = (x₁ + x₂)² − 4x₁x₂ = S² − 4P", 2),
    ("x₁²x₂ + x₁x₂²", lambda s, p: s * p, "x₁²x₂ + x₁x₂² = x₁x₂(x₁ + x₂) = P·S", 2),
]


def _viete(level: int) -> Callable[[Random], Variant]:
    forms = [f for f in _VIETE if f[3] == level]

    def make(rng: Random) -> Variant:
        a = rng.choice([1, 1, 2])
        b, c = pick(rng, -9, 9), pick(rng, -9, 9)
        delta = b * b - 4 * a * c
        if delta <= 0 or math.isqrt(delta) ** 2 == delta:
            raise Reject                            # muốn nghiệm vô tỉ: buộc dùng Viète
        s, p = Fraction(-b, a), Fraction(c, a)
        expr, f, how, _ = rng.choice(forms)
        val = f(s, p)
        eq = f"{poly([a, b, c])} = 0"
        # Nhiễu từ lỗi hay gặp: nhầm dấu S (quên dấu trừ của −b/a), nhầm dấu P, lẫn S với P
        wrong = []
        for w in (f(-s, p), f(s, -p), f(-s, -p), s * s + 2 * p, p if val != p else s, -val):
            if w != val and w not in wrong:
                wrong.append(w)
        wrong = wrong[:3]
        sol = [
            f"Δ = ({num(b)})² − 4·{num(a)}·({num(c)}) = {delta} > 0 nên phương trình có hai nghiệm phân biệt x₁, x₂.",
            f"Theo định lí Viète: S = x₁ + x₂ = −b/a = {num(s)}; P = x₁x₂ = c/a = {num(p)}.",
            f"{how} = {num(val)}.",
        ]
        return Variant(
            statement=f"Cho phương trình {eq}. Chứng tỏ phương trình có hai nghiệm phân biệt x₁, x₂ và "
                      f"không giải phương trình, tính giá trị của biểu thức A = {expr}.",
            stem=f"Biết phương trình {eq} có hai nghiệm x₁, x₂. Giá trị của {expr} bằng",
            answer=f"A = {num(val)}",
            choices=[num(val)] + [num(w) for w in wrong],
            solution=sol, hint="Nhập giá trị của A, ví dụ: 13/2",
            data={"coeffs": [a, b, c], "expr": expr, "value": str(val)},
        )

    return make


_A_PARABOL = [Fraction(1, 2), Fraction(-1, 2), 2, -2, Fraction(1, 4), 3, -1, Fraction(1, 3), -3]


def _parabol(rng: Random) -> Variant:
    a = Fraction(rng.choice(_A_PARABOL))
    t = pick(rng, -4, 4)
    y0 = a * t * t
    if y0.denominator != 1:
        raise Reject
    if rng.random() < 0.5:
        sol = [f"Điểm M({num(t)}; {num(y0)}) thuộc đồ thị nên {num(y0)} = a·({num(t)})² = {t * t}a.",
               f"Suy ra a = {num(y0)}/{t * t} = {num(a)} (thỏa mãn a ≠ 0)."]
        return Variant(
            statement=f"Cho hàm số y = ax² (a ≠ 0). Tìm a, biết đồ thị hàm số đi qua điểm M({num(t)}; {num(y0)}).",
            stem=f"Đồ thị hàm số y = ax² đi qua điểm M({num(t)}; {num(y0)}). Giá trị của a là",
            answer=f"a = {num(a)}",
            choices=[num(a), num(-a), num(y0 * t * t) if abs(y0 * t * t) != abs(a) else num(a + 1), num(Fraction(y0, t))],
            solution=sol, hint="Nhập giá trị của a",
            data={"kind": "find_a", "t": t, "y": str(y0), "a": str(a)},
        )
    sol = [f"Thay x = {num(t)} vào y = {poly([a, 0, 0])}: y = {num(a)}·({num(t)})² = {num(y0)}."]
    return Variant(
        statement=f"Cho hàm số y = {poly([a, 0, 0])}. Tính giá trị của hàm số tại x = {num(t)}.",
        stem=f"Cho hàm số y = {poly([a, 0, 0])}. Giá trị của hàm số tại x = {num(t)} là",
        answer=f"y = {num(y0)}",
        choices=[num(y0), num(-y0), num(a * 2 * t), num(a * t)],
        solution=sol, hint="Nhập giá trị của y",
        data={"kind": "eval", "a": str(a), "t": t, "y": str(y0)},
    )


def _tham_so(rng: Random) -> Variant:
    p, q, r = pick(rng, -6, 6), pick(rng, -9, 9), pick(rng, -5, 5)
    m = q + p * r - r * r               # x² − p·x + m − q = 0 có nghiệm x = r
    eq = f"x² {'−' if p > 0 else '+'} {abs(p) if abs(p) != 1 else ''}x + m {'−' if q > 0 else '+'} {abs(q)} = 0"
    sol = [f"x = {num(r)} là nghiệm nên ({num(r)})² − ({num(p)})·({num(r)}) + m − ({num(q)}) = 0.",
           f"⇔ {r * r - p * r - q} + m = 0 ⇔ m = {num(m)}."]
    return Variant(
        statement=f"Cho phương trình {eq} (m là tham số). Tìm m để phương trình có một nghiệm x = {num(r)}.",
        stem=f"Phương trình {eq} (m là tham số) có một nghiệm x = {num(r)} khi",
        answer=f"m = {num(m)}",
        choices=[f"m = {num(m)}", f"m = {num(-m)}" if m else "m = 1", f"m = {num(q - p * r - r * r)}", f"m = {num(q + p * r + r * r)}"],
        solution=sol, hint="Nhập giá trị của m",
        data={"p": p, "q": q, "r": r, "m": m},
    )


def _gia_tri_can(rng: Random) -> Variant:
    p, q = rng.randint(1, 5), rng.randint(1, 5)
    k = pick(rng, 2, 9, (q,))
    x = k * k
    val = Fraction(k + p, k - q)
    expr = f"A = (√x + {p})/(√x − {q})"
    sol = [f"x = {x} thỏa mãn điều kiện x ≥ 0, x ≠ {q * q}; khi đó √x = {k}.",
           f"A = ({k} + {p})/({k} − {q}) = {num(val)}."]
    return Variant(
        statement=f"Cho biểu thức {expr} với x ≥ 0, x ≠ {q * q}. Tính giá trị của A khi x = {x}.",
        stem=f"Giá trị của biểu thức {expr} tại x = {x} là",
        answer=f"A = {num(val)}",
        choices=[num(val), num(Fraction(x + p, x - q)), num(Fraction(k + p, k + q)), num(Fraction(k - p, k - q))],
        solution=sol, hint="Nhập giá trị của A",
        data={"p": p, "q": q, "x": x, "value": str(val)},
    )


def _lap_he(rng: Random) -> Variant:
    if rng.random() < 0.5:
        a, b = rng.randrange(100, 501, 20), rng.randrange(100, 501, 20)
        pa, pb = rng.sample([10, 15, 20, 25, 30], 2)
        if a == b or (a * pa) % 100 or (b * pb) % 100:
            raise Reject
        n, m = a + b, a + b + (a * pa + b * pb) // 100
        sol = [
            "Gọi x, y lần lượt là số sản phẩm tổ A, tổ B làm trong tháng 3 (x, y ∈ ℕ*).",
            f"Ta có hệ: x + y = {n} và (100% + {pa}%)x + (100% + {pb}%)y = {m}, "
            f"tức {dec(Fraction(100 + pa, 100))}x + {dec(Fraction(100 + pb, 100))}y = {m}.",
            f"Trừ vế theo vế cho phương trình thứ nhất: {dec(Fraction(pa, 100))}x + {dec(Fraction(pb, 100))}y = {m - n}; "
            f"thế y = {n} − x vào rồi giải.",
            f"Giải ra x = {a}, y = {b} (thỏa mãn).",
            f"Vậy tháng 3 tổ A làm được {a} sản phẩm, tổ B làm được {b} sản phẩm.",
        ]
        stmt = (f"Tháng 3, hai tổ A và B sản xuất được {n} sản phẩm. Tháng 4, tổ A tăng {pa}%, tổ B tăng {pb}% "
                f"so với tháng 3 nên cả hai tổ sản xuất được {m} sản phẩm. Hỏi tháng 3 mỗi tổ sản xuất được bao nhiêu sản phẩm?")
        ans = f"Tổ A: {a} sản phẩm; tổ B: {b} sản phẩm"
        data = {"kind": "sx", "n": n, "m": m, "pa": pa, "pb": pb, "x": a, "y": b}
    else:
        a, b = rng.randint(4, 20), rng.randint(4, 20)
        pa, pb = rng.sample([5, 6, 7, 8, 9, 10, 12, 15], 2)
        if a == b:
            raise Reject
        n, m = a + b, a * pa + b * pb
        sol = [
            "Gọi x, y lần lượt là số bông hoa hồng và hoa cúc đã mua (x, y ∈ ℕ*).",
            f"Ta có hệ: x + y = {n} và {pa}x + {pb}y = {m}.",
            f"Từ phương trình thứ nhất y = {n} − x, thế vào: {pa}x + {pb}({n} − x) = {m} ⇔ {pa - pb}x = {m - pb * n} ⇔ x = {a}.",
            f"Suy ra y = {b} (thỏa mãn). Vậy người đó mua {a} bông hồng và {b} bông cúc.",
        ]
        stmt = (f"Một người mua {n} bông hoa gồm hoa hồng và hoa cúc hết tổng số tiền là {m} nghìn đồng. "
                f"Biết giá mỗi bông hoa hồng là {pa} nghìn đồng, mỗi bông hoa cúc là {pb} nghìn đồng. "
                "Hỏi người đó đã mua bao nhiêu bông hoa mỗi loại?")
        ans = f"Hoa hồng: {a} bông; hoa cúc: {b} bông"
        data = {"kind": "hoa", "n": n, "m": m, "pa": pa, "pb": pb, "x": a, "y": b}
    return Variant(statement=stmt, stem=stmt, answer=ans, choices=[], solution=sol,
                   check="ordered", hint="Nhập theo đúng thứ tự đề hỏi, ví dụ: 15; 10", data=data)


_EVENTS = [
    ("là số chia hết cho 2", lambda v: v % 2 == 0),
    ("là số chia hết cho 3", lambda v: v % 3 == 0),
    ("là số chia hết cho 5", lambda v: v % 5 == 0),
    ("là số nguyên tố", lambda v: v > 1 and all(v % d for d in range(2, math.isqrt(v) + 1))),
    ("là số chính phương", lambda v: math.isqrt(v) ** 2 == v),
]


def _xac_suat(rng: Random) -> Variant:
    n = rng.randint(10, 30)
    name, ok = rng.choice(_EVENTS)
    fav = [v for v in range(1, n + 1) if ok(v)]
    pr = Fraction(len(fav), n)
    shown = ", ".join(map(str, fav))
    sol = [f"Không gian mẫu gồm {n} kết quả có thể, đồng khả năng.",
           f"Các kết quả thuận lợi cho biến cố A: {shown} — có {len(fav)} kết quả.",
           f"P(A) = {len(fav)}/{n} = {num(pr)}."]
    stmt = (f"Một hộp có {n} tấm thẻ cùng loại được đánh số 1, 2, …, {n}. Rút ngẫu nhiên một tấm thẻ từ hộp. "
            f"Tính xác suất của biến cố A: \"Số ghi trên thẻ {name}\".")
    return Variant(
        statement=stmt,
        stem=f"Một hộp có {n} tấm thẻ cùng loại được đánh số 1, 2, …, {n}. Rút ngẫu nhiên một tấm thẻ. "
             f"Xác suất để số ghi trên thẻ {name} bằng",
        answer=f"P(A) = {num(pr)}",
        choices=[num(pr), num(1 - pr), num(Fraction(len(fav), n - 1)), num(Fraction(len(fav) + 1, n))],
        solution=sol, hint="Nhập phân số tối giản, ví dụ: 2/5",
        data={"n": n, "event": name, "p": str(pr)},
    )


_SURVEYS = [
    ("môn thể thao yêu thích", ["Bóng đá", "Cầu lông", "Bơi lội", "Cờ vua"]),
    ("phương tiện đến trường", ["Xe đạp", "Xe buýt", "Đi bộ", "Bố mẹ đưa"]),
    ("loại sách yêu thích", ["Truyện tranh", "Khoa học", "Văn học", "Lịch sử"]),
]


def _tan_so(rng: Random) -> Variant:
    n = rng.choice([20, 25, 40, 50])
    what, cats = rng.choice(_SURVEYS)
    cuts = sorted(rng.sample(range(1, n), 3))
    counts = [cuts[0], cuts[1] - cuts[0], cuts[2] - cuts[1], n - cuts[2]]
    i = rng.randrange(4)
    pct = [Fraction(c * 100, n) for c in counts]
    table = "; ".join(f"{c}: {k}" for c, k in zip(cats, counts))
    sol = [f"Tần số của nhóm \"{cats[i]}\" là {counts[i]}; cỡ mẫu n = {n}.",
           f"Tần số tương đối = {counts[i]}/{n} · 100% = {dec(pct[i])}%."]
    others = [dec(pct[j]) + "%" for j in range(4) if j != i]
    return Variant(
        statement=f"Kết quả khảo sát {what} của {n} học sinh như sau: {table}. "
                  f"Tính tần số tương đối (theo phần trăm) của nhóm \"{cats[i]}\".",
        stem=f"Khảo sát {what} của {n} học sinh: {table}. Tần số tương đối của nhóm \"{cats[i]}\" là",
        answer=f"{dec(pct[i])}%",
        choices=[f"{dec(pct[i])}%"] + others,
        solution=sol, hint="Nhập theo phần trăm, ví dụ: 28%",
        data={"n": n, "counts": counts, "i": i},
    )


_TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (6, 8, 10), (9, 12, 15)]
_RATIOS = {
    "sin B": lambda ab, ac, bc: Fraction(ac, bc), "cos B": lambda ab, ac, bc: Fraction(ab, bc),
    "tan B": lambda ab, ac, bc: Fraction(ac, ab), "sin C": lambda ab, ac, bc: Fraction(ab, bc),
    "cos C": lambda ab, ac, bc: Fraction(ac, bc), "tan C": lambda ab, ac, bc: Fraction(ab, ac),
}


def _ti_so(rng: Random) -> Variant:
    ab, ac, bc = rng.choice(_TRIPLES)
    if rng.random() < 0.5:
        ab, ac = ac, ab
    name = rng.choice(list(_RATIOS))
    val = _RATIOS[name](ab, ac, bc)
    wrong = sorted({v for v in (Fraction(ab, bc), Fraction(ac, bc), Fraction(ac, ab), Fraction(ab, ac)) if v != val})
    if len(wrong) < 3:
        raise Reject
    sol = [f"Tam giác ABC vuông tại A: BC² = AB² + AC² = {ab}² + {ac}² = {bc * bc} ⇒ BC = {bc} cm.",
           f"{name} = {'AC/BC' if name in ('sin B', 'cos C') else 'AB/BC' if name in ('cos B', 'sin C') else 'AC/AB' if name == 'tan B' else 'AB/AC'} = {num(val)}."]
    return Variant(
        statement=f"Cho tam giác ABC vuông tại A có AB = {ab} cm, AC = {ac} cm. Tính {name}.",
        stem=f"Cho tam giác ABC vuông tại A có AB = {ab} cm, AC = {ac} cm. Khi đó {name} bằng",
        answer=f"{name} = {num(val)}",
        choices=[num(val)] + [num(w) for w in wrong[:3]],
        solution=sol, hint="Nhập phân số tối giản, ví dụ: 4/5",
        data={"ab": ab, "ac": ac, "ratio": name, "value": str(val)},
    )


def _the_tich(rng: Random) -> Variant:
    shape = rng.choice(["trụ", "nón", "cầu"])
    r = rng.randint(2, 9)
    h = rng.randint(3, 15)
    if shape == "trụ":
        v = Fraction(r * r * h)
        desc, formula = f"hình trụ có bán kính đáy {r} cm và chiều cao {h} cm", f"V = πr²h = π·{r}²·{h}"
        wrong = [Fraction(2 * r * h), Fraction(r * r * h, 3), Fraction(r * h)]
    elif shape == "nón":
        v = Fraction(r * r * h, 3)
        desc, formula = f"hình nón có bán kính đáy {r} cm và chiều cao {h} cm", f"V = (1/3)πr²h = (1/3)·π·{r}²·{h}"
        wrong = [Fraction(r * r * h), Fraction(r * h, 3), Fraction(2 * r * r * h, 3)]
    else:
        v = Fraction(4 * r ** 3, 3)
        desc, formula = f"hình cầu có bán kính {r} cm", f"V = (4/3)πR³ = (4/3)·π·{r}³"
        wrong = [Fraction(4 * r * r), Fraction(r ** 3), Fraction(4 * r ** 3)]
    if v.denominator != 1 and shape != "cầu":
        raise Reject
    ans = f"V = {num(v)}π cm³"
    return Variant(
        statement=f"Tính thể tích của {desc}. (Để kết quả dưới dạng chứa π.)",
        stem=f"Thể tích của {desc} là",
        answer=ans,
        choices=[f"{num(v)}π cm³"] + [f"{num(w)}π cm³" for w in wrong],
        solution=[f"{formula} = {num(v)}π (cm³)."], hint="Nhập hệ số của π, ví dụ: 48π",
        data={"shape": shape, "r": r, "h": h, "coef": str(v)},
    )


TEMPLATES: list[Template] = [
    Template("bpt-bac-nhat", "ALG-2", "prove_inequality", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _bpt),
    Template("pt-bac-hai", "ALG-6", "solve_equation", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _pt_bac_hai),
    Template("he-pt", "ALG-1", "solve_system", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _he_pt),
    Template("viete-co-ban", "ALG-6", "evaluate_root_expression", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _viete(1)),
    Template("viete-bien-doi", "ALG-6", "evaluate_root_expression", 2, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _viete(2)),
    Template("parabol", "ALG-6", "analyze_function", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _parabol),
    Template("tham-so-nghiem", "ALG-6", "find_parameter", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _tham_so),
    Template("gia-tri-can", "ALG-3", "simplify_expression", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _gia_tri_can),
    Template("lap-he", "ALG-1", "word_problem", 2, ("tra_loi_ngan", "tu_luan"), _lap_he),
    Template("xac-suat-the", "PRO-8", "compute_probability", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _xac_suat),
    Template("tan-so-tuong-doi", "STA-7", "analyze_statistics", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _tan_so),
    Template("ti-so-luong-giac", "GEO-4", "compute_length", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _ti_so),
    Template("the-tich", "GEO-10", "compute_area", 1, ("trac_nghiem", "tra_loi_ngan", "tu_luan"), _the_tich),
]
TEMPLATE_BY_ID = {t.id: t for t in TEMPLATES}
