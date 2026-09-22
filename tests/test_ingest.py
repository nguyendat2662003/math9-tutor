"""Kiểm thử khâu nhập dữ liệu — chạy offline, không cần mạng."""

import pytest
from math9_ingest.dedup import dedupe, minhash, similarity
from math9_ingest.normalize import fix_decimal_comma, normalize, strip_noise
from math9_ingest.quality import Verdict, assess
from math9_ingest.segment import split_problems

SAMPLE = """
SỞ GIÁO DỤC VÀ ĐÀO TẠO HÀ NỘI
ĐỀ CHÍNH THỨC
KỲ THI TUYỂN SINH LỚP 10 THPT NĂM HỌC 2024-2025
Môn thi: TOÁN
Trang 1/2

Bài 1. (2,0 điểm)
Cho biểu thức A = (x + 2)/(x - 1) với x khác 1.
a) Rút gọn biểu thức A khi x = 2,5.
b) Tìm x để A > 0.

Bài 2. (2,5 điểm)
Giải phương trình x^2 - 5x + 6 = 0.

Bài 3. (3,0 điểm)
Cho đường tròn (O) và điểm A nằm ngoài đường tròn. Kẻ hai tiếp tuyến AB, AC
với đường tròn (B, C là các tiếp điểm).
a) Chứng minh tứ giác ABOC nội tiếp một đường tròn.
b) Chứng minh OA vuông góc với BC.
c) Gọi H là giao điểm của OA và BC. Chứng minh H là trung điểm của BC.

Họ và tên thí sinh: ................ Số báo danh: ..........
------ HẾT ------
"""


def test_strip_noise_removes_headers():
    out = strip_noise(SAMPLE)
    assert "Trang 1/2" not in out
    assert "Số báo danh" not in out
    assert "ĐỀ CHÍNH THỨC" not in out
    assert "tuyến AB, AC" in out          # nội dung toán phải còn nguyên


def test_decimal_comma_converted_but_score_preserved():
    assert fix_decimal_comma("x = 2,5") == "x = 2.5"
    assert fix_decimal_comma("(2,0 điểm)") == "(2,0 điểm)"   # mốc điểm giữ nguyên
    assert fix_decimal_comma("x1, x2 là nghiệm") == "x1, x2 là nghiệm"


def test_split_into_problems_and_parts():
    probs = split_problems(normalize(SAMPLE))
    assert len(probs) == 3
    assert [len(p.parts) for p in probs] == [2, 1, 3]
    assert probs[0].score == 2.0
    assert probs[2].parts[2].label == "c"


def test_geometry_detected():
    probs = split_problems(normalize(SAMPLE))
    assert probs[2].likely_geometry is True
    assert probs[1].likely_geometry is False   # phương trình bậc hai, không phải hình


def test_quality_accepts_clean_and_rejects_junk():
    probs = split_problems(normalize(SAMPLE))
    assert assess(probs[1]).verdict in (Verdict.AUTO_ACCEPT, Verdict.NEEDS_REVIEW)

    from math9_ingest.segment import Part, Problem
    junk = Problem(number="9", stem="ab", parts=[Part("a", "cd")])
    assert assess(junk).verdict == Verdict.REJECT


def test_quality_flags_broken_font():
    from math9_ingest.segment import Part, Problem
    broken = Problem(
        number="1", stem="",
        parts=[Part("a", "Gi(cid:97)i ph(cid:117)ong tr(cid:105)nh x 2 5 x + 6 = 0 v a t i n h")],
    )
    r = assess(broken)
    assert r.verdict in (Verdict.NEEDS_OCR, Verdict.REJECT)
    assert r.flags


def test_dedupe_catches_reposted_exam():
    """Cùng một bài đăng lại với khác biệt định dạng phải bị gộp."""
    a = "Bài 1. Giải phương trình x^2 - 5x + 6 = 0."
    b = "Câu 3: Giải phương trình  x^2 – 5x + 6 = 0"     # khác số hiệu, khác dấu gạch
    c = "Bài 1. Cho tam giác ABC vuông tại A, tính độ dài đường cao AH."
    res = dedupe([a, b, c])
    assert len(res.kept) == 2
    assert 1 in res.duplicates


def test_minhash_similarity_scale():
    a = minhash("Cho đường tròn tâm O bán kính R và điểm A nằm ngoài")
    b = minhash("Cho đường tròn tâm O bán kính R và điểm A nằm ngoài.")
    c = minhash("Giải hệ phương trình hai ẩn bằng phương pháp thế")
    assert similarity(a, b) > 0.9
    assert similarity(a, c) < 0.5
