"""Instagram Graph API から直近の投稿を取得する。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import requests

GRAPH = "https://graph.facebook.com/v21.0"
FIELDS = (
    "id,caption,media_type,media_url,permalink,timestamp,"
    "children{id,media_type,media_url}"
)


@dataclass
class Media:
    id: str
    caption: str
    media_type: str  # IMAGE / VIDEO / CAROUSEL_ALBUM
    media_url: str
    permalink: str
    timestamp: datetime
    # (kind, url) kind は "PHOTO" / "VIDEO"。カルーセルは子要素を展開。
    assets: list[tuple[str, str]] = field(default_factory=list)


def _kind(media_type: str) -> str:
    return "VIDEO" if media_type == "VIDEO" else "PHOTO"


def parse_media(item: dict) -> Media:
    assets: list[tuple[str, str]] = []
    if item.get("media_type") == "CAROUSEL_ALBUM":
        for c in item.get("children", {}).get("data", []):
            if c.get("media_url"):
                assets.append((_kind(c["media_type"]), c["media_url"]))
    elif item.get("media_url"):
        assets.append((_kind(item["media_type"]), item["media_url"]))
    return Media(
        id=item["id"],
        caption=item.get("caption") or "",
        media_type=item["media_type"],
        media_url=item.get("media_url", ""),
        permalink=item.get("permalink", ""),
        timestamp=datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%S%z"),
        assets=assets,
    )


def fetch_recent(ig_user_id: str, token: str, limit: int = 10) -> list[Media]:
    r = requests.get(
        f"{GRAPH}/{ig_user_id}/media",
        params={"fields": FIELDS, "limit": limit, "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    return [parse_media(i) for i in r.json().get("data", [])]
