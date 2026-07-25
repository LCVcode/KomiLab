from __future__ import annotations

import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

from komilab.config.paths import AppPaths

KATAGO_VERSION = "v1.16.5"
KATAGO_EIGEN_URL = (
    "https://github.com/lightvector/KataGo/releases/download/v1.16.5/"
    "katago-v1.16.5-eigen-linux-x64.zip"
)


class ReviewConfigError(RuntimeError):
    pass


def ensure_cpu_katago(paths: AppPaths) -> Path:
    engine_dir = paths.data_dir / "engines" / "katago-v1.16.5-eigen-linux-x64"
    katago = engine_dir / "katago"
    if katago.exists():
        katago.chmod(0o755)
        return katago

    engine_dir.mkdir(parents=True, exist_ok=True)
    zip_path = engine_dir / "katago.zip"
    urllib.request.urlretrieve(KATAGO_EIGEN_URL, zip_path)  # noqa: S310 - pinned prototype URL
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(engine_dir)
    if not katago.exists():
        raise ReviewConfigError("Downloaded KataGo archive did not contain a katago executable.")
    katago.chmod(0o755)
    return katago


def render_katrain_config(paths: AppPaths, katago_path: Path) -> Path:
    base_config = _find_base_katrain_config()
    with base_config.open(encoding="utf-8") as file:
        config = json.load(file)

    config.setdefault("engine", {})["katago"] = str(katago_path)
    config["engine"]["backend"] = "local"
    config.setdefault("general", {})["debug_level"] = 2

    output = paths.generated_dir / "katrain-config.json"
    paths.generated_dir.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)
    return output


def _find_base_katrain_config() -> Path:
    user_config = Path.home() / ".katrain" / "config.json"
    if user_config.exists():
        return user_config

    cache_root = Path.home() / ".cache" / "uv" / "archive-v0"
    candidates = sorted(cache_root.glob("*/katrain/config.json")) if cache_root.exists() else []
    if candidates:
        return candidates[-1]

    katrain_exe = shutil.which("katrain")
    if katrain_exe:
        # If a system KaTrain exists but has not created a config yet, ask the
        # user to run it once or install through the uv-tool fallback.
        raise ReviewConfigError("KaTrain config was not found. Run KaTrain once, then try again.")

    raise ReviewConfigError("KaTrain package config was not found.")
