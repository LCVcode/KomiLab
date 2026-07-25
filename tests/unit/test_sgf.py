from __future__ import annotations

import pytest

from komilab.games.sgf import SGFValidationError, validate_sgf_file


def test_valid_sgf(tmp_path) -> None:
    path = tmp_path / "game.sgf"
    path.write_text("(;GM[1]FF[4]SZ[19];B[dd];W[pp])", encoding="utf-8")
    validate_sgf_file(path)


def test_html_rejected(tmp_path) -> None:
    path = tmp_path / "game.sgf"
    path.write_text("<!doctype html><html></html>", encoding="utf-8")
    with pytest.raises(SGFValidationError):
        validate_sgf_file(path)
