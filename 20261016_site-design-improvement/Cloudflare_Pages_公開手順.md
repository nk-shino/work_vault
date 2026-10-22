# Cloudflare Pages 公開手順（静かな資料館 モック）

更新: 2026-10-22。公開単位: `20261016_site-design-improvement/improve/`（仮決定）。

## 方式の選定

Git 接続連携ではなく **wrangler 直接アップロード** を標準とする。
理由: 本リポジトリ（nk-shino/work_vault）は 98_Pass（認証情報）を含むため、Cloudflare 側 GitHub App に読み取り権限を渡さない。

## 事前準備

- Cloudflare アカウント（無料）を作成
- Node.js の入った PC（`npx` で wrangler を実行）

## 手順

1. ログイン

   ```
   npx wrangler login
   ```

2. デプロイ用 dist を作成（`shots` と `tools` を除外）

   ```
   cd 20261016_site-design-improvement
   rm -rf dist && mkdir dist && cp -r improve/. dist/ && rm -rf dist/shots dist/tools
   ```

3. 初回デプロイ（`--project-name` は以降も同じ名前を使う）

   ```
   npx wrangler pages deploy dist --project-name=<プロジェクト名>
   ```

4. 確認

   - 表示される `https://<プロジェクト名>.pages.dev` を開く
   - `/`（入口）・各頁・存在しない URL（→404 頁）を確認
   - `curl -I https://<ドメイン>/` で CSP などのヘッダを確認

5. ドメイン確定後の置換

   ```
   sed -i 's/REPLACE-WITH-PROJECT.pages.dev/<プロジェクト名>.pages.dev/g' improve/sitemap.xml
   ```

   `robots.txt` に `Sitemap: https://<ドメイン>/sitemap.xml` を追記してコミットし、手順2・3 を再実行。

6. 更新時: テスト（`improve/` で `node tools/run-tests.js`、112/112 を確認）→ 手順2・3 を再実行。

## 独自ドメイン（後日・任意）

- Cloudflare Registrar で取得（原価・年間約 $10）または既存ドメインを移管
- Pages → Custom domains で追加（DNS は自動設定）
- 追加後、手順5の置換をやり直す

## 注意

- 本リポジトリと Cloudflare の Git 接続は行わない（98_Pass 保護のため）
- Void エディタは保守終了（2026-06-02 アーカイブ）。動作はするが脆弱性修正が入らず、常用は非推奨。成果物自体はプレーンな静的ファイル構成のため、他のエディタでそのまま開ける
- `.playwright-mcp/`・`dist/` は検証・ビルド成果物。コミット対象外
