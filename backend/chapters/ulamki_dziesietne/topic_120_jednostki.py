import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "divides_by_the_wrong_power_of_ten",
    "multiplies_instead_of_dividing",
    "divides_by_one_power_too_many",
)
def dec_unit_1() -> dict | None:
    """Jednostki długości (poziom 1)."""
    v = random.randint(2, 99)
    pairs = [("mm", "cm", 10), ("cm", "m", 100), ("m", "km", 1000)]
    unit_in, unit_out, factor = random.choice(pairs)

    q_str = (
        rf"\text{{Zamień: }} {v} \text{{ }} {unit_in} = \_\_\_ \text{{ }} {unit_out}"
    )
    c_str = fmt_dec(round(v / factor, 4))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "divides_by_the_wrong_power_of_ten": fmt_dec(
                round(v / (factor / 10 if factor > 10 else 100), 4)
            ),
            "multiplies_instead_of_dividing": fmt_dec(round(v * factor, 2)),
            "divides_by_one_power_too_many": fmt_dec(round(v / (factor * 10), 4)),
        },
        parameters={"v": v, "unit_in": unit_in, "unit_out": unit_out, "factor": factor},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_instead_of_dividing",
    "divides_by_one_power_too_many",
    "divides_by_one_power_too_few",
)
def dec_unit_2() -> dict | None:
    """Jednostki masy (poziom 2)."""
    v = random.randint(2, 99)
    pairs = [("g", "dag", 10), ("dag", "kg", 100), ("g", "kg", 1000)]
    unit_in, unit_out, factor = random.choice(pairs)

    q_str = (
        rf"\text{{Zamień: }} {v} \text{{ }} {unit_in} = \_\_\_ \text{{ }} {unit_out}"
    )
    c_str = fmt_dec(round(v / factor, 4))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_instead_of_dividing": fmt_dec(round(v * factor, 4)),
            "divides_by_one_power_too_many": fmt_dec(round(v / (factor * 10), 4)),
            "divides_by_one_power_too_few": fmt_dec(round(v / (factor / 10), 4)),
        },
        parameters={"v": v, "unit_in": unit_in, "unit_out": unit_out, "factor": factor},
    )

    if problem:
        return problem


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
