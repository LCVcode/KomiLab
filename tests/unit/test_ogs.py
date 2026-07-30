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


def test_ogs_handicap_json_to_sgf_uses_setup_stones_and_white_to_play() -> None:
    sgf = ogs_json_to_sgf(
        {
            "id": 88417728,
            "name": "Handicap game",
            "handicap": 2,
            "players": {"black": {"username": "Black"}, "white": {"username": "White"}},
            "gamedata": {
                "width": 19,
                "height": 19,
                "komi": 0.5,
                "rules": "japanese",
                "handicap": 2,
                "initial_player": "white",
                "initial_state": {"black": "pddp", "white": ""},
                "moves": [[15, 15], [2, 2]],
            },
        }
    )
    assert "HA[2]" in sgf
    assert "AB[pd][dp]" in sgf
    assert "PL[W]" in sgf
    assert ";W[pp];B[cc]" in sgf


def test_ogs_free_handicap_json_to_sgf_converts_opening_placements_to_setup() -> None:
    sgf = ogs_json_to_sgf(
        {
            "id": 2,
            "name": "Free handicap game",
            "handicap": 5,
            "players": {"black": {"username": "Black"}, "white": {"username": "White"}},
            "gamedata": {
                "width": 19,
                "height": 19,
                "komi": 0.5,
                "rules": "japanese",
                "handicap": 5,
                "free_handicap_placement": True,
                "initial_player": "black",
                "initial_state": {"black": "", "white": ""},
                "moves": [
                    [2, 4],
                    [3, 2],
                    [2, 15],
                    [4, 16],
                    [15, 3],
                    [15, 15],
                    [3, 3],
                ],
            },
        }
    )
    assert "HA[5]" in sgf
    assert "AB[ce][dc][cp][eq][pd]" in sgf
    assert "PL[W]" in sgf
    assert ";W[pp];B[dd]" in sgf
    assert ";B[ce]" not in sgf
