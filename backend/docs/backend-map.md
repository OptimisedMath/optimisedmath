# Backend file map

What a filename does not tell you. Module ownership and layering: [layered-modules.md](layered-modules.md); each module's own docstring says what it owns.

| Path | Purpose |
| ------ | --------- |
| `chapters/<slug>/topic_{id}_{slug}.py` | Problem generators — auto-registered by that filename, `_` prefix for helpers. Copy an existing chapter file when adding content |
| `data/` | Curriculum YAML |
| `data/misconceptions.yaml` | Misconception catalogue and the rules for authoring one; its optional `deconstruction:` key is validated against `deconstruction.py`'s registry at load time |
| `storage/users.db` | SQLite file — access only via `core/db.py` |
