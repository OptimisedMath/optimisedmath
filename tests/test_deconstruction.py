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
        ("parameters", "expected_factor", "expected_scaled_n"),
        [
            pytest.param(
                {"n": 2, "d": 3, "factor": 4},
                4,
                8,
                id="simple-scale-up",
            ),
            pytest.param(
                {"n": 1, "d": 5, "factor": 2},
                2,
                2,
                id="small-factor",
            ),
            pytest.param(
                {"n": 7, "d": 9, "factor": 6},
                6,
                42,
                id="larger-numerator-and-factor",
            ),
        ],
    )
    def test_step_sequence(self, parameters, expected_factor, expected_scaled_n):
        steps = build_steps(
            "expands_to_target_denominator_without_finding_factor", parameters
        )

        assert len(steps) == 2
        assert all(isinstance(step, Step) for step in steps)

        find_factor_step, scale_numerator_step = steps

        assert find_factor_step.answer == str(expected_factor)
        assert scale_numerator_step.answer == str(expected_scaled_n)

        # The multiplier is never written as its own number in the first step's
        # question — only the starting and target denominators are, which is the
        # hidden-operand shape this walkthrough proves (#187, #202). It only
        # surfaces once the second step names it, having been found in the first.
        assert str(expected_factor) not in find_factor_step.question
        assert str(expected_factor) in scale_numerator_step.question

        assert all(step.working_line is not None for step in steps)
        assert all(step.question for step in steps)
