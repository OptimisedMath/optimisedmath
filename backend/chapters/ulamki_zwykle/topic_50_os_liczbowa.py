import random
from backend.core.utils import (
    build_problem_dict,
    declares_traps,
    generate_universal_number_line,
    format_answers,
)


@declares_traps(
    "counts_ticks_for_both_parts",
    "counts_ticks_for_the_denominator",
    "counts_gaps_from_the_far_end",
)
def frac_number_line_1() -> dict | None:
    """Jeden skok = 1/x (poziom 1)."""
    d = random.randint(3, 8)
    n = random.randint(1, d - 1)
    q_str = rf"\text{{Jaki ułamek zaznaczono na osi?}}"

    # Standard 0 to 1
    svg_graphic = generate_universal_number_line(d, {0: "0", d: "1"}, n)

    c_str, _ = format_answers(n, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "counts_ticks_for_both_parts": format_answers(n + 1, d + 1)[0],
            "counts_ticks_for_the_denominator": format_answers(n, d + 1)[0],
            "counts_gaps_from_the_far_end": format_answers(d - n, d)[0],
        },
        image_html=svg_graphic,
        grading_policy="equivalent_accepted",
        parameters={"n": n, "d": d},
    )
    if result:
        return result


@declares_traps(
    "counts_ticks_for_both_parts",
    "reads_the_wrong_whole_interval",
    "counts_gaps_from_the_far_end",
)
def frac_number_line_2() -> dict | None:
    """Jeden skok to wielokrotność (poziom 2)."""
    d = random.randint(3, 8)
    n = random.randint(1, d - 1)
    W = random.randint(1, 5)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    # Mixed number between W and W+1
    svg_graphic = generate_universal_number_line(d, {0: str(W), d: str(W + 1)}, n)

    c_str, _ = format_answers(n, d, W)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "counts_ticks_for_both_parts": format_answers(n + 1, d + 1, W)[0],
            "reads_the_wrong_whole_interval": format_answers(n, d, W + 1)[0],
            "counts_gaps_from_the_far_end": format_answers(d - n, d, W)[0],
        },
        image_html=svg_graphic,
        grading_policy="equivalent_accepted",
        parameters={"n": n, "d": d, "W": W},
    )
    if result:
        return result


@declares_traps(
    "assumes_the_labels_are_one_apart",
    "off_by_one_gap",
    "reads_the_wrong_whole_interval",
)
def frac_number_line_3() -> dict | None:
    """Wskazywanie liczby mieszanej (poziom 3)."""
    # Level 3: Decrypt the Axis (Gap > 1)
    d = random.choice([2, 3, 4])
    D = random.choice(
        [2, 3]
    )  # Difference between integer labels (e.g., 2 means labels are 1 and 3)
    gap = d * D

    total_ticks = gap + random.randint(2, 4)
    if total_ticks > 15:
        total_ticks = 15

    idx1 = random.randint(1, 2)
    idx2 = idx1 + gap
    W = random.randint(1, 5)

    labeled = {idx1: str(W), idx2: str(W + D)}

    valid_targets = [
        i for i in range(idx1 + 1, total_ticks + 1) if (i - idx1) % d != 0 and i != idx2
    ]
    if not valid_targets:
        return None
    target = random.choice(valid_targets)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    svg_graphic = generate_universal_number_line(total_ticks, labeled, target)

    ticks_from_W = target - idx1
    whole = W + (ticks_from_W // d)
    num = ticks_from_W % d

    c_str, _ = format_answers(num, d, whole)

    # Treated the span between the two labels as a single whole number
    span_num = ticks_from_W
    span_whole = W
    if span_num > gap:
        span_whole += span_num // gap
        span_num = span_num % gap
    span_str, _ = format_answers(span_num, gap, span_whole)

    # Landed one gap past (or short of) the target
    num2 = num + 1
    whole2 = whole
    if num2 == d:
        num2 = 1
        whole2 += 1
    off_by_one_str, _ = format_answers(num2, d, whole2)

    # Took the whole part from the wrong labelled interval
    wrong_whole = W if whole != W else W + 1
    wrong_whole_str, _ = format_answers(num, d, wrong_whole)

    if len({c_str, span_str, off_by_one_str, wrong_whole_str}) == 4:
        result = build_problem_dict(
            q_str,
            c_str,
            traps={
                "assumes_the_labels_are_one_apart": span_str,
                "off_by_one_gap": off_by_one_str,
                "reads_the_wrong_whole_interval": wrong_whole_str,
            },
            image_html=svg_graphic,
            grading_policy="equivalent_accepted",
            parameters={
                "d": d,
                "D": D,
                "gap": gap,
                "idx1": idx1,
                "idx2": idx2,
                "W": W,
                "target": target,
                "total_ticks": total_ticks,
            },
        )
        if result:
            return result


@declares_traps(
    "counts_from_the_axis_edge_not_the_label",
    "off_by_one_gap",
    "uses_total_ticks_as_the_denominator",
)
def frac_number_line_4() -> dict | None:
    """Trudne przedziały (poziom 4)."""
    # Level 4: Extrapolation (Target is outside the labeled bounds)
    d = random.choice([3, 4, 5])
    W = random.randint(1, 5)

    idx1 = random.randint(1, 3)
    idx2 = idx1 + d  # Gap is exactly 1 whole number for simplicity

    total_ticks = idx2 + random.randint(3, 5)

    labeled = {idx1: str(W), idx2: str(W + 1)}

    # Target MUST be strictly to the right of idx2
    valid_targets = [i for i in range(idx2 + 1, total_ticks + 1) if (i - idx1) % d != 0]
    if not valid_targets:
        return None
    target = random.choice(valid_targets)
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"

    svg_graphic = generate_universal_number_line(total_ticks, labeled, target)

    ticks_from_W = target - idx1
    whole = W + (ticks_from_W // d)
    num = ticks_from_W % d

    c_str, _ = format_answers(num, d, whole)

    # Started counting from the visual start of the axis instead of idx1
    edge_whole = W + (target // d)
    edge_num = target % d
    if edge_num == 0:
        edge_num = 1
    edge_str, _ = format_answers(edge_num, d, edge_whole)

    # Landed one gap past (or short of) the target
    num2 = num + 1
    whole2 = whole
    if num2 == d:
        num2 = 1
        whole2 += 1
    off_by_one_str, _ = format_answers(num2, d, whole2)

    # Used total ticks on screen as the denominator
    total_num = num
    if total_num >= total_ticks:
        total_num = total_ticks - 1
    total_ticks_str, _ = format_answers(total_num, total_ticks, whole)

    if len({c_str, edge_str, off_by_one_str, total_ticks_str}) == 4:
        result = build_problem_dict(
            q_str,
            c_str,
            traps={
                "counts_from_the_axis_edge_not_the_label": edge_str,
                "off_by_one_gap": off_by_one_str,
                "uses_total_ticks_as_the_denominator": total_ticks_str,
            },
            image_html=svg_graphic,
            grading_policy="equivalent_accepted",
            parameters={
                "d": d,
                "W": W,
                "idx1": idx1,
                "idx2": idx2,
                "target": target,
                "total_ticks": total_ticks,
            },
        )
        if result:
            return result
