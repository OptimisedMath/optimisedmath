# Backend file map

Module ownership and layers: [layered-modules.md](layered-modules.md).

| Path | Purpose |
| ------ | --------- |
| `core/utils.py` | Shared helpers |
| `chapters/<slug>/topic_{id}_{slug}.py` | Problem generators (auto-registered; `_` prefix for helpers; copy an existing chapter file when adding content) |
| `deconstruction.py` | Walkthrough registry and `build_steps()`; one `@declares_deconstruction(...)` function per Misconception |
| `deconstruction_step.py` | Deconstruction step state transitions — grade, Reveal, advance, persist, completion/Abandonment; used by `session.py`'s `/deconstruction/*` use-cases and `submission_cycle.py`'s Navigation |
| `step_grading.py` | Deconstruction step grading — target answer, correct/incorrect, no Trap/`options_map` |
| `data/` | Curriculum YAML |
| `data/misconceptions.yaml` | Misconception catalogue; optional `deconstruction:` key per entry, validated against `deconstruction.py`'s registry at load time |
| `storage/users.db` | SQLite file; access via `core/db.py` |
