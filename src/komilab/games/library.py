from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from komilab.sources.ogs import ImportedGame


@dataclass(frozen=True)
class TrackedGame:
    ogs_game_id: str
    source_url: str
    sgf_path: Path
    sha256: str
    is_finished: bool
    phase: str
    imported_at: str
    updated_at: str


class GameLibrary:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def upsert_imported_game(self, imported: ImportedGame) -> bool:
        """Store imported game metadata. Returns True when SGF content changed."""
        now = _now()
        previous = self.get_by_ogs_id(imported.game_id)
        changed = previous is None or previous.sha256 != imported.sha256
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO games (
                    ogs_game_id, source_url, sgf_path, sha256,
                    is_finished, phase, imported_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ogs_game_id) DO UPDATE SET
                    source_url = excluded.source_url,
                    sgf_path = excluded.sgf_path,
                    sha256 = excluded.sha256,
                    is_finished = excluded.is_finished,
                    phase = excluded.phase,
                    updated_at = excluded.updated_at
                """,
                (
                    imported.game_id,
                    imported.source_url,
                    str(imported.sgf_path),
                    imported.sha256,
                    int(imported.is_finished),
                    imported.phase,
                    now,
                    now,
                ),
            )
        return changed

    def get_by_ogs_id(self, game_id: str) -> TrackedGame | None:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT ogs_game_id, source_url, sgf_path, sha256,
                       is_finished, phase, imported_at, updated_at
                FROM games WHERE ogs_game_id = ?
                """,
                (game_id,),
            ).fetchone()
        return _tracked_from_row(row) if row else None

    def unfinished_games(self) -> list[TrackedGame]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT ogs_game_id, source_url, sgf_path, sha256,
                       is_finished, phase, imported_at, updated_at
                FROM games
                WHERE is_finished = 0
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [_tracked_from_row(row) for row in rows]

    def recent_games(self, limit: int = 5) -> list[TrackedGame]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT ogs_game_id, source_url, sgf_path, sha256,
                       is_finished, phase, imported_at, updated_at
                FROM games
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_tracked_from_row(row) for row in rows]

    def _migrate(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    ogs_game_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    sgf_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    is_finished INTEGER NOT NULL DEFAULT 0,
                    phase TEXT NOT NULL DEFAULT '',
                    imported_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)


def _tracked_from_row(row: tuple[object, ...]) -> TrackedGame:
    return TrackedGame(
        ogs_game_id=str(row[0]),
        source_url=str(row[1]),
        sgf_path=Path(str(row[2])),
        sha256=str(row[3]),
        is_finished=bool(row[4]),
        phase=str(row[5]),
        imported_at=str(row[6]),
        updated_at=str(row[7]),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
