# English codebase, Polish user interface

The product targets Polish students (klasy 4–8, Egzamin Ósmoklasisty), but the engineering vocabulary and codebase stay in English. Polish appears only in user-facing copy: UI labels, feedback messages, curriculum display names, and pedagogical docstrings inside problem generators.

**Why:** Agents and contributors default to English; mixing Polish identifiers into Python/TypeScript creates friction, inconsistent search, and split mental models. Keeping one canonical English term in code (`Streak`, `Flawless`, `Trap`) while rendering Polish in the UI avoids translating the entire stack.

**Rules:**

1. **Glossary (`CONTEXT.md`)** — English canonical terms only. Where the UI uses different Polish copy, note it as `_UI (PL)_:` under that term.
2. **Code** — English for modules, types, fields, tests, and internal comments. Exception: one-line Polish docstrings on `topic_*.py` generators describing the pedagogical intent.
3. **Frontend** — Polish for all visible strings. English only in component names, props, and types (mirroring backend field names).
4. **API payloads** — English keys (`streak`, `flawless_eligible`). Values shown to the student (feedback, chapter names) may be Polish.
5. **Do not** introduce Polish synonyms as alternate code names (e.g. no `passa` field alongside `streak`).

**Considered options:** Full Polish codebase (rejected — poor tooling/agent ergonomics); bilingual identifiers (rejected — doubles maintenance); English UI (rejected — wrong market).

**Consequences:** When adding a domain term, pick the English name first, add Polish UI copy separately, and record both in `CONTEXT.md`. Renaming a glossary term is a deliberate migration, not a drive-by rename.
