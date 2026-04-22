import math
import uuid
import re
from fractions import Fraction
import random


def format_answers(num, den, whole=0):
    total_num = (whole * den) + num
    u_str = str(total_num) if den == 1 else rf"\frac{{{total_num}}}{{{den}}}"

    divisor = math.gcd(total_num, den)
    simp_num = total_num // divisor
    simp_den = den // divisor

    i_str = str(simp_num) if simp_den == 1 else rf"\frac{{{simp_num}}}{{{simp_den}}}"

    final_whole = simp_num // simp_den
    final_num = simp_num % simp_den

    if final_num == 0:
        c_str = str(final_whole)
    elif final_whole > 0:
        c_str = rf"{final_whole}\frac{{{final_num}}}{{{simp_den}}}"
    else:
        c_str = rf"\frac{{{final_num}}}{{{simp_den}}}"

    return c_str, i_str, u_str


def format_fraction_question(n, d, w=None):
    if w is not None and w > 0:
        return rf"{w}\frac{{{n}}}{{{d}}}"
    else:
        return rf"\frac{{{n}}}{{{d}}}"


def build_problem_dict(
    q_str,
    c_str,
    i_str=None,
    u_str=None,
    t1=None,
    t2=None,
    t3=None,
    w1=None,
    w2=None,
    grading_policy="standard",
    image_html=None,
):

    options_map = {}
    if c_str is not None:
        options_map[c_str] = "correct"
    if t1 is not None:
        options_map[t1] = "t1"
    if t2 is not None:
        options_map[t2] = "t2"
    if t3 is not None:
        options_map[t3] = "t3"
    if w1 is not None:
        options_map[w1] = "w1"
    if w2 is not None:
        options_map[w2] = "w2"

    expected_count = 1 + sum(1 for x in [t1, t2, t3, w1, w2] if x is not None)
    if len(options_map) != expected_count:
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
        "image_html": image_html,  # <--- NEW FIELD FOR GRAPHICS
        "correct": c_str,
        "improper": i_str,
        "unsimplified": u_str,
        "options": options,
        "options_map": options_map,
        "grading_policy": grading_policy,
    }


def generate_fraction_svg(n, d, start_val=0):
    """Draws a mathematical number line for fractions with white lines."""
    width = 600
    height = 140
    svg = f'<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    svg += '<line x1="40" y1="80" x2="560" y2="80" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>'
    svg += '<polygon points="555,72 570,80 555,88" fill="#ffffff" />'

    start_x = 80
    end_x = 520
    spacing = (end_x - start_x) / d

    for i in range(d + 1):
        x = start_x + i * spacing
        svg += f'<line x1="{x}" y1="70" x2="{x}" y2="90" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>'
        if i == 0:
            svg += f'<text x="{x}" y="125" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">{start_val}</text>'
        elif i == d:
            svg += f'<text x="{x}" y="125" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">{start_val + 1}</text>'

        if i == n:
            svg += f'<line x1="{x}" y1="20" x2="{x}" y2="55" stroke="#e74c3c" stroke-width="4" stroke-linecap="round"/>'
            svg += f'<polygon points="{x-8},50 {x+8},50 {x},65" fill="#e74c3c" />'
            svg += f'<text x="{x}" y="15" font-family="sans-serif" font-size="32" font-weight="bold" fill="#e74c3c" text-anchor="middle">?</text>'
    svg += "</svg>"
    return svg


def generate_universal_number_line(ticks_count, labeled_ticks, target_tick):
    """Draws a mathematical number line with custom intervals and labels."""
    width = 600
    height = 140
    svg = f'<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    svg += '<line x1="40" y1="80" x2="560" y2="80" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>'
    svg += '<polygon points="45,72 30,80 45,88" fill="#ffffff" />'
    svg += '<polygon points="555,72 570,80 555,88" fill="#ffffff" />'

    start_x = 80
    end_x = 520
    spacing = (end_x - start_x) / ticks_count

    for i in range(ticks_count + 1):
        x = start_x + i * spacing
        # Labeled ticks are slightly longer for readability
        tick_len = 20 if i in labeled_ticks else 10
        y1 = 80 - tick_len / 2
        y2 = 80 + tick_len / 2

        svg += f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>'

        if i in labeled_ticks:
            svg += f'<text x="{x}" y="125" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle">{labeled_ticks[i]}</text>'

        if i == target_tick:
            svg += f'<line x1="{x}" y1="20" x2="{x}" y2="55" stroke="#e74c3c" stroke-width="4" stroke-linecap="round"/>'
            svg += f'<polygon points="{x-8},50 {x+8},50 {x},65" fill="#e74c3c" />'
            svg += f'<text x="{x}" y="15" font-family="sans-serif" font-size="32" font-weight="bold" fill="#e74c3c" text-anchor="middle">?</text>'

    svg += "</svg>"
    return svg


def clean_latex(latex_str):
    s = latex_str.replace("$\\displaystyle", "").replace("$", "").strip()

    # FIX: Injects a space between a whole number and a fraction so 1\frac{3}{4} doesn't become 13/4
    s = re.sub(r"(\d)\\frac", r"\1 \\frac", s)

    s = re.sub(r"\\frac\{(\d+)\}\{(\d+)\}", r"\1/\2", s)
    return s.strip()


def check_text_answer(correct_latex, user_text):
    """Checks if the user's text matches the correct answer string, preserving crucial spaces."""
    clean_correct = clean_latex(correct_latex)

    # Remove spaces around slashes and commas, but KEEP spaces between numbers!
    clean_correct = re.sub(r"\s*([/,])\s*", r"\1", clean_correct)
    clean_correct = " ".join(clean_correct.split())

    clean_user = re.sub(r"\s*([/,])\s*", r"\1", str(user_text))
    clean_user = " ".join(clean_user.split())

    return clean_correct == clean_user


def parse_to_fraction(val_str):
    try:
        if "," in val_str or "." in val_str:
            clean_val = val_str.replace(",", ".").replace(" ", "").strip()
            return Fraction(clean_val)

        if "displaystyle" in val_str or "\\frac" in val_str:
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
                else:
                    return Fraction(
                        whole * frac.denominator - frac.numerator, frac.denominator
                    )

        return Fraction(val_str)
    except Exception:
        return None


def fmt_dec(val):
    s = f"{float(val):.10f}"
    s = s.rstrip("0").rstrip(".")
    if not s:
        s = "0"
    return s.replace(".", ",")
