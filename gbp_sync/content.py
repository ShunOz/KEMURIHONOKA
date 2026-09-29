"""Instagramのキャプションを GBP 投稿文に整形する。"""
from __future__ import annotations

import os
import re

import requests

MAX_LEN = 1500  # GBP localPost summary の上限


def clean_caption(caption: str) -> str:
    text = re.sub(r"(?:^|\s)[#＃]\S+", "", caption)  # ハッシュタグ除去
    text = re.sub(r"@\w[\w.]*", "", text)  # メンション除去
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_summary(caption: str, store_name: str, permalink: str, rewrite: bool = False) -> str:
    text = clean_caption(caption)
    if rewrite and text:
        text = _rewrite_with_claude(text, store_name) or text
    if not text:
        text = f"{store_name}の最新情報をInstagramで更新しました。"
    if permalink:
        text = f"{text}\n\n最新情報はInstagramでも: {permalink}"
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 1] + "…"
    return text


def _rewrite_with_claude(text: str, store_name: str) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5-5",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"「{store_name}」のInstagram投稿をGoogleビジネスプロフィールの"
                        "最新情報として書き直してください。事実は変えず、絵文字は控えめに、"
                        "電話番号・URL・ハッシュタグは入れず、1200文字以内。"
                        "本文のみ出力してください。\n\n" + text
                    ),
                }],
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:  # 失敗時は元の文章で続行
        print(f"  (Claude整形をスキップ: {e})")
        return None
