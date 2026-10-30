---
title: 環境準備_MCPとスキル_claude-codemax_2026-10-30
type: report
phase: develop
status: 設定待ち（未接続）
project: 既存サイト改善
created: 2026-10-30
updated: 2026-10-30
---

# 環境準備（claude codemax 側の事前設定）

設定例_MCP_20261029.md（Kohden Code・opencode.json 向け）を Claude Code 向けに読み替えたもの。元の資料と同じく未接続で、接続と値の入力はユーザーの承認後に実施する。書式の変換部分（.mcp.json）と元資料からの転載部分を区別してある。

## 1. Playwright MCP（Microsoft 公式）— 今回の作業で接続する

実画面検証に使う。設定はプロジェクト直下の `.mcp.json` に書く（Claude Code 形式に変換した例）。

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless", "--isolated"]
    }
  }
}
```

- `--headless --isolated` を固定する（元資料どおり）。既定は headed・プロファイル永続化で、認証情報が保持されうるため
- 接続先を限定する場合は `--allowed-origins`／`--blocked-origins` を追加する。スクリーンショットの保存先は `--output-dir` で作業フォルダ配下に限定する
- ネイティブ Windows の端末では、npx 経由の stdio サーバーに `cmd /c` のラッパーが要る。その場合の書き方:

```json
{ "command": "cmd", "args": ["/c", "npx", "@playwright/mcp@latest", "--headless", "--isolated"] }
```

- 設定後、Claude Code の `/mcp` で接続状態を確認する

## 2. GitHub 公式 MCP — 今回の作業では接続しなくてよい

元資料での用途は技術スタック監視用（toolsets は dependabot・security_advisories・repos に絞る。read-only モードを推奨）。モック取り込みの作業に必須ではない。接続する場合はユーザーの承認を取り、次の形をとる（変換例）:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_MCP_TOKEN}" }
    }
  }
}
```

- トークンの値はユーザーが環境変数へ設定する。設定ファイル・文書・会話ログに値を書かない。`${…}` の部分はユーザー入力
- OAuth（scope repo・read:user。元資料どおり）を使う場合は、`/mcp` 画面からの接続承認で行う

## 3. Analytics MCP（GA4）— 対象外

未デプロイのサイトに計測対象が無く、導入判断はデプロイ承認（S-15）の後（元資料 §3 どおり）。今回の環境準備では設定しない。接続する段階になったら、読み取り専用（analytics.readonly）でのみ行う。設定変更は GA4 管理画面で運営者が行う。

## 4. スキル — 必読リストで代替する

こちら側では site-dev-context スキル（所在一覧・方針・失敗記録の入口）を使っている。claude codemax 側にこのスキルは無いため、代わりに 00_必読リスト.md を入口として使う。作業開始時と再開時に必読リストへ戻ることが、スキルの代わりの運用になる。

## 5. 共通規約から転記する部分

エージェント構成_20261029\共通規約.md のうち、この作業に効く部分だけを転記する。正本の所在表や媒介と報告の運用はこちら側の流儀のため転記しない。

- 承認境界（§2の要旨）: commit/push・デプロイ・実API呼び出し・依存の追加・秘密情報へのアクセスは明示承認が必要。過去の承認を無期限の許可として再利用しない。承認待ちでも、影響調査など独立して安全な作業は続けてよい
- 秘密値（§3）: トークン・キーの値を閲覧・出力・文書化・外部送信しない。環境変数名と用途のみ扱う
- 記録分離（§4）: テスト結果は PASS／FAIL／BLOCKED／NOT RUN を区別する。実施していない検証を実施済みと書かない。過去の記録・今回の実測・モック・実API・本番を混同しない
- 切断対策（§5の要旨）: 長い作業は区切りごとに保管庫へ保存し、タスクID・状態・変更ファイル・未完了・次の1手を残す。再開時は保管庫の記録と git diff を確認してから続ける。タイムアウト時は成功/失敗を推測せず、実際の保存・変更状態を確認する

## 6. トークン入力の区分（まとめ）

| 設定 | 値の入力 | 今回の要否 |
|---|---|---|
| Playwright MCP | 不要（フラグのみ） | 接続する |
| GitHub MCP | 必要（ユーザーが環境変数へ設定） | 不要。接続する場合は承認後 |
| GA4 MCP | 必要（サービスアカウント・ADC） | 対象外（S-15 の後） |
