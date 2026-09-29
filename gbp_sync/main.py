"""煙仄 各店舗の Instagram 最新投稿を GBP に反映する。

使い方:
  python -m gbp_sync.main              # ドライラン (投稿しない)
  python -m gbp_sync.main --apply      # 実投稿
  python -m gbp_sync.main --apply --only shinjuku
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import content, instagram, state
from .gbp import GBP

CONFIG = Path(__file__).resolve().parent.parent / "config" / "locations.yaml"


def select_new(media: list[instagram.Media], done: set[str], max_age_days: int, limit: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    fresh = [m for m in media if m.id not in done and m.timestamp >= cutoff and m.assets]
    fresh.sort(key=lambda m: m.timestamp)  # 古い順に投稿
    return fresh[:limit]


def process(loc: dict, cfg: dict, done: set[str], gbp: GBP | None, account: str, apply: bool) -> list[str]:
    token = os.environ.get(loc["ig_token_env"], "")
    if not (loc["ig_user_id"] and loc["gbp_location"] and token):
        print(f"[{loc['key']}] 設定/トークン未設定のためスキップ")
        return []
    media = instagram.fetch_recent(loc["ig_user_id"], token, cfg["lookback_posts"])
    targets = select_new(media, done, cfg["max_age_days"], cfg["max_posts_per_run"])
    posted: list[str] = []
    for m in targets:
        summary = content.build_summary(m.caption, loc["name"], m.permalink, cfg["rewrite_with_claude"])
        first_photo = next((u for k, u in m.assets if k == "PHOTO"), None)
        print(f"[{loc['key']}] {m.id} {m.media_type} assets={len(m.assets)}\n{summary}\n")
        if not apply:
            continue
        cta = (cfg["post_cta"], loc.get("cta_url", ""))
        gbp.create_post(account, loc["gbp_location"], summary, first_photo, cta)
        if cfg["upload_media_to_gallery"]:
            for kind, url in m.assets:
                try:
                    gbp.add_media(account, loc["gbp_location"], kind, url)
                except RuntimeError as e:  # 1件失敗しても続行
                    print(f"  media失敗: {e}")
        posted.append(m.id)
    return posted


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    conf = yaml.safe_load(CONFIG.read_text())
    gbp = account = None
    if args.apply:
        gbp = GBP(os.environ["GBP_CLIENT_ID"], os.environ["GBP_CLIENT_SECRET"], os.environ["GBP_REFRESH_TOKEN"])
        account = os.environ["GBP_ACCOUNT"]  # "accounts/<ID>"

    st = state.load()
    failed = False
    for loc in conf["locations"]:
        if args.only and loc["key"] != args.only:
            continue
        try:
            new = process(loc, conf["settings"], set(st.get(loc["key"], [])), gbp, account, args.apply)
            st[loc["key"]] = (st.get(loc["key"], []) + new)[-200:]
        except Exception as e:  # 片方の店舗の失敗で他方を止めない
            failed = True
            print(f"[{loc['key']}] エラー: {e}", file=sys.stderr)
    if args.apply:
        state.save(st)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
