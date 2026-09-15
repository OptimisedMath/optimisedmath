# Telemetry stores an answer three times, and its outcome in four buckets

A Student in Radio mode taps a button and telemetry stores the option string the generator built — LaTeX, `\frac{8}{9}`. A Student in Input mode types the same answer and telemetry stores `8/9`. These are the same answer, but they never group, so a query built to find what Students get wrong returns a confident, wrong answer. Fixing that needs more than a cleaner string: three different facts are wanted from one Submission's answer, and no single representation carries all three at once. Decided by #244; the outcome-vocabulary half was settled separately in #259 because a first pass proposed cutting the grader's seven values at some length rather than asking what the values already named.

**Decision — three forms, written once, at write time.** Every answer — the Student's and the Problem's correct one — is stored three ways inside the Submission cycle, where the input mode (Radio or Input) is still known:

- **Raw** — the string exactly as it arrived, never touched.
- **Answer form** — Raw with LaTeX normalized away and nothing else changed. Mode-independent by construction, so a Radio option and the same answer typed become one Answer form; `0,5` and `1/2` stay two, because that difference is sometimes the entire diagnosis.
- **Answer value** — the exact rational the answer denotes, notation erased. `0,5`, `1/2` and `2/4` collapse to one Answer value.

Both derived forms are computed at write time because the input mode is what tells you how to read the raw string, and that knowledge exists nowhere later in the pipeline — a row read back out of the table cannot recover which mode produced it from the string alone.

**Decision — outcome collapses to four buckets, not seven (#259).** `answer_outcome` holds `correct`, `trap`, `wrong`, `soft_error` — the four buckets `CONTEXT.md`'s **Answer Outcome** entry already names — rather than the seven values the grader computes internally on its way to a verdict:

| Grader's internal value | Stored outcome |
|---|---|
| `correct` | `correct` |
| `trap` | `trap` |
| `wrong` | `wrong` |
| `exact_match_violation` | `wrong` — unless the typed string matched a declared Trap, in which case it was already `trap` |
| `syntax_error` | `soft_error` |
| `format_mismatch` | `soft_error` |
| `unsimplified` | `soft_error` |

The collapse is safe only because the three-form answer sits beside it — every distinction the column no longer draws is recomputable from Answer form and Answer value instead of being lost:

| Discarded leaf | Recovered from |
|---|---|
| `syntax_error` | `answer_value` is NULL — only the unparseable path fails to produce one |
| `format_mismatch` | `soft_error`, and the Student's Answer form is a different kind of number from the correct Answer form |
| `unsimplified` | `soft_error`, same kind of number, Answer value equal |
| `exact_match_violation` | `wrong`, and Answer value equals the correct value — only possible under `exact_match_only` |

**Considered options — three-form storage:** Deriving Answer form and Answer value at read time in SQL (rejected — the transformations are regex-driven Python, the existing LaTeX cleaner and fraction parser; SQLite cannot express them, and reimplementing them in SQL is a second copy to keep in sync with the first); storing Answer value alone and dropping Raw or Answer form (rejected — value-only storage erases exactly the mistake `format_mismatch` and `exact_match_only` Levels exist to catch, since `2/4`, `4/8` and `0,5` would all read as one indistinguishable correct-valued row, hiding the wrong-form pattern instead of surfacing it); resolving a Problem's Unit into the stored value at write time (rejected — see ADR-0005's amendment: converting to the Problem's own expected unit makes the stored numbers Level-relative, so the same stored number means a different thing on a different Level, which looks correct and is not).

**Considered options — outcome vocabulary:** Keeping the grader's seven values as the stored outcome (rejected — every distinction beyond the four buckets is recomputable from the recorded answer once it is stored in three forms, so the extra values would be redundant with data already being written); a second column recording what the outcome cost the Student, alongside the four-bucket outcome (rejected — `lock_answer` is exactly the complement of the Soft Error bucket with no exception in `backend/answer_grading.py`, so a cost column would carry zero information the outcome column doesn't already carry, and the two could disagree about a single Submission — the mistake #253 deletes `is_correct` to stop making).

**Consequences:** `answer_outcome` becomes total and never NULL — `correct` is a value, not an absence, closing the gap where `GROUP BY answer_outcome` used to omit every good answer by omission. `is_correct` duplicated exactly that absence and is removed. If an author later declares a Trap for what was previously an unanticipated wrong answer, existing rows for that answer read as `trap` from that point on rather than `wrong` — the anticipated/unanticipated distinction those two values exist to draw, working as intended, not a defect. No grading verdict changes: `lock_answer`, `feedback_type` and `feedback_msg` stay separate keys on `EvalResult`, untouched by what telemetry records. This ADR is a forward decision recorded ahead of the build — the columns and the two normalization functions ship with #253, the Deconstruction attempt table sharing the same outcome vocabulary with #258.
