# 初期設定ガイド

集める値は全部で下の表のとおり。A(Instagram)とB(GBP)は独立して進められる。
Bは Google の承認待ちが数日かかることがあるので、**先にBの申請だけ出す**のがおすすめ。

| 値 | 置き場所 | 取得元 |
|---|---|---|
| ig_user_id ×2 | config/locations.yaml | A-4 |
| IG_TOKEN_SHINJUKU / IG_TOKEN_IKEBUKURO | GitHub Secrets | A-4 |
| GBP_CLIENT_ID / GBP_CLIENT_SECRET | GitHub Secrets | B-3 |
| GBP_REFRESH_TOKEN | GitHub Secrets | B-4 |
| GBP_ACCOUNT (`accounts/…`) | GitHub Secrets | B-5 |
| gbp_location ×2 (`locations/…`) | config/locations.yaml | B-5 |
| ANTHROPIC_API_KEY (任意) | GitHub Secrets | console.anthropic.com |

## B. Google Business Profile (先に申請)
1. **GCPプロジェクト作成**: https://console.cloud.google.com/ (店舗のGBPオーナー権限を持つGoogleアカウントで)
2. **API利用申請**: 「Google Business Profile API access request」フォームを提出
   (プロジェクト番号、店舗のメール、用途「自店舗の最新情報・写真投稿の自動化」)。承認まで数日。
   承認後、APIライブラリで次を有効化:
   - My Business Account Management API
   - My Business Business Information API
   - Google My Business API (v4: 投稿・写真はこれ)
3. **OAuthクライアント作成**: 「APIとサービス → OAuth同意画面」を作成し、
   **公開ステータスを「本番環境」にする** (「テスト」のままだとリフレッシュトークンが7日で失効する)。
   「認証情報 → OAuthクライアントID」を「ウェブアプリケーション」で作成し、
   リダイレクトURIに `https://developers.google.com/oauthplayground` を追加。
   → GBP_CLIENT_ID / GBP_CLIENT_SECRET
4. **リフレッシュトークン取得**: https://developers.google.com/oauthplayground を開く →
   右上の歯車で「Use your own OAuth credentials」にチェックしID/Secretを入力 →
   スコープ欄に `https://www.googleapis.com/auth/business.manage` → Authorize →
   「Exchange authorization code for tokens」→ **Refresh token** をコピー → GBP_REFRESH_TOKEN
5. **IDの確認** (ローカルで):
   `GBP_CLIENT_ID=.. GBP_CLIENT_SECRET=.. GBP_REFRESH_TOKEN=.. python -m gbp_sync.setup_helper gbp`
   → `accounts/…` を GBP_ACCOUNT に、各店舗の `locations/…` を config/locations.yaml の gbp_location に。

## A. Instagram
前提: 両店舗のInstagramが「プロフェッショナルアカウント(ビジネス/クリエイター)」で、
それぞれFacebookページとリンク済み (Instagram設定 → アカウントセンター等)。
1. https://developers.facebook.com/ でアプリを作成 (種類: ビジネス)。
   自分たちのアカウントだけを扱うので、アプリは開発モードのままでよい (アプリ審査不要)。
   ただし、操作するFacebookアカウントがアプリの管理者/開発者であること。
2. Graph API エクスプローラ (https://developers.facebook.com/tools/explorer/) で
   そのアプリを選び、権限 `instagram_basic` `pages_show_list` `pages_read_engagement`
   を付けて「ユーザートークン」を生成 (両店舗のページを選択して許可)。
3. 長期トークン化 (60日):
   `curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<短期トークン>"`
4. `FB_USER_TOKEN=<長期トークン> python -m gbp_sync.setup_helper ig`
   → 店舗ごとに ig_user_id と**ページトークン**が表示される。
   ig_user_id を config/locations.yaml へ、ページトークンを IG_TOKEN_SHINJUKU / IG_TOKEN_IKEBUKURO へ。
   長期ユーザートークンから得たページトークンは**有効期限なし**なので、定期更新は不要
   (パスワード変更や権限の取り消しで失効する)。

## GitHub Secrets 登録
リポジトリ Settings → Secrets and variables → Actions → New repository secret に、上表の値を登録。

## 動作確認
1. Actions →「GBP sync」→ Run workflow → `apply` を **false** (ドライラン)。ログに投稿予定の文章が出る。
2. 文章とtoneを確認、必要なら config/locations.yaml を調整。
3. `apply` を true で手動実行 → GBPに投稿されたか確認。以後は毎日10:00 JSTに自動実行。
