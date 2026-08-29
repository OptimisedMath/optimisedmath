# Backend file map

Module ownership and layers: [layered-modules.md](layered-modules.md).

| Path | Purpose |
|------|---------|
| `core/utils.py` | Shared helpers |
| `chapters/<slug>/topic_{id}_{slug}.py` | Problem generators (auto-registered; `_` prefix for helpers; copy an existing chapter file when adding content) |
| `deconstruction.py` | Walkthrough registry and `build_steps()`; one `@declares_deconstruction(...)` function per Misconception |
| `data/` | Curriculum YAML |
| `data/misconceptions.yaml` | Misconception catalogue; optional `deconstruction:` key per entry, validated against `deconstruction.py`'s registry at load time |
| `storage/users.db` | SQLite file; access via `core/db.py` |
