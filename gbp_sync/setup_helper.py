"""初期設定用の補助コマンド (投稿はしない・読み取りのみ)。

  # 1) Facebookページ経由で、管理しているInstagramの数値IDとページトークンを一覧
  FB_USER_TOKEN=<長期ユーザートークン> python -m gbp_sync.setup_helper ig

  # 2) GBPのアカウントIDとロケーションIDを一覧
  GBP_CLIENT_ID=.. GBP_CLIENT_SECRET=.. GBP_REFRESH_TOKEN=.. python -m gbp_sync.setup_helper gbp
"""
from __future__ import annotations

import os
import sys

import requests

from .gbp import GBP
from .instagram import GRAPH


def ig() -> None:
    r = requests.get(
        f"{GRAPH}/me/accounts",
        params={
            "fields": "name,access_token,instagram_business_account{id,username}",
            "access_token": os.environ["FB_USER_TOKEN"],
        },
        timeout=30,
    )
    r.raise_for_status()
    for p in r.json().get("data", []):
        acc = p.get("instagram_business_account")
        if not acc:
            continue
        print(f"@{acc['username']}\n  ig_user_id: {acc['id']}\n  ページ: {p['name']}")
        print(f"  ページトークン(Secretsへ。表示は1回だけ): {p['access_token']}\n")


def gbp() -> None:
    g = GBP(os.environ["GBP_CLIENT_ID"], os.environ["GBP_CLIENT_SECRET"], os.environ["GBP_REFRESH_TOKEN"])
    h = {"Authorization": f"Bearer {g._token()}"}
    accs = requests.get("https://mybusinessaccountmanagement.googleapis.com/v1/accounts", headers=h, timeout=30)
    accs.raise_for_status()
    for a in accs.json().get("accounts", []):
        print(f"GBP_ACCOUNT = {a['name']}  ({a.get('accountName', '')})")
        locs = requests.get(
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{a['name']}/locations",
            params={"readMask": "name,title,storefrontAddress.addressLines"},
            headers=h,
            timeout=30,
        )
        locs.raise_for_status()
        for loc in locs.json().get("locations", []):
            print(f"  gbp_location: {loc['name']}   {loc.get('title', '')}")


if __name__ == "__main__":
    {"ig": ig, "gbp": gbp}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
