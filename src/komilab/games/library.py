from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from komilab.sources.ogs import ImportedGame

SCHEMA_VERSION = 2


@dataclass(frozen=True)
class TrackedGame:
    ogs_game_id: str
    source: str
    source_url: str
    sgf_path: Path
    sha256: str
    is_finished: bool
    phase: str
    imported_at: str
    updated_at: str
    last_checked_at: str
    last_changed_at: str


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
        last_changed_at = now if changed else previous.last_changed_at

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO games (
                    ogs_game_id, source, source_url, sgf_path, sha256,
                    is_finished, phase, imported_at, updated_at,
                    last_checked_at, last_changed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ogs_game_id) DO UPDATE SET
                    source = excluded.source,
                    source_url = excluded.source_url,
                    sgf_path = excluded.sgf_path,
                    sha256 = excluded.sha256,
                    is_finished = excluded.is_finished,
                    phase = excluded.phase,
                    updated_at = excluded.updated_at,
                    last_checked_at = excluded.last_checked_at,
                    last_changed_at = excluded.last_changed_at
                """,
                (
                    imported.game_id,
                    imported.source,
                    imported.source_url,
                    str(imported.sgf_path),
                    imported.sha256,
                    int(imported.is_finished),
                    imported.phase,
                    now,
                    now,
                    now,
                    last_changed_at,
                ),
            )
        return changed

    def get_by_ogs_id(self, game_id: str) -> TrackedGame | None:
        with self._connect() as con:
            row = con.execute(_SELECT_GAMES + " WHERE ogs_game_id = ?", (game_id,)).fetchone()
        return _tracked_from_row(row) if row else None

    def unfinished_games(self) -> list[TrackedGame]:
        with self._connect() as con:
            rows = con.execute(
                _SELECT_GAMES
                + """
                WHERE is_finished = 0
                ORDER BY last_checked_at DESC
                """
            ).fetchall()
        return [_tracked_from_row(row) for row in rows]

    def recent_games(self, limit: int = 5) -> list[TrackedGame]:
        with self._connect() as con:
            rows = con.execute(
                _SELECT_GAMES
                + """
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
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    ogs_game_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL DEFAULT 'ogs',
                    source_url TEXT NOT NULL,
                    sgf_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    is_finished INTEGER NOT NULL DEFAULT 0,
                    phase TEXT NOT NULL DEFAULT '',
                    imported_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_checked_at TEXT NOT NULL,
                    last_changed_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(con, "source", "TEXT NOT NULL DEFAULT 'ogs'")
            self._ensure_column(con, "last_checked_at", "TEXT")
            self._ensure_column(con, "last_changed_at", "TEXT")
            now = _now()
            con.execute("UPDATE games SET source = 'ogs' WHERE source IS NULL OR source = ''")
            con.execute(
                """
                UPDATE games
                SET last_checked_at = COALESCE(NULLIF(last_checked_at, ''), updated_at, ?)
                """,
                (now,),
            )
            con.execute(
                """
                UPDATE games
                SET last_changed_at = COALESCE(NULLIF(last_changed_at, ''), updated_at, ?)
                """,
                (now,),
            )
            con.execute(
                """
                INSERT INTO schema_meta (key, value) VALUES ('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )

    @staticmethod
    def _ensure_column(con: sqlite3.Connection, name: str, definition: str) -> None:
        columns = {row[1] for row in con.execute("PRAGMA table_info(games)")}
        if name not in columns:
            con.execute(f"ALTER TABLE games ADD COLUMN {name} {definition}")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)


_SELECT_GAMES = """
SELECT ogs_game_id, source, source_url, sgf_path, sha256,
       is_finished, phase, imported_at, updated_at,
       last_checked_at, last_changed_at
FROM games
"""


def _tracked_from_row(row: tuple[object, ...]) -> TrackedGame:
    return TrackedGame(
        ogs_game_id=str(row[0]),
        source=str(row[1]),
        source_url=str(row[2]),
        sgf_path=Path(str(row[3])),
        sha256=str(row[4]),
        is_finished=bool(row[5]),
        phase=str(row[6]),
        imported_at=str(row[7]),
        updated_at=str(row[8]),
        last_checked_at=str(row[9]),
        last_changed_at=str(row[10]),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
