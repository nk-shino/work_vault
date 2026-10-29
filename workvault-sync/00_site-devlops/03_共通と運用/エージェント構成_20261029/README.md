---
title: エージェント構成案 README（サイト運営開発サイクル）
type: report
phase: develop
status: 提案（未配備）
project: 既存サイト改善
updated: 2026-10-29
---

# エージェント構成案 README

ノート `00_site-devlops/2026-10-29.md` の再開事項（§9）1〜7に応じて作成した構成案。提案であり、実際のエージェントフォルダへの配備・読み込み検証は未実施（§9-5 の区別どおり）。

## 1. 構成（進行管理＋4専門役）

| 役割 | ファイル | 権限の要点 |
| --- | --- | --- |
| 進行管理（セッション本体） | 進行管理.md | 割当・並行上限2体・承認台帳・再開メモ |
| 調査・要件判断 | agent/site-research.md | edit: deny／web調査 可 |
| 情報整理・整合性確認 | agent/site-curator.md | edit: 可（文書・データ） |
| 設計・UI/UX | agent/site-design.md | edit: 可（動画・URL・アニメーションの設計前提を含む） |
| 実装・デバッグ | agent/site-implement.md | edit: 可（fixture・基準値を維持） |
| 独立レビュー・検証 | agent/site-review.md | edit: deny／公開前の権利・秘密・混入チェックを含む |

## 2. 役割数の判断根拠（2026-10-29 の事例調査より）

- Anthropic 公式 agent teams: 「まず3〜5 teammates」「集中した3体は散らばった5体に勝る」。同一ファイル編集は並列にしない
- Google Research（2026-01・arXiv:2512.08296）: 構造なしの独立並列は誤りを17.2倍に増幅、オーケストレータ付きは4.4倍に抑制
- 個人報告（2026-08〜09）: 並列は2〜3体が実用上限。レビューと仲裁が労働の約半分になる例あり
- 結論: 提示済み4役（§5）を基本に、設計と実装を分担（逐次実行）・独立レビューを分離。専門役ファイルは5本だが、**同時並行で動かすのは2体まで**。安全・権利は進行管理の承認台帳＋レビュー担当の公開前チェックに組み込み、専任役を置かない
- 対象が BMAD Method（8専門役）級の大規模開発なら専門役の追加を検討する。ソロの静的サイト運用では、レビューと仲裁のコストが専門性の利得を上回る

## 3. 配備手順（未実施・実施時にこのとおり行う）

1. 配置先を選ぶ。プロジェクト単位ならワークスペース `.kohden-code/agent/<name>.md`、全プロジェクト共通なら `~/.config/kohden-code/agent/<name>.md`（Kohden Code 公式仕様: frontmatter は description／mode／model／permission など。unknown フィールドは options へ退避される）
2. agent/ 配下の5ファイルを上記フォルダへコピーする（ファイル名を変えない）
3. 進行管理.md の内容は AGENTS.md への追記か、セッション開始プロンプトとして使う（サブエージェントファイルにはしない）
4. Kohden Code を再起動する（設定は起動時に読み込まれ、実行中のセッションには反映されない）
5. 起動後、各エージェントが起動できること・権限（site-review の edit: deny など）が効いていることを検証する
6. 検証結果を保管庫の実行ログと検証記録.md に追記する

## 4. 利用するスキル・ツール（2026-10-29 時点で導入済みを確認）

| スキル | 利用する役割 | 用途 |
| --- | --- | --- |
| site-dev-context | 全役 | 所在・失敗記録・方針・未決の読み込み |
| ui-revamp | 設計 | 改修手順（調査→範囲合意→実装→検証→記録） |
| frontend-design | 設計 | 視覚設計の原則（token・type・motion の意図的な選択） |
| verification-before-completion / forced-logging | 実装・進行管理 | 完了報告前の記録確認 |
| anthropic-skills（docx/xlsx/pptx/pdf） | 情報整理・進行管理 | 報告書・台帳を Office 形式で出すとき。使用前に最新版を取得 |
| vault-change-and-report / vault-sync | 進行管理 | 保管庫への登録と GitHub 同期（同期は承認後に実行） |

## 5. 今回作成したものと検証

- 検証結果は `検証記録.md`。既知の未確認事項もそこに列挙する
- 動画・URL・アニメーションの担当範囲は site-design（設計前提）・site-review（検証観点）・進行管理（承認区分）に組み込み済み
