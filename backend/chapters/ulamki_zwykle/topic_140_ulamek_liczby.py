import random
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps("reads_it_as_a_mixed_number", "swaps_the_numerator_and_denominator")
def frac_frac_of_int_1() -> dict | None:
    """Całości bez reszty (poziom 1)."""
    d = random.randint(2, 8)
    n = random.randint(1, d - 1)
    k = d * random.randint(2, 6)

    q_str = (
        rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
    )

    c_str, _ = format_answers((k // d) * n, 1)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "reads_it_as_a_mixed_number": format_answers(k * d + n, d)[0],
            "swaps_the_numerator_and_denominator": format_answers(k // n * d, 1)[0],
        },
        fillers=[format_answers((k // d) * n + 1, 1)[0]],
    )
    if problem:
        return problem


@declares_traps(
    "inverts_the_fraction_before_multiplying", "multiplies_the_denominator_too"
)
def frac_frac_of_int_2() -> dict | None:
    """Trudniejsze liczby (poziom 2)."""
    d = random.randint(3, 9)
    n = random.randint(1, d - 1)
    k = random.randint(4, 15)
    if k % d == 0:
        return None

    q_str = (
        rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
    )

    c_str, _ = format_answers(n * k, d)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "inverts_the_fraction_before_multiplying": format_answers(k * d, n)[0],
            "multiplies_the_denominator_too": format_answers(n * k, d * k)[0],
        },
        fillers=[format_answers(n * k + 1, d)[0]],
    )
    if problem:
        return problem


@declares_traps(
    "uses_one_more_than_the_denominator",
    "applies_the_fraction_again_instead_of_inverting",
)
def frac_frac_of_int_3() -> dict | None:
    """Gdy wynik jest ułamkiem (poziom 3)."""
    d = random.randint(3, 8)
    n = random.randint(2, d - 1)
    whole = d * random.randint(2, 6)
    part = (whole // d) * n

    q_str = rf"\text{{Znajdź liczbę, której }} \frac{{{n}}}{{{d}}} \text{{ wynosi }} {part}."
    c_str = str(whole)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "uses_one_more_than_the_denominator": str(int((part // n) * (d + 1))),
            "applies_the_fraction_again_instead_of_inverting": str(int(part * n // d)),
        },
        fillers=[str(whole + d)],
    )
    if problem:
        return problem


@declares_traps("gives_only_the_fraction_not_the_total", "adds_only_the_numerator")
def frac_frac_of_int_4() -> dict | None:
    """Ułamek z liczby mieszanej (poziom 4)."""
    d = random.randint(3, 6)
    n = random.randint(1, d - 1)
    base = d * random.randint(2, 5)

    is_increase = random.choice([True, False])
    action = "Powiększ" if is_increase else "Pomniejsz"

    q_str = rf"\text{{{action} liczbę }} {base} \text{{ o }} \frac{{{n}}}{{{d}}} \text{{ jej wartości.}}"

    change = (base // d) * n
    c_val = base + change if is_increase else base - change

    problem = build_problem_dict(
        q_str,
        str(c_val),
        traps={
            "gives_only_the_fraction_not_the_total": str(change),
            "adds_only_the_numerator": (
                str(base + n) if is_increase else str(base - n)
            ),
        },
        fillers=[str(c_val + 1)],
    )
    if problem:
        return problem
