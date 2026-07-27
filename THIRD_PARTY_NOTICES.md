# Third-Party Notices

KomiLab itself is distributed under the MIT License. It currently does not vendor third-party runtime source code or binaries in this repository.

## Runtime integrations

- **GTK / PyGObject**: Loaded from the user's Linux system Python environment for the GTK 3 launcher UI. These components are provided by the operating system distribution and are not bundled by KomiLab.
- **KaTrain**: Launched as an external application from `PATH` or through `uv tool run --from katrain katrain`. KaTrain is not bundled in this repository. Its PyPI metadata declares the MIT license.
- **KataGo**: The prototype can download the official KataGo Eigen Linux x64 release from the upstream GitHub release URL at runtime. KataGo is not bundled in this repository. KataGo is distributed upstream under the MIT license.
- **OGS game data**: Game records are downloaded from Online-Go.com for user-requested game IDs/URLs. Users should only download games they are permitted to access and review.

## Development tools

The locked development tools are used for local testing, linting, formatting, and type checking. They are not bundled with KomiLab releases by this repository.

Known license metadata from the current environment:

- `pytest`: MIT
- `ruff`: MIT
- `ty`: license metadata not declared in the installed package metadata checked here; upstream project is by Astral.
- `pluggy`: MIT
- `packaging`: Apache-2.0 OR BSD-2-Clause
- `pathspec`: MPL-2.0

If KomiLab later bundles any third-party code, binaries, models, or assets, this file and release packaging should be updated with the corresponding license texts and attribution notices. Future GitHub releases should also preserve upstream copyright notices for any redistributed artifacts.
