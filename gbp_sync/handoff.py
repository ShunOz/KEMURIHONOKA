"""半自動モード: 投稿文と写真/動画を用意し、GitHub Issue で担当者に渡す。

GBP APIが使えない場合の運用。担当者はIssueの文章をコピーし、
成果物(artifact)の写真/動画と一緒に GBPアプリ/管理画面から投稿する。
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

from .instagram import Media

EXT = {"PHOTO": "jpg", "VIDEO": "mp4"}


def prepare(m: Media, summary: str, loc: dict, outdir: Path) -> Path:
    """out/<店舗>/<投稿ID>/ に post.txt と写真/動画を保存する。"""
    d = outdir / loc["key"] / m.id
    d.mkdir(parents=True, exist_ok=True)
    (d / "post.txt").write_text(summary + "\n", encoding="utf-8")
    for i, (kind, url) in enumerate(m.assets, 1):
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        (d / f"{i:02d}_{kind.lower()}.{EXT[kind]}").write_bytes(r.content)
    return d


def issue_body(m: Media, summary: str, loc: dict, run_url: str) -> str:
    n_p = sum(1 for k, _ in m.assets if k == "PHOTO")
    n_v = sum(1 for k, _ in m.assets if k == "VIDEO")
    return f"""**{loc['name']}** の Instagram 新着を GBP に投稿してください。

- Instagram: {m.permalink}
- 写真 {n_p} 枚 / 動画 {n_v} 本 → [ダウンロード(Actionsの成果物 `gbp-post-materials`)]({run_url})
  (`{loc['key']}/{m.id}/` フォルダ内。成果物は90日で消えます)

### 投稿文 (そのままコピー)
```
{summary}
```

### 手順
- [ ] GBP の「更新情報を追加」→ 写真を1枚選び、上の文章を貼って投稿
- [ ] 残りの写真・動画は「写真を追加」から登録
- [ ] 完了したらこのIssueをクローズ

※ 写真は10KB〜5MB・400×300px以上、動画は30秒以内・75MB以下。
"""


def create_issue(m: Media, summary: str, loc: dict) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not (token and repo):
        raise RuntimeError("manualモードには GITHUB_TOKEN / GITHUB_REPOSITORY が必要です (Actions上で実行してください)")
    run_url = (
        f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}"
        f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    )
    first = summary.strip().splitlines()[0][:40]
    r = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={
            "title": f"[GBP投稿] {loc['name']} {m.timestamp:%m/%d} {first}",
            "body": issue_body(m, summary, loc, run_url),
            "labels": ["gbp-post"],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["html_url"]
