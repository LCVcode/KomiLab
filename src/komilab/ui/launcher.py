from __future__ import annotations

# ruff: noqa: E402
import threading
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
_gi_repository: Any = __import__("gi.repository", fromlist=["Gdk", "GLib", "Gtk"])
Gdk: Any = _gi_repository.Gdk
GLib: Any = _gi_repository.GLib
Gtk: Any = _gi_repository.Gtk

from komilab.config.paths import get_app_paths
from komilab.games.library import GameLibrary, TrackedGame
from komilab.games.sgf import SGFValidationError, validate_sgf_file
from komilab.review.config import ReviewConfigError, ensure_cpu_katago, render_katrain_config
from komilab.review.katrain import KaTrainFrontend, KaTrainLaunchError
from komilab.sources.ogs import OGSDownloadError, OGSGameSource, OGSReferenceError

TEST_URL = "https://online-go.com/game/88417735"


class LauncherWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="KomiLab")
        self.set_default_size(660, 520)
        self.set_border_width(12)
        self.set_wmclass("komilab", "KomiLab")
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.paths = get_app_paths()
        self.paths.ensure()
        self.library = GameLibrary(self.paths.database_path)
        self.source = OGSGameSource()
        self.frontend = KaTrainFrontend(on_exit=self._on_katrain_exit)
        self.selected_sgf_path: Path | None = None

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

        self.update_button = Gtk.Button(label="Update In-Progress Games")
        self.update_button.connect("clicked", lambda *_: self.update_in_progress_games())
        buttons.pack_start(self.update_button, False, False, 0)

        self.open_selected_button = Gtk.Button(label="Open Selected")
        self.open_selected_button.connect("clicked", lambda *_: self.open_selected_game())
        self.open_selected_button.set_sensitive(False)
        buttons.pack_start(self.open_selected_button, False, False, 0)

        self.stop_button = Gtk.Button(label="Stop KaTrain")
        self.stop_button.connect("clicked", lambda *_: self.frontend.stop())
        self.stop_button.set_sensitive(False)
        buttons.pack_start(self.stop_button, False, False, 0)

        self.status = Gtk.Label(label="Analysis engine: handled by KaTrain for this prototype")
        self.status.set_xalign(0)
        root.pack_start(self.status, False, False, 0)

        ongoing_label = Gtk.Label()
        ongoing_label.set_markup("<b>Locally saved online games still in progress</b>")
        ongoing_label.set_xalign(0)
        root.pack_start(ongoing_label, False, False, 0)

        self.ongoing_store = Gtk.ListStore(str, str, str)
        self.ongoing_view = self._create_game_view(self.ongoing_store)
        root.pack_start(self._scrolled(self.ongoing_view), True, True, 0)

        completed_label = Gtk.Label()
        completed_label.set_markup("<b>Completed local games</b>")
        completed_label.set_xalign(0)
        root.pack_start(completed_label, False, False, 0)

        self.completed_store = Gtk.ListStore(str, str, str)
        self.completed_view = self._create_game_view(self.completed_store)
        root.pack_start(self._scrolled(self.completed_view), True, True, 0)

        self.refresh_game_lists()
        self.connect("destroy", self._on_destroy)

    def _create_game_view(self, store: object) -> object:
        view = Gtk.TreeView(model=store)
        for title, column_id in [("OGS Game", 0), ("Status", 1)]:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=column_id)
            column.set_resizable(True)
            view.append_column(column)
        selection = view.get_selection()
        selection.connect("changed", self._on_game_selected)
        view.connect("row-activated", lambda *_: self.open_selected_game())
        return view

    def _scrolled(self, child: object) -> object:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(120)
        scrolled.add(child)
        return scrolled

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
            self.library.upsert_imported_game(imported)
            katago_path = ensure_cpu_katago(self.paths)
            config_path = render_katrain_config(self.paths, katago_path)
        except (OGSReferenceError, OGSDownloadError, SGFValidationError, ReviewConfigError) as exc:
            GLib.idle_add(self._finish_with_error, str(exc))
            return
        GLib.idle_add(self._launch_sgf, imported.sgf_path, config_path)

    def update_in_progress_games(self) -> None:
        unfinished = self.library.unfinished_games()
        if not unfinished:
            self.status.set_text("No tracked in-progress games to update.")
            return
        self._set_busy(True, f"Checking {len(unfinished)} in-progress game(s)…")
        threading.Thread(target=self._update_worker, args=(unfinished,), daemon=True).start()

    def _update_worker(self, games: list[TrackedGame]) -> None:
        checked = 0
        changed = 0
        errors = 0
        for game in games:
            checked += 1
            try:
                imported = self.source.download(game.ogs_game_id, self.paths.games_dir)
                validate_sgf_file(imported.sgf_path)
                if self.library.upsert_imported_game(imported):
                    changed += 1
            except (OGSReferenceError, OGSDownloadError, SGFValidationError):
                errors += 1
        GLib.idle_add(self._finish_update, checked, changed, errors)

    def _finish_update(self, checked: int, changed: int, errors: int) -> bool:
        self._set_busy(
            False, f"Update complete: {changed} changed, {checked} checked, {errors} failed."
        )
        self.refresh_game_lists()
        return False

    def open_selected_game(self) -> None:
        if self.selected_sgf_path is None:
            self._show_error("Select a saved game first.")
            return
        try:
            validate_sgf_file(self.selected_sgf_path)
        except SGFValidationError as exc:
            self._show_error(str(exc))
            return
        self._set_busy(True, "Preparing KataGo engine…")
        threading.Thread(
            target=self._local_launch_worker, args=(self.selected_sgf_path,), daemon=True
        ).start()

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
        self.update_button.set_sensitive(False)
        self.open_selected_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.refresh_game_lists()
        self.iconify()
        return False

    def _on_katrain_exit(self, code: int) -> None:
        GLib.idle_add(self._restore_after_katrain, code)

    def _restore_after_katrain(self, code: int) -> bool:
        self.deiconify()
        self.present()
        self.download_button.set_sensitive(True)
        self.update_button.set_sensitive(True)
        self.open_selected_button.set_sensitive(self.selected_sgf_path is not None)
        self.stop_button.set_sensitive(False)
        self.status.set_text(f"KaTrain exited with code {code}.")
        self.refresh_game_lists()
        return False

    def _finish_with_error(self, message: str) -> bool:
        self._set_busy(False, "Analysis engine: not running")
        self._show_error(message)
        return False

    def _set_busy(self, busy: bool, message: str) -> None:
        self.download_button.set_sensitive(not busy)
        self.update_button.set_sensitive(not busy)
        self.open_selected_button.set_sensitive(not busy and self.selected_sgf_path is not None)
        self.status.set_text(message)

    def _on_game_selected(self, selection: Any) -> None:
        model, row_iter = selection.get_selected()
        if row_iter is None:
            self.selected_sgf_path = None
            self.open_selected_button.set_sensitive(False)
            return
        self.selected_sgf_path = Path(model[row_iter][2])
        self.open_selected_button.set_sensitive(not self.frontend.is_running())

    def refresh_game_lists(self) -> None:
        self.ongoing_store.clear()
        self.completed_store.clear()
        for game in self.library.unfinished_games():
            self.ongoing_store.append(
                [game.ogs_game_id, game.phase or "in progress", str(game.sgf_path)]
            )
        for game in self.library.completed_games():
            self.completed_store.append([game.ogs_game_id, "finished", str(game.sgf_path)])

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

    def _on_destroy(self, *_args: object) -> None:
        self.frontend.stop()
        Gtk.main_quit()


def run() -> None:
    window = LauncherWindow()
    window.show_all()
    Gtk.main()
