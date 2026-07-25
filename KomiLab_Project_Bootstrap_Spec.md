# KomiLab Project Bootstrap Specification

## 1. Purpose of This Document

This document defines the initial product, architecture, engineering constraints, packaging strategy, agent roles, and reusable skills for **KomiLab**.

It is intended to be given to an agentic coding system so that it can generate the starting state of the repository without needing to rediscover the core product decisions.

The generated project should preserve the decisions in this document unless a later project-level decision explicitly supersedes them.

---

# 2. Project Identity

## 2.1 Name

**KomiLab**

## 2.2 Tagline

**Local AI review for your Go games.**

Alternative descriptive subtitle:

**Review OGS games with local AI.**

## 2.3 Project Summary

KomiLab is a Linux desktop application that gives non-technical Go players a simple path from a public Online Go Server game to an interactive local AI review.

The user pastes an OGS game URL or game ID. KomiLab downloads the SGF, validates and stores it, prepares a controlled KaTrain configuration, selects a usable KataGo backend, and launches stock KaTrain with the downloaded game.

KaTrain provides the visible interactive review interface. KataGo provides local AI analysis. KomiLab owns the surrounding workflow, configuration, packaging, process supervision, backend probing, local game library, diagnostics, and future model management.

The initial goal is not to replace KaTrain. The goal is to make the OGS-to-KaTrain workflow simple, reliable, packaged, and approachable.

---

# 3. Product Goals

KomiLab must provide:

1. A simple Linux installation experience.
2. The ability to download a public OGS game using a full game URL or numeric game ID.
3. An interactive AI review interface through stock KaTrain.
4. Live exploration of alternative moves while score predictions and AI recommendations update.
5. Quick, reliable shutdown of KaTrain and KataGo.
6. Automatic selection of a usable accelerated or CPU KataGo backend.
7. Sensible analysis defaults that work without requiring users to understand KataGo.
8. App-controlled configuration exposed through the application rather than manual file editing.
9. Clear diagnostics and fallback behavior.
10. An architecture that keeps future improvements easy.

---

# 4. Target Users

The primary user is a Go player who:

- Plays games on OGS.
- Wants local AI review.
- May not know what KataGo, KaTrain, OpenCL, CUDA, TensorRT, neural-network weights, or SGF tooling are.
- Should not need to use a terminal.
- Should not need to choose a neural-network model.
- Should not need to configure GPU backends manually.
- Should be able to close the review and know that the AI engine has stopped.

The product should hide implementation details unless they are needed for troubleshooting.

---

# 5. Explicit Scope

## 5.1 Initial Platform Scope

- Linux only.
- x86-64 only.
- Ubuntu 22.04 and newer are the primary tested baseline.
- AppImage should aim for broader Linux distribution compatibility where practical.
- X11 is preferred.
- Wayland should be supported where KaTrain and its GUI stack permit it.
- NVIDIA GPU support is the prioritized accelerated path.
- CPU-only analysis must be available as a fallback.

## 5.2 Initial Game Source Scope

- Public OGS games.
- Input accepted as:
  - Numeric OGS game ID.
  - Full OGS game URL.
  - Local SGF file.
- Account login and account synchronization are not part of the MVP.

## 5.3 Initial Review Scope

- Stock KaTrain is the review frontend.
- Stock KataGo is the analysis engine.
- KomiLab does not initially fork or embed KaTrain.
- KomiLab launches KaTrain as a supervised external process.

## 5.4 Initial Packaging Scope

Primary packages:

1. Snap.
2. AppImage.

Future package:

3. Debian package (`.deb`).

All package formats must be built from the same source tree and release definition.

---

# 6. Non-Goals for the MVP

The following should be deliberately postponed:

- OGS account authentication.
- Automatic synchronization of all games from an OGS account.
- Support for multiple game servers.
- A custom Go board or review frontend.
- A KaTrain fork.
- A user-facing model marketplace.
- Multiple model catalogs.
- Cloud-hosted analysis.
- Mobile support.
- Automatic training plans.
- Player progress analytics.
- Multiple simultaneous review sessions.
- Advanced automatic benchmarking and engine tuning.
- A general-purpose plugin framework.
- User editing of raw KaTrain or KataGo configuration files.

Interfaces should leave room for these capabilities without implementing them prematurely.

---

# 7. Core User Experience

## 7.1 Main Flow

```text
Launch KomiLab
    ↓
Paste OGS game URL or ID
    ↓
Click "Download and Review"
    ↓
KomiLab validates input
    ↓
KomiLab downloads and validates SGF
    ↓
KomiLab probes the best available KataGo backend
    ↓
KomiLab generates controlled KaTrain/KataGo configuration
    ↓
KomiLab hides or minimizes its launcher window
    ↓
KomiLab launches stock KaTrain with the configuration and SGF
    ↓
The KaTrain review window becomes the primary visible interface
    ↓
The user reviews the game and explores variations
    ↓
The user closes KaTrain
    ↓
KomiLab confirms child processes stopped
    ↓
KomiLab returns to the launcher and recent-games view
```

## 7.2 Visible User Controls

The initial launcher should remain small.

Recommended controls:

- OGS game URL or ID input.
- `Download and Review` button.
- `Open Local SGF` button.
- Recent games list.
- Settings button.
- Diagnostics or troubleshooting entry.
- Simple engine status:
  - `Analysis engine: NVIDIA GPU`
  - `Analysis engine: CPU — analysis may be slower`
  - `Analysis engine: not running`

## 7.3 Error Experience

Errors should explain the outcome and next step without exposing stack traces.

Examples:

```text
That OGS game could not be found.
Check the game URL or ID and try again.
```

```text
The GPU analysis engine could not start.
KomiLab switched to CPU analysis.
```

```text
The downloaded file was not a valid Go game record.
```

Detailed technical information belongs in logs and optional diagnostics.

---

# 8. System Architecture

## 8.1 High-Level Architecture

```text
KomiLab Launcher
├── OGS import service
├── SGF validation
├── Local game library
├── Application configuration
├── Backend probe
├── Model manager
├── KaTrain configuration adapter
├── Review frontend adapter
├── Process supervisor
├── Logging and diagnostics
└── Packaging/runtime integration
        ↓
Stock KaTrain
        ↓
Stock KataGo
        ↓
Neural-network model
```

## 8.2 Responsibility of Each Component

### KomiLab

KomiLab owns:

- User-facing launch workflow.
- OGS input normalization.
- SGF downloading.
- SGF validation.
- Local game metadata.
- Recent game history.
- App-specific settings.
- Generated KaTrain configuration.
- Generated KataGo configuration.
- Backend probing.
- Model selection.
- Model storage.
- KaTrain process startup.
- KaTrain process supervision.
- Process-group shutdown.
- Logs and diagnostics.
- Package resource discovery.

### KaTrain

KaTrain owns:

- Board rendering.
- Move navigation.
- Variation exploration.
- Candidate move display.
- Score estimation display.
- Ownership visualization.
- Interactive analysis controls.
- Communication with KataGo during review.

KaTrain is stock upstream software in the MVP.

### KataGo

KataGo owns:

- Position evaluation.
- Candidate move generation.
- Score and ownership estimates.
- Search behavior.
- Neural-network inference.

### Neural-Network Model

The model is a separate weights file loaded by KataGo.

It is not KaTrain and it is not KataGo.

```text
KaTrain → KataGo → neural-network weights
GUI       engine     learned model
```

The MVP bundles one pinned, tested model. Users do not select a model.

---

# 9. Architectural Principles

## 9.1 Minimal Dependencies

KomiLab must prefer:

1. Python standard library.
2. Existing dependencies already required by the selected GUI approach.
3. Small, mature dependencies only when they clearly reduce risk or complexity.

Every new runtime dependency requires justification.

Avoid:

- Large web frameworks.
- Embedded browser runtimes.
- Electron.
- Node.js.
- General-purpose dependency-injection frameworks.
- Plugin frameworks before they are needed.
- Redundant HTTP, logging, configuration, or database libraries when the standard library is adequate.

## 9.2 Replaceable Boundaries

External systems must be hidden behind narrow interfaces.

Required boundaries:

- `GameSource`
- `ReviewFrontend`
- `EngineBackendProbe`
- `ModelProvider`
- `ModelStorage`
- `ConfigRenderer`
- `ProcessSupervisor`

The MVP may have only one implementation for several of these interfaces. The boundary still matters.

## 9.3 Configuration Ownership

KomiLab has one authoritative application configuration.

Suggested path:

```text
~/.config/komilab/config.toml
```

Generated external-tool configuration is separate:

```text
~/.config/komilab/generated/
├── katrain-config.json
└── katago-analysis.cfg
```

Rules:

- `config.toml` represents user intent.
- Generated files represent implementation details.
- Generated files may be recreated.
- Users change supported settings through the KomiLab UI.
- KomiLab should not require users to manually edit generated files.
- KaTrain should be launched against KomiLab’s generated configuration, not an uncontrolled global KaTrain configuration.

## 9.4 User Data Separation

Suggested XDG layout:

```text
~/.config/komilab/
├── config.toml
└── generated/

~/.local/share/komilab/
├── games/
├── models/
├── database.sqlite3
└── licenses/

~/.cache/komilab/
├── downloads/
└── engine/

~/.local/state/komilab/
└── logs/
```

Actual paths must use the XDG environment variables when defined.

## 9.5 Packaging Independence

Core application code must not assume Snap or AppImage paths.

Package-specific code should resolve a `RuntimeLayout` or equivalent object containing:

- KaTrain entry point.
- KataGo executable paths.
- Bundled model path.
- Default configuration templates.
- License files.
- Desktop assets.

Core services receive these paths through configuration or dependency injection.

---

# 10. Proposed Python Package Structure

```text
komilab/
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE
├── CHANGELOG.md
├── src/
│   └── komilab/
│       ├── __init__.py
│       ├── __main__.py
│       ├── application.py
│       ├── cli.py
│       ├── ui/
│       │   ├── launcher.py
│       │   ├── settings.py
│       │   ├── recent_games.py
│       │   └── errors.py
│       ├── config/
│       │   ├── models.py
│       │   ├── loader.py
│       │   ├── migration.py
│       │   └── paths.py
│       ├── games/
│       │   ├── models.py
│       │   ├── library.py
│       │   ├── sgf.py
│       │   └── filenames.py
│       ├── sources/
│       │   ├── base.py
│       │   └── ogs.py
│       ├── review/
│       │   ├── base.py
│       │   ├── katrain.py
│       │   └── supervisor.py
│       ├── engine/
│       │   ├── models.py
│       │   ├── probe.py
│       │   ├── backends.py
│       │   ├── healthcheck.py
│       │   └── config.py
│       ├── models/
│       │   ├── metadata.py
│       │   ├── provider.py
│       │   ├── bundled.py
│       │   ├── remote.py
│       │   ├── storage.py
│       │   └── verify.py
│       ├── runtime/
│       │   ├── layout.py
│       │   ├── discovery.py
│       │   └── environment.py
│       ├── diagnostics/
│       │   ├── logging.py
│       │   ├── report.py
│       │   └── sanitization.py
│       └── errors.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   │   ├── sgf/
│   │   ├── fake_katago/
│   │   └── fake_katrain/
│   └── packaging/
├── assets/
│   ├── komilab.desktop
│   ├── komilab.svg
│   └── licenses/
├── packaging/
│   ├── snap/
│   │   └── snapcraft.yaml
│   ├── appimage/
│   │   ├── AppRun
│   │   └── build.sh
│   └── debian/
│       └── README.md
├── scripts/
│   ├── build-snap
│   ├── build-appimage
│   ├── smoke-test
│   └── verify-licenses
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
└── .opencode/
    ├── agents/
    └── skills/
```

The exact GUI module structure may change after choosing a toolkit. Architectural boundaries should remain.

---

# 11. Python Tooling Requirements

All Python development must use:

- **uv** for environments, dependency management, lock files, and command execution.
- **Ruff** for linting and formatting.
- **ty** for static type checking.
- **pytest** for testing unless a strong reason emerges to use the standard-library test runner.

Required commands should be exposed through project scripts or documented task commands.

Baseline commands:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

Developer formatting command:

```bash
uv run ruff format .
uv run ruff check --fix .
```

Rules:

- Commit `uv.lock`.
- Keep dependency groups explicit.
- Do not add Poetry, pip-tools, Black, Flake8, isort, mypy, or Pyright unless a future decision explicitly replaces the selected toolchain.
- Ruff owns formatting, linting, and import sorting.
- ty owns static type checking.
- CI must run all required checks.
- Production code must be type annotated.
- Avoid blanket type ignores.
- Any lint suppression must be narrow and documented.

---

# 12. OGS Integration

## 12.1 Input Normalization

Accept:

```text
12345678
```

and:

```text
https://online-go.com/game/12345678
```

Normalize either form into an internal OGS game identifier.

The parser should:

- Reject malformed IDs.
- Reject unsupported hosts.
- Ignore harmless URL query parameters and fragments.
- Avoid treating arbitrary remote URLs as trusted download sources.

## 12.2 Download Behavior

The OGS implementation should:

- Download a public completed game as SGF.
- Use explicit connection and read timeouts.
- Limit maximum response size.
- Write downloads to a temporary file.
- Validate before moving into permanent storage.
- Install the SGF atomically.
- Avoid overwriting an existing imported game without a clear rule.
- Record source metadata.

## 12.3 SGF Validation

The MVP does not need a full SGF editing library.

Validation should be sufficient to confirm:

- The response is text-like SGF data.
- It contains an SGF game tree.
- It represents Go where practical to determine.
- It is not an HTML error page.
- Its size is within safe bounds.
- It can be passed to KaTrain.

A small internal parser or carefully selected lightweight SGF dependency may be used. The dependency must be justified.

## 12.4 Future Extension

OGS must implement a general source interface:

```python
from pathlib import Path
from typing import Protocol


class GameSource(Protocol):
    def normalize_reference(self, value: str) -> str: ...
    def download(self, reference: str, destination: Path) -> "ImportedGame": ...
```

Future implementations might include:

- Local SGF source.
- KGS.
- Fox.
- Tygem.
- Account synchronization.

The MVP should not implement these beyond local SGF opening.

---

# 13. KaTrain Integration

## 13.1 Selected Approach

Use **stock KaTrain via a thin integration layer**.

Do not initially:

- Fork KaTrain.
- Embed its UI.
- Reimplement its board.
- Patch its source at runtime.
- Couple unrelated KomiLab modules to KaTrain internals.

## 13.2 Handoff

KomiLab launches KaTrain with:

- A generated KaTrain configuration path.
- The selected SGF path.

Conceptual invocation:

```bash
katrain \
  ~/.config/komilab/generated/katrain-config.json \
  ~/.local/share/komilab/games/12345678.sgf
```

The exact argument order and version-specific behavior must be verified against the pinned KaTrain version and covered by an integration test.

## 13.3 Frontend Behavior

KaTrain is the user-visible review frontend.

KomiLab should:

1. Generate required config.
2. Launch KaTrain.
3. Hide or minimize the launcher.
4. Supervise the KaTrain process.
5. Restore the launcher when KaTrain exits.
6. Record the review session result.
7. Confirm that associated child processes have terminated.

## 13.4 Adapter Interface

```python
from pathlib import Path
from typing import Protocol


class ReviewFrontend(Protocol):
    def open_game(self, sgf_path: Path) -> "ReviewSession": ...
    def is_running(self) -> bool: ...
    def stop(self) -> None: ...
```

Initial implementation:

```text
ReviewFrontend
└── KaTrainFrontend
```

This allows future replacement or deeper integration without changing OGS, model, and library modules.

## 13.5 Version Pinning

Each KomiLab release must pin a tested KaTrain version.

Generated configuration schemas and launch behavior are release-controlled compatibility concerns.

---

# 14. KataGo Integration

## 14.1 Backend Strategy

Prioritize NVIDIA acceleration, while retaining CPU fallback.

Potential KataGo backends may include:

- NVIDIA-optimized backend where packaging and compatibility are acceptable.
- OpenCL.
- Eigen CPU.
- Generic CPU fallback.

The exact first accelerated backend must be selected through implementation testing.

## 14.2 Automatic Probe

KomiLab should probe on first use and when relevant runtime conditions change.

Conceptual sequence:

```text
Detect relevant hardware and drivers
    ↓
Try preferred NVIDIA-capable backend
    ↓
Run a short engine health check
    ↓ success
Persist selected backend
```

On failure:

```text
Try next accelerated backend
    ↓
Run health check
    ↓ failure
Try CPU backend
```

Probe results should include:

- Backend attempted.
- Executable used.
- Exit code.
- Sanitized stderr.
- Health-check result.
- Selected fallback.
- Probe timestamp.
- Relevant environment details.

The normal UI should display only the selected outcome.

## 14.3 Process Management

KaTrain normally owns the KataGo process it starts. KomiLab still owns the overall review session.

Requirements:

- Launch KaTrain in its own process group/session.
- Track the process.
- On normal KaTrain exit, verify the process group is gone.
- On KomiLab-requested stop, send graceful termination.
- Escalate only when graceful termination fails.
- Never leave orphaned KaTrain or KataGo processes.
- Log abnormal shutdown behavior.
- Do not expose force-kill details to users unless troubleshooting requires it.

## 14.4 Generated Configuration

KomiLab must generate a KataGo analysis configuration with sensible defaults and selected resource limits.

Generated configuration must not be the authoritative user settings source.

---

# 15. Analysis Defaults and Settings

Analysis behavior must be configurable through KomiLab, with sensible defaults.

Recommended defaults:

- Perform a quick whole-game analysis pass.
- Give the current viewed position deeper analysis.
- Allow the user to request deeper analysis.
- Use conservative resource limits.
- Do not continue analysis after the review program closes.
- Prefer responsiveness over maximum search depth.
- Avoid saturating the entire machine by default.

Illustrative app-level configuration:

```toml
[engine]
backend = "auto"
cpu_threads = 4
prefer_gpu = true

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

Exact values must be validated on representative machines.

Settings presented to normal users should use human-readable labels. Advanced engine concepts may be hidden behind an advanced settings section.

---

# 16. Model Management

## 16.1 MVP Behavior

Bundle one tested neural-network model.

The user should not choose from a model list.

The release pins:

```text
KomiLab version
KaTrain version
KataGo version/builds
Default model
Default analysis configuration
```

Treat this as a tested release unit.

## 16.2 Required Extensibility

The bundled model must be an implementation of a general model-provider interface.

```text
ModelProvider
├── BundledModelProvider
├── RemoteCatalogProvider       # future
└── LocalImportProvider         # future
```

Core engine code asks the model manager for an active model. It must not assume the model was bundled.

```python
model = model_manager.get_active_model()
engine_config = engine_config_renderer.render(model=model, backend=backend)
```

## 16.3 Future Remote Models

The architecture must leave room for:

- Reading a trusted remote model catalog.
- Displaying available model metadata.
- Downloading a selected model.
- Download progress.
- Checksum verification.
- Atomic installation.
- Compatibility checks.
- Model versioning.
- Switching active models.
- Removing downloaded models.
- Preserving a known-good fallback model.
- Multiple trusted catalogs later.

## 16.4 Model Metadata

Suggested metadata:

```yaml
id: kata-default-19x19
display_name: Default KataGo Model
version: 2026.07
source:
  type: bundled
sha256: "<checksum>"
engine:
  minimum_version: "<version>"
boards:
  - 19
capabilities:
  human_style: false
```

Remote models must be treated as data, never executable code.

## 16.5 Verification

Model files should be:

- Downloaded over HTTPS.
- Size-limited.
- Checksum-verified.
- Written to temporary storage first.
- Installed atomically.
- Rejected when metadata and file content do not match expectations.

---

# 17. Local Game Library

Use SQLite through Python’s standard library unless a later need justifies another storage layer.

Suggested metadata:

- Internal ID.
- OGS game ID.
- Source type.
- Source URL.
- SGF path.
- Black player.
- White player.
- Game date.
- Result.
- Import timestamp.
- Last reviewed timestamp.
- Import checksum.
- Review count.
- Optional analysis/profile version.

The library should support:

- Recent games.
- Duplicate detection.
- Reopening a game.
- Missing-file detection.
- Safe schema migrations.

Do not store generated KataGo analysis data in the initial database unless it is required by the chosen KaTrain integration.

---

# 18. Packaging

## 18.1 Shared Packaging Model

All formats should consume a common staged application layout.

```text
Staged KomiLab application
├── Python application
├── Python runtime and dependencies
├── Stock KaTrain
├── KataGo backend executables
├── Bundled model
├── Default templates
├── Desktop metadata
└── License and attribution files
```

Format adapters then produce:

```text
├── Snap
├── AppImage
└── .deb
```

## 18.2 Snap

Snap is the preferred package format.

Requirements:

- Use strict confinement where practical.
- Declare required network access.
- Support desktop display access.
- Support X11.
- Support Wayland where feasible.
- Support access to host GPU drivers as required.
- Store user data in appropriate writable locations.
- Test KaTrain and KataGo subprocess startup inside confinement.
- Test NVIDIA behavior on a real supported system.
- Test CPU fallback.
- Avoid exposing package-internal paths to users.

## 18.3 AppImage

AppImage should provide a broad download-and-run option.

Requirements:

- Build on a sufficiently old compatible base.
- Bundle required user-space libraries while avoiding libraries that should come from the host.
- Keep host GPU driver interaction functional.
- Include desktop entry and icon metadata.
- Provide optional desktop integration guidance.
- Test on Ubuntu and at least one non-Ubuntu distribution.
- Do not claim universal compatibility.
- Prefer X11 when environment selection is needed.

## 18.4 Debian Package

A `.deb` may be added after paths, dependencies, and runtime behavior stabilize.

It should:

- Follow Debian filesystem conventions.
- Declare dependencies accurately.
- Integrate with desktop menus.
- Support clean uninstall.
- Avoid duplicating package logic that belongs in the common staging process.

## 18.5 Release Automation

CI should:

- Run Python checks.
- Run unit and integration tests.
- Build staged artifacts.
- Build Snap.
- Build AppImage.
- Run package smoke tests.
- Produce checksums.
- Produce a license manifest.
- Attach release artifacts to tagged releases.

Package publication may be added after local builds are stable.

---

# 19. Licensing and Redistribution

Before public release, audit and document licenses for:

- KomiLab.
- KaTrain.
- KataGo.
- Neural-network model.
- Python dependencies.
- Fonts.
- Icons.
- Images.
- Other bundled assets.

Do not blindly redistribute all upstream repository assets.

Requirements:

- Include all required notices.
- Keep a machine-readable or generated dependency/license manifest where practical.
- Avoid assets that prohibit intended redistribution or commercial use.
- Record exact upstream versions and source locations.
- Make license verification part of release checks.

---

# 20. Logging and Diagnostics

## 20.1 Logging

Use Python’s standard `logging` package unless a future requirement proves it insufficient.

Logs should include:

- Application version.
- Package format.
- Runtime paths.
- Backend probe decisions.
- Selected KataGo backend.
- KaTrain launch command with sensitive paths sanitized where needed.
- Process exit codes.
- OGS request outcomes.
- SGF validation failures.
- Configuration migration events.
- Model verification events.
- Fallback decisions.

Logs must not contain secrets if authentication is added later.

## 20.2 Diagnostic Report

Provide an optional report containing:

- KomiLab version.
- KaTrain version.
- KataGo build/version.
- Active model metadata.
- Selected backend.
- X11/Wayland session type.
- Package format.
- Relevant XDG paths.
- Recent sanitized errors.
- Backend probe summary.

The report should be exportable or copyable without requiring terminal use.

---

# 21. Testing Strategy

## 21.1 Unit Tests

Cover:

- OGS URL and ID parsing.
- Invalid references.
- SGF validation.
- File naming.
- XDG path resolution.
- Configuration loading.
- Configuration migration.
- Generated KaTrain configuration.
- Generated KataGo configuration.
- Model metadata.
- Model checksum verification.
- Backend ranking.
- Probe-result parsing.
- Error-to-user-message mapping.

## 21.2 Integration Tests

Use fake executables for KaTrain and KataGo.

Test:

- Launch argument construction.
- Config and SGF handoff.
- Process supervision.
- Graceful shutdown.
- Forced shutdown fallback.
- Child process cleanup.
- Paths containing spaces.
- Nonzero exits.
- Missing executable behavior.
- GPU probe failure and CPU fallback.
- Temporary XDG directories.
- Duplicate game import.
- Interrupted download recovery.

## 21.3 Network Tests

Prefer deterministic mocked/local HTTP tests.

Test:

- Success.
- 404.
- Timeout.
- Connection failure.
- HTML error response.
- Oversized response.
- Truncated SGF.
- Duplicate download.
- Atomic installation.

Live OGS tests should be limited and not required for ordinary CI.

## 21.4 Packaging Smoke Tests

For each package:

- Launch KomiLab.
- Open settings.
- Import a fixture SGF.
- Launch fake or real KaTrain.
- Verify writable paths.
- Verify subprocess startup.
- Verify clean shutdown.
- Verify desktop file.
- Verify logs.
- Verify CPU fallback.
- Verify accelerated backend on designated hardware runners or manual test systems.

## 21.5 Manual Compatibility Matrix

At minimum:

- Ubuntu 22.04 X11.
- Ubuntu current LTS X11.
- Ubuntu current LTS Wayland.
- NVIDIA proprietary driver system.
- CPU-only system.
- One non-Ubuntu AppImage test system.

---

# 22. Security and Reliability Considerations

- Never execute downloaded SGF or model content.
- Restrict OGS input to expected forms.
- Limit HTTP response sizes.
- Use timeouts.
- Verify models.
- Use temporary files and atomic moves.
- Avoid shell command construction.
- Pass subprocess arguments as lists.
- Avoid `shell=True`.
- Use process groups for cleanup.
- Sanitize logs.
- Preserve user game files across upgrades.
- Separate bundled assets from user-managed assets.
- Keep a bundled fallback model.
- Make configuration migrations reversible where practical.
- Avoid destructive cleanup of user data.
- Never remove unknown files from user directories.

---

# 23. Initial Milestones

## Milestone 0: Repository Foundation

- Create `pyproject.toml`.
- Configure uv.
- Commit `uv.lock`.
- Configure Ruff.
- Configure ty.
- Configure pytest.
- Create source layout.
- Create CI.
- Add architecture decision records or equivalent concise decisions.
- Add agent and skill files from this document.

## Milestone 1: Local SGF Review

- Resolve app paths.
- Load app configuration.
- Open a local SGF.
- Generate KaTrain config.
- Launch stock KaTrain.
- Supervise process.
- Restore launcher after exit.
- Verify cleanup.

## Milestone 2: OGS Import

- Parse OGS ID/URL.
- Download SGF.
- Validate.
- Store atomically.
- Add SQLite game record.
- Show recent games.
- Launch imported game.

## Milestone 3: Engine Probe and Fallback

- Define backend metadata.
- Bundle candidate KataGo builds.
- Implement probe.
- Implement health check.
- Select backend.
- Generate KataGo config.
- Log outcome.
- Show simple status.
- Implement CPU fallback.

## Milestone 4: Controlled Settings

- Settings UI.
- Analysis defaults.
- Resource limits.
- Config persistence.
- Config migration.
- Regenerate external configs.

## Milestone 5: Snap

- Common staging layout.
- Snapcraft configuration.
- X11 test.
- Wayland test.
- Network test.
- NVIDIA test.
- CPU fallback test.
- Clean shutdown test.

## Milestone 6: AppImage

- AppDir staging.
- AppRun.
- Build automation.
- Ubuntu compatibility tests.
- Non-Ubuntu compatibility test.
- Desktop integration metadata.
- GPU/CPU tests.

## Milestone 7: Release Hardening

- License audit.
- Diagnostic report.
- Error-message review.
- User documentation.
- Clean-machine smoke tests.
- Tagged release pipeline.

---

# 24. Definition of Done for the MVP

The MVP is complete when a non-technical user on a supported Ubuntu x86-64 desktop can:

1. Install or run KomiLab using Snap or AppImage.
2. Paste a public OGS game URL or ID.
3. Download the game without using a terminal.
4. Open the game automatically in KaTrain.
5. Explore alternative moves interactively.
6. See AI score predictions update.
7. Use NVIDIA acceleration when available.
8. Fall back to CPU when acceleration fails.
9. Close the review normally.
10. Have KaTrain and KataGo stop completely.
11. Reopen a recently imported game.
12. Change supported analysis settings through KomiLab.
13. Obtain a useful diagnostic report when something fails.

---

# 25. Agent and Skill Layout

Recommended OpenCode layout:

```text
.opencode/
├── agents/
│   ├── architect.md
│   ├── python-developer.md
│   ├── engine-integrator.md
│   ├── qa-reviewer.md
│   ├── packaging-release.md
│   └── user-advocate.md
└── skills/
    ├── komilab-architecture/
    │   └── SKILL.md
    ├── python-project/
    │   └── SKILL.md
    ├── ogs-integration/
    │   └── SKILL.md
    ├── katrain-integration/
    │   └── SKILL.md
    ├── katago-integration/
    │   └── SKILL.md
    ├── model-management/
    │   └── SKILL.md
    ├── linux-packaging/
    │   └── SKILL.md
    └── testing-desktop-subprocesses/
        └── SKILL.md
```

If the selected coding system uses a different discovery path, preserve the file contents and adapt only the containing paths.

---

# 26. Skill Drafts

## 26.1 `.opencode/skills/komilab-architecture/SKILL.md`

```markdown
# KomiLab Architecture

## Purpose

Preserve KomiLab's product boundaries, extensibility, minimal-dependency goals, and non-technical-user experience.

Use this skill for all architectural decisions and for work that crosses multiple KomiLab modules.

## Product Definition

KomiLab is a Linux x86-64 desktop launcher and integration layer that:

1. Accepts a public OGS game URL or game ID.
2. Downloads and validates the SGF.
3. Selects a usable local KataGo backend.
4. Generates controlled KaTrain and KataGo configuration.
5. Launches stock KaTrain with the SGF.
6. Supervises the review session and ensures clean shutdown.

KaTrain is the visible review frontend. KataGo is the analysis engine. A separate neural-network weights file is loaded by KataGo.

## Mandatory Decisions

- Use Python.
- Use stock KaTrain through an adapter; do not fork it initially.
- Target Linux x86-64.
- Test Ubuntu 22.04 and newer first.
- Prefer X11 while supporting Wayland where practical.
- Prioritize NVIDIA acceleration.
- Provide CPU fallback.
- Use Snap and AppImage initially.
- Leave room for `.deb`.
- Keep runtime dependencies minimal.
- Keep app settings in an app-owned configuration file.
- Change supported settings through the app.
- Treat generated KaTrain and KataGo configuration as disposable implementation details.
- Bundle one default model initially.
- Hide model choice from ordinary users.
- Preserve interfaces for future remote model catalogs and downloads.

## Architecture Rules

External integrations must sit behind narrow interfaces:

- `GameSource`
- `ReviewFrontend`
- `EngineBackendProbe`
- `ModelProvider`
- `ModelStorage`
- `ConfigRenderer`
- `ProcessSupervisor`

Core modules must not know package-format-specific paths. Resolve packaged resources through a runtime-layout abstraction.

Do not introduce a general plugin system in the MVP. Use clear interfaces and dependency injection instead.

## Dependency Direction

Preferred dependency flow:

```text
UI
↓
Application services
↓
Domain interfaces
↓
Integration adapters
↓
External programs and network services
```

Domain and application modules must not import Snap, AppImage, OGS URL details, KaTrain internals, or specific KataGo executable layouts directly.

## Configuration Rules

Authoritative configuration:

```text
~/.config/komilab/config.toml
```

Generated configuration:

```text
~/.config/komilab/generated/
```

User data:

```text
~/.local/share/komilab/
```

Use XDG environment variables when present.

## Change Evaluation

Before accepting an implementation, ask:

1. Does this expose technical details unnecessarily?
2. Does this hardwire KaTrain, KataGo, OGS, a model, or a package path into unrelated code?
3. Can the component be replaced behind an existing interface?
4. Does this add a dependency that the standard library could avoid?
5. Does this make future remote model management harder?
6. Does this risk orphaning child processes?
7. Does this preserve user data across upgrades?
8. Can the failure be explained clearly to a non-technical user?

## Explicit Non-Goals

Do not add these without a new project decision:

- Custom Go board.
- KaTrain fork.
- OGS account synchronization.
- Cloud analysis.
- Plugin framework.
- Multiple game servers.
- User-facing model marketplace.
- Mobile support.
```

---

## 26.2 `.opencode/skills/python-project/SKILL.md`

```markdown
# KomiLab Python Engineering

## Purpose

Define mandatory Python development practices for KomiLab.

## Toolchain

Use:

- `uv` for environments, dependency management, locking, and command execution.
- `ruff` for formatting, linting, and import sorting.
- `ty` for static type checking.
- `pytest` for tests.

Do not add Poetry, pip-tools, Black, Flake8, isort, mypy, or Pyright unless a later project decision explicitly replaces the chosen toolchain.

Commit:

- `pyproject.toml`
- `uv.lock`

Required validation:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

Formatting:

```bash
uv run ruff format .
uv run ruff check --fix .
```

## Dependency Policy

Prefer, in order:

1. Python standard library.
2. Dependencies already required by the chosen GUI stack.
3. Small, mature libraries with clear maintenance and licensing.

Every added runtime dependency must have a written justification in the change description.

Avoid:

- Webview runtimes.
- Embedded browsers.
- Node.js.
- Heavy framework abstractions.
- Duplicate configuration, HTTP, logging, or database libraries when the standard library is sufficient.

## Project Layout

Use a `src/` layout.

```text
src/komilab/
tests/
```

Keep integration-specific code in adapter modules.

## Type Safety

- Type annotate production code.
- Use precise return types.
- Prefer immutable value objects where appropriate.
- Avoid `Any`.
- Avoid broad `# type: ignore`.
- Narrow unavoidable suppressions to one expression and explain them.
- Keep protocol/interface definitions small.

## Error Handling

- Define domain-specific exceptions.
- Preserve the original cause with exception chaining.
- Translate technical failures into user-facing messages at the UI boundary.
- Never expose raw stack traces in the normal interface.
- Log technical details.
- Do not silently swallow failures.

## Filesystem Rules

- Use `pathlib.Path`.
- Follow XDG paths.
- Use temporary files and atomic moves for downloads and generated assets.
- Never assume the current working directory.
- Never delete unknown user files.
- Test paths containing spaces and non-ASCII characters.

## Subprocess Rules

- Pass argument lists, not shell strings.
- Never use `shell=True` for KaTrain or KataGo.
- Use explicit environments.
- Use process groups/sessions for supervised review processes.
- Capture and log failures without deadlocking pipes.
- Ensure child processes are stopped on shutdown.

## Logging

Use the standard `logging` package.

- Use module loggers.
- Use structured, stable event wording.
- Avoid secrets.
- Include enough context for diagnostics.
- Do not log full SGF content.

## Tests

- Prefer deterministic tests.
- Use temporary XDG directories.
- Use fake KaTrain and KataGo executables.
- Mock OGS through a local test server or transport boundary.
- Cover errors, fallback, cleanup, migrations, and paths with spaces.
```

---

## 26.3 `.opencode/skills/ogs-integration/SKILL.md`

```markdown
# OGS Integration

## Purpose

Define how KomiLab accepts, downloads, validates, and stores public OGS games.

## Accepted Input

Accept:

- Numeric game ID.
- Full `online-go.com` game URL.

Normalize both into one internal game identifier.

Reject:

- Unsupported hosts.
- Malformed identifiers.
- Arbitrary remote download URLs.

## Download Requirements

- Use explicit connect and read timeouts.
- Limit response size.
- Download to temporary storage.
- Validate before permanent installation.
- Move into place atomically.
- Detect duplicates.
- Preserve source metadata.
- Produce clear errors for unavailable or invalid games.

## SGF Validation

At minimum, verify:

- Response is not an HTML error page.
- Content resembles an SGF game tree.
- Content is within size limits.
- File can be handed to KaTrain.
- Go game metadata is present where practical.

Avoid a heavy SGF framework unless a lightweight implementation is demonstrably insufficient.

## Interface Boundary

OGS must implement `GameSource`.

Other modules must not construct OGS URLs directly.

## Future Compatibility

Do not couple game-library or review code to OGS-specific identifiers.

Leave room for:

- Account synchronization.
- Other Go servers.
- Local imports.
- Additional source metadata.

Do not implement those features in the MVP.
```

---

## 26.4 `.opencode/skills/katrain-integration/SKILL.md`

```markdown
# KaTrain Integration

## Purpose

Define how KomiLab uses stock KaTrain as an external review frontend.

## Core Decision

Use stock, version-pinned KaTrain.

Do not:

- Fork KaTrain initially.
- Embed its UI.
- Duplicate its board or analysis interface.
- Patch upstream source at runtime.
- Import KaTrain internals from unrelated modules.

## Launch Handoff

KomiLab supplies:

- Generated KaTrain configuration.
- Selected SGF file.

The exact CLI invocation must be verified against the pinned version and covered by an integration test.

## User Experience

When review begins:

1. Generate configuration.
2. Hide or minimize the KomiLab launcher.
3. Launch KaTrain.
4. Treat KaTrain as the primary visible interface.
5. Supervise the process.
6. Restore KomiLab when KaTrain exits.
7. Record review history.
8. Verify process cleanup.

## Interface

Implement KaTrain behind `ReviewFrontend`.

The adapter owns:

- Command construction.
- Environment construction.
- Process launch.
- Session state.
- Exit interpretation.
- Stop behavior.
- Version compatibility checks.

## Configuration

KaTrain must consume KomiLab-generated configuration.

Do not rely on uncontrolled user-global KaTrain settings for required behavior.

KomiLab's app configuration remains authoritative.

## Compatibility

Pin a KaTrain version per KomiLab release.

Test:

- SGF opening.
- Config argument handling.
- X11.
- Wayland where practical.
- Paths containing spaces.
- Normal exit.
- Crash exit.
- Process-group cleanup.
- Snap.
- AppImage.
```

---

## 26.5 `.opencode/skills/katago-integration/SKILL.md`

```markdown
# KataGo Integration

## Purpose

Define KataGo backend selection, health checking, configuration, logging, and lifecycle requirements.

## Backend Goals

- Prioritize NVIDIA acceleration.
- Prefer an easy automatic selection.
- Provide CPU fallback.
- Keep backend details out of the normal user flow.
- Log every probe decision.

## Probe Process

For each candidate backend:

1. Confirm the executable is available.
2. Build a controlled minimal configuration.
3. Run a short health check.
4. Apply a timeout.
5. Capture exit code and sanitized stderr.
6. Record success or failure.
7. Select the highest-ranked working backend.

Persist the selected result, but re-probe when:

- The configured backend changes.
- Packaged engine versions change.
- Relevant driver or hardware conditions appear to change.
- The selected backend fails at runtime.

## UI Behavior

Normal UI:

```text
Analysis engine: NVIDIA GPU
```

or:

```text
Analysis engine: CPU — analysis may be slower
```

Do not expose backend implementation details unless the user opens diagnostics.

## Configuration

Generate KataGo configuration from KomiLab app settings.

Support configurable:

- Backend preference.
- CPU thread limit.
- Whole-game analysis effort.
- Live analysis effort.
- Deep analysis effort.
- Background analysis.
- Resource limits.

Use conservative defaults.

## Process Rules

KaTrain may start KataGo, but KomiLab owns the review session.

- Launch KaTrain in a supervised process group.
- Confirm child cleanup.
- Terminate gracefully first.
- Escalate only when required.
- Never leave orphaned AI processes.
- Log abnormal shutdowns.

## Versioning

Pin KataGo builds per KomiLab release.

Do not silently mix arbitrary engine binaries and generated configurations.
```

---

## 26.6 `.opencode/skills/model-management/SKILL.md`

```markdown
# Model Management

## Purpose

Keep KomiLab's initial bundled KataGo model simple while preserving a clean path to remote catalogs, downloads, imports, and model switching.

## MVP

- Bundle one tested model.
- Select it automatically.
- Do not present model choice to ordinary users.
- Treat the model as part of the pinned release unit.
- Preserve a bundled known-good fallback.

## Architecture

Use a `ModelProvider` boundary.

Initial implementation:

```text
BundledModelProvider
```

Future implementations:

```text
RemoteCatalogProvider
LocalImportProvider
```

Engine code must request an active model from the model manager. It must not contain bundled-model path assumptions.

## Metadata

Track:

- Stable model ID.
- Display name.
- Version.
- Source.
- SHA-256.
- Required KataGo version.
- Supported board sizes.
- Optional capabilities.

## Remote Download Requirements

Future remote model support must include:

- Trusted HTTPS sources.
- Explicit catalog metadata.
- Download progress.
- Size limits.
- Checksum verification.
- Temporary files.
- Atomic installation.
- Compatibility validation.
- Clear rollback/fallback.
- Separate bundled and user-managed storage.

Downloaded models are data and must never be executed.

## Update Rules

Application updates must not silently replace a user-selected downloaded model.

Bundled defaults and user-managed models must remain separate.
```

---

## 26.7 `.opencode/skills/linux-packaging/SKILL.md`

```markdown
# Linux Packaging

## Purpose

Define shared and format-specific packaging requirements for KomiLab.

## Supported Formats

Initial:

- Snap.
- AppImage.

Future:

- Debian package.

## Shared Staging Layout

Build one staged application containing:

- KomiLab.
- Python runtime and dependencies.
- Stock KaTrain.
- KataGo backend executables.
- Bundled model.
- Templates.
- Desktop metadata.
- Licenses.

Package formats consume this shared layout.

Core code must not hardcode package-specific paths.

## Snap

- Preferred package.
- Use appropriate confinement.
- Declare network access.
- Support X11.
- Support Wayland where practical.
- Enable required GPU-driver access.
- Test NVIDIA acceleration.
- Test CPU fallback.
- Test subprocess startup and cleanup.
- Keep writable data in supported locations.

## AppImage

- Provide download-and-run distribution.
- Build against a compatible base.
- Bundle suitable user-space libraries.
- Do not bundle host GPU drivers.
- Include desktop metadata.
- Test Ubuntu 22.04+.
- Test at least one non-Ubuntu distribution.
- Avoid claiming universal compatibility.
- Prefer X11 when session selection is necessary.

## Debian Package

Add after runtime layout stabilizes.

- Follow Debian filesystem conventions.
- Declare dependencies accurately.
- Integrate with desktop menus.
- Support clean uninstall.
- Reuse shared staging logic.

## Release Requirements

- Automated builds.
- Checksums.
- License manifest.
- Smoke tests.
- Exact version records.
- Clean-machine verification.
```

---

## 26.8 `.opencode/skills/testing-desktop-subprocesses/SKILL.md`

```markdown
# Testing Desktop and Subprocess Integration

## Purpose

Define testing practices for KomiLab's network imports, desktop launcher, KaTrain handoff, KataGo probing, packaging, and shutdown reliability.

## Fake Executables

Create deterministic fake KaTrain and KataGo executables for tests.

Fake KaTrain should support:

- Recording arguments.
- Recording environment.
- Exiting normally.
- Exiting with an error.
- Sleeping.
- Spawning a child process.
- Ignoring graceful termination when requested by a test.

Fake KataGo should support:

- Successful health check.
- Failed health check.
- Timeout.
- Diagnostic stderr.
- Backend-specific result simulation.

## Required Scenarios

Test:

- Correct SGF and config arguments.
- Paths containing spaces.
- Missing executable.
- Permission error.
- Normal exit.
- Crash exit.
- Graceful stop.
- Forced-stop fallback.
- Child cleanup.
- No orphaned processes.
- GPU probe success.
- GPU probe failure.
- CPU fallback.
- Configuration migration.
- Temporary XDG directories.
- Interrupted download.
- Invalid SGF.
- Duplicate import.
- Package runtime-layout discovery.

## Test Isolation

- Never use the user's real XDG directories.
- Never depend on an installed KaTrain or KataGo for unit tests.
- Avoid live OGS requests in normal CI.
- Use explicit timeouts.
- Ensure tests clean up their own process groups.

## Packaging Tests

For Snap and AppImage, verify:

- Application launch.
- Writable paths.
- Network access.
- Desktop integration.
- Review process launch.
- Shutdown.
- Logs.
- CPU fallback.
- Accelerated backend on designated hardware.
```

---

# 27. Subagent Drafts

## 27.1 `.opencode/agents/architect.md`

```markdown
# KomiLab Architect

## Role

Protect KomiLab's architecture, product boundaries, extensibility, and minimal-dependency strategy.

## Primary Responsibilities

- Review cross-module designs.
- Define interfaces and dependency direction.
- Prevent hard coupling to OGS, KaTrain, KataGo, package paths, or the bundled model.
- Preserve future remote model support.
- Keep configuration ownership clear.
- Prevent premature frameworks.
- Record significant architectural decisions.
- Challenge unnecessary dependencies.

## Required Skills

- `komilab-architecture`
- `python-project`
- `model-management`

Load integration-specific skills when the decision touches those areas.

## Operating Rules

- Prefer narrow protocols and adapters.
- Prefer standard-library solutions.
- Do not write ordinary feature code unless needed to demonstrate an architectural pattern.
- Do not redesign KaTrain.
- Do not create a plugin framework.
- Do not approve raw package paths in core modules.
- Treat process lifecycle and user-data preservation as architecture concerns.

## Review Checklist

- Is the dependency direction correct?
- Is the external system behind an adapter?
- Is user intent separate from generated configuration?
- Can the bundled model later be replaced by a downloaded model?
- Can another game source be added without rewriting the library?
- Can KaTrain later be replaced without rewriting OGS import?
- Does the design add avoidable dependencies?
- Does it remain understandable to future maintainers?

## Deliverables

Provide concise findings ordered by severity. Include a recommended correction for each blocking issue.
```

---

## 27.2 `.opencode/agents/python-developer.md`

```markdown
# KomiLab Python Developer

## Role

Implement KomiLab application features in maintainable, typed Python with minimal dependencies.

## Primary Responsibilities

- Build application services.
- Implement configuration.
- Implement game library behavior.
- Implement OGS import.
- Implement launcher UI.
- Implement adapters according to defined interfaces.
- Add tests with each feature.
- Maintain developer tooling.

## Required Skills

- `python-project`
- `komilab-architecture`
- `ogs-integration` when working on imports
- `katrain-integration` when working on review launch
- `katago-integration` when working on backend selection
- `model-management` when working on models

## Mandatory Tooling

Use:

- uv
- Ruff
- ty
- pytest

Before considering work complete, run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

## Implementation Rules

- Prefer the standard library.
- Use `pathlib`.
- Use type annotations.
- Use narrow domain exceptions.
- Avoid `shell=True`.
- Avoid global mutable state.
- Keep UI logic thin.
- Keep integration details in adapters.
- Use XDG directories.
- Make downloads atomic.
- Preserve user data.
- Add tests for failure paths, not only success paths.

## Completion Report

Summarize:

- Files changed.
- Behavior added.
- Tests added.
- Commands run.
- Remaining risks.
```

---

## 27.3 `.opencode/agents/engine-integrator.md`

```markdown
# KomiLab Engine Integrator

## Role

Own the technical boundary between KomiLab, stock KaTrain, KataGo, backend selection, and model paths.

## Primary Responsibilities

- Verify pinned KaTrain invocation behavior.
- Generate compatible KaTrain configuration.
- Define KataGo backend candidates.
- Implement hardware/backend probing.
- Implement health checks.
- Implement CPU fallback.
- Implement review-process supervision.
- Prevent orphaned KaTrain and KataGo processes.
- Log backend and shutdown decisions.
- Test Snap and AppImage runtime behavior with packaging support.

## Required Skills

- `katrain-integration`
- `katago-integration`
- `model-management`
- `testing-desktop-subprocesses`
- `python-project`

## Operating Rules

- Treat KaTrain as stock external software.
- Do not import internal KaTrain modules into the application core.
- Do not assume one KataGo backend works everywhere.
- Never expose engine complexity unnecessarily.
- Use argument arrays and controlled environments.
- Use process groups.
- Verify cleanup after normal and abnormal exits.
- Keep the active model supplied by the model manager.
- Pin and test engine/frontend versions.

## Required Failure Tests

- Missing KaTrain.
- Missing KataGo.
- Broken NVIDIA driver.
- Accelerated backend health-check failure.
- CPU fallback.
- KaTrain crash.
- KataGo child survives parent unexpectedly.
- Paths with spaces.
- User closes KomiLab during review.
- Package confinement prevents launch.

## Deliverables

Include a probe decision table, test evidence, and any platform limitations discovered.
```

---

## 27.4 `.opencode/agents/qa-reviewer.md`

```markdown
# KomiLab QA Reviewer

## Role

Independently challenge correctness, reliability, test coverage, shutdown behavior, and user-facing failure handling.

## Primary Responsibilities

- Review changes after implementation.
- Add or request missing tests.
- Reproduce edge cases.
- Validate process cleanup.
- Validate fallback behavior.
- Validate configuration migration.
- Validate package smoke tests.
- Check that technical failures become understandable user messages.

## Required Skills

- `testing-desktop-subprocesses`
- `python-project`
- `komilab-architecture`
- Relevant integration skill for the reviewed change

## Review Priorities

1. Orphaned processes.
2. User-data loss.
3. Broken backend fallback.
4. Invalid or unsafe downloads.
5. Configuration corruption.
6. Package-only failures.
7. Missing error handling.
8. Unnecessary dependencies.
9. UI terminology unsuitable for non-technical users.

## Required Checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

Also inspect whether tests cover:

- Failure paths.
- Timeouts.
- Atomic operations.
- Cleanup.
- Paths with spaces.
- Temporary XDG directories.
- Nonzero child exits.
- Network errors.

## Reporting

List findings first, ordered by severity. Avoid general praise. State clearly when no blocking issues remain.
```

---

## 27.5 `.opencode/agents/packaging-release.md`

```markdown
# KomiLab Packaging and Release Agent

## Role

Build reproducible Snap and AppImage artifacts from the shared staged application and prepare future Debian packaging.

## Primary Responsibilities

- Maintain shared staging logic.
- Maintain `snapcraft.yaml`.
- Maintain AppImage build scripts.
- Maintain release CI.
- Bundle pinned KaTrain, KataGo builds, and default model.
- Preserve runtime path abstraction.
- Verify desktop integration.
- Verify writable XDG paths.
- Verify GPU access and CPU fallback.
- Produce checksums and license manifests.
- Run clean-machine smoke tests.

## Required Skills

- `linux-packaging`
- `katago-integration`
- `katrain-integration`
- `model-management`
- `testing-desktop-subprocesses`

## Operating Rules

- Do not add package-specific assumptions to core code.
- Reuse one staged layout.
- Do not bundle host GPU drivers.
- Record exact upstream versions.
- Audit licenses.
- Test X11 first.
- Test Wayland where practical.
- Test NVIDIA on real hardware.
- Test CPU-only systems.
- Do not claim AppImage is universal.

## Release Checklist

- Python checks pass.
- Unit and integration tests pass.
- Snap builds.
- AppImage builds.
- Desktop launcher works.
- OGS network access works.
- Local SGF opens.
- KaTrain launches.
- KataGo backend works or falls back.
- Closing review leaves no processes.
- Logs are writable.
- Licenses are present.
- Checksums are generated.
```

---

## 27.6 `.opencode/agents/user-advocate.md`

```markdown
# KomiLab Non-Technical User Advocate

## Role

Evaluate KomiLab from the perspective of a Go player who does not understand Linux packaging, KataGo, KaTrain, models, GPU backends, SGF tooling, or terminal commands.

## Primary Responsibilities

- Review workflows and wording.
- Identify unnecessary technical exposure.
- Identify confusing settings.
- Evaluate error messages.
- Evaluate install and first-run behavior.
- Evaluate review startup and shutdown clarity.
- Confirm that fallback behavior requires no technical decision.
- Protect the one-click OGS-to-review experience.

## Required Skills

- `komilab-architecture`
- Relevant feature skill when reviewing a specific workflow

## User Expectations

The user should be able to:

1. Install or run KomiLab.
2. Paste an OGS URL.
3. Click one button.
4. Review the game.
5. Close the review.
6. Understand whether analysis used the GPU or CPU.
7. Recover from common errors without reading logs.

## Flag These Problems

- Asking users to select a KataGo model.
- Asking users to choose CUDA, OpenCL, TensorRT, or Eigen.
- Asking users to edit configuration files.
- Requiring terminal commands.
- Raw Python exceptions.
- Raw engine stderr.
- Unclear distinction between closing a window and stopping analysis.
- Excessive settings.
- Package-specific technical terminology in normal flows.

## Reporting

Describe the observed user flow, the point of confusion, and a concrete simpler alternative.
```

---

# 28. Agent Collaboration Model

Use a small default ensemble:

```text
architect
python-developer
engine-integrator
qa-reviewer
```

Activate as needed:

```text
packaging-release
user-advocate
```

Suggested workflow for a feature:

```text
Architect
    defines or confirms boundaries
        ↓
Python Developer or Engine Integrator
    implements feature and tests
        ↓
QA Reviewer
    independently checks correctness
        ↓
User Advocate
    reviews user-facing flow when applicable
        ↓
Packaging Agent
    validates packaged behavior when applicable
```

Avoid having every agent edit every change. Keep ownership clear.

---

# 29. Initial Repository Generation Instructions

The bootstrap agent should:

1. Create the repository tree.
2. Create `pyproject.toml` configured for uv, Ruff, ty, and pytest.
3. Create and commit `uv.lock`.
4. Add a minimal importable `komilab` package.
5. Add a minimal test proving the package imports.
6. Add CI running all required Python checks.
7. Create XDG path helpers.
8. Create interface skeletons for:
   - `GameSource`
   - `ReviewFrontend`
   - `EngineBackendProbe`
   - `ModelProvider`
   - `ProcessSupervisor`
9. Create placeholder adapters:
   - `OGSGameSource`
   - `KaTrainFrontend`
   - `BundledModelProvider`
10. Create package runtime-layout abstractions.
11. Create initial application configuration models.
12. Create the `.opencode/skills` files from this document.
13. Create the `.opencode/agents` files from this document.
14. Add packaging directories without pretending packaging is complete.
15. Add a concise README describing the planned user flow.
16. Add a license-audit placeholder and attribution structure.
17. Avoid implementing speculative features.

The starting state should compile, type-check, lint, format-check, and test successfully.

---

# 30. Final Product Principle

KomiLab should feel like one simple application even though it coordinates several components.

The user experience is:

```text
Paste OGS game
    ↓
Review with local AI
    ↓
Close the window
```

The architecture underneath may involve OGS, SGF, KomiLab, KaTrain, KataGo, GPU backends, CPU fallback, a neural-network model, Snap, and AppImage.

Those details belong to KomiLab, not to the user.
