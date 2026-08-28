"""Best-score persistence for Pixel Aircraft Battle."""

from __future__ import annotations

from pathlib import Path

from games.common.json_store import load_json_object, non_negative_int, save_json_object

PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


def load_best_score(path: Path = PLAYER_DATA_PATH) -> int:
    payload = load_json_object(path)
    if payload is None:
        return 0
    return non_negative_int(payload.get("best_score"))


def save_best_score(score: int, path: Path = PLAYER_DATA_PATH) -> bool:
    return save_json_object(path, {"best_score": max(0, int(score))})
