"""Pure tests for the Deconstruction step registry — no Session, DB, or HTTP."""

import pytest

from backend.deconstruction import (
    Step,
    UnregisteredDeconstructionError,
    build_steps,
)


def test_build_steps_raises_for_unregistered_misconception():
    with pytest.raises(UnregisteredDeconstructionError):
        build_steps("no_such_misconception", {})


class TestOperatesOnUnlikeFractionsDirectly:
    """Table-driven: representative `parameters` shapes for the first walkthrough."""

    @pytest.mark.parametrize(
        (
            "parameters",
            "expected_common",
            "expected_scaled_n1",
            "expected_scaled_n2",
            "expected_final_answer",
        ),
        [
            pytest.param(
                {"n1": 1, "d1": 3, "n2": 1, "d2": 4, "operation": "+"},
                12,
                4,
                3,
                r"\frac{7}{12}",
                id="addition-coprime-denominators",
            ),
            pytest.param(
                {"n1": 1, "d1": 2, "n2": 1, "d2": 4, "operation": "+"},
                8,
                4,
                2,
                r"\frac{3}{4}",
                id="addition-factor-related-denominators-reduces",
            ),
            pytest.param(
                {"n1": 3, "d1": 4, "n2": 1, "d2": 3, "operation": "-"},
                12,
                9,
                4,
                r"\frac{5}{12}",
                id="subtraction-coprime-denominators",
            ),
        ],
    )
    def test_step_sequence(
        self,
        parameters,
        expected_common,
        expected_scaled_n1,
        expected_scaled_n2,
        expected_final_answer,
    ):
        steps = build_steps("operates_on_unlike_fractions_directly", parameters)

        assert len(steps) == 4
        assert all(isinstance(step, Step) for step in steps)

        common_denominator_step, scale_first_step, scale_second_step, combine_step = (
            steps
        )

        assert common_denominator_step.answer == str(expected_common)
        assert scale_first_step.answer == str(expected_scaled_n1)
        assert scale_second_step.answer == str(expected_scaled_n2)
        assert combine_step.answer == expected_final_answer

        # The multi-step, cross-Chapter shape carries a working line throughout —
        # unlike the no-working-line comparison Misconception in a later batch.
        assert all(step.working_line is not None for step in steps)
        assert all(step.question for step in steps)

    def test_rejects_unsupported_operation(self):
        with pytest.raises(ValueError):
            build_steps(
                "operates_on_unlike_fractions_directly",
                {"n1": 1, "d1": 2, "n2": 1, "d2": 3, "operation": "*"},
            )


class TestExpandsToTargetDenominatorWithoutFindingFactor:
    """Table-driven: representative `parameters` shapes for the hidden-operand walkthrough."""

    @pytest.mark.parametrize(
        ("parameters", "expected_target_denominator", "expected_scaled_n"),
        [
            pytest.param(
                {"n": 2, "d": 3, "factor": 4},
                12,
                8,
                id="simple-scale-up",
            ),
            pytest.param(
                {"n": 1, "d": 5, "factor": 2},
                10,
                2,
                id="small-factor",
            ),
            pytest.param(
                {"n": 7, "d": 9, "factor": 6},
                54,
                42,
                id="larger-numerator-and-factor",
            ),
        ],
    )
    def test_step_sequence(
        self, parameters, expected_target_denominator, expected_scaled_n
    ):
        steps = build_steps(
            "expands_to_target_denominator_without_finding_factor", parameters
        )

        assert len(steps) == 2
        assert all(isinstance(step, Step) for step in steps)

        find_factor_step, scale_numerator_step = steps
        factor = str(parameters["factor"])

        assert find_factor_step.answer == factor
        assert scale_numerator_step.answer == str(expected_scaled_n)
        assert str(expected_target_denominator) in find_factor_step.question

        # The multiplier is never written as its own number in the first step's
        # question — only the starting and target denominators are, which is the
        # hidden-operand shape this walkthrough proves (#187, #202). It only
        # surfaces once the second step names it, having been found in the first.
        assert factor not in find_factor_step.question
        assert factor in scale_numerator_step.question

        assert all(step.working_line is not None for step in steps)
        assert all(step.question for step in steps)


class TestDoesNotAlignDecimalsBeforeColumnArithmetic:
    """Table-driven: representative `parameters` shapes for the column-layout walkthrough.

    The three shapes mirror the three generators that reference this Misconception —
    the second operand carrying more decimal places (dec_add_3), the first carrying
    more (dec_sub_2), and both already tied (dec_add_1) — normalised to a shared
    `v1`/`v2`/`operation` contract (#199).
    """

    @pytest.mark.parametrize(
        ("parameters", "expected_places", "expected_padded", "expected_combined"),
        [
            pytest.param(
                {"v1": 1.2, "v2": 0.05, "operation": "+"},
                2,
                ("1,20", "0,05"),
                "1,25",
                id="second-operand-has-more-decimal-places",
            ),
            pytest.param(
                {"v1": 5.43, "v2": 2.1, "operation": "-"},
                2,
                ("5,43", "2,10"),
                "3,33",
                id="first-operand-has-more-decimal-places",
            ),
            pytest.param(
                {"v1": 2.3, "v2": 1.5, "operation": "+"},
                1,
                ("2,3", "1,5"),
                "3,8",
                id="decimal-places-already-tied",
            ),
        ],
    )
    def test_step_sequence(
        self, parameters, expected_places, expected_padded, expected_combined
    ):
        steps = build_steps(
            "does_not_align_decimals_before_column_arithmetic", parameters
        )

        assert len(steps) == 2
        assert all(isinstance(step, Step) for step in steps)

        find_places_step, compute_step = steps

        assert find_places_step.answer == str(expected_places)
        assert compute_step.answer == expected_combined

        # The column-layout shape (#187, #199): each working line is a laid-out
        # LaTeX array, not a single inline expression, and the second step's
        # array carries the zero-padded operands the first step found the count for.
        assert find_places_step.working_line is not None
        assert compute_step.working_line is not None
        assert r"\begin{array}" in find_places_step.working_line
        assert r"\begin{array}" in compute_step.working_line
        assert all(operand in compute_step.working_line for operand in expected_padded)

        # Distinct working lines even when padding is a no-op, so the frontend's
        # flash-on-change still fires on the second step.
        assert find_places_step.working_line != compute_step.working_line

        assert all(step.question for step in steps)

    @pytest.mark.parametrize(
        ("parameters", "expected_phrase"),
        [
            pytest.param(
                {"v1": 2.3, "v2": 1.5, "operation": "+"},
                "1 miejsce",
                id="singular",
            ),
            pytest.param(
                {"v1": 1.2, "v2": 0.05, "operation": "+"},
                "2 miejsca",
                id="plural-two-to-four",
            ),
        ],
    )
    def test_place_count_is_declined_for_the_numeral(self, parameters, expected_phrase):
        _, compute_step = build_steps(
            "does_not_align_decimals_before_column_arithmetic", parameters
        )

        assert expected_phrase in compute_step.question

    def test_rejects_unsupported_operation(self):
        with pytest.raises(ValueError):
            build_steps(
                "does_not_align_decimals_before_column_arithmetic",
                {"v1": 1.2, "v2": 0.05, "operation": "*"},
            )
