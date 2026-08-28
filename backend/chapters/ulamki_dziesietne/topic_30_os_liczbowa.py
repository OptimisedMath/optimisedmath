import random
from backend.core.utils import (
    build_problem_dict,
    declares_traps,
    fmt_dec,
    generate_universal_number_line,
)


@declares_traps(
    "assumes_a_hundredth_step",
    "off_by_one_gap",
    "counts_gaps_from_the_far_end",
)
def dec_number_line_1() -> dict | None:
    """Oś co 0.1 (poziom 1)."""
    # Level 1: Absolute basics. 10 ticks, whole numbers. Step is always 0.1.
    base = random.randint(0, 20)
    target = random.randint(1, 9)
    step = 0.1

    c_val = base + target * step

    labeled = {0: str(base), 10: str(base + 1)}
    svg_graphic = generate_universal_number_line(10, labeled, target)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    c_str = fmt_dec(round(c_val, 1))
    hundredth_str = fmt_dec(round(base + target * 0.01, 2))
    off_by_one_str = fmt_dec(round(c_val + step, 1))
    far_end_target = 10 - target if target != 5 else 6
    far_end_str = fmt_dec(round(base + far_end_target * step, 1))

    if len({c_str, hundredth_str, off_by_one_str, far_end_str}) == 4:
        problem = build_problem_dict(
            q_str,
            c_str,
            traps={
                "assumes_a_hundredth_step": hundredth_str,
                "off_by_one_gap": off_by_one_str,
                "counts_gaps_from_the_far_end": far_end_str,
            },
            image_html=svg_graphic,
            parameters={"base": base, "target": target},
        )
        if problem:
            return problem


@declares_traps(
    "assumes_a_ten_times_smaller_step",
    "off_by_one_gap",
    "counts_gaps_from_the_far_end",
)
def dec_number_line_2() -> dict | None:
    """Oś co 0.01 (poziom 2)."""
    # Level 2: 10 ticks, but with decimals (hundredths and thousandths). Step 0.01 or 0.001.
    step = random.choice([0.01, 0.001])
    base_mult = random.randint(1, 99)
    if base_mult % 10 == 0:
        base_mult += 1
    base = base_mult * (step * 10)

    target = random.randint(1, 9)
    c_val = base + target * step

    labeled = {0: fmt_dec(round(base, 3)), 10: fmt_dec(round(base + 10 * step, 3))}
    svg_graphic = generate_universal_number_line(10, labeled, target)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    c_str = fmt_dec(round(c_val, 4))
    smaller_step_str = fmt_dec(round(base + target * (step / 10), 5))
    off_by_one_str = fmt_dec(round(c_val + step, 4))
    far_end_target = 10 - target if target != 5 else 6
    far_end_str = fmt_dec(round(base + far_end_target * step, 4))

    if len({c_str, smaller_step_str, off_by_one_str, far_end_str}) == 4:
        problem = build_problem_dict(
            q_str,
            c_str,
            traps={
                "assumes_a_ten_times_smaller_step": smaller_step_str,
                "off_by_one_gap": off_by_one_str,
                "counts_gaps_from_the_far_end": far_end_str,
            },
            image_html=svg_graphic,
            parameters={"step": step, "base": base, "target": target},
        )
        if problem:
            return problem


@declares_traps(
    "assumes_a_tenth_step",
    "off_by_one_gap",
    "counts_gaps_from_the_far_end",
)
def dec_number_line_3() -> dict | None:
    """Oś co 0.2 lub podobne (poziom 3)."""
    # Level 3: Easy Scale Intro. 5 ticks, whole numbers. Step is 0.2.
    ticks = 5
    step = 0.2
    base = random.randint(0, 20)

    target = random.randint(1, 4)
    c_val = base + target * step

    labeled = {0: str(base), ticks: str(base + 1)}
    svg_graphic = generate_universal_number_line(ticks, labeled, target)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    c_str = fmt_dec(round(c_val, 1))
    tenth_str = fmt_dec(round(base + target * 0.1, 1))
    off_by_one_str = fmt_dec(round(c_val + step, 1))
    far_end_target = ticks - target if ticks - target != target else target + 1
    far_end_str = fmt_dec(round(base + far_end_target * step, 1))

    if len({c_str, tenth_str, off_by_one_str, far_end_str}) == 4:
        problem = build_problem_dict(
            q_str,
            c_str,
            traps={
                "assumes_a_tenth_step": tenth_str,
                "off_by_one_gap": off_by_one_str,
                "counts_gaps_from_the_far_end": far_end_str,
            },
            image_html=svg_graphic,
            parameters={"base": base, "target": target},
        )
        if problem:
            return problem


@declares_traps(
    "assumes_a_hundredth_step",
    "off_by_one_gap",
    "counts_gaps_from_the_far_end",
)
def dec_number_line_4() -> dict | None:
    """Duży odstęp (poziom 4)."""
    # Level 4: Advanced Scale. 4 or 5 ticks, decimal numbers.
    ticks = random.choice([4, 5])
    step = 0.02 if ticks == 5 else 0.025
    base = random.randint(1, 50) * 0.1

    target = random.randint(1, ticks - 1)
    c_val = base + target * step

    labeled = {
        0: fmt_dec(round(base, 2)),
        ticks: fmt_dec(round(base + ticks * step, 2)),
    }
    svg_graphic = generate_universal_number_line(ticks, labeled, target)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    c_str = fmt_dec(round(c_val, 3))
    hundredth_str = fmt_dec(round(base + target * 0.01, 3))
    off_by_one_str = fmt_dec(round(c_val + step, 3))
    far_end_target = ticks - target if ticks - target != target else target + 1
    far_end_str = fmt_dec(round(base + far_end_target * step, 3))

    if len({c_str, hundredth_str, off_by_one_str, far_end_str}) == 4:
        problem = build_problem_dict(
            q_str,
            c_str,
            traps={
                "assumes_a_hundredth_step": hundredth_str,
                "off_by_one_gap": off_by_one_str,
                "counts_gaps_from_the_far_end": far_end_str,
            },
            image_html=svg_graphic,
            parameters={"ticks": ticks, "base": base, "target": target},
        )
        if problem:
            return problem


@declares_traps(
    "doubles_the_step_past_the_last_label",
    "off_by_one_gap",
    "doubles_the_whole_distance",
)
def dec_number_line_5() -> dict | None:
    """Duży odstęp cz. 2 (poziom 5)."""
    # Level 5: Extrapolation. 10 ticks, target is outside bounds.
    ticks = 10
    step = random.choice([0.1, 0.01])
    base = random.randint(1, 50) * step

    idx1 = random.randint(1, 3)
    idx2 = idx1 + random.randint(1, 2)
    target = random.randint(idx2 + 2, 9)
    c_val = base + target * step

    labeled = {
        idx1: fmt_dec(round(base + idx1 * step, 3)),
        idx2: fmt_dec(round(base + idx2 * step, 3)),
    }
    svg_graphic = generate_universal_number_line(ticks, labeled, target)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    c_str = fmt_dec(round(c_val, 3))
    doubled_past_str = fmt_dec(
        round(base + idx2 * step + (target - idx2) * step * 2, 3)
    )
    off_by_one_str = fmt_dec(round(c_val + step, 3))
    doubled_all_str = fmt_dec(round(base + target * step * 2, 3))

    if len({c_str, doubled_past_str, off_by_one_str, doubled_all_str}) == 4:
        problem = build_problem_dict(
            q_str,
            c_str,
            traps={
                "doubles_the_step_past_the_last_label": doubled_past_str,
                "off_by_one_gap": off_by_one_str,
                "doubles_the_whole_distance": doubled_all_str,
            },
            image_html=svg_graphic,
            parameters={
                "step": step,
                "base": base,
                "idx1": idx1,
                "idx2": idx2,
                "target": target,
            },
        )
        if problem:
            return problem


@declares_traps(
    "off_by_one_gap",
    "assumes_a_tenth_step",
    "off_by_one_gap_backwards",
)
def dec_number_line_6() -> dict | None:
    """Dziwne przedziały (poziom 6)."""
    # Level 6: Exam Boss. Scattered labels, calculate the step.
    ticks = 10
    step = random.choice([0.1, 0.2, 0.05])
    base = random.randint(1, 50) * step

    idx1 = random.randint(0, 2)
    idx2 = random.randint(6, 8)
    target = random.choice([x for x in range(3, 10) if x not in [idx1, idx2]])
    c_val = base + target * step

    labeled = {
        idx1: fmt_dec(round(base + idx1 * step, 3)),
        idx2: fmt_dec(round(base + idx2 * step, 3)),
    }
    svg_graphic = generate_universal_number_line(ticks, labeled, target)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    c_str = fmt_dec(round(c_val, 3))
    off_by_one_str = fmt_dec(round(c_val + step, 3))
    tenth_str = fmt_dec(round(base + idx1 * step + (target - idx1) * 0.1, 3))
    backwards_str = fmt_dec(round(c_val - step, 3))

    if len({c_str, off_by_one_str, tenth_str, backwards_str}) == 4:
        problem = build_problem_dict(
            q_str,
            c_str,
            traps={
                "off_by_one_gap": off_by_one_str,
                "assumes_a_tenth_step": tenth_str,
                "off_by_one_gap_backwards": backwards_str,
            },
            image_html=svg_graphic,
            parameters={
                "step": step,
                "base": base,
                "idx1": idx1,
                "idx2": idx2,
                "target": target,
            },
        )
        if problem:
            return problem
