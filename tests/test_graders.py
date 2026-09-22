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
