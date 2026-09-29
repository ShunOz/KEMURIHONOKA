"""Instagramの投稿を、MEO/SEOを意識したGBP投稿文に整形する。

方針 (GBPのポリシーに沿う):
- 冒頭100文字 (一覧で見える範囲) に「店名・エリア・業態・話題」を入れる
- 狙う検索語は文中に自然に1〜2回。羅列・詰め込みはしない (審査落ち/評価低下の原因)
- 電話番号・URL・ハッシュタグ・過度な記号は入れない (リンクはCTAボタンで出す)
- 150〜300文字目安。最後に来店を促す一文
"""
from __future__ import annotations

import os
import re

import requests

MAX_LEN = 1500  # GBP localPost summary の上限
TARGET_MAX = 400  # 生成文の上限 (これを超えたら不合格→再整形/切り詰め)

_URL = re.compile(r"https?://|www\.", re.I)
_PHONE = re.compile(r"0\d{1,4}[-ー－\s]?\d{1,4}[-ー－\s]?\d{3,4}")


def clean_caption(caption: str) -> str:
    text = re.sub(r"(?:^|\s)[#＃]\S+", "", caption)  # ハッシュタグ除去
    text = re.sub(r"@\w[\w.]*", "", text)  # メンション除去
    text = _URL.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate(text: str, loc: dict) -> list[str]:
    """ポリシー/MEO観点の問題点を返す (空なら合格)。"""
    seo = loc.get("seo") or {}
    problems = []
    if _URL.search(text):
        problems.append("URLを含む")
    if _PHONE.search(text):
        problems.append("電話番号を含む")
    if "#" in text or "＃" in text:
        problems.append("ハッシュタグを含む")
    if re.search(r"[!！]{2,}", text):
        problems.append("感嘆符の多用")
    if loc["name"] not in text[:100]:
        problems.append("冒頭100文字に店名がない")
    if seo.get("area") and seo["area"] not in text:
        problems.append("エリア名がない")
    if len(text) > TARGET_MAX:
        problems.append("長すぎる")
    for kw in seo.get("keywords") or []:  # 詰め込み検知
        if text.count(kw) > 2:
            problems.append(f"キーワード過多: {kw}")
    return problems


def template_summary(caption: str, loc: dict) -> str:
    """LLMを使えない時の代替。店名・エリア・業態を冒頭に置く。"""
    seo = loc.get("seo") or {}
    area, cat = seo.get("area", ""), seo.get("category", "")
    head = f"{loc['name']}（{area}{cat}）からのお知らせです。".replace("（）", "")
    body = clean_caption(caption) or "最新の様子をお届けします。"
    tail = f"{seo['nearby']}。ご来店をお待ちしております。" if seo.get("nearby") else "ご来店をお待ちしております。"
    return f"{head}\n{body}\n\n{tail}"


def build_summary(caption: str, loc: dict, rewrite: bool = False, tone: str = "") -> str:
    text = None
    if rewrite and clean_caption(caption):
        text = _generate(clean_caption(caption), loc, tone)
    if not text:
        text = template_summary(caption, loc)
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 1] + "…"
    return text


def _prompt(caption: str, loc: dict, tone: str, problems: list[str] | None = None) -> str:
    seo = loc.get("seo") or {}
    fix = f"\n前回の案は次の理由で不合格でした。必ず直してください: {'、'.join(problems)}\n" if problems else ""
    return f"""あなたは飲食店のGoogleビジネスプロフィール運用担当です。
下のInstagram投稿をもとに、MEO/SEOを意識した「最新情報」の投稿文を日本語で1つ作ってください。

# 店舗情報
- 店名(表記は一字一句このまま): {loc['name']}
- エリア: {seo.get('area', '')} / アクセス: {seo.get('nearby', '')}
- 業態: {seo.get('category', '')}
- 強み・名物: {', '.join(seo.get('features') or [])}
- 狙う検索語(自然に入れる場合のみ。全部入れる必要はない): {', '.join(seo.get('keywords') or [])}
- 口調: {tone or '丁寧で親しみやすい'}

# ルール
- 冒頭100文字以内に、店名・エリア・業態(または話題)を自然に含める
- 検索語は多くても1〜2個、各1〜2回まで。羅列・詰め込みは禁止
- 事実はInstagram投稿の内容のみ。価格・日時・メニュー名・特典を創作しない
- 電話番号・URL・ハッシュタグ・メンション・絵文字の連発・「!!」は禁止
- 150〜300文字、最後に来店を促す一文
- 本文のみ出力(見出しや説明は不要)
{fix}
# Instagram投稿
{caption}"""


def _call_claude(prompt: str) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-5-5", "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"].strip()


def _generate(caption: str, loc: dict, tone: str) -> str | None:
    """生成→検証→不合格なら指摘つきで1回だけ再生成。それでも不合格ならNone(テンプレへ)。"""
    problems: list[str] | None = None
    for _ in range(2):
        try:
            text = _call_claude(_prompt(caption, loc, tone, problems))
        except Exception as e:
            print(f"  (Claude生成をスキップ: {e})")
            return None
        if not text:
            return None
        problems = validate(text, loc)
        if not problems:
            return text
        print(f"  (検証NG: {problems})")
    return None
