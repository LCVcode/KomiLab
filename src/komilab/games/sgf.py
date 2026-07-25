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
