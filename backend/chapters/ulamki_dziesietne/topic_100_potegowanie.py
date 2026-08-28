import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_squaring",
    "one_hundredth_too_large",
)
def dec_pow_1() -> dict | None:
    """Kwadrat ułamka dziesiętnego (poziom 1)."""
    v = random.randint(2, 9) / 10
    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"

    c_str = fmt_dec(round(v**2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_by_the_exponent": fmt_dec(round(v * 2, 1)),
            "ignores_the_point_before_squaring": fmt_dec(round(v * 10) ** 2),
            "one_hundredth_too_large": fmt_dec(round(v**2 + 0.01, 2)),
        },
        parameters={"v": v},
    )
    if problem:
        return problem
