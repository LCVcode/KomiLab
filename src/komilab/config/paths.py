from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_ID = "komilab"


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path
    cache_dir: Path
    state_dir: Path

    @property
    def games_dir(self) -> Path:
        return self.data_dir / "games"

    @property
    def generated_dir(self) -> Path:
        return self.config_dir / "generated"

    @property
    def logs_dir(self) -> Path:
        return self.state_dir / "logs"

    def ensure(self) -> None:
        for path in [
            self.config_dir,
            self.data_dir,
            self.cache_dir,
            self.state_dir,
            self.games_dir,
            self.generated_dir,
            self.logs_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def _xdg_dir(env_name: str, default: Path) -> Path:
    value = os.environ.get(env_name)
    return Path(value).expanduser() if value else default


def get_app_paths() -> AppPaths:
    home = Path.home()
    return AppPaths(
        config_dir=_xdg_dir("XDG_CONFIG_HOME", home / ".config") / APP_ID,
        data_dir=_xdg_dir("XDG_DATA_HOME", home / ".local" / "share") / APP_ID,
        cache_dir=_xdg_dir("XDG_CACHE_HOME", home / ".cache") / APP_ID,
        state_dir=_xdg_dir("XDG_STATE_HOME", home / ".local" / "state") / APP_ID,
    )
