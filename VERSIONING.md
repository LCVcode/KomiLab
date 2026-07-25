# Versioning

KomiLab uses semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Current version:

```text
0.2.0
```

Version changes must be made with `uv` so `pyproject.toml`, `uv.lock`, and the local environment stay consistent.

Examples:

```bash
uv version --bump patch
uv version --bump minor
uv version --bump major
uv version 0.1.0
```

Guidance while pre-1.0:

- Patch: small fixes to the current prototype behavior.
- Minor: meaningful new prototype capability, such as engine probing, generated config, game library, or settings UI.
- Major: reserved for future stable/public compatibility-breaking releases.

After changing the version, run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```
