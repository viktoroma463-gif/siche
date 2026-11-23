from app.rules.copy_lock import COPY_LOCK_DISCLAIMER, evaluate_micro_test


def test_length_boundaries():
    assert evaluate_micro_test("太短", "tweak").status == "locked"
    assert evaluate_micro_test("字" * 79, "tweak").status == "locked"
    assert evaluate_micro_test("字" * 80, "tweak").status == "unlock"
    assert evaluate_micro_test("字" * 301, "tweak").status == "locked"


def test_vague_long_answer_unlocks():
    text = "好的，写得很好，没问题，可以，同意，差不多，我觉得可以就这样直接用吧。" * 3
    assert 80 <= len(text) <= 300
    assert evaluate_micro_test(text, "tweak").status == "unlock"


def test_disclaimer_forbids_direct_paste():
    assert "不可以直接粘贴" in COPY_LOCK_DISCLAIMER
    assert "截图" in COPY_LOCK_DISCLAIMER
    assert "反思" in COPY_LOCK_DISCLAIMER
