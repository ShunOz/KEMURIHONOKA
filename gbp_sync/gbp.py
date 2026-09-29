"""Google Business Profile API クライアント (投稿 + 写真/動画)。

必要: GBP API の利用承認済みGCPプロジェクトと、business.manage スコープの
OAuth リフレッシュトークン。
"""
from __future__ import annotations

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://mybusiness.googleapis.com/v4"


class GBP:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._creds = (client_id, client_secret, refresh_token)
        self._access: str | None = None

    def _token(self) -> str:
        if not self._access:
            cid, secret, refresh = self._creds
            r = requests.post(
                TOKEN_URL,
                data={
                    "client_id": cid,
                    "client_secret": secret,
                    "refresh_token": refresh,
                    "grant_type": "refresh_token",
                },
                timeout=30,
            )
            r.raise_for_status()
            self._access = r.json()["access_token"]
        return self._access

    def _post(self, path: str, body: dict) -> dict:
        r = requests.post(
            f"{API}/{path}",
            json=body,
            headers={"Authorization": f"Bearer {self._token()}"},
            timeout=60,
        )
        if not r.ok:
            raise RuntimeError(f"GBP {path} -> {r.status_code}: {r.text}")
        return r.json()

    def create_post(
        self,
        account: str,
        location: str,
        summary: str,
        photo_url: str | None = None,
        cta: tuple[str, str] | None = None,
    ) -> dict:
        body: dict = {
            "languageCode": "ja",
            "summary": summary,
            "topicType": "STANDARD",
        }
        if photo_url:
            body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": photo_url}]
        if cta and cta[1]:
            body["callToAction"] = {"actionType": cta[0], "url": cta[1]}
        return self._post(f"{account}/{location}/localPosts", body)

    def add_media(self, account: str, location: str, kind: str, url: str) -> dict:
        """写真/動画を写真タブに追加。kind は PHOTO or VIDEO。"""
        return self._post(
            f"{account}/{location}/media",
            {
                "mediaFormat": kind,
                "locationAssociation": {"category": "ADDITIONAL"},
                "sourceUrl": url,
            },
        )
