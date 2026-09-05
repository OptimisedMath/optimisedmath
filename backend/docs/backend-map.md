# Backend file map

What a filename does not tell you. Module ownership and layering: [layered-modules.md](layered-modules.md); each module's own docstring says what it owns.

| Path | Purpose |
| ------ | --------- |
| `chapters/<slug>/topic_{id}_{slug}.py` | Problem generators. The filename decides which files are scanned; every module-level callable in one without a `_` prefix is then registered, so a helper must take the prefix. A generator's numeric suffix matches its Level number in the Topic's YAML — reorder the Levels and the functions get renamed with them, or the suffix starts lying (#233). Copy an existing chapter file when adding content; docstring and Trap comments are required ([documentation.md](../../docs/agents/documentation.md)) |
| `data/` | Curriculum YAML |
| `data/misconceptions.yaml` | Misconception catalogue and the rules for authoring one. Validated at load time in both directions: a Trap's `misconception:` must name a catalogue entry, **and every catalogue entry must be referenced by at least one Trap** — an entry added ahead of the Traps that will use it fails the load. Its optional `deconstruction:` key is checked against `deconstruction.py`'s registry |
| `storage/users.db` | SQLite file — access only via `core/db.py` |
