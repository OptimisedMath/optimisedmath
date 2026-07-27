"""Shared formatting, parsing, and problem-dict utilities for generators."""

import uuid
import re
import random
from decimal import Decimal
from fractions import Fraction


def _format_improper_unsimplified(num, den):
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


def format_answers(num, den, whole=0):
    total_num = (whole * den) + num
    u_str = _format_improper_unsimplified(total_num, den)
    c_str = _format_mixed(Fraction(total_num, den))
    return c_str, u_str


def format_fraction_question(n, d, w=None):
    if w is not None and w > 0:
        return rf"{w}\frac{{{n}}}{{{d}}}"
    return rf"\frac{{{n}}}{{{d}}}"


def format_fraction_answer(num, den, whole=0, *, simplify=True) -> str:
    if simplify:
        c_str, _ = format_answers(num, den, whole)
        return c_str
    if whole:
        return format_fraction_question(num, den, whole)
    return str(num) if den == 1 else rf"\frac{{{num}}}{{{den}}}"


def build_problem_dict(
    q_str,
    c_str,
    t1=None,
    t2=None,
    t3=None,
    w1=None,
    w2=None,
    grading_policy="standard",
    image_html=None,
    deconstruction=None,
):
    """Build the canonical problem dict with options, options_map, and grading_policy."""
    option_entries = [
        (c_str, "correct"),
        (t1, "t1"),
        (t2, "t2"),
        (t3, "t3"),
        (w1, "w1"),
        (w2, "w2"),
    ]

    options_map = {}
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

    return {
        "problem_id": str(uuid.uuid4()),
        "question": q_str,
        "image_html": image_html,
        "correct": c_str,
        "options": options,
        "options_map": options_map,
        "grading_policy": grading_policy,
        "deconstruction": deconstruction,
    }


def generate_universal_number_line(ticks_count, labeled_ticks, target_tick):
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
        f"<feMerge><feMergeNode in=\"coloredBlur\"/><feMergeNode in=\"SourceGraphic\"/></feMerge>"
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


def clean_latex(latex_str):
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


def _standardize_spacing(s):
    s = re.sub(r"\s*([/,])\s*", r"\1", str(s))
    return " ".join(s.split())


def check_text_answer(correct_latex, user_text):
    """Checks if the user's text matches the correct answer string."""
    clean_correct = clean_latex(correct_latex)
    return _standardize_spacing(clean_correct) == _standardize_spacing(user_text)


def parse_to_fraction(val_str):
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


def fmt_dec(val):
    d = Decimal(str(val))
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if not s or s == "-0":
        s = "0"
    return s.replace(".", ",")


def clean_mobile_input(user_string):
    """Sanitizes user input to match engine expectations and fix hardware laziness."""
    if not user_string:
        return ""

    s = str(user_string).strip().lower()

    s = s.replace(".", ",")

    s = re.sub(r"(\d)[-\,](\d+/)", r"\1 \2", s)

    s = re.sub(r"\s+", " ", s)

    return s.strip()
