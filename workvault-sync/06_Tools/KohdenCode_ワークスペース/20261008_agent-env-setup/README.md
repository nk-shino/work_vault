# 20261008 エージェント作業環境セットアップ

作業分析レポートを踏まえた環境構築・MCP導入・LLM検討・Skills導入の記録。

## 実施内容

### 1. 開発環境の確認(認証手続きはスキップ)

| 項目 | 状態 |
|---|---|
| Python | 3.14 / 3.13 / 3.12 登録済(py ランチャー) |
| Node.js | v24.19.0 |
| Git | 2.54.0 |
| PowerShell | 5.1 |

- Web系(Next.js/React/TypeScript)は既存プロジェクト側で管理。本ワークスペースでは触らない。
- Python案件は案件ごとに `.venv` を作成する方針(共通固定はしない)。

### 2. MCP 導入

`~/.config/kohden-code/opencode.json` に以下を追加:

- **firecrawl** (local, npx): Web/YouTube/X の情報取得(S12の要件に対応)
  - `FIRECRAWL_API_KEY` を環境変数で設定要(認証手続きは今回はスキップ)
- 既存: github / context7 / playwright / brave-search / figma は維持
- postgres は enabled: false のまま(必要時に有効化)

### 3. LLM の使い分け検討

| 用途 | ツール | 備考 |
|---|---|---|
| 対話・調査・資料整理 | KohdenGPT | 過去チャット検索との相性が良い |
| 実行エージェント | Kohden Code / Claude Code | ファイル操作・改修・検証の実行担当 |
| 大量処理・併用候補 | Codex | 必要時のみ。日常使用はまだ様子見 |
| 動画パイプライン | Claude Code Pro 前提 | 週2本想定。CC製品連携は今後設計 |

指針: 提案より実行を優先。「AIに任せる」のは分類・実装・記録まで。
レビュー・最終確認は人に残す(用語レビュー、動画完成確認)。

### 4. P0 Skills 導入

`~/.config/kohden-code/skills/` に以下を作成:

1. **evidence-and-change-review** — 根拠整理と変更完了判定
2. **legacy-vba-investigation** — 既存VBAの解析・改修・検証支援
3. **vault-change-and-report** — Obsidian保管庫整理と作業記録更新

P1(windowa-execution-preflight / inventory-package-maintenance)は次回以降に段階導入。

## 効果測定の開始値

導入前の実績を取るため、次の作業時に記録する:

- 調査開始〜実行可能な成果物までの時間
- 人の追加指示回数 / コード再修正回数
- 根拠不明の記述数 / 未検証完了表現の件数

### 5. 段階的実行(2026-10-08 追加)

| 段階 | 内容 | 状態 |
|---|---|---|
| 1 | 環境変数方針 | firecrawl はキーレスモードで scrape/search 可(レート制限あり)。キー取得時に `~/.config/kohden-code/.env` へ登録 |
| 2 | MCP動作確認 | keyless scrape 動作確認済。Kohden Code 再起動後に firecrawl MCP が有効化される |
| 3 | P1 Skills | windows-execution-preflight / inventory-package-maintenance を作成 |
| 4 | 効果測定 | effect-metrics.md に記録テンプレ作成。導入前の基準値取りを開始 |

### 6. MCP 一覧と使用方法

| 名称 | 種別 | コマンド/URL | 主用途 | 使用手順・注意 |
|---|---|---|---|---|
| github | Remote | `https://api.githubcopilot.com/mcp/` | Copilot 由来の補助(コード提案) | `GITHUB_PAT` で認証。Kohden Code 側で自動接続される。|
| context7 | Local | `npx -y @upstash/context7-mcp` | 最新ライブラリ公式ドキュメント取得 | 質問ごとに `context7_resolve-library-id` → `context7_query-docs` の順で呼び出す。APIキー不要。|
| playwright | Local | `npx -y @playwright/mcp@latest` | ブラウザ操作(Playwright) | `playwright_browser_*` 系ツールでナビゲーションや操作を行う。初回は依存を自動インストール。|
| brave-search | Local | `npx -y @brave/brave-search-mcp-server` | Brave Search API 経由のWeb検索 | `BRAVE_API_KEY` 必須。`firecrawl_search` 等とは別系統。|
| postgres | Local | `npx -y @modelcontextprotocol/server-postgres ...` | DB 接続 | `enabled:false`。使う際は接続文字列と資格情報を用意し `enabled:true` へ変更。|
| firecrawl | Local | `npx -y firecrawl-mcp` | Web/YouTube/X 取得、スクレイプ | 現在は keyless モード。スループットが必要なら `FIRECRAWL_API_KEY` を `.env` に登録。使用時は `firecrawl_search`, `firecrawl_scrape`, `firecrawl_parse` などを呼び出す。|
| figma | Local | `npx -y figma-developer-mcp --stdio` | Figma API 操作 | `FIGMA_API_KEY` 必須。デザイン取得やノード情報抽出に使用。|

共通の使い方: `~/.config/kohden-code/opencode.json` に登録済みなので、Kohden Code を再起動すると自動起動される。環境変数が必要な MCP( github / brave-search / firecrawl / figma / postgres )は `.env` または端末側環境変数に設定する。

## 未実施(意図的に保留)

- FIRECRAWL_API_KEY 等の認証・キー設定
- タスクスケジューラへの定期実行登録
- 棚卸セット ver2 の現行運用への配置
- 本番データに触れる操作全般
