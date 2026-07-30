from __future__ import annotations

import hashlib
import json
import re
import tempfile
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

MAX_GAME_JSON_BYTES = 10 * 1024 * 1024
USER_AGENT = "KomiLab prototype/0.1"


class OGSReferenceError(ValueError):
    pass


class OGSDownloadError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImportedGame:
    game_id: str
    source: str
    source_url: str
    sgf_path: Path
    sha256: str
    is_finished: bool
    phase: str


class OGSGameSource:
    def normalize_reference(self, value: str) -> str:
        value = value.strip()
        if re.fullmatch(r"[1-9][0-9]*", value):
            return value

        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"}:
            raise OGSReferenceError("Enter an OGS game ID or online-go.com game URL.")
        if parsed.netloc.lower() not in {"online-go.com", "www.online-go.com"}:
            raise OGSReferenceError("Only online-go.com game URLs are supported.")

        match = re.fullmatch(r"/game/([1-9][0-9]*)(?:/.*)?", parsed.path)
        if not match:
            raise OGSReferenceError("That does not look like an OGS game URL.")
        return match.group(1)

    def download(self, reference: str, destination_dir: Path) -> ImportedGame:
        game_id = self.normalize_reference(reference)
        destination_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://online-go.com/api/v1/games/{game_id}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    raise OGSDownloadError("OGS returned an unexpected response.")
                payload = response.read(MAX_GAME_JSON_BYTES + 1)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise OGSDownloadError("That OGS game could not be found.") from exc
            raise OGSDownloadError(f"OGS returned HTTP {exc.code}.") from exc
        except urllib.error.URLError as exc:
            raise OGSDownloadError("Could not connect to OGS.") from exc

        if len(payload) > MAX_GAME_JSON_BYTES:
            raise OGSDownloadError("OGS response was too large.")

        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OGSDownloadError("OGS returned invalid game data.") from exc

        sgf = ogs_json_to_sgf(data)
        sha256 = hashlib.sha256(sgf.encode("utf-8")).hexdigest()
        phase = _game_phase(data)
        is_finished = _is_finished(data, phase)
        final_path = destination_dir / f"{game_id}.sgf"

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=destination_dir, delete=False
        ) as tmp:
            tmp.write(sgf)
            tmp_path = Path(tmp.name)
        tmp_path.replace(final_path)

        return ImportedGame(
            game_id=game_id,
            source="ogs",
            source_url=f"https://online-go.com/game/{game_id}",
            sgf_path=final_path,
            sha256=sha256,
            is_finished=is_finished,
            phase=phase,
        )


def _game_phase(data: dict[str, object]) -> str:
    gamedata = data.get("gamedata")
    if isinstance(gamedata, dict):
        gamedata_phase = gamedata.get("phase")
        if gamedata_phase:
            return str(gamedata_phase)
    if data.get("phase"):
        return str(data["phase"])
    return ""


def _is_finished(data: dict[str, object], phase: str) -> bool:
    if phase.lower() in {"finished", "ended", "gameover", "stone removal"}:
        return True
    return bool(data.get("ended") or data.get("outcome"))


def _sgf_escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("]", r"\]").replace("\n", " ")


def _sgf_coord(x: int, y: int) -> str:
    if x < 0 or y < 0:
        return ""
    letters = "abcdefghijklmnopqrstuvwxyz"
    return letters[x] + letters[y]


def _initial_state_coords(value: object) -> list[str]:
    if not isinstance(value, str) or len(value) % 2 != 0:
        return []
    return [value[index : index + 2] for index in range(0, len(value), 2)]


def _setup_property(name: str, coords: list[str]) -> str:
    return name + "".join(f"[{_sgf_escape(coord)}]" for coord in coords)


def _initial_player(data: dict[str, object], gamedata: Mapping[object, object]) -> str:
    value = gamedata.get("initial_player", data.get("initial_player", "black"))
    return "W" if str(value).lower() == "white" else "B"


def _free_handicap_enabled(gamedata: Mapping[object, object]) -> bool:
    return bool(gamedata.get("free_handicap_placement"))


def _as_int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    return default


def ogs_json_to_sgf(data: dict[str, object]) -> str:
    game_id = str(data.get("id", ""))
    gamedata_value = data.get("gamedata")
    if not isinstance(gamedata_value, dict):
        raise OGSDownloadError("OGS game data did not include moves.")
    gamedata = cast(dict[object, object], gamedata_value)

    width = _as_int(gamedata.get("width", data.get("width")), 19)
    height = _as_int(gamedata.get("height", data.get("height")), 19)
    if width != height:
        raise OGSDownloadError("Only square Go boards are supported by this prototype.")

    players = data.get("players") if isinstance(data.get("players"), dict) else {}
    black = players.get("black", {}) if isinstance(players, dict) else {}
    white = players.get("white", {}) if isinstance(players, dict) else {}
    black_name = black.get("username", "Black") if isinstance(black, dict) else "Black"
    white_name = white.get("username", "White") if isinstance(white, dict) else "White"

    handicap = _as_int(gamedata.get("handicap", data.get("handicap")), 0)
    initial_state = gamedata.get("initial_state")
    black_setup: list[str] = []
    white_setup: list[str] = []
    if isinstance(initial_state, dict):
        black_setup = _initial_state_coords(initial_state.get("black"))
        white_setup = _initial_state_coords(initial_state.get("white"))

    moves = gamedata.get("moves")
    if not isinstance(moves, list):
        raise OGSDownloadError("OGS game data did not include a move list.")

    move_start_index = 0
    if handicap and _free_handicap_enabled(gamedata) and not black_setup:
        for move in moves[:handicap]:
            if not isinstance(move, list) or len(move) < 2:
                continue
            x = _as_int(move[0], -1)
            y = _as_int(move[1], -1)
            coord = _sgf_coord(x, y)
            if coord:
                black_setup.append(coord)
                move_start_index += 1
        if black_setup:
            # OGS represents free handicap placement as the first N black "moves".
            # SGF/KaTrain need those stones represented as setup stones, with White
            # to play after the handicap placement is complete.
            move_start_index = len(black_setup)

    props = [
        "(;GM[1]FF[4]",
        f"CA[UTF-8]AP[KomiLab:0.1]SZ[{width}]",
        f"KM[{_sgf_escape(gamedata.get('komi', data.get('komi', 6.5)))}]",
        f"RU[{_sgf_escape(gamedata.get('rules', data.get('rules', '')))}]",
        f"PB[{_sgf_escape(black_name)}]PW[{_sgf_escape(white_name)}]",
        f"GN[{_sgf_escape(data.get('name', 'OGS game ' + game_id))}]",
        f"GC[Imported from https://online-go.com/game/{game_id}]",
    ]
    if handicap:
        props.append(f"HA[{handicap}]")
    if black_setup:
        props.append(_setup_property("AB", black_setup))
    if white_setup:
        props.append(_setup_property("AW", white_setup))
    if black_setup or white_setup:
        player_to_move = "W" if handicap and black_setup else _initial_player(data, gamedata)
        props.append(f"PL[{player_to_move}]")
    if data.get("outcome"):
        props.append(f"RE[{_sgf_escape(data['outcome'])}]")

    move_parts: list[str] = []
    color = "W" if handicap and black_setup else _initial_player(data, gamedata)
    for move in moves[move_start_index:]:
        if not isinstance(move, list) or len(move) < 2:
            continue
        x = _as_int(move[0], -1)
        y = _as_int(move[1], -1)
        move_parts.append(f";{color}[{_sgf_coord(x, y)}]")
        color = "W" if color == "B" else "B"

    return "".join(props + move_parts) + ")\n"
