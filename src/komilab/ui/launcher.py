from __future__ import annotations

# ruff: noqa: E402
import threading
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "3.0")
_gi_repository: Any = __import__("gi.repository", fromlist=["Gdk", "GLib", "Gtk"])
Gdk: Any = _gi_repository.Gdk
GLib: Any = _gi_repository.GLib
Gtk: Any = _gi_repository.Gtk

from komilab.config.paths import get_app_paths
from komilab.games.sgf import SGFValidationError, validate_sgf_file
from komilab.review.config import ReviewConfigError, ensure_cpu_katago, render_katrain_config
from komilab.review.katrain import KaTrainFrontend, KaTrainLaunchError
from komilab.sources.ogs import OGSDownloadError, OGSGameSource, OGSReferenceError

TEST_URL = "https://online-go.com/game/88417735"


class LauncherWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="KomiLab")
        self.set_default_size(560, 260)
        self.set_border_width(12)
        self.set_wmclass("komilab", "KomiLab")
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.paths = get_app_paths()
        self.paths.ensure()
        self.source = OGSGameSource()
        self.frontend = KaTrainFrontend(on_exit=self._on_katrain_exit)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(root)

        title = Gtk.Label()
        title.set_markup("<b>KomiLab</b> — Local AI review for your Go games")
        title.set_xalign(0)
        root.pack_start(title, False, False, 0)

        hint = Gtk.Label(label="Paste an OGS game URL or ID, then open it in stock KaTrain.")
        hint.set_xalign(0)
        root.pack_start(hint, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(TEST_URL)
        self.entry.set_text(TEST_URL)
        self.entry.connect("activate", lambda *_: self.download_and_review())
        root.pack_start(self.entry, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root.pack_start(buttons, False, False, 0)

        self.download_button = Gtk.Button(label="Download and Review")
        self.download_button.connect("clicked", lambda *_: self.download_and_review())
        buttons.pack_start(self.download_button, False, False, 0)

        self.local_button = Gtk.Button(label="Open Local SGF")
        self.local_button.connect("clicked", lambda *_: self.open_local_sgf())
        buttons.pack_start(self.local_button, False, False, 0)

        self.stop_button = Gtk.Button(label="Stop KaTrain")
        self.stop_button.connect("clicked", lambda *_: self.frontend.stop())
        self.stop_button.set_sensitive(False)
        buttons.pack_start(self.stop_button, False, False, 0)

        self.status = Gtk.Label(label="Analysis engine: handled by KaTrain for this prototype")
        self.status.set_xalign(0)
        root.pack_start(self.status, False, False, 0)

        self.recent = Gtk.Label(label=self._recent_text())
        self.recent.set_xalign(0)
        root.pack_start(self.recent, False, False, 0)

        self.connect("destroy", self._on_destroy)

    def download_and_review(self) -> None:
        reference = self.entry.get_text().strip()
        if not reference:
            self._show_error("Enter an OGS game URL or ID.")
            return
        self._set_busy(True, "Downloading OGS game…")
        threading.Thread(target=self._download_worker, args=(reference,), daemon=True).start()

    def _download_worker(self, reference: str) -> None:
        try:
            imported = self.source.download(reference, self.paths.games_dir)
            validate_sgf_file(imported.sgf_path)
            katago_path = ensure_cpu_katago(self.paths)
            config_path = render_katrain_config(self.paths, katago_path)
        except (OGSReferenceError, OGSDownloadError, SGFValidationError, ReviewConfigError) as exc:
            GLib.idle_add(self._finish_with_error, str(exc))
            return
        GLib.idle_add(self._launch_sgf, imported.sgf_path, config_path)

    def open_local_sgf(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Open SGF",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )
        sgf_filter = Gtk.FileFilter()
        sgf_filter.set_name("SGF files")
        sgf_filter.add_pattern("*.sgf")
        dialog.add_filter(sgf_filter)
        try:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                if filename:
                    path = Path(filename)
                    try:
                        validate_sgf_file(path)
                    except SGFValidationError as exc:
                        self._show_error(str(exc))
                        return
                    self._set_busy(True, "Preparing KataGo engine…")
                    threading.Thread(
                        target=self._local_launch_worker, args=(path,), daemon=True
                    ).start()
        finally:
            dialog.destroy()

    def _local_launch_worker(self, path: Path) -> None:
        try:
            katago_path = ensure_cpu_katago(self.paths)
            config_path = render_katrain_config(self.paths, katago_path)
        except ReviewConfigError as exc:
            GLib.idle_add(self._finish_with_error, str(exc))
            return
        GLib.idle_add(self._launch_sgf, path, config_path)

    def _launch_sgf(self, sgf_path: Path, config_path: Path) -> bool:
        try:
            self.frontend.open_game(
                sgf_path,
                config_path=config_path,
                log_path=self.paths.logs_dir / "katrain.log",
            )
        except KaTrainLaunchError as exc:
            self._finish_with_error(str(exc))
            return False
        self._set_busy(False, f"KaTrain running: {sgf_path.name}")
        self.download_button.set_sensitive(False)
        self.local_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.iconify()
        return False

    def _on_katrain_exit(self, code: int) -> None:
        GLib.idle_add(self._restore_after_katrain, code)

    def _restore_after_katrain(self, code: int) -> bool:
        self.deiconify()
        self.present()
        self.download_button.set_sensitive(True)
        self.local_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.status.set_text(f"KaTrain exited with code {code}.")
        self.recent.set_text(self._recent_text())
        return False

    def _finish_with_error(self, message: str) -> bool:
        self._set_busy(False, "Analysis engine: not running")
        self._show_error(message)
        return False

    def _set_busy(self, busy: bool, message: str) -> None:
        self.download_button.set_sensitive(not busy)
        self.local_button.set_sensitive(not busy)
        self.status.set_text(message)

    def _show_error(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def _recent_text(self) -> str:
        games = sorted(
            self.paths.games_dir.glob("*.sgf"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not games:
            return "Recent games: none yet"
        return "Recent games: " + ", ".join(path.name for path in games[:5])

    def _on_destroy(self, *_args: object) -> None:
        self.frontend.stop()
        Gtk.main_quit()


def run() -> None:
    window = LauncherWindow()
    window.show_all()
    Gtk.main()
