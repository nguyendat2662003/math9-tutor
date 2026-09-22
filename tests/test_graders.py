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
