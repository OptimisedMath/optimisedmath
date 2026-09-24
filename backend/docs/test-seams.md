# Test seams

Which property a test protects, and which seam owns it — so an agent adding a
test does not guess at either.

## Three properties, one figure

A Geometria figure can be wrong in three independent ways. Each has a name and
an owning seam.

- **P1 — a label cannot disagree with its own figure.** True by construction
  almost everywhere: `EdgeLabel`, `AngleArc` and `Altitude` read their printed
  text off the constructed `Figure`, never off a second copy of the number. It
  is not true where a label's text is *not* derived from the figure — the
  `unknown` flag, which claims a letter (`a`, `b`, `c`… for an edge, `α β γ δ`
  for an arc, always `h` for an altitude) instead of the measured value. P1 is
  tested only there; asserting it anywhere else asserts the code equals
  itself.
- **P2 — a figure's labels cannot disagree with the Problem's answer and
  Traps.** Nothing in `core/scene/` enforces this: a generator builds the
  figure from pool numbers and separately retypes those numbers into the
  answer and the Traps, and the two can drift. Owned by the generator seam —
  tested exhaustively per Level over its pool, plus a registry-wide floor
  every scene-drawn generator inherits.
- **P3 — a figure is legible.** No label sits on top of another label or
  crosses a stroke. `render.py`'s placement pass already scores this per
  candidate position; owned by the renderer seam, tested registry-wide over
  every scene-drawn generator's figures.

## Rules

**Test at the highest seam that already exists.** Don't invent a lower one. A
function reached only through a higher-level contract is covered there:
`core/utils.py`'s helpers are mostly exercised through grading, the Trap-slug
contract, and Curriculum load-time validation rather than direct unit tests,
and that counts as coverage, not a gap.

**A generator's contract is registry-wide.** Once a property is decided worth
testing for one generator, it is asserted over every entry of
`problem_generation.FUNCTION_REGISTRY` (or the scene-marked subset of it), so
a future generator inherits the contract without a new test being written for
it. Prior art: `test_trap_slugs.py`, `test_no_negative_answers.py`,
`test_parameter_variety.py` and `test_problem_variety.py` already sweep the
whole registry this way.

**No golden or snapshot tests.** A golden asserts "unchanged", never
"correct" — one blessed on the same commit as a bug passes forever, and any
change to the pen unit, a stroke factor or a placement weight rewrites every
coordinate, so the routine fix is to re-record it. That trains a reviewer to
stop reading the diff, and a real defect then arrives looking like a cosmetic
one.

**Pin data by passing it in — never by replacing a module constant.**
Patching a tunable the system is designed to vary (a Deconstruction trigger
count, a reveal threshold) is configuration, and legitimate. Patching a
generator's pool to fake data the system is *not* designed to vary is not:
pin it by passing the value in as a parameter instead.

### The registry patch on the boundary

Four tests monkeypatch `FUNCTION_REGISTRY` directly. Three of them
(`tests/test_session.py`, `tests/test_problem_generation.py` ×2) install a
`fixture_multi_1` entry that has no real counterpart — it exists only under
the fixture Curriculum those tests build, so patching it in is the sole
injection seam for "which callable backs this generator name", not a fake
standing in for real data. That is configuration, cleanly.

`tests/test_api_contract.py::test_generator_messages_override_yaml_traps` is
the one that sits awkwardly: it replaces the *real* `dec_compare_1` entry with
a stub that returns a fixed set of Traps and a generator-supplied message,
then runs the real Curriculum through `generate_level_problem`. By the letter
of the pinning rule this fakes a real generator's output. It is kept on the
configuration side because what it pins is not the comparison `dec_compare_1`
performs but a grading-precedence property — a generator-supplied message
overriding a Trap's YAML default — and `dec_compare_1` takes no parameter to
pin a specific Trap/message combination through. The registry is the only
seam that reaches it. If a second test needs the same thing, prefer giving the
generator itself a parameter (the split-helper pattern Geometria's Levels
use) over reaching for a second registry patch.

## Running the suite

From the repo root, not from `backend/`. The DB is isolated per test by the
autouse `isolated_db` fixture in `tests/conftest.py` — no test manages its own
database file.
