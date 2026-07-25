from __future__ import annotations

from pathlib import Path

from komilab.games.library import GameLibrary
from komilab.sources.ogs import ImportedGame


def _game(game_id: str, sha: str, finished: bool = False) -> ImportedGame:
    return ImportedGame(
        game_id=game_id,
        source_url=f"https://online-go.com/game/{game_id}",
        sgf_path=Path(f"{game_id}.sgf"),
        sha256=sha,
        is_finished=finished,
        phase="finished" if finished else "play",
    )


def test_upsert_reports_changed_and_tracks_unfinished(tmp_path) -> None:
    library = GameLibrary(tmp_path / "database.sqlite3")

    assert library.upsert_imported_game(_game("1", "aaa")) is True
    assert library.upsert_imported_game(_game("1", "aaa")) is False
    assert library.upsert_imported_game(_game("1", "bbb")) is True

    unfinished = library.unfinished_games()
    assert len(unfinished) == 1
    assert unfinished[0].ogs_game_id == "1"

    library.upsert_imported_game(_game("1", "ccc", finished=True))
    assert library.unfinished_games() == []
