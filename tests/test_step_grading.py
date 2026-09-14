"""Pure tests for Deconstruction step grading — no Session, DB, or HTTP."""

from backend.step_grading import (
    ORDERING_ANSWER_SEPARATOR,
    grade_ordering_step,
    grade_step,
)


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


def test_ordering_correct_order_matches():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    result = grade_ordering_step(answer, answer)
    assert result == {"is_correct": True}


def test_ordering_wrong_order_is_incorrect():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    submitted = ORDERING_ANSWER_SEPARATOR.join(["b", "a", "c", "d"])
    result = grade_ordering_step(submitted, answer)
    assert result["is_correct"] is False


def test_ordering_ignores_surrounding_whitespace_per_item():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c"])
    submitted = " a | b | c "
    result = grade_ordering_step(submitted, answer)
    assert result == {"is_correct": True}


def test_ordering_wrong_item_count_is_incorrect():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    submitted = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c"])
    result = grade_ordering_step(submitted, answer)
    assert result["is_correct"] is False


def test_ordering_accepted_order_other_than_answer_matches():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    accepted = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "d", "c"])
    result = grade_ordering_step(accepted, answer, accepted_orders=[accepted])
    assert result == {"is_correct": True}


def test_ordering_answer_itself_still_matches_with_accepted_orders_set():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    accepted = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "d", "c"])
    result = grade_ordering_step(answer, answer, accepted_orders=[accepted])
    assert result == {"is_correct": True}


def test_ordering_non_member_order_is_incorrect_with_accepted_orders_set():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    accepted = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "d", "c"])
    submitted = ORDERING_ANSWER_SEPARATOR.join(["d", "c", "b", "a"])
    result = grade_ordering_step(submitted, answer, accepted_orders=[accepted])
    assert result["is_correct"] is False


def test_ordering_no_accepted_orders_grades_exactly_as_before():
    answer = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "c", "d"])
    submitted = ORDERING_ANSWER_SEPARATOR.join(["b", "a", "c", "d"])
    result = grade_ordering_step(submitted, answer, accepted_orders=None)
    assert result["is_correct"] is False
