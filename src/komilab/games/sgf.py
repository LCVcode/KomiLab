from __future__ import annotations

from pathlib import Path

MAX_SGF_BYTES = 5 * 1024 * 1024


class SGFValidationError(ValueError):
    pass


def validate_sgf_file(path: Path) -> None:
    data = path.read_bytes()
    if not data:
        raise SGFValidationError("The game record is empty.")
    if len(data) > MAX_SGF_BYTES:
        raise SGFValidationError("The game record is too large.")
    prefix = data[:200].lstrip().lower()
    if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html"):
        raise SGFValidationError("The downloaded file was an HTML page, not an SGF game.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SGFValidationError("The game record is not valid UTF-8 text.") from exc
    compact = text.lstrip()
    if not compact.startswith("(") or ";" not in compact[:20]:
        raise SGFValidationError("The file does not look like an SGF game tree.")
    if "GM[1]" not in text and "GM[" in text:
        raise SGFValidationError("The SGF does not appear to be a Go game.")


def count_sgf_moves(path: Path) -> int:
    """Return a lightweight count of played black/white moves in an SGF file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0

    moves = 0
    in_value = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_value:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "]":
                in_value = False
            index += 1
            continue

        if char == "[":
            in_value = True
        elif char == ";":
            next_index = index + 1
            while next_index < len(text) and text[next_index].isspace():
                next_index += 1
            if next_index < len(text) and text[next_index] in {"B", "W"}:
                prop_index = next_index + 1
                while prop_index < len(text) and text[prop_index].isspace():
                    prop_index += 1
                if prop_index < len(text) and text[prop_index] == "[":
                    moves += 1
        index += 1
    return moves
