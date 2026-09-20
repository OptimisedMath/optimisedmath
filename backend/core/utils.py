"""Shared formatting, parsing, and problem-dict utilities for generators."""

import math
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


# --- Units ---


def declares_units(*units: str) -> Any:
    """Declare the Units a generator may pick from, and hand it that tuple.

    `generate_problem` calls a generator with no arguments, so a Unit cannot be
    passed in — the generator draws its own. That leaves the Level's
    `expected_units` and the generator's choice as two lists that could drift, so
    the declaration is checked against the YAML at load time, exactly as
    `declares_traps` is (ADR-0005 as amended by #237).
    """

    def decorate(func: Any) -> Any:
        func.expected_units = tuple(units)
        return func

    return decorate


def declared_units(func: Any) -> tuple[str, ...]:
    """The Units a generator declares, or an empty tuple if it declares none."""
    return getattr(func, "expected_units", ())


# --- Filler generation (ADR-0009) ---

_MAX_TRAPS = 3
_FILLER_DELTAS = (-3, -2, -1, 1, 2, 3)

_MIXED_RE = re.compile(r"^(-?)(\d+)\\frac\{(\d+)\}\{(\d+)\}$")
_FRACTION_RE = re.compile(r"^(-?)\\frac\{(\d+)\}\{(\d+)\}$")
_SLASH_RE = re.compile(r"^(-?)(\d+)/(\d+)$")
_DECIMAL_RE = re.compile(r"^(-?\d+),(\d+)$")
_WHOLE_RE = re.compile(r"^-?\d+$")


def _is_negative_option(value: str) -> bool:
    return value.lstrip().startswith("-")


def _in_lowest_terms(numerator: int, denominator: int) -> bool:
    return math.gcd(numerator, denominator) == 1


def _answer_form(value: str) -> str:
    """Which of the five forms in ADR-0009's table `value` is written in."""
    if _MIXED_RE.fullmatch(value):
        return "mixed"
    if _FRACTION_RE.fullmatch(value):
        return "fraction"
    if _SLASH_RE.fullmatch(value):
        return "slash"
    if _DECIMAL_RE.fullmatch(value):
        return "decimal"
    if _WHOLE_RE.fullmatch(value):
        return "whole"
    return "unrecognized"


def _decimal_from_units(units: int, places: int) -> str:
    scale = 10**places
    sign = "-" if units < 0 else ""
    whole, frac = divmod(abs(units), scale)
    return f"{sign}{whole},{str(frac).zfill(places)}"


def _filler_candidates(source: str) -> list[str]:
    """Near misses of `source`, written in its own Answer form (ADR-0009's table).

    Each candidate keeps the source's shape: a mixed number stays mixed with a
    whole part >= 1, a proper fraction stays proper and an improper one improper,
    the denominator stays above 1, a fraction keeps being in lowest terms iff the
    source was, and a decimal keeps its number of decimal places.
    """
    if m := _MIXED_RE.fullmatch(source):
        sign, whole_s, num_s, den_s = m.groups()
        whole, num, den = int(whole_s), int(num_s), int(den_s)
        lowest = _in_lowest_terms(num, den)
        out = []
        for delta in _FILLER_DELTAS:
            new_whole = whole + delta
            if new_whole >= 1:
                out.append(f"{sign}{new_whole}\\frac{{{num}}}{{{den}}}")
        for delta in _FILLER_DELTAS:
            new_num = num + delta
            if 0 < new_num < den and _in_lowest_terms(new_num, den) == lowest:
                out.append(f"{sign}{whole}\\frac{{{new_num}}}{{{den}}}")
        for delta in _FILLER_DELTAS:
            new_den = den + delta
            if new_den > 1 and 0 < num < new_den and _in_lowest_terms(num, new_den) == lowest:
                out.append(f"{sign}{whole}\\frac{{{num}}}{{{new_den}}}")
        return out

    if m := _FRACTION_RE.fullmatch(source):
        sign, num_s, den_s = m.groups()
        num, den = int(num_s), int(den_s)
        proper = num < den
        lowest = _in_lowest_terms(num, den)
        out = []
        for delta in _FILLER_DELTAS:
            new_num = num + delta
            if new_num <= 0 or (new_num < den) != proper:
                continue
            if _in_lowest_terms(new_num, den) != lowest:
                continue
            out.append(f"{sign}\\frac{{{new_num}}}{{{den}}}")
        for delta in _FILLER_DELTAS:
            new_den = den + delta
            if new_den <= 1 or (num < new_den) != proper:
                continue
            if _in_lowest_terms(num, new_den) != lowest:
                continue
            out.append(f"{sign}\\frac{{{num}}}{{{new_den}}}")
        return out

    if m := _SLASH_RE.fullmatch(source):
        sign, num_s, den_s = m.groups()
        num, den = int(num_s), int(den_s)
        proper = num < den
        lowest = _in_lowest_terms(num, den)
        out = []
        for delta in _FILLER_DELTAS:
            new_num = num + delta
            if new_num <= 0 or (new_num < den) != proper:
                continue
            if _in_lowest_terms(new_num, den) != lowest:
                continue
            out.append(f"{sign}{new_num}/{den}")
        for delta in _FILLER_DELTAS:
            new_den = den + delta
            if new_den <= 1 or (num < new_den) != proper:
                continue
            if _in_lowest_terms(num, new_den) != lowest:
                continue
            out.append(f"{sign}{num}/{new_den}")
        return out

    if m := _DECIMAL_RE.fullmatch(source):
        whole_s, frac_s = m.groups()
        places = len(frac_s)
        negative = whole_s.startswith("-")
        value = int(whole_s.lstrip("-") + frac_s)
        units = -value if negative else value
        return [_decimal_from_units(units + delta, places) for delta in _FILLER_DELTAS]

    if _WHOLE_RE.fullmatch(source):
        value = int(source)
        return [str(value + delta) for delta in _FILLER_DELTAS]

    return []


def _values_equal(a: str, b: str) -> bool:
    """Whether `a` and `b` are the same Answer value, per ADR-0009's Filler collision rule."""
    fraction_a, fraction_b = parse_to_fraction(a), parse_to_fraction(b)
    if fraction_a is not None and fraction_b is not None:
        return fraction_a == fraction_b
    return a == b


def _is_valid_filler(candidate: str, screen: list[str], allow_negative_options: bool) -> bool:
    if not allow_negative_options and _is_negative_option(candidate):
        return False
    return not any(_values_equal(candidate, value) for value in screen)


def _pooled_candidates(
    sources: list[str], screen: list[str], allow_negative_options: bool
) -> list[str]:
    pool: list[str] = []
    seen: set[str] = set()
    for source in sources:
        for candidate in _filler_candidates(source):
            if candidate in seen:
                continue
            seen.add(candidate)
            if _is_valid_filler(candidate, screen, allow_negative_options):
                pool.append(candidate)
    return pool


def _make_fillers(
    authored_values: list[str],
    trap_values: list[str],
    correct: str,
    needed: int,
    allow_negative_options: bool,
) -> list[tuple[str, str]]:
    """Invent up to `needed` Fillers per ADR-0009, or fewer when candidates run out."""
    if needed <= 0:
        return []

    screen = list(authored_values)
    sources = list(dict.fromkeys(trap_values + [correct]))
    picked: list[str] = []

    correct_form = _answer_form(correct)
    correct_is_lonely = (
        sum(_answer_form(value) == correct_form for value in authored_values) == 1
    )
    if correct_is_lonely:
        rescue_pool = [
            candidate
            for candidate in _filler_candidates(correct)
            if _is_valid_filler(candidate, screen, allow_negative_options)
        ]
        if rescue_pool:
            pick = random.choice(rescue_pool)
            picked.append(pick)
            screen.append(pick)

    while len(picked) < needed:
        pool = _pooled_candidates(sources, screen, allow_negative_options)
        if not pool:
            break
        pick = random.choice(pool)
        picked.append(pick)
        screen.append(pick)

    return [(value, FILLER_SLUG) for value in picked]


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
    expected_unit: str | None = None,
    allow_negative_options: bool = False,
) -> ProblemDict:
    """Build the canonical problem dict with options, options_map, and grading_policy.

    `traps` maps Trap slug -> answer string, in the order a Problem should offer
    them (ADR-0008). At most three are offered — the first three whose value is
    not `None`, not negative (unless `allow_negative_options`), and not a string
    already taken. A Trap that cannot be offered frees its slot for the next one.

    Any slot the Traps leave empty is filled by a Filler invented from the shared
    rule in ADR-0009, unless `fillers` is passed explicitly — an escape hatch for
    a call the rule cannot serve (comparison symbols, an Answer form it cannot
    parse), which replaces the rule for that call. A `None` Filler is skipped.

    `parameters` is the structured values the Problem was generated from, keyed by the
    generator's own operand names, for a Deconstruction walkthrough to consume. Required
    on every call — a generator that omits it fails at call time, not silently.

    `expected_unit` is the Unit the answer carries. Every option stays a bare number —
    Radio mode appends the Unit to all four buttons at render time, so it can never be
    the discriminator (#213) — and the Level must declare it in `expected_units`.
    """
    trap_items = list((traps or {}).items())

    accepted_traps: list[tuple[str, str]] = []
    screen = [c_str]
    for slug, value in trap_items:
        if len(accepted_traps) >= _MAX_TRAPS:
            break
        if value is None:
            continue
        if not allow_negative_options and _is_negative_option(value):
            continue
        if value in screen:
            continue
        accepted_traps.append((value, slug))
        screen.append(value)

    option_entries: list[tuple[str, str]] = [(c_str, "correct")] + accepted_traps
    is_comparison = {value for value, _ in option_entries}.issubset({"<", ">", "="})

    if fillers is not None:
        option_entries += [(value, FILLER_SLUG) for value in fillers if value is not None]
    elif not is_comparison:
        needed = _MAX_TRAPS - len(accepted_traps)
        trap_values = [value for _, value in trap_items if value is not None]
        option_entries += _make_fillers(
            screen, trap_values, c_str, needed, allow_negative_options
        )

    options_map: dict[str, str] = {}
    for value, label in option_entries:
        options_map[value] = label

    options = list(options_map.keys())

    if is_comparison:
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
    if expected_unit is not None:
        problem["expected_unit"] = expected_unit
    return problem


# --- Expression parameter (Kolejność wykonywania działań) ---

_FRAC_TOKEN_RE = re.compile(r"\\frac\{(-?\d+)\}\{(\d+)\}")


def latex_to_expression(latex: str) -> str:
    """Convert a Kolejność generator's LaTeX question into its ASCII `expression` parameter.

    `\\frac{n}{d}` becomes `n/d` and `\\cdot` becomes `*`; `+ - : ^ ( )` and decimal
    commas already agree with the ASCII grammar `backend.expression` parses, so no
    other substitution is needed. Relies on every Kolejność `q` string containing
    nothing else LaTeX-specific — true today, and `backend.expression.parse` failing
    on an emitted `expression` is the guard if a future template breaks that.
    """
    return _FRAC_TOKEN_RE.sub(r"\1/\2", latex).replace("\\cdot", "*")


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
    """Format an answer value with a Polish decimal comma, exactly.

    Figure labels use `core.scene.render._fmt` instead, which rounds; that
    docstring owns why the two cannot be one function.
    """
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
