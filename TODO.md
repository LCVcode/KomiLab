# KomiLab Working Prototype TODO

Test OGS game for prototype validation:

```text
https://online-go.com/game/88417735
```

## Prototype Goal

Build a local developer prototype that can:

1. Accept an OGS URL or game ID.
2. Download and validate the SGF.
3. Store the SGF locally.
4. Generate controlled KaTrain and KataGo configuration.
5. Select OpenCL KataGo when usable, otherwise CPU KataGo.
6. Launch stock KaTrain with the SGF.
7. Supervise shutdown and avoid orphaned processes.

Packaging is not required for the first working prototype, but code should keep Snap/AppImage compatibility in mind.

---

## Phase 0: Repository Foundation

- [x] Create `pyproject.toml` using `uv`.
- [x] Add `uv.lock`.
- [x] Configure Ruff formatting/linting.
- [x] Configure `ty` type checking.
- [x] Configure pytest.
- [x] Create `src/komilab/` package layout.
- [x] Create `tests/` layout.
- [x] Add basic README with prototype instructions.
- [x] Add `.gitignore` for Python, uv, build outputs, logs, and local artifacts.

Validation commands:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

---

## Phase 1: Core Paths and Configuration

- [x] Implement XDG path resolver:
  - config: `~/.config/komilab/`
  - data: `~/.local/share/komilab/`
  - cache: `~/.cache/komilab/`
  - state/logs: `~/.local/state/komilab/`
- [ ] Implement app config model.
- [ ] Implement TOML config load/save using stdlib `tomllib` for reads.
- [ ] Create generated config directory:
  - `~/.config/komilab/generated/`
- [ ] Add default prototype settings:

```toml
[engine]
backend = "auto"
prefer_gpu = true
cpu_threads = 4

[analysis]
whole_game_enabled = true
initial_visits = 80
live_visits = 300
deep_visits = 1200
background_analysis = true

[review]
close_engine_on_exit = true
restore_launcher_on_exit = true

[logging]
level = "info"
```

---

## Phase 2: OGS Input Normalization

- [ ] Implement `GameSource` protocol.
- [x] Implement `OGSGameSource.normalize_reference`.
- [x] Accept numeric IDs, e.g.:

```text
88417735
```

- [x] Accept full OGS URLs, e.g.:

```text
https://online-go.com/game/88417735
```

- [x] Reject unsupported hosts.
- [x] Reject malformed IDs.
- [x] Ignore query strings and fragments.
- [x] Unit test valid and invalid inputs.

---

## Phase 3: OGS SGF Download

- [x] Verify OGS public game retrieval path. Prototype uses `https://online-go.com/api/v1/games/{id}` and converts the returned move JSON to SGF because the direct SGF endpoint returned 403 during testing.
- [x] Implement download with:
  - explicit timeout,
  - max response size,
  - temporary file,
  - atomic install.
- [x] Test with:

```text
https://online-go.com/game/88417735
```

- [ ] Handle:
  - 404/not found,
  - inaccessible/private game,
  - timeout,
  - connection failure,
  - HTML error response,
  - oversized response.
- [x] Store imported SGF under:

```text
~/.local/share/komilab/games/88417735.sgf
```

---

## Phase 4: SGF Validation

- [x] Implement lightweight SGF validation.
- [x] Confirm file:
  - is text-like,
  - starts like an SGF game tree,
  - is not HTML,
  - appears to be a Go game where practical,
  - is within size limits.
- [ ] Add fixture tests for:
  - valid SGF,
  - HTML error page,
  - empty file,
  - oversized file,
  - malformed SGF.

---

## Phase 5: Local Game Library

- [x] Create SQLite schema using stdlib `sqlite3`.
- [x] Track:
  - internal ID,
  - OGS game ID,
  - source URL,
  - SGF path,
  - import checksum,
  - import timestamp,
  - last reviewed timestamp,
  - review count.
- [x] Implement duplicate detection.
- [x] Implement recent games query.
- [x] Add safe initial migration mechanism.

---

## Phase 6: Runtime Layout

- [ ] Implement `RuntimeLayout` abstraction.
- [ ] For developer prototype, support configurable paths to:
  - `katrain`,
  - KataGo OpenCL binary,
  - KataGo CPU/Eigen binary,
  - bundled/default model,
  - default KataGo config template.
- [ ] Do not hardcode Snap/AppImage paths in core services.

---

## Phase 7: Model Provider

- [ ] Implement `ModelProvider` protocol.
- [ ] Implement `BundledModelProvider`.
- [ ] Use default model:

```text
kata1-b18c384nbt-s9996604416-d4316597426.bin.gz
```

- [ ] Store model metadata:
  - ID,
  - display name,
  - version/source,
  - SHA-256,
  - supported board sizes.
- [ ] Keep future model selection possible, but do not expose model selection in prototype UI.

---

## Phase 8: KataGo Backend Probe

- [ ] Define backend metadata model.
- [ ] Support prototype backends:
  - OpenCL,
  - CPU/Eigen.
- [ ] Probe order:

```text
OpenCL
CPU/Eigen
```

- [ ] Implement health check with timeout.
- [ ] Capture:
  - attempted backend,
  - executable path,
  - exit code,
  - sanitized stderr,
  - selected fallback,
  - timestamp.
- [ ] Persist selected backend result.
- [ ] Show simple engine status:
  - `Analysis engine: GPU`
  - `Analysis engine: CPU — analysis may be slower`
  - `Analysis engine: not available`

Deferred intentionally:

- [ ] CUDA backend.
- [ ] TensorRT backend.

---

## Phase 9: Generated Config Rendering

- [ ] Generate KaTrain config ending in `config.json`, e.g.:

```text
~/.config/komilab/generated/katrain-config.json
```

- [ ] Generate KataGo analysis config:

```text
~/.config/komilab/generated/katago-analysis.cfg
```

- [ ] Render KaTrain config fields for:
  - selected KataGo executable,
  - selected model path,
  - generated KataGo config path,
  - max visits,
  - fast visits,
  - analysis defaults.
- [ ] Verify against pinned KaTrain config schema.
- [ ] Add tests that generated JSON contains expected paths and values.

Important KaTrain launch contract:

```bash
katrain /path/to/katrain-config.json /path/to/game.sgf
```

KaTrain only treats the first argument as a custom config if it ends with `config.json`.

---

## Phase 10: KaTrain Process Supervisor

- [ ] Implement `ReviewFrontend` protocol.
- [x] Implement `KaTrainFrontend`.
- [x] Implement initial process supervision.
- [x] Launch KaTrain with argument list, never shell string.
- [x] Use separate process group/session.
- [ ] On normal exit, verify process group is gone.
- [ ] On stop request:
  - terminate gracefully,
  - wait,
  - escalate only if needed.
- [ ] Add fake KaTrain executable tests for:
  - argument construction,
  - config + SGF handoff,
  - paths with spaces,
  - normal exit,
  - nonzero exit,
  - child cleanup.

---

## Phase 11: Minimal GTK Launcher

Decision: use GTK 3 via PyGObject.

- [x] Create small launcher window with:
  - OGS URL/ID input,
  - `Download and Review` button,
  - `Open Local SGF` button,
  - recent games list,
  - engine status label,
  - diagnostics button/entry.
- [x] Prefer X11:

```text
GDK_BACKEND=x11,wayland
```

- [x] Keep UI errors friendly and non-technical.
- [x] Hide or minimize launcher while KaTrain is running.
- [x] Restore launcher when KaTrain exits.

---

## Phase 12: Diagnostics and Logging

- [ ] Configure stdlib logging.
- [ ] Write logs under XDG state path.
- [ ] Log:
  - app version,
  - runtime layout,
  - OGS import result,
  - SGF validation errors,
  - backend probe attempts,
  - selected backend,
  - KaTrain command with sanitized paths where needed,
  - process exit codes.
- [ ] Implement basic diagnostic report including:
  - KomiLab version,
  - KaTrain version,
  - KataGo version/backend,
  - model metadata,
  - X11/Wayland session type,
  - recent sanitized errors.

---

## Phase 13: End-to-End Prototype Test

Manual end-to-end test:

1. Start KomiLab from developer environment.
2. Paste:

```text
https://online-go.com/game/88417735
```

3. Click `Download and Review`.
4. Confirm SGF is downloaded and stored.
5. Confirm backend probe selects OpenCL or CPU.
6. Confirm generated configs exist.
7. Confirm KaTrain opens the game.
8. Explore variations in KaTrain.
9. Close KaTrain.
10. Confirm KomiLab returns to launcher.
11. Confirm no KaTrain/KataGo orphan processes remain.
12. Confirm recent games contains the imported game.

---

## Phase 14: Prototype Hardening

- [ ] Handle missing KaTrain executable gracefully.
- [ ] Handle missing KataGo executable gracefully.
- [ ] Handle missing model gracefully.
- [ ] Handle backend probe failure gracefully.
- [ ] Handle invalid OGS URL gracefully.
- [ ] Handle duplicate imports.
- [ ] Test paths containing spaces.
- [ ] Test temporary XDG directories.
- [ ] Add smoke-test script.

---

## Later, Not Required for Prototype

- [ ] Snap packaging.
- [ ] AppImage packaging.
- [ ] License manifest.
- [ ] Full settings UI.
- [ ] Remote model catalog.
- [ ] User-facing model selection.
- [ ] CUDA backend.
- [ ] TensorRT backend.
- [ ] OGS account login/sync.
