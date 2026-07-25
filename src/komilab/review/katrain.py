from __future__ import annotations

import os
import shlex
import shutil
import signal
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class KaTrainLaunchError(RuntimeError):
    pass


@dataclass
class ReviewSession:
    process: subprocess.Popen[bytes]
    command: list[str]

    def is_running(self) -> bool:
        return self.process.poll() is None

    def stop(self) -> None:
        if not self.is_running():
            return
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=5)


class KaTrainFrontend:
    def __init__(self, on_exit: Callable[[int], None] | None = None) -> None:
        self._session: ReviewSession | None = None
        self._on_exit = on_exit

    def open_game(
        self, sgf_path: Path, config_path: Path | None = None, log_path: Path | None = None
    ) -> ReviewSession:
        if self._session and self._session.is_running():
            raise KaTrainLaunchError("KaTrain is already running.")
        command = discover_katrain_command()
        if config_path is not None:
            command.append(str(config_path))
        command.append(str(sgf_path))
        env = os.environ.copy()
        env.setdefault("KIVY_NO_ARGS", "1")
        env.setdefault("GDK_BACKEND", "x11,wayland")
        stdout_target = subprocess.DEVNULL
        stderr_target = subprocess.DEVNULL
        log_file = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_file = log_path.open("ab")
            stdout_target = log_file
            stderr_target = subprocess.STDOUT
        try:
            process = subprocess.Popen(
                command,
                env=env,
                stdout=stdout_target,
                stderr=stderr_target,
                start_new_session=True,
            )
        except OSError as exc:
            raise KaTrainLaunchError(f"Could not launch KaTrain: {exc}") from exc
        self._session = ReviewSession(process=process, command=command)
        threading.Thread(target=self._wait_for_exit, args=(process, log_file), daemon=True).start()
        return self._session

    def is_running(self) -> bool:
        return bool(self._session and self._session.is_running())

    def stop(self) -> None:
        if self._session:
            self._session.stop()

    def _wait_for_exit(
        self, process: subprocess.Popen[bytes], log_file: object | None = None
    ) -> None:
        code = process.wait()
        if log_file is not None:
            close = getattr(log_file, "close", None)
            if close is not None:
                close()
        if self._on_exit:
            self._on_exit(code)


def discover_katrain_command() -> list[str]:
    override = os.environ.get("KOMILAB_KATRAIN_COMMAND")
    if override:
        return shlex.split(override)
    katrain = shutil.which("katrain")
    if katrain:
        return [katrain]
    uv = shutil.which("uv")
    if uv:
        return [uv, "tool", "run", "--from", "katrain", "katrain"]
    raise KaTrainLaunchError("Could not find KaTrain. Install it or set KOMILAB_KATRAIN_COMMAND.")
