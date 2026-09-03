"""Pure tests for the Deconstruction step registry — no Session, DB, or HTTP."""

import pytest

from backend.deconstruction import (
    DeconstructionContractError,
    Step,
    UnregisteredDeconstructionError,
    build_steps,
)
from backend.step_grading import ORDERING_ANSWER_SEPARATOR


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
            "expected_combined_numerator",
            "expected_final_answer",
        ),
        [
            pytest.param(
                {"n1": 1, "d1": 3, "n2": 1, "d2": 4, "operation": "+"},
                12,
                4,
                3,
                7,
                r"\frac{7}{12}",
                id="addition-coprime-denominators",
            ),
            pytest.param(
                {"n1": 1, "d1": 2, "n2": 1, "d2": 4, "operation": "+"},
                4,
                2,
                1,
                3,
                r"\frac{3}{4}",
                id="addition-factor-related-denominators-reduces",
            ),
            pytest.param(
                {"n1": 3, "d1": 4, "n2": 1, "d2": 3, "operation": "-"},
                12,
                9,
                4,
                5,
                r"\frac{5}{12}",
                id="subtraction-coprime-denominators",
            ),
            # The whole parts are optional and convert each operand to an improper
            # fraction before anything else happens, so the scaling steps work on
            # 3/2 and 7/3 rather than on 1/2 and 1/3 — and the last step lands on
            # the mixed-number Problem's own answer instead of its fractional
            # remainder (#224).
            pytest.param(
                {
                    "whole1": 1,
                    "n1": 1,
                    "d1": 2,
                    "whole2": 2,
                    "n2": 1,
                    "d2": 3,
                    "operation": "+",
                },
                6,
                9,
                14,
                23,
                r"3\frac{5}{6}",
                id="addition-mixed-number-operands",
            ),
            pytest.param(
                {
                    "whole1": 3,
                    "n1": 1,
                    "d1": 4,
                    "whole2": 1,
                    "n2": 1,
                    "d2": 3,
                    "operation": "-",
                },
                12,
                39,
                16,
                23,
                r"1\frac{11}{12}",
                id="subtraction-mixed-number-operands",
            ),
            # A zero whole part is the plain-fraction case spelled out: `whole * d + n`
            # leaves the operand untouched, so this must match the coprime row above.
            pytest.param(
                {
                    "whole1": 0,
                    "n1": 1,
                    "d1": 3,
                    "whole2": 0,
                    "n2": 1,
                    "d2": 4,
                    "operation": "+",
                },
                12,
                4,
                3,
                7,
                r"\frac{7}{12}",
                id="addition-explicit-zero-whole-parts",
            ),
        ],
    )
    def test_step_sequence(
        self,
        parameters,
        expected_common,
        expected_scaled_n1,
        expected_scaled_n2,
        expected_combined_numerator,
        expected_final_answer,
    ):
        steps = build_steps("operates_on_unlike_fractions_directly", parameters)

        # A scaling step is dropped for an operand whose denominator is already the
        # LCD — nothing to expand, so nothing to ask (#225).
        d1, d2 = parameters["d1"], parameters["d2"]
        expected_scaling_steps = (d1 != expected_common) + (d2 != expected_common)
        assert len(steps) == 3 + expected_scaling_steps
        assert all(isinstance(step, Step) for step in steps)

        common_denominator_step = steps[0]
        scaling_steps = steps[1:-2]
        combine_step, simplify_step = steps[-2:]

        assert common_denominator_step.answer == str(expected_common)
        expected_scaled = [
            str(scaled)
            for denominator, scaled in (
                (d1, expected_scaled_n1),
                (d2, expected_scaled_n2),
            )
            if denominator != expected_common
        ]
        assert [step.answer for step in scaling_steps] == expected_scaled
        # The combining step takes a bare numerator over the shared denominator,
        # and only the simplifying step after it lands on the Problem's answer (#225).
        assert combine_step.answer == str(expected_combined_numerator)
        assert simplify_step.answer == expected_final_answer

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

    def test_rejects_equal_denominators(self):
        """This walkthrough opens by saying the two denominators differ (#224).

        On a like-denominator Problem that opening line is a falsehood about what the
        Student can see, so a mis-mapped Trap is refused rather than rendered.
        """
        with pytest.raises(DeconstructionContractError):
            build_steps(
                "operates_on_unlike_fractions_directly",
                {"n1": 1, "d1": 5, "n2": 2, "d2": 5, "operation": "+"},
            )

    def test_missing_required_parameter_names_every_absent_key(self):
        with pytest.raises(DeconstructionContractError) as raised:
            build_steps(
                "operates_on_unlike_fractions_directly",
                {"n1": 1, "d1": 2, "n2": 1},
            )

        error = raised.value
        assert error.misconception_slug == "operates_on_unlike_fractions_directly"
        assert set(error.missing_keys) == {"d2", "operation"}


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


class TestOrderingStepType:
    """Pure coverage for the ordering-input step type (#198): the wire contract
    and control only. #186's priority-ladder walkthrough for
    `ignores_the_order_of_operations` is batch two and not authored here, so
    these exercise the type mechanism with stand-in items."""

    def test_typed_step_defaults(self):
        step = Step(question="q", working_line=None, answer="5")

        assert step.input_type == "typed"
        assert step.items is None

    def test_ordering_step_carries_its_items_and_delimited_answer(self):
        items = ("brackets", "powers", "multiply-divide", "add-subtract")
        step = Step(
            question="Order the priority tiers.",
            working_line=None,
            answer=ORDERING_ANSWER_SEPARATOR.join(items),
            input_type="ordering",
            items=items,
        )

        assert step.input_type == "ordering"
        assert step.items == items
        assert step.answer == "brackets|powers|multiply-divide|add-subtract"


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


class TestOperatesOnMixedNumberWithoutConverting:
    """Table-driven: `parameters` shapes for the precondition-conversion walkthrough.

    Six generators across three topics reference this Misconception — a mixed number
    multiplied, divided, or raised to a power, either alone or against a whole number,
    a plain fraction, or a second mixed number — normalised to a shared
    `whole1`/`n1`/`d1`/`whole2`/`n2`/`d2`/`operation` contract (`p` replaces the second
    operand when `operation == "^"`, since a power has none) (#200).

    `expected_target_mixed` pins down *which* operand the first step converts: the one
    carrying a whole part, or the first of the two when both do.
    """

    @pytest.mark.parametrize(
        (
            "parameters",
            "expected_target_mixed",
            "expected_target_improper",
            "expected_final_answer",
        ),
        [
            pytest.param(
                {
                    "whole1": 1,
                    "n1": 1,
                    "d1": 2,
                    "whole2": 0,
                    "n2": 3,
                    "d2": 1,
                    "operation": "*",
                },
                r"1\frac{1}{2}",
                3,
                r"4\frac{1}{2}",
                id="mixed-times-whole-number",
            ),
            pytest.param(
                {
                    "whole1": 0,
                    "n1": 1,
                    "d1": 2,
                    "whole2": 1,
                    "n2": 1,
                    "d2": 3,
                    "operation": "*",
                },
                r"1\frac{1}{3}",
                4,
                r"\frac{2}{3}",
                id="plain-fraction-times-mixed-number",
            ),
            pytest.param(
                {
                    "whole1": 1,
                    "n1": 1,
                    "d1": 2,
                    "whole2": 1,
                    "n2": 1,
                    "d2": 3,
                    "operation": "*",
                },
                r"1\frac{1}{2}",
                3,
                "2",
                id="mixed-times-mixed",
            ),
            pytest.param(
                {
                    "whole1": 2,
                    "n1": 1,
                    "d1": 4,
                    "whole2": 0,
                    "n2": 3,
                    "d2": 1,
                    "operation": ":",
                },
                r"2\frac{1}{4}",
                9,
                r"\frac{3}{4}",
                id="mixed-divided-by-whole-number",
            ),
            pytest.param(
                {
                    "whole1": 1,
                    "n1": 1,
                    "d1": 2,
                    "whole2": 1,
                    "n2": 1,
                    "d2": 4,
                    "operation": ":",
                },
                r"1\frac{1}{2}",
                3,
                r"1\frac{1}{5}",
                id="mixed-divided-by-mixed",
            ),
            pytest.param(
                {"whole1": 1, "n1": 1, "d1": 2, "p": 2, "operation": "^"},
                r"1\frac{1}{2}",
                3,
                r"2\frac{1}{4}",
                id="mixed-raised-to-power",
            ),
        ],
    )
    def test_step_sequence(
        self,
        parameters,
        expected_target_mixed,
        expected_target_improper,
        expected_final_answer,
    ):
        steps = build_steps("operates_on_mixed_number_without_converting", parameters)

        assert len(steps) == 2
        assert all(isinstance(step, Step) for step in steps)

        convert_step, operate_step = steps

        assert expected_target_mixed in convert_step.question
        assert convert_step.answer == str(expected_target_improper)
        assert operate_step.answer == expected_final_answer

        # The conversion is its own step, and the second step's working line shows
        # the operands already converted — the precondition-conversion shape (#187,
        # #200): the operation is only reachable once the mixed number is gone.
        assert convert_step.working_line is not None
        assert operate_step.working_line is not None
        assert convert_step.working_line != operate_step.working_line
        assert str(expected_target_improper) in operate_step.working_line

        assert all(step.question for step in steps)

    def test_rejects_unsupported_operation(self):
        with pytest.raises(ValueError):
            build_steps(
                "operates_on_mixed_number_without_converting",
                {
                    "whole1": 1,
                    "n1": 1,
                    "d1": 2,
                    "whole2": 0,
                    "n2": 3,
                    "d2": 1,
                    "operation": "+",
                },
            )


class TestComparesDecimalsByWrongDigitOrder:
    """Table-driven: representative `parameters` shapes for the no-working-line
    comparison walkthrough. The shapes mirror dec_compare_1/2/3, normalised to a
    shared `s1`/`s2` contract — the two decimal strings exactly as shown on
    screen, trailing zeros preserved where the generator deliberately carries
    them (#187, #201).
    """

    @pytest.mark.parametrize(
        ("parameters", "expected_places", "expected_sign"),
        [
            pytest.param(
                {"s1": "0,45", "s2": "0,23"},
                2,
                ">",
                id="same-decimal-places-different-digits",
            ),
            pytest.param(
                {"s1": "0,5", "s2": "0,42"},
                2,
                ">",
                id="first-operand-fewer-decimal-places",
            ),
            pytest.param(
                {"s1": "2,05", "s2": "2,5"},
                2,
                "<",
                id="second-operand-more-decimal-places",
            ),
            pytest.param(
                {"s1": "0,5", "s2": "0,50"},
                2,
                "=",
                id="equal-with-trailing-zero",
            ),
            pytest.param(
                {"s1": "3,070", "s2": "3,07"},
                3,
                "=",
                id="equal-with-trailing-zero-and-whole-part",
            ),
        ],
    )
    def test_step_sequence(self, parameters, expected_places, expected_sign):
        steps = build_steps("compares_decimals_by_wrong_digit_order", parameters)

        assert len(steps) == 2
        assert all(isinstance(step, Step) for step in steps)

        find_places_step, compare_sign_step = steps

        assert find_places_step.answer == str(expected_places)
        assert compare_sign_step.answer == expected_sign

        # The no-working-line shape (#187, #201): there is no expression to
        # transform, so neither step authors one.
        assert find_places_step.working_line is None
        assert compare_sign_step.working_line is None

        assert all(step.question for step in steps)
        assert parameters["s1"] in find_places_step.question
        assert parameters["s2"] in find_places_step.question
        assert parameters["s1"] in compare_sign_step.question
        assert parameters["s2"] in compare_sign_step.question
