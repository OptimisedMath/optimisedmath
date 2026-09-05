"""Ułamki Dziesiętne — Jednostki: generatory Problemów."""

import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


# Every Level here converted to a LARGER unit, so every draw divided. Converting
# downwards is half of what the podstawa asks for and the direction children get
# wrong more often, so each Level draws its direction 50/50 and offers only the
# Traps that direction can produce — a wrong rule for one direction is the correct
# answer for the other. `declares_traps` is the union across both branches.
def _unit_problem(pairs: list[tuple[str, str, int]]) -> dict | None:
    """Draw one conversion from `pairs`, in either direction."""
    unit_small, unit_large, factor = random.choice(pairs)
    upwards = random.random() < 0.5

    if upwards:
        v: int | float = random.randint(2, 99)
        unit_in, unit_out = unit_small, unit_large
        c_str = fmt_dec(round(v / factor, 4))
        traps = {
            "multiplies_instead_of_dividing": fmt_dec(round(v * factor, 4)),
            "divides_by_one_power_too_many": fmt_dec(round(v / (factor * 10), 4)),
            # At factor 10 this is the dividend copied back, which names no rule.
            "divides_by_one_power_too_few": (
                fmt_dec(round(v / (factor / 10), 4)) if factor > 10 else None
            ),
        }
        fillers: list[str | None] = [] if factor > 10 else [fmt_dec(v / factor + 1)]
    else:
        v = random.randint(11, 99) / 10
        unit_in, unit_out = unit_large, unit_small
        c_str = fmt_dec(round(v * factor, 4))
        traps = {
            "divides_instead_of_multiplying": fmt_dec(round(v / factor, 4)),
            "multiplies_by_one_power_too_many": fmt_dec(round(v * factor * 10, 4)),
        }
        fillers = [fmt_dec(round((v * factor) + 1, 4))]

    q_str = (
        rf"\text{{Zamień: }} {fmt_dec(v)} \text{{ }} {unit_in} "
        rf"= \_\_\_ \text{{ }} {unit_out}"
    )

    return build_problem_dict(
        q_str,
        c_str,
        traps=traps,
        fillers=fillers,
        parameters={
            "v": v,
            "unit_in": unit_in,
            "unit_out": unit_out,
            "factor": factor,
        },
    )


@declares_traps(
    "multiplies_instead_of_dividing",
    "divides_by_one_power_too_many",
    "divides_by_one_power_too_few",
    "divides_instead_of_multiplying",
    "multiplies_by_one_power_too_many",
)
def dec_unit_1() -> dict | None:
    """Jednostki długości (poziom 1)."""
    return _unit_problem([("mm", "cm", 10), ("cm", "m", 100), ("m", "km", 1000)])


@declares_traps(
    "multiplies_instead_of_dividing",
    "divides_by_one_power_too_many",
    "divides_by_one_power_too_few",
    "divides_instead_of_multiplying",
    "multiplies_by_one_power_too_many",
)
def dec_unit_2() -> dict | None:
    """Jednostki masy (poziom 2)."""
    return _unit_problem([("g", "dag", 10), ("dag", "kg", 100), ("g", "kg", 1000)])


@declares_traps(
    "writes_grosze_in_the_tenths_place",
    "writes_grosze_as_tens_of_grosze",
)
def dec_unit_3() -> dict | None:
    """Złote i grosze (poziom 3)."""
    zl = random.randint(2, 15)
    gr = random.randint(1, 9)  # Single digit grosze forces the "0" trap (e.g. 5.08)

    q_str = rf"\text{{Zamień na złote: }} {zl} \text{{ zł }} {gr} \text{{ gr}}"
    c_str = fmt_dec(zl + (gr / 100))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "writes_grosze_in_the_tenths_place": fmt_dec(zl + (gr / 10)),
            "writes_grosze_as_tens_of_grosze": f"{zl},{gr}0",
        },
        fillers=[fmt_dec(zl + ((gr + 1) / 100))],
        parameters={"zl": zl, "gr": gr},
    )
    if problem:
        return problem
