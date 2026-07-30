# KomiLab Prototype

Version: 0.3.2

KomiLab is a Linux desktop launcher for reviewing OGS games locally in stock KaTrain.

## Run the prototype

```bash
uv venv --python 3.10 --system-site-packages .venv
uv sync
uv run komilab
```

The prototype uses GTK 3 through the system `python3-gi` package.

Paste an OGS URL such as:

```text
https://online-go.com/game/88417735
```

Then click **Download and Review**.

Imported OGS games are tracked locally. In-progress and completed games appear in separate lists. Select a saved game and click **Open Selected** to review it. If a tracked game is still in progress, use **Update In-Progress Games** to re-check OGS and overwrite the local SGF when newer moves are found.

On first review, the prototype prepares a known-good CPU KataGo binary under:

```text
~/.local/share/komilab/engines/
```

KaTrain stdout/stderr is captured at:

```text
~/.local/state/komilab/logs/katrain.log
```

## KaTrain command discovery

The prototype launches `katrain` from `PATH` if available. If not, it falls back to:

```bash
uv tool run --from katrain katrain
```

Override with:

```bash
KOMILAB_KATRAIN_COMMAND="/path/to/katrain" uv run komilab
```

## Versioning

Use `uv version` for all version updates. See `VERSIONING.md`.

## Licensing

KomiLab is free and open-source software distributed under the MIT License. See
`LICENSE`.

Third-party tools used or launched by the prototype, including GTK/PyGObject,
KaTrain, KataGo, and development tooling, are not vendored in this repository.
See `THIRD_PARTY_NOTICES.md` for current notes.
