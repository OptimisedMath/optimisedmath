"""Shared formatting, parsing, and problem-dict utilities for generators."""

import uuid
import re
import random
from decimal import Decimal
from fractions import Fraction
from typing import Any

ProblemDict = dict[str, Any]

# --- Fraction formatting ---


def _format_improper_unsimplified(num: int, den: int) -> str:
    if den == 1:
        return str(num)
    return rf"\frac{{{num}}}{{{den}}}"


def _format_mixed(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)

    n, d = value.numerator, value.denominator
    whole = int(value)
    rem = abs(n) % d

    if rem == 0:
        return str(whole)

    if whole == 0:
        sign = "-" if n < 0 else ""
        return rf"{sign}\frac{{{rem}}}{{{d}}}"

    sign = "-" if n < 0 else ""
    return rf"{sign}{abs(whole)}\frac{{{rem}}}{{{d}}}"


def format_answers(num: int, den: int, whole: int = 0) -> tuple[str, str]:
    total_num = (whole * den) + num
    u_str = _format_improper_unsimplified(total_num, den)
    c_str = _format_mixed(Fraction(total_num, den))
    return c_str, u_str


def format_fraction_question(n: int, d: int, w: int | None = None) -> str:
    if w is not None and w > 0:
        return rf"{w}\frac{{{n}}}{{{d}}}"
    return rf"\frac{{{n}}}{{{d}}}"


def format_fraction_answer(
    num: int, den: int, whole: int = 0, *, simplify: bool = True
) -> str:
    if simplify:
        c_str, _ = format_answers(num, den, whole)
        return c_str
    if whole:
        return format_fraction_question(num, den, whole)
    return str(num) if den == 1 else rf"\frac{{{num}}}{{{den}}}"


# --- Trap slugs ---

# Every Filler shares one label: `answer + 1` has no rule behind it to name.
FILLER_SLUG = "filler"


def declares_traps(*slugs: str) -> Any:
    """Declare the full Trap-slug vocabulary a generator can emit, across all templates.

    A generator picks its template at random, so no single call reveals the whole
    vocabulary — but the curriculum loader has to validate the YAML against it at
    load time. This attribute is that static declaration; `tests/test_trap_slugs.py`
    runs each generator repeatedly to prove the declaration and the body agree.
    """

    def decorate(func: Any) -> Any:
        func.trap_slugs = frozenset(slugs)
        return func

    return decorate


def declared_trap_slugs(func: Any) -> frozenset[str]:
    """The Trap slugs a generator declares, or an empty set if it declares none."""
    return getattr(func, "trap_slugs", frozenset())


# --- Problem dict builder ---


def build_problem_dict(
    q_str: str,
    c_str: str,
    *,
    parameters: dict[str, int | float | str],
    traps: dict[str, str | None] | None = None,
    fillers: list[str | None] | None = None,
    grading_policy: str = "standard",
    image_html: str | None = None,
) -> ProblemDict | None:
    """Build the canonical problem dict with options, options_map, and grading_policy.

    `traps` maps Trap slug -> answer string; `fillers` are padding options that carry
    no rule and all share `FILLER_SLUG`. A `None` value is skipped, so a generator may
    offer a Trap conditionally. Returns None when two options collide.

    `parameters` is the structured values the Problem was generated from, keyed by the
    generator's own operand names, for a Deconstruction walkthrough to consume. Required
    on every call — a generator that omits it fails at call time, not silently.
    """
    option_entries: list[tuple[str | None, str]] = [(c_str, "correct")]
    option_entries += [(value, slug) for slug, value in (traps or {}).items()]
    option_entries += [(value, FILLER_SLUG) for value in (fillers or [])]

    options_map: dict[str, str] = {}
    for value, label in option_entries:
        if value is not None:
            options_map[value] = label

    if len(options_map) != sum(value is not None for value, _ in option_entries):
        return None

    options = list(options_map.keys())

    if set(options).issubset({"<", ">", "="}):
        order = {"<": 0, "=": 1, ">": 2}
        options.sort(key=lambda x: order.get(x, 3))
    else:
        random.shuffle(options)

    problem: ProblemDict = {
        "problem_id": str(uuid.uuid4()),
        "question": q_str,
        "image_html": image_html,
        "correct": c_str,
        "options": options,
        "options_map": options_map,
        "grading_policy": grading_policy,
        "parameters": parameters,
    }
    return problem


# --- Number line SVG ---


def generate_universal_number_line(
    ticks_count: int, labeled_ticks: dict[int, str], target_tick: int
) -> str:
    """Draws a mathematical number line with custom intervals and labels."""
    width = 4000
    height = 900
    svg = f'<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">'

    svg += f'<line x1="250" y1="500" x2="3750" y2="500" stroke="#cbd5e1" stroke-width="15" stroke-linecap="round"/>'
    svg += '<polygon points="3725,463 3775,500 3725,537" fill="#cbd5e1" />'

    start_x = 500
    end_x = 3500
    spacing = (end_x - start_x) / ticks_count
    filter_id = f"glow-{uuid.uuid4().hex[:8]}"
    target_x = start_x + target_tick * spacing

    svg += (
        f'<defs><filter id="{filter_id}">'
        f'<feGaussianBlur stdDeviation="10" result="coloredBlur"/>'
        f'<feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f"</filter></defs>"
    )
    svg += (
        f'<line x1="{target_x}" y1="125" x2="{target_x}" y2="375" stroke="#f43f5e" '
        f'stroke-width="20" stroke-linecap="round" filter="url(#{filter_id})"/>'
    )
    svg += (
        f'<polygon points="{target_x - 50},350 {target_x + 50},350 {target_x},425" '
        f'fill="#f43f5e" filter="url(#{filter_id})" />'
    )

    for i in range(ticks_count + 1):
        x = start_x + i * spacing
        tick_len = 125 if i in labeled_ticks else 75
        tick_width = 15 if i in labeled_ticks else 10
        y1 = 500 - tick_len / 2
        y2 = 500 + tick_len / 2

        tick_color = "#e2e8f0" if i in labeled_ticks else "#64748b"
        svg += f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{tick_color}" stroke-width="{tick_width}" stroke-linecap="round"/>'

        if i in labeled_ticks:
            svg += f'<text x="{x}" y="750" font-family="system-ui, -apple-system, sans-serif" font-size="100" font-weight="600" fill="#f1f5f9" text-anchor="middle">{labeled_ticks[i]}</text>'

    svg += "</svg>"
    return svg


# --- Format-mismatch soft error ---


def check_format_mismatch(user_text: str, correct_latex: str) -> str | None:
    """Intercept answers that are mathematically correct but use the wrong notation.

    Shared by `answer_grading.grade()` and `step_grading.grade_step()` — a Deconstruction
    step needs the same forgiving-notation check a Problem does, without the Trap/
    options_map machinery around it.
    """
    user_str = str(user_text)
    if "/" in user_str and "," in correct_latex:
        return "Wynik poprawny matematycznie, ale to jest zadanie z ułamków dziesiętnych! Zapisz odpowiedź używając przecinka, a nie ułamka zwykłego."
    if ("," in user_str or "." in user_str) and "\\frac" in correct_latex:
        return "Wynik poprawny matematycznie, ale w tym zadaniu powinieneś użyć ułamka zwykłego, a nie dziesiętnego!"
    return None


# --- LaTeX normalization & answer checking ---


def clean_latex(latex_str: str) -> str:
    """Normalize LaTeX to plain text for string comparison."""
    s = str(latex_str).replace("$", "").strip()
    s = re.sub(r"\\displaystyle\s*", "", s)
    s = re.sub(r"(-?\d)\\(?:d|t)?frac", r"\1 \\frac", s)

    while True:
        new_s = s
        new_s = re.sub(r"-\\(?:d|t)?frac\{(\d+)\}\{(\d+)\}", r"-\1/\2", new_s)
        new_s = re.sub(r"\\(?:d|t)?frac\{(-?\d+)\}\{(\d+)\}", r"\1/\2", new_s)
        if new_s == s:
            break
        s = new_s

    return s.strip()


def _standardize_spacing(s: str) -> str:
    s = re.sub(r"\s*([/,])\s*", r"\1", str(s))
    return " ".join(s.split())


def check_text_answer(correct_latex: str, user_text: str) -> bool:
    """Checks if the user's text matches the correct answer string."""
    clean_correct = clean_latex(correct_latex)
    return _standardize_spacing(clean_correct) == _standardize_spacing(user_text)


def parse_to_fraction(val_str: str) -> Fraction | None:
    """Parse forgiving student input into a Fraction, or None on failure."""
    try:
        val_str = str(val_str).strip()

        if re.search(r"\d,\d+/", val_str):
            val_str = re.sub(r"(\d),(\d+/)", r"\1 \2", val_str)
        elif "," in val_str or "." in val_str:
            clean_val = val_str.replace(",", ".").replace(" ", "").strip()
            return Fraction(clean_val)

        if "displaystyle" in val_str or "\\frac" in val_str or "\\dfrac" in val_str:
            val_str = clean_latex(val_str)

        val_str = val_str.strip()

        if " " in val_str:
            parts = val_str.split(" ")
            if len(parts) == 2 and "/" in parts[1]:
                whole = int(parts[0])
                frac = Fraction(parts[1])
                if whole >= 0:
                    return Fraction(
                        whole * frac.denominator + frac.numerator, frac.denominator
                    )
                return Fraction(
                    whole * frac.denominator - frac.numerator, frac.denominator
                )

        return Fraction(val_str)
    except Exception:
        return None


# --- Decimal & mobile input ---


def fmt_dec(val: int | float | Decimal | str) -> str:
    d = Decimal(str(val))
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if not s or s == "-0":
        s = "0"
    return s.replace(".", ",")


def clean_mobile_input(user_string: str) -> str:
    """Sanitizes user input to match engine expectations and fix hardware laziness."""
    if not user_string:
        return ""

    s = str(user_string).strip().lower()

    s = s.replace(".", ",")

    s = re.sub(r"(\d)[-\,](\d+/)", r"\1 \2", s)

    s = re.sub(r"\s+", " ", s)

    return s.strip()
