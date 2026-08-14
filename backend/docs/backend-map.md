# Backend file map

Module ownership and layers: [layered-modules.md](layered-modules.md).

| Path | Purpose |
|------|---------|
| `core/utils.py` | Shared helpers |
| `chapters/<slug>/topic_{id}_{slug}.py` | Problem generators (auto-registered; `_` prefix for helpers) |
| `data/` | Curriculum YAML |
| `storage/users.db` | SQLite file; access via `core/db.py` |
