# Contributing to KomiLab

Thank you for helping make KomiLab better.

## License of contributions

KomiLab is distributed under the MIT License. By submitting a contribution, you
agree that your contribution is licensed under the same MIT License unless a
separate written agreement says otherwise.

## Development checks

Before opening a pull request, run:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

## Third-party code and assets

Do not add third-party source code, binaries, models, game records, images, or
other assets unless their license is compatible with redistribution in a FOSS
project and their copyright/license notices are included.

If a contribution adds bundled third-party material, update
`THIRD_PARTY_NOTICES.md` in the same change.
