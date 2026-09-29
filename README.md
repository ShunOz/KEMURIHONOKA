# 煙仄 GBP 自動更新

煙仄 新宿店 / 煙仄2nd 池袋店の Instagram 最新投稿(写真・動画・キャプション)を、
Googleビジネスプロフィール(GBP)の「最新情報」と写真タブへ毎日自動反映します。

## 仕組み
GitHub Actions (毎日10:00 JST) → Instagram Graph API で直近投稿取得 → 未投稿かつ14日以内のものを処理
→ `state/posted.json` に記録(二重処理防止)。処理方法は `--mode` で切替:
- `manual` (現在の運用): 投稿文を作り、写真/動画をダウンロードして成果物 `gbp-post-materials` に保存、
  担当者向けの **GitHub Issue** (ラベル `gbp-post`) を作成。担当者がGBPに貼り付けて投稿し、Issueを閉じる。
- `api`: GBP APIで完全自動投稿 (API利用承認が必要。承認後、ワークフローの `MODE` を `api` に変更)
- `dry-run`: 内容確認のみ

- 写真: 最新情報の画像 + 写真タブに登録
- 動画: 写真タブに登録 (GBPの最新情報投稿APIは動画非対応のため。30秒/75MBまで)
- カルーセル: 全画像/動画を展開して写真タブへ、最初の画像を最新情報に使用
- 投稿文: MEO/SEO向けにClaudeが作成 (下記)。APIキー無し/検証NGならテンプレ文で代替

## 投稿文のMEO/SEO方針
`config/locations.yaml` の `seo`(エリア・最寄り・業態・狙う検索語・強み)と `tone` をもとに生成。
- 冒頭100文字に 店名+エリア+業態/話題 (一覧表示で見える範囲)
- 検索語は自然に1〜2個まで。詰め込み禁止 (GBP審査・評価低下の回避)
- 事実はInstagram投稿の内容のみ。価格・日時・特典を創作しない
- 電話番号/URL/ハッシュタグ/「!!」なし (リンクはCTAボタン)。150〜300文字、末尾に来店を促す一文
- 生成後に自動検証し、NGなら指摘つきで1回再生成、それでもNGならテンプレ文にフォールバック
- 店名は登録名(NAP)と一字一句同じ表記を使用

## セットアップ (要手動)
詳細な手順は [docs/SETUP.md](docs/SETUP.md) を参照。
1. `config/locations.yaml` の TODO(ig_user_id, gbp_location, cta_url, seo.*, tone)を記入
2. **Instagram**: 各店舗アカウントをビジネス/クリエイターにし、Metaアプリで
   長期トークンを発行(60日で失効、要更新) → Secrets `IG_TOKEN_SHINJUKU` / `IG_TOKEN_IKEBUKURO`
3. **GBP**: GCPで Business Profile API の利用申請・承認 → OAuth(scope `business.manage`)で
   リフレッシュトークン取得 → Secrets `GBP_CLIENT_ID` `GBP_CLIENT_SECRET` `GBP_REFRESH_TOKEN`
   `GBP_ACCOUNT` (`accounts/xxxx`)
4. (任意) `ANTHROPIC_API_KEY`
5. Actions の「GBP sync」を `apply=false` で手動実行して内容確認 → 問題なければ有効化

## ローカル実行
    pip install -r requirements.txt
    pytest
    python -m gbp_sync.main                 # ドライラン
    python -m gbp_sync.main --mode api      # GBP APIで実投稿 (要API承認)
