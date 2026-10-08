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

## 未実施(意図的に保留)

- FIRECRAWL_API_KEY 等の認証・キー設定
- タスクスケジューラへの定期実行登録
- 棚卸セット ver2 の現行運用への配置
- 本番データに触れる操作全般
