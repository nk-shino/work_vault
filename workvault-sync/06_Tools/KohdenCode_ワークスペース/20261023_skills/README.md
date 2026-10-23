---
title: Kohden Code スキル一覧(2026-10-23 スナップショット)
type: note
phase: operate
status: active
project: KohdenCode
updated: 2026-10-23
tags:
  - kohden-code
  - スキル
  - 一覧
related: "[[20261008_skills]]"
---

# Kohden Code スキル一覧(2026-10-23 スナップショット)

Kohden Code に保存されている全スキルを保管庫へ取り込んだ。**正本は設定フォルダ**(`~/.config/kohden-code/skills/` と `~/.cache/kohden-code/builtin-skills/`)で、本フォルダは 2026-10-23 時点の写し。スキルを編集した場合は本書の該当 SKILL.md を差し替えるか、次のスナップショットを作る。

## 取り込み範囲

| 区分 | 件数 | 原典 | 本フォルダ内の位置 |
|---|---|---|---|
| ユーザースキル | 34(うち docx/pdf/pptx/xlsx は anthropic-skills 配下) | `~/.config/kohden-code/skills/` | `skills/<スキル名>/SKILL.md` |
| 同梱スキル(builtin) | 4 | `~/.cache/kohden-code/builtin-skills/1.18.33-nk.9/` | `builtin_1.18.33-nk.9/<スキル名>/SKILL.md` |

前回スナップショット [[20261008_skills]] は 7 種だったので、約2週間で +31 種(builtin 4 種を含む)に増えた。増分の中心は保管庫・コミット運用系と文章品質系。20261008_skills は当時の記録としてそのまま残す。builtin は Kohden Code の更新で新バージョン(`1.18.33-nk.X`)が配布されるため、版はフォルダ名で区別する。

## 一覧

### 保管庫・GitHub 運用

| スキル | 概要 |
|---|---|
| vault-change-and-report | 保管庫の整理と作業記録・日報の更新。成果物は作成時点で正しい置き場へ入れる |
| vault-commit-routing | 「コミット/保管庫」という言葉で GitHub 同期と保管庫操作を振り分ける |
| vault-sync | Work_Vault を GitHub nk-shino/work_vault へ同期。ミラー状態の確認・欠落調査も管轄 |
| commit-message | Conventional Commits 形式のコミットメッセージと PR 説明の作成 |
| task-account-router | 業務用/生活用/サイト構築用のどのアカウントで作業すべきかを判定 |
| github-issue-board | issue 起票・Project V2 看板への追加・Status 列の移動を統一手順で行う |
| worktrees | git worktree による分離作業レーンの管理 |

### 文章品質・記録の信頼性

| スキル | 概要 |
|---|---|
| deai-writing | AI 生成と判断されやすい記述を排除した文章作成・多パス点検 |
| citation-verification | 出典付き生成と出典の原票照合。社内 RAG のセットアップ要件も管轄 |
| authority-claim-verification | 「会議で決定」等の権威づけ主張を検証し、事実/提案/未決を区別させる |
| evidence-and-change-review | 事実・推定・提案・決定・未確認を区別し、変更完了判定まで行う |
| forced-logging | 完了報告の前に、実行ログと学習記録が実際に書かれたかを検証する |
| verification-before-completion | 完了宣言前の検証チェックリスト。動作確認の省略を防ぐ |

### 開発プロセス・設計

| スキル | 概要 |
|---|---|
| brainstorming | 実装前の設計対話(Socratic 方式)。要件が曖昧なときに使う |
| writing-plans | 実装計画を markdown 文書として書き起こす |
| test-driven-development | RED-GREEN-REFACTOR の TDD サイクル |
| systematic-debugging | 4 フェーズの根本原因デバッグ。修正前に使う |
| simplify | 動作を変えずにコードを読みやすく簡潔化する |
| security-review | OWASP Top 10 に基づくセキュリティレビュー |
| verification-planning | 非自明な変更に対する検証計画の立案 |
| deepwork | 大規模・高リスク・多フェーズの作業向けの高コスト orchestrator ワークフロー |
| codemap | 未知リポジトリの階層コードマップ生成。高コストなので明示指定時のみ |
| clonedeps | 依存ライブラリのソースをローカルへ clone して内部を調査可能にする |
| reflect | 過去の作業から繰り返しパターンを見つけ、再利用可能なスキル/設定を提案する |
| ui-revamp | 公式デザインシステム等の一次資料に基づいて既存アプリの UI/UX を改修する手順 |

### ドキュメント生成(anthropic-skills 配下)

| スキル | 概要 |
|---|---|
| docx | Word 文書(.docx/.dotx)の作成・読み取り・編集 |
| pdf | PDF の読み取り・結合・分割・OCR・フォーム入力など |
| pptx | PowerPoint(.pptx/.potx)の作成・読み取り・編集 |
| xlsx | 表計算(.xlsx/.xlsm/.csv 等)の作成・編集・変換 |

### 業務固有

| スキル | 概要 |
|---|---|
| inventory-package-maintenance | 棚卸セットの整合性点検と次版作成。恒久手順と回次固有データを分ける |
| legacy-vba-investigation | 既存 VBA(Excel マクロ)の解析・改修・検証。外部アプリ操作と Excel 内部処理を分離 |
| monthly-work-report | 月次業務報告(読み上げ原稿+報告スライド)の作成手順。2026-10-23 新規作成 |
| windows-execution-preflight | Windows 実行前の確認と障害切り分け。0 件を成功扱いにしない |

### 同梱スキル(builtin 1.18.33-nk.9)

| スキル | 概要 |
|---|---|
| anthropic-skills | 上記ドキュメント系 4 スキルを GitHub から取得して配置する取得用スキル |
| customize-kohden-code | Kohden Code 自身の設定(agents/skills/MCP/権限)を編集するときに使う |
| m365-read | Microsoft Graph API 経由で自分のメール/Teams/SharePoint/OneDrive を読み取り(読み取り専用) |
| skill-creator | スキルの新規作成・改修・評価・ベンチマーク |
