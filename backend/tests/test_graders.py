from evals.graders.answer import grade


def test_unicode_minus_and_separators():
    assert grade("x = -2 hoặc x = 4", "x = 4; x = −2")
    assert not grade("x = 2 hoặc x = 4", "x = 4; x = −2")


def test_decimal_comma():
    assert grade("2.5", "2,5")


def test_set_notation_equivalent():
    assert grade("S = {2; 3}", "x = 2 hoặc x = 3")


def test_multiple_choice_value_or_letter():
    gold = {"letter": "B", "value": "14"}
    assert grade("Kết quả là 14", gold)
    assert grade("Chọn B", gold)
    assert not grade("Chọn A, kết quả 15", gold)


def test_sqrt_and_fraction():
    assert grade("x = 1/2", "x = 1/2")
    assert grade("Q = 6√x", "Q = 6√x")


def test_conditions_and_approximations_ignored():
    """Các trường hợp thật từ baseline smoke — đáp án đúng nhưng kèm điều kiện."""
    assert grade("B = √x/(√x + 3) với x > 0, x ≠ 9.", "B = √x/(√x + 3)")
    assert grade("A = (√x + 6)/(√x + 2), với x ≥ 0, x ≠ 1.", "A = (√x + 6)/(√x + 2)")
    assert grade("Thể tích lớn nhất là 256π/81 dm³ ≈ 9,93 dm³, đạt được khi h = 8/3 dm.", "256π/81 dm³ (h = 8/3 dm)")
    assert grade("Chu vi khu đất ABCD là 1040 m.", "1040 m (x = 250, y = 270)")
    assert grade("Tháng 3, tổ A sản xuất được 320 sản phẩm.", "320")
    assert grade("∛(−27) = −3", {"letter": "B", "value": "−3"})
    assert grade("Vậy diện tích mặt cầu bằng 16π cm², xấp xỉ 50,3 cm².", {"letter": "D", "value": "16π cm²"})
    assert grade("Khi tốc độ gió là 8 m/s, lực tác động lên cánh buồm là 1280 N.", {"letter": "C", "value": "1280 N"})


def test_wrong_still_wrong():
    assert not grade("Chu vi khu đất là 1000 m.", "1040 m (x = 250, y = 270)")
    assert not grade("∛(−27) = 3", {"letter": "B", "value": "−3"})
    assert not grade("m = 1 hoặc m = -5", "m = 1")


# ---- ca thật từ lần chạy eval golden: đáp án ĐÚNG nhưng bị chấm sai ----

def test_binary_minus_without_spaces():
    assert grade("Giá trị nhỏ nhất là (4-2√2)/R", "(4 − 2√2)/R khi góc AOC = 45°")
    assert not grade("Giá trị nhỏ nhất là (5-2√2)/R", "(4 − 2√2)/R khi góc AOC = 45°")


def test_thousands_space():
    assert grade("Chi phí khoảng 14000 đồng", "≈ 14 000 đồng")
    assert grade("14 000 đồng", "14000 đồng")


def test_gold_starting_with_approx():
    assert grade("Thể tích khoảng $1139$ cm³", "≈ 1139 cm³")
    assert grade("Vậy xấp xỉ $1139$ cm³", "≈ 1139 cm³")
    assert grade("Diện tích xung quanh là $1884$ cm².", "Sxq ≈ 1884 cm²")
    assert not grade("Thể tích khoảng $1140$ cm³", "≈ 1139 cm³")


def test_latex_answers():
    assert grade(r"$P = \dfrac{60}{17}$", "P = 60/17")
    assert grade(r"$\frac{1}{3}$", {"letter": "D", "value": "1/3"})
    assert grade(r"Bất đẳng thức cần tìm là $x \le 50$", {"letter": "A", "value": "x ≤ 50"})
    assert not grade(r"$x \ge 50$", {"letter": "A", "value": "x ≤ 50"})


def test_answer_in_dollars_ignores_restated_question_numbers():
    gold = {"letter": "B", "value": "14"}
    assert grade("Có $14$ xe 7 chỗ qua trạm.", gold)
    assert not grade("Có $15$ xe 7 chỗ qua trạm.", gold)


def test_true_false_words_vs_letters():
    assert grade("Đúng ; Đúng ; Đúng ; Sai", "Đ - Đ - Đ - S")
    assert grade("Đ, S, S, Đ", "Đ - S - S - Đ")
    assert not grade("Đúng ; Sai ; Sai ; Sai", "Đ - S - S - Đ")


def test_sqrt_followed_by_closing_paren():
    assert grade("Bán kính là $(3√2)/2$ cm.", {"letter": "C", "value": "3√2/2 cm"})


def test_khi_only_cuts_conditions_with_expression():
    assert grade("Mực nước sau khi thả vật cao khoảng 1,13 m.", "1,13")
    assert grade("Biểu thức xác định khi $x ≤ 1/2$.", {"letter": "B", "value": "x ≤ 1/2"})    # đáp án nằm SAU "khi"
    assert grade("Giá trị nhỏ nhất là 4 khi x = 2", "4")                                         # vẫn là đuôi điều kiện


def test_interval_notation_matches_inequality():
    assert grade("Tập nghiệm S = (−1; +∞)", "x > −1")
    assert grade(r"$S = (3; +\infty)$", "x > 3")
    assert grade("S = [2; +∞)", "x ≥ 2")
    assert grade("S = (−∞; 5]", "x ≤ 5")
    assert not grade("S = (−∞; −1)", "x > −1")
    assert not grade("S = (−1; +∞)", "x ≥ −1")
