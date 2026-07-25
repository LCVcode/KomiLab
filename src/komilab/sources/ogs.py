from __future__ import annotations

import hashlib
import json
import re
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
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
    source_url: str
    sgf_path: Path
    sha256: str


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
        final_path = destination_dir / f"{game_id}.sgf"

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=destination_dir, delete=False
        ) as tmp:
            tmp.write(sgf)
            tmp_path = Path(tmp.name)
        tmp_path.replace(final_path)

        return ImportedGame(
            game_id=game_id,
            source_url=f"https://online-go.com/game/{game_id}",
            sgf_path=final_path,
            sha256=sha256,
        )


def _sgf_escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("]", r"\]").replace("\n", " ")


def _sgf_coord(x: int, y: int) -> str:
    if x < 0 or y < 0:
        return ""
    letters = "abcdefghijklmnopqrstuvwxyz"
    return letters[x] + letters[y]


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
    gamedata = data.get("gamedata")
    if not isinstance(gamedata, dict):
        raise OGSDownloadError("OGS game data did not include moves.")

    width = _as_int(gamedata.get("width", data.get("width")), 19)
    height = _as_int(gamedata.get("height", data.get("height")), 19)
    if width != height:
        raise OGSDownloadError("Only square Go boards are supported by this prototype.")

    players = data.get("players") if isinstance(data.get("players"), dict) else {}
    black = players.get("black", {}) if isinstance(players, dict) else {}
    white = players.get("white", {}) if isinstance(players, dict) else {}
    black_name = black.get("username", "Black") if isinstance(black, dict) else "Black"
    white_name = white.get("username", "White") if isinstance(white, dict) else "White"

    props = [
        "(;GM[1]FF[4]",
        f"CA[UTF-8]AP[KomiLab:0.1]SZ[{width}]",
        f"KM[{_sgf_escape(gamedata.get('komi', data.get('komi', 6.5)))}]",
        f"RU[{_sgf_escape(gamedata.get('rules', data.get('rules', '')))}]",
        f"PB[{_sgf_escape(black_name)}]PW[{_sgf_escape(white_name)}]",
        f"GN[{_sgf_escape(data.get('name', 'OGS game ' + game_id))}]",
        f"GC[Imported from https://online-go.com/game/{game_id}]",
    ]
    if data.get("outcome"):
        props.append(f"RE[{_sgf_escape(data['outcome'])}]")

    moves = gamedata.get("moves")
    if not isinstance(moves, list):
        raise OGSDownloadError("OGS game data did not include a move list.")

    move_parts: list[str] = []
    color = "B"
    for move in moves:
        if not isinstance(move, list) or len(move) < 2:
            continue
        x = _as_int(move[0], -1)
        y = _as_int(move[1], -1)
        move_parts.append(f";{color}[{_sgf_coord(x, y)}]")
        color = "W" if color == "B" else "B"

    return "".join(props + move_parts) + ")\n"
