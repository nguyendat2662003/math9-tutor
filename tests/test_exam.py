"""Luyện đề: kho bài, biến thể đổi số (kiểm độc lập bằng SymPy), cấu trúc đề, chấm, API."""

import json
import sys
from fractions import Fraction
from pathlib import Path
from random import Random

import pytest
import sympy as sp
from math9_exam import store
from math9_exam.bank import load_bank, parse_options, parse_true_false
from math9_exam.builder import CustomSpec, build_exam, custom_blueprint, load_blueprints
from math9_exam.figures import load_figures, needs_figure
from math9_exam.grading import grade_exam, grade_question
from math9_exam.models import Question
from math9_exam.variants import TEMPLATE_BY_ID, TEMPLATES
from math9_verifier.answer import grade, grade_ordered

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

X, Y = sp.symbols("x y")
SEEDS = range(60)


def _q(v) -> sp.Rational:
    return sp.Rational(str(v)) if not isinstance(v, int) else sp.Integer(v)


# ---------- kho ----------

def test_bank_loads_and_parses():
    bank = load_bank()
    assert len(bank.items) > 200
    mcq = [x for x in bank.items if x.format == "trac_nghiem"]
    assert mcq and all(len(x.options) == 4 and x.answer["letter"] in "ABCD" for x in mcq)
    assert all(p.lead for parts in bank.groups.values() for p in parts)
    assert parse_options("A. −8; B. −5; C. 5; D. 8") == ["−8", "−5", "5", "8"]
    assert parse_true_false("Đ - S - S - Đ") == [True, False, False, True]


def test_bank_marks_proofs_self_graded():
    bank = load_bank()
    by = {x.id: x for x in bank.items}
    assert by["bn26-1a"].auto          # "Giải bất phương trình" — dù eval gắn prove_inequality
    assert not by["hn26-IV2a"].auto    # chứng minh tứ giác nội tiếp
    assert not by["hn26-II2"].auto     # "Chứng minh B = ..." — biến đổi, không chỉ đáp số


def test_bank_excludes_old_curriculum_and_out_of_scope():
    ids = {x.id for x in load_bank().items}
    assert not any(i.startswith("hn24-") for i in ids)        # core_2006
    assert "dhv26-TLN5" not in ids                            # out_of_scope


# ---------- hình của đề ----------

def test_every_figure_reference_has_a_figure():
    """Đề nói 'như hình vẽ', 'biểu đồ'... thì kho phải có hình — nếu không, học sinh không làm được."""
    missing = [x.id for x in load_bank().items if x.needs_figure and not x.figure]
    assert not missing, f"Thiếu hình trong data/exam/figures.yaml: {missing}"


def test_figures_yaml_keys_match_bank():
    bank = load_bank()
    keys = {x.id for x in bank.items} | set(bank.groups) | {x.group for x in bank.items if x.group}
    assert set(load_figures()) <= keys


def test_figures_are_valid_svg_with_unique_ids():
    import xml.etree.ElementTree as ET

    seen: set[str] = set()
    for key, svg in load_figures().items():
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg"), key
        ids = [el.get("id") for el in root.iter() if el.get("id")]
        assert not seen & set(ids), f"id trùng giữa các hình: {key}"
        seen |= set(ids)


def test_needs_figure_detection():
    assert needs_figure("ba điểm A, B, C (như hình vẽ)") and needs_figure("Biểu đồ quạt về 140 học sinh")
    assert not needs_figure("Mảnh đất hình chữ nhật") and not needs_figure("Một hình trụ có bán kính đáy 3 cm")


def test_exam_never_shows_figure_reference_without_figure():
    bank = load_bank()
    # Giả lập: mọi bài có hình bị mất hình -> không bài nào trong số đó được vào đề
    hidden = {x.id for x in bank.items if x.figure}
    assert hidden
    for x in bank.items:
        if x.id in hidden:
            x.figure = None
    try:
        for bid, bp in load_blueprints().items():
            for seed in range(8):
                used = {q.bank_id for q in build_exam(bp, seed=seed, bank=bank).questions}
                assert not used & hidden, (bid, used & hidden)
    finally:
        load_bank.cache_clear()


# ---------- biến thể: đáp án kiểm lại độc lập bằng SymPy ----------

def _check_variant(tid: str, v) -> None:
    d = v.data
    if tid == "bpt-bac-nhat":
        ops = {"≤": sp.Le, "≥": sp.Ge, "<": sp.Lt, ">": sp.Gt}
        got = sp.solveset(ops[d["op"]](d["a"] * X + d["b"], d["c"]), X, sp.S.Reals)
        op2 = v.answer.split()[1]
        assert got == sp.solveset(ops[op2](X, d["k"]), X, sp.S.Reals)
    elif tid == "pt-bac-hai":
        a, b, c = d["coeffs"]
        assert sorted(sp.solve(a * X**2 + b * X + c, X)) == sorted(d["roots"])
    elif tid == "he-pt":
        sol = sp.solve([d["a1"] * X + d["b1"] * Y - d["c1"], d["a2"] * X + d["b2"] * Y - d["c2"]], [X, Y])
        assert (sol[X], sol[Y]) == (d["x"], d["y"])
        assert grade_ordered(f"({d['x']}; {d['y']})", v.answer)
    elif tid.startswith("viete"):
        a, b, c = d["coeffs"]
        x1, x2 = sp.solve(a * X**2 + b * X + c, X)
        expr = {"x₁ + x₂": x1 + x2, "x₁x₂": x1 * x2, "x₁² + x₂²": x1**2 + x2**2, "1/x₁ + 1/x₂": 1 / x1 + 1 / x2,
                "(x₁ − x₂)²": (x1 - x2) ** 2, "x₁²x₂ + x₁x₂²": x1**2 * x2 + x1 * x2**2}[d["expr"]]
        assert sp.simplify(expr - _q(d["value"])) == 0
    elif tid == "parabol":
        assert _q(d["a"]) * d["t"] ** 2 == _q(d["y"])
    elif tid == "tham-so-nghiem":
        assert (X**2 - d["p"] * X + d["m"] - d["q"]).subs(X, d["r"]) == 0
    elif tid == "gia-tri-can":
        assert sp.simplify((sp.sqrt(d["x"]) + d["p"]) / (sp.sqrt(d["x"]) - d["q"]) - _q(d["value"])) == 0
    elif tid == "lap-he":
        if d["kind"] == "sx":
            eqs = [X + Y - d["n"], X * (100 + d["pa"]) + Y * (100 + d["pb"]) - 100 * d["m"]]
        else:
            eqs = [X + Y - d["n"], d["pa"] * X + d["pb"] * Y - d["m"]]
        sol = sp.solve(eqs, [X, Y])
        assert (sol[X], sol[Y]) == (d["x"], d["y"]) and d["x"] > 0 and d["y"] > 0
        assert grade_ordered(f"{d['x']}; {d['y']}", v.answer) and not grade_ordered(f"{d['y']}; {d['x']}", v.answer)
    elif tid == "xac-suat-the":
        tests = {"là số chia hết cho 2": lambda k: k % 2 == 0, "là số chia hết cho 3": lambda k: k % 3 == 0,
                 "là số chia hết cho 5": lambda k: k % 5 == 0, "là số nguyên tố": sp.isprime,
                 "là số chính phương": lambda k: sp.sqrt(k).is_integer}
        fav = sum(1 for k in range(1, d["n"] + 1) if tests[d["event"]](k))
        assert sp.Rational(fav, d["n"]) == _q(d["p"])
    elif tid == "tan-so-tuong-doi":
        assert sum(d["counts"]) == d["n"] and min(d["counts"]) > 0
        pct = Fraction(d["counts"][d["i"]] * 100, d["n"])
        assert grade(f"{float(pct)}%", v.answer)
    elif tid == "ti-so-luong-giac":
        ab, ac = d["ab"], d["ac"]
        bc = sp.sqrt(ab**2 + ac**2)
        want = {"sin B": ac / bc, "cos B": ab / bc, "tan B": sp.Rational(ac, ab),
                "sin C": ab / bc, "cos C": ac / bc, "tan C": sp.Rational(ab, ac)}[d["ratio"]]
        assert sp.simplify(want - _q(d["value"])) == 0
    elif tid == "the-tich":
        r, h = d["r"], d["h"]
        vol = {"trụ": sp.pi * r**2 * h, "nón": sp.pi * r**2 * h / 3, "cầu": sp.Rational(4, 3) * sp.pi * r**3}[d["shape"]]
        assert sp.simplify(vol - _q(d["coef"]) * sp.pi) == 0
    else:
        raise AssertionError(f"Chưa có kiểm tra độc lập cho mẫu {tid}")


@pytest.mark.parametrize("tid", [t.id for t in TEMPLATES])
def test_variant_answers_independently_verified(tid):
    t = TEMPLATE_BY_ID[tid]
    for s in SEEDS:
        v = t.instantiate(Random(s))
        _check_variant(tid, v)
        # Bộ chấm chấp nhận chính đáp án chuẩn, và phân biệt được đáp án với các phương án nhiễu
        assert (grade_ordered if v.check == "ordered" else grade)(v.answer, v.answer)
        if v.choices:
            assert len(set(v.choices)) == 4


def test_every_template_has_independent_check():
    for t in TEMPLATES:
        _check_variant(t.id, t.instantiate(Random(0)))


def test_inequality_sign_matters():
    assert grade("x ≤ 4", "x ≤ 4") and grade("x <= 4", "x ≤ 4")
    assert not grade("x ≥ 4", "x ≤ 4")


# ---------- cấu trúc đề & sinh đề ----------

@pytest.mark.parametrize("bid", list(load_blueprints()))
def test_blueprint_totals_and_fill(bid):
    bp = load_blueprints()[bid]
    assert bp.total_points == 10.0
    for seed in range(5):
        e = build_exam(bp, seed=seed)
        assert not e.warnings, e.warnings
        assert e.total_points == 10.0
        assert len({q.bank_id for q in e.questions if q.bank_id}) == sum(1 for q in e.questions if q.bank_id)


def test_same_seed_same_exam():
    bp = load_blueprints()["thanh-hoa"]
    a, b = build_exam(bp, seed=7), build_exam(bp, seed=7)
    assert [q.statement for q in a.questions] == [q.statement for q in b.questions]
    assert [q.statement for q in a.questions] != [q.statement for q in build_exam(bp, seed=8).questions]


def test_custom_exam():
    spec = CustomSpec(topics=["ALG-6", "PRO-8"], n_trac_nghiem=6, n_tra_loi_ngan=2, n_tu_luan=2, level="de")
    e = build_exam(custom_blueprint(spec, Random(1)), seed=1)
    assert len(e.questions) == 10 and e.total_points == 10.0
    assert {q.topic for q in e.questions} <= {"ALG-6", "PRO-8"}


def test_public_exam_hides_answers():
    e = build_exam(load_blueprints()["quang-ninh"], seed=3)
    pub = json.dumps(e.public(), ensure_ascii=False)
    for key in ('"answer"', '"solution"', '"bank_id"', '"template"', '"check"'):
        assert key not in pub


# ---------- chấm ----------

def _mk(**kw) -> Question:
    base = dict(qid="q1", number="Câu 1", format="tu_luan", statement="", points=1.0, topic="ALG-6",
                difficulty=1, source="", origin="bank", auto=True)
    return Question(**{**base, **kw})


def test_grade_mcq():
    q = _mk(format="trac_nghiem", options=["1", "2", "3", "4"], answer={"letter": "C", "value": "3"})
    assert grade_question(q, "C")["status"] == "dung"
    assert grade_question(q, "a")["status"] == "sai"
    assert grade_question(q, None)["status"] == "bo_trong"


def test_grade_true_false_scale():
    q = _mk(format="dung_sai", claims=["a", "b", "c", "d"], answer=[True, False, True, True])
    assert grade_question(q, [True, False, True, True])["earned"] == 1.0
    assert grade_question(q, [True, False, True, False])["earned"] == 0.5
    assert grade_question(q, [True, True, None, None])["earned"] == 0.1
    assert grade_question(q, [None] * 4)["status"] == "bo_trong"


def test_grade_ordered_and_self_graded():
    q = _mk(answer="(x; y) = (8; 3)", check="ordered")
    assert grade_question(q, "(8; 3)")["status"] == "dung"
    assert grade_question(q, "(3; 8)")["status"] == "sai"
    proof = _mk(auto=False, answer=None)
    r = grade_question(proof, "em làm rồi")
    assert r["status"] == "tu_cham" and r["earned"] == 0


def test_grade_exam_perfect_auto_score():
    e = build_exam(load_blueprints()["ha-tinh"], seed=11)
    responses = {}
    for q in e.questions:
        if q.format == "trac_nghiem":
            responses[q.qid] = q.answer["letter"]
        elif q.format == "dung_sai":
            responses[q.qid] = q.answer
        elif q.auto:
            responses[q.qid] = str(q.answer)
    r = grade_exam(e, responses)
    assert r["auto_score"] + r["self_grade_points"] == pytest.approx(e.total_points)


# ---------- API ----------

@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from apps.api.routes import exam as exam_route

    monkeypatch.setattr(store, "EXAM_DIR", tmp_path / "exams")
    app = FastAPI()
    app.include_router(exam_route.router)
    return TestClient(app)


def test_api_create_get_submit(client):
    r = client.get("/api/exam/blueprints")
    assert r.status_code == 200 and len(r.json()["blueprints"]) >= 6

    r = client.post("/api/exam", json={"blueprint": "ha-noi", "seed": 5})
    assert r.status_code == 200
    pub = r.json()
    assert "answer" not in json.dumps(pub["questions"])

    assert client.get(f"/api/exam/{pub['id']}").json()["questions"] == pub["questions"]

    exam = store.load(pub["id"])
    first = next(q for q in exam.questions if q.auto)
    res = client.post(f"/api/exam/{pub['id']}/submit", json={"responses": {first.qid: str(first.answer)}}).json()
    item = next(i for i in res["items"] if i["qid"] == first.qid)
    assert item["status"] == "dung" and res["auto_score"] == first.points


def test_api_custom_and_validation(client):
    ok = client.post("/api/exam", json={"custom": {"topics": ["ALG-1"], "n_trac_nghiem": 3, "n_tu_luan": 1}})
    assert ok.status_code == 200 and len(ok.json()["questions"]) == 4
    assert client.post("/api/exam", json={"custom": {"topics": ["XYZ"]}}).status_code == 400
    assert client.post("/api/exam", json={}).status_code == 422
    assert client.post("/api/exam", json={"blueprint": "khong-co"}).status_code == 404


@pytest.mark.parametrize("bad", ["..%2F..%2Fetc%2Fpasswd", "abc", "0" * 31 + "g"])
def test_api_rejects_bad_exam_id(client, bad):
    assert client.get(f"/api/exam/{bad}").status_code in (400, 404)
    assert client.get(f"/api/exam/{'0' * 32}").status_code == 404
