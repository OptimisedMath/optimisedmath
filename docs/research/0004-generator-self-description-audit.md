# Generator self-description audit: all 95 generators

Audit findings for [#227](https://github.com/OptimisedMath/optimisedmath/issues/227). Related: [#221](https://github.com/OptimisedMath/optimisedmath/issues/221), [#226](https://github.com/OptimisedMath/optimisedmath/issues/226).

**Question**: for each of the 95 generators in `backend/chapters/`, does what the generator says about itself match what it actually does?

**Method**: every generator body read in full, once. Class 1 was extracted mechanically (AST docstrings joined against the YAML `function:` → `name:` map); classes 2 and 3 are judgement calls made while reading, with the load-bearing ones confirmed by sampling the generator 2 000–3 000 times and inspecting the emitted parameters.

**Baseline**: `main` at `6535bb0`. The 95 YAML `function:` entries all resolve to a defined generator, and no generator is orphaned.

**Deliberately not fixed here.** This is the report the issue asked for; fixes follow separately.

---

## Summary

| Class | Instances |
|---|---|
| 1 — docstring vs YAML `name:` | **4** |
| 2 — level name vs what the generator produces | **21** (5 severe) |
| 3 — degenerate control flow | **9** (3 severe) |
| Bonus — correctness defects found while reading | **4** |
| Bonus — generators whose yield makes `all_test.py` flaky | **2** |

The severe cases, in one line each:

- `dec_sub_1` ("Bez pożyczania") **guarantees borrowing on every problem** — the guard is inverted.
- `frac_ord_3` ("Dwa Zestawy") has fully hard-coded operands: the Level ships **exactly two problems, forever**.
- `frac_mult_2` and `frac_div_frac_2` both have the #226 seeded-loop shape — each ships **one fixed numerator pair**.
- `dec_div_2` ("Przez liczbę całkowitą (z resztą)") divides by a decimal, and always exactly.
- `dec_mix_2` ("Ułamki w dzieleniu dziesiętnym") contains no division.

---

## Class 1 — docstring vs YAML `name:`

Four instances, all in `Ułamki Zwykłe`. These are the ones #221 identified; **none of the fixes are on `main`**, so they are still live. `frac_sub_5` is a fifth in #221's table but compares equal as a string — it is Class 2 below.

| Generator | File | Docstring says | YAML `name:` | Correct |
|---|---|---|---|---|
| `frac_add_3` | `ulamki_zwykle/topic_60_dodawanie.py:75` | "Liczby mieszane z wyłączaniem" | "Różne mianowniki - wstęp" | **YAML** — the body builds two coprime unlike denominators, no mixed numbers |
| `frac_add_4` | `ulamki_zwykle/topic_60_dodawanie.py:105` | "Różne mianowniki - wstęp" | "Liczby mieszane z wyłączaniem" | **YAML** — two mixed numbers over a single shared `d` |
| `frac_sub_2` | `ulamki_zwykle/topic_70_odejmowanie.py:38` | "Liczby mieszane" | "Różne mianowniki - wstęp" | **YAML** — `d2 = d1 * factor`, no mixed numbers |
| `frac_sub_3` | `ulamki_zwykle/topic_70_odejmowanie.py:81` | "Zabieranie całości" | "Różne mianowniki - zaawansowane" | **YAML** — coprime unlike denominators, no whole parts |

No other docstring/YAML pair differs. Every one of the other 91 docstrings is the YAML name verbatim plus `(poziom N)`.

---

## Class 2 — level name vs what the generator produces

Ordered by severity within each Chapter. "Proposed" is the name that is true of the emitted Problems; it is a suggestion, not a decision.

### Ułamki Zwykłe

| Generator | Level name | What it actually emits | Proposed |
|---|---|---|---|
| `frac_div_num_2` (T100 L2) | "Gdy licznik się nie dzieli" | `k : n/d` — a **whole number divided by a fraction**. No numerator is being divided at all, and the Topic is "Dzielenie przez liczbę" | "Dzielenie liczby przez ułamek" — **and** check whether it belongs in T100 |
| `frac_div_num_1` (T100 L1) | "Dzielenie licznika" | `n/d : k` answered as `n/(d·k)` — the numerator is **never** divided; `k` is always pushed into the denominator | "Gdy licznik się nie dzieli" (L1 and L2 read as shifted by one, exactly like the Add/Sub case) |
| `frac_frac_of_int_4` (T140 L4) | "Ułamek z liczby mieszanej" | "Powiększ/Pomniejsz liczbę {base} o {n}/{d} jej wartości" — **no mixed number appears anywhere** | "Powiększanie i pomniejszanie o ułamek" |
| `frac_frac_of_int_3` (T140 L3) | "Gdy wynik jest ułamkiem" | The inverse task ("znajdź liczbę, której n/d wynosi …"), and `whole = d * randint(2,6)`, so the answer is **always an integer** | "Szukanie liczby z jej ułamka" |
| `frac_mult_4` (T90 L4) | "Wielkie skracanie" | Two mixed numbers multiplied. **No cancelling is involved**; both Traps are about mixed-number handling | "Mnożenie liczb mieszanych" |
| `frac_mult_3` (T90 L3) | "Mnożenie liczb mieszanych" (plural) | One proper fraction times **one** mixed number | "Mnożenie przez liczbę mieszaną" |
| `frac_sub_5` (T70 L5) | "Różne mianowniki" | A single shared `d` — denominators are always **equal**. `n1 < n2` forces borrowing; all three Traps are borrowing Traps. Also collides with the L2 and L3 names in the same Topic | "Odejmowanie z pożyczaniem całości" (as #221 already proposed) |
| `frac_add_2` (T60 L2) | "Skracanie wyniku" | `d2 = d1 * factor`; **nothing guarantees the result reduces**. The real subject is one denominator being a multiple of the other — which is exactly what `frac_sub_2` is named "Różne mianowniki - wstęp" for | "Różne mianowniki - wstęp", matching its Sub twin |

### Ułamki Dziesiętne

| Generator | Level name | What it actually emits | Proposed |
|---|---|---|---|
| `dec_sub_1` (T60 L1) | "Bez pożyczania" | The guard `if d1 >= d2: return None` keeps only pairs whose **minuend tenth is smaller**, so every emitted problem requires borrowing. Confirmed: 675/675 distinct problems over 2 000 draws | Invert the guard to `if d1 <= d2` — the name is right, the code is wrong. **This is a defect, not a naming choice** |
| `dec_div_2` (T90 L2) | "Przez liczbę całkowitą (z resztą)" | Divisor is `d/10` — a **decimal**, not an integer — and `v1/v2` is always exact, so there is **no remainder** either | "Dzielenie przez części dziesiąte" |
| `dec_div_4` (T90 L4) | "Przez ułamek dziesiętny (zaawansowane)" | Divisor `d ∈ {2,4,5}` is an **integer**; the question text itself says "dopisz zero na końcu dzielnej" | "Dzielenie z dopisaniem zera" — and note L2/L4 have each other's subject |
| `dec_mix_2` (T130 L2) | "Ułamki w dzieleniu dziesiętnym" | `n1/d1 + dec_val` — **addition**, never division. What is true is that `d1 ∈ {3,6,7,9}` makes the decimal non-terminating | "Dodawanie, gdy ułamek nie ma skończonego rozwinięcia" |
| `dec_mix_3` (T130 L3) | "Z nawiasami i różnymi typami" | One multiplication *or* one division of a fraction by a decimal. **No brackets anywhere** | "Mnożenie i dzielenie różnych typów" |
| `dec_unit_1` (T120 L1) | "Zamiana na mniejsze (mm, cm)" | `mm→cm`, `cm→m`, `m→km` — always to the **larger** unit, always dividing. Identical direction to L2; the actual L1/L2 split is length vs mass | "Jednostki długości" |
| `dec_unit_3` (T120 L3) | "Jednostki pieniężne i wagowe (mieszane)" | Only `zł`/`gr`. **No weight unit appears** | "Złote i grosze" |
| `dec_mult_3` (T80 L3) | "Z dużą ilością zer" | `{1.5, 2.5, 3.5, 4.5} · {0.2, 0.4, 0.6, 0.8}` — **no zeros are involved** in operands or products | "Połówki przez części dziesiąte" |
| `dec_number_line_5` (T30 L5) | "Duży odstęp cz. 2" | Extrapolation: the target sits **outside** the two labelled ticks. That is the subject, and it is unrelated to L4 | "Poza ostatnią etykietą" |
| `dec_number_line_4` (T30 L4) | "Duży odstęp" | Step is `0.02` or `0.025` — **smaller** than every earlier Level's step, not a larger gap | "Oś co 0,02 i 0,025" |
| `dec_number_line_2` (T30 L2) | "Oś co 0.01" | `step = random.choice([0.01, 0.001])` — half the problems are thousandths | "Oś co 0,01 i 0,001" |
| `dec_number_line_3` (T30 L3) | "Oś co 0.2 lub podobne" | Step is **always exactly** `0.2` with 5 ticks; "lub podobne" promises variation that does not exist | "Oś co 0,2" |
| `dec_to_frac_2` (T10 L2) | "Ze zwykłego na dziesiętny (mianowniki 10, 100)" | `d ∈ {4,5,20,25}` — **10 and 100 never appear** as denominators. The real L2/L3 split is proper fraction vs mixed number, not the denominator set | "Ze zwykłego na dziesiętny (ułamek właściwy)" |

**Low severity, listed for completeness** (name is loose rather than false): `dec_sub_2` "Z pożyczaniem" does not *guarantee* borrowing, the mirror of the `dec_sub_1` defect; `dec_order_4` "Złożone Działania" covers one two-bracket and one bracket-free template.

---

## Class 3 — degenerate control flow

### Severe: the Level ships a fixed problem set

| Generator | Line | The dead construct | Effect (measured) |
|---|---|---|---|
| `frac_ord_3` | `ulamki_zwykle/topic_130_kolejnosc.py:132` | **Both** templates assign literal Fractions (`a, b = Fraction(1,2), Fraction(1,3)` …). No randomness at all | **2 distinct problems** over 2 000 draws — the entire Level |
| `frac_div_frac_2` | `ulamki_zwykle/topic_110_dzielenie_ulamkow.py:36` | `n1, n2 = 2, 4` then `while math.gcd(n1, n2) == 1:` — the seed pair has `gcd == 2`, so the loop never runs (**this is #226**) | Every problem is `2/d1 : 4/d2`; 42 distinct questions |
| `frac_mult_2` | `ulamki_zwykle/topic_90_mnozenie_ulamkow.py:43` | `n1, d2 = 2, 4` then `while math.gcd(n1, d2) == 1:` — same shape, second instance | Every problem is `2/d1 · n2/4`; 49 distinct questions. The "Skracanie na krzyż" being practised is always the same 2-and-4 cancellation |

### Unreachable guards and no-ops (harmless today, misleading to read)

| Generator | Line | Construct | Why it never fires |
|---|---|---|---|
| `frac_exp_2` | `topic_20_rozszerzanie.py:68` | `if wrong_factor < 1: wrong_factor = factor + 2` | `factor ≥ 2`, so `wrong_factor ≥ 1` always |
| `frac_sub_2` | `topic_70_odejmowanie.py:58` | `abs(d1 - d2) if d1 != d2 else 1` | `d2 = d1 * factor` with `factor ≥ 2` — never equal |
| `frac_number_line_4` | `topic_50_os_liczbowa.py:176` | `if total_ticks > 16: total_ticks = 16` | `idx2 ≤ 8`, so `total_ticks ≤ 13` |
| `frac_add_1` | `topic_60_dodawanie.py:28` | `abs(n1 + n2 - 1)` | `n1 + n2 ≥ 2`, so the value is never negative |
| `dec_order_1` | `topic_110_kolejnosc.py:48` | `(a - b) / c if c != 0 else 0` | `c = randint(2,5) * 0.1` — never zero |
| `dec_unit_3` | `topic_120_jednostki.py:81` | `ones_digit = gr % 10`, commented "Bulletproof" | `gr = randint(1, 9)` — the modulo is the identity |

---

## Bonus — correctness defects found while reading

Outside the issue's three classes, but they surfaced on the same read and each one ships a wrong answer or a wrong Trap.

1. **`frac_ord_5` and `frac_ord_6` publish the wrong answer when the expression is negative.** Both end with `if ans < 0: ans = abs(ans)`, so the Problem states an answer that is the negation of the displayed expression's true value. Reachable in both: `frac_ord_5` at `a = b = 1/3, c = 1/2`; `frac_ord_6` at five of its operand combinations, e.g. `a = 1/2, b = c = 1/3, d = 1/4`. The fix is to reject the draw, not to flip the sign.
2. **`dec_mix_2`'s `adds_numerators_and_denominators` Trap uses the wrong denominator** — `format_answers(n1 + n2, d1 + 10)` where the slug (and every sibling generator) means `d1 + d2`. It happens to be right only when `d2 == 10`, i.e. one third of draws (`topic_130_dzialania_mieszane.py:67`).
3. **`frac_sub_2`'s `subtracts_numerators_without_expanding` Trap can be zero** — `abs(n1 - n2)` is `0` whenever `n1 == n2`, offering `0` as a distractor (`topic_70_odejmowanie.py:54`).
4. **`frac_frac_of_int_1`'s `swaps_the_numerator_and_denominator` Trap divides by a non-divisor** — `k // n * d` floors on a `k` that `n` need not divide, so the Trap value does not model the stated misconception (`topic_140_ulamek_liczby.py:28`).

---

## Generator yield — the `all_test.py` flake

Not a naming or control-flow fault, but it surfaced on the same read and it is why
`all_test.py::test_universal_math_structure[frac_sub_2]` fails intermittently on a
clean tree.

`all_test.py` asks each generator for **10 valid Problems in at most 100 attempts**.
A generator that rejects most of its draws — by an explicit guard, or by
`build_problem_dict` returning `None` when two options collide — can miss that floor
by chance. Measured yield (fraction of calls returning a Problem, 20 000 draws each),
and the resulting per-run failure probability:

| Generator | Yield | `P(<10 in 100)` | Why the draws die |
|---|---|---|---|
| `frac_sub_2` | 0.19 | 0.42% | The guard `if (n1 * factor) <= n2: return None` kills 57% of draws; an option collision then kills 54% of the survivors |
| `frac_sub_3` | 0.20 | 0.25% | Same shape: the coprime-and-ordering guards kill 68% of draws, collisions 37% of the survivors |
| `frac_comp_3` | 0.27 | 0.001% | — |
| every other generator | ≥ 0.31 | negligible | — |

Over the 95 parametrized cases that is a **~0.7% chance of a red `all_test.py` on any
given run**, concentrated almost entirely in `frac_sub_2`. Reproduced on `main` at the
audit baseline, with no source change involved.

Two independent things are worth separating here. The **test** is fragile: a fixed
100-attempt budget encodes an assumption about yield that no generator declares. The
**generators** are wasteful: `frac_sub_2` throws away four draws in five, and roughly
half of the survivors die on an option collision, which is the Trap arithmetic
colliding with the correct answer rather than bad luck. Raising the attempt budget
hides the flake; constraining the draw so the guard passes by construction fixes both.

---

## What this says about a standing check

The issue asked whether the drift is widespread enough to justify a permanent CI assertion. On this evidence: **no for Class 1, yes for Class 3.**

- **Class 1 is 4 instances, all from one already-diagnosed edit** in two adjacent files, and all four already have fixes waiting in the #221 branch. A `docstring == YAML name` assertion would hard-couple the same Polish prose in two places, exactly as the issue anticipated, to catch a fault that has occurred once. The cheaper fix is to stop repeating the name: derive the docstring's subject line from the YAML at load time, or drop the name from the docstring entirely.
- **Class 3 is mechanical and a check would be cheap.** Two of the three severe instances are the *same seeded-loop shape*, found independently in two files, and neither the test suite nor a reader notices. A variety assertion — draw each generator N times, require more than a floor of distinct `parameters` tuples — would have caught `frac_ord_3`, `frac_mult_2` and `frac_div_frac_2` together, needs no duplicated prose, and does not fail on rewording. The floor has to skip the number-line Levels, whose `question` is a constant string with the variation living in the SVG.
- **Class 2 cannot be checked automatically at all** — 21 instances, every one a judgement about whether Polish prose is true of a distribution of Problems. It is also the biggest group, which argues for making it part of the review checklist when a Level is added or reworked.
