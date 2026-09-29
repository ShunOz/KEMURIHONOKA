"""投稿済みInstagram IDの記録 (state/posted.json)。"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "state" / "posted.json"


def load(path: Path = PATH) -> dict[str, list[str]]:
    return json.loads(path.read_text()) if path.exists() else {}


def save(data: dict[str, list[str]], path: Path = PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
