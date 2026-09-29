# 煙仄 GBP 自動更新

煙仄 新宿店 / 煙仄2nd 池袋店の Instagram 最新投稿(写真・動画・キャプション)を、
Googleビジネスプロフィール(GBP)の「最新情報」と写真タブへ毎日自動反映します。

## 仕組み
GitHub Actions (毎日10:00 JST) → Instagram Graph API で直近投稿取得 → 未投稿かつ14日以内のものを
GBP API で投稿 → `state/posted.json` に記録(二重投稿防止)。

- 写真: 最新情報の画像 + 写真タブに登録
- 動画: 写真タブに登録 (GBPの最新情報投稿APIは動画非対応のため。30秒/75MBまで)
- カルーセル: 全画像/動画を展開して写真タブへ、最初の画像を最新情報に使用
- 投稿文: キャプションからハッシュタグ/メンションを除去、末尾にInstagramリンク。
  `rewrite_with_claude: true` でGBP向けにClaudeが整形

## セットアップ (要手動)
1. `config/locations.yaml` の TODO(ig_user_id, gbp_location, cta_url)を記入
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
    python -m gbp_sync.main            # ドライラン
    python -m gbp_sync.main --apply    # 実投稿
