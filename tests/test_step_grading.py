"""Pure tests for Deconstruction step grading — no Session, DB, or HTTP."""

from backend.step_grading import grade_step


def test_correct_answer():
    result = grade_step("12", "12")
    assert result == {"is_correct": True}


def test_wrong_answer_is_not_soft():
    result = grade_step("11", "12")
    assert result["is_correct"] is False
    assert "soft_error" not in result


def test_unparseable_answer_is_a_soft_error():
    result = grade_step("banana", "12")
    assert result["is_correct"] is False
    assert result["soft_error"] is True
    assert result["feedback_msg"]


def test_equivalent_value_wrong_notation_is_a_soft_error():
    result = grade_step("0,5", r"\frac{1}{2}")
    assert result["is_correct"] is False
    assert result["soft_error"] is True
    assert result["feedback_msg"]


def test_equivalent_fraction_value_matches():
    result = grade_step("1/2", r"\frac{1}{2}")
    assert result == {"is_correct": True}
