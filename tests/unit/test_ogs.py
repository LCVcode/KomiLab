from __future__ import annotations

import pytest

from komilab.sources.ogs import OGSGameSource, OGSReferenceError, ogs_json_to_sgf


def test_normalize_id() -> None:
    assert OGSGameSource().normalize_reference("88417735") == "88417735"


def test_normalize_url() -> None:
    assert (
        OGSGameSource().normalize_reference("https://online-go.com/game/88417735?x=1#y")
        == "88417735"
    )


def test_reject_other_hosts() -> None:
    with pytest.raises(OGSReferenceError):
        OGSGameSource().normalize_reference("https://example.com/game/88417735")


def test_ogs_json_to_sgf() -> None:
    sgf = ogs_json_to_sgf(
        {
            "id": 1,
            "name": "Black vs White",
            "players": {"black": {"username": "Black"}, "white": {"username": "White"}},
            "gamedata": {
                "width": 19,
                "height": 19,
                "komi": 6.5,
                "rules": "japanese",
                "moves": [[3, 3], [15, 15]],
            },
        }
    )
    assert "GM[1]" in sgf
    assert "PB[Black]PW[White]" in sgf
    assert ";B[dd];W[pp]" in sgf
