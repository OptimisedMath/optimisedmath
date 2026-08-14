# Domain docs

How to consume this repo's glossary and ADRs.

## Language split

English in code and glossary; Polish in student-facing UI. See [ADR-0001](../adr/0001-english-code-polish-ui.md).

## Before exploring

- [CONTEXT.md](../../CONTEXT.md) — glossary. Use these terms in names and issue titles; check each entry's `_Avoid_` line.
- [docs/adr/](../adr/) — ADRs that touch the area you're about to work in.

If a concept isn't in the glossary yet, either the project doesn't use that language (reconsider) or there's a gap for `/domain-modeling`.

## ADR conflicts

If your output contradicts an existing ADR, surface it rather than silently overriding:

> *Contradicts ADR-0002 (backend owns game rules) — but worth reopening because…*
