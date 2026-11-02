---
name: writing-plans
description: Write detailed implementation plans as markdown documents. Use after design is agreed (brainstorming skill) or when the user asks for "計画", "プラン", "実装計画", "見積もり", or when a task is large enough to span multiple files/sessions. Also use when the user says "計画を立てて" before implementation. Do not use for small single-file tasks.
---

# 実装計画の作成 (Writing Plans)

## 目的

実装を正確に実行できる状態にする。計画は「後で読む人(またはエージェント)が、文脈なしで実装できる」精度で書く。

## 計画書の配置

- このワークスペースの慣習に従い、`.kohden-code/plans/` 配下に `YYYYMMDD_<topic>.md` として保存する(既存の plans フォルダ運用があればそれに従う)

## 計画書の構造

```markdown
# <機能名> 実装計画

## 目的
なぜこれを作るか(1〜3 行)

## 現状と関連箇所
- 既存コードの該当箇所(ファイルパス付き)
- 関連する既存パターン・制約

## 設計
採用するアプローチと、棄却した案とその理由

## タスク一覧
実行順に番号を振る。各タスクは:
- 「〜を実装」ではなく「<ファイル> に <何をする>」と具体的に
- 検証方法を付ける(実行するコマンド、期待結果)
- 1 タスク = レビュー可能な単位(目安: 数十〜数百行の変更)

## リスクと未決事項
- 懸念点と緩和策
- 後で決めること
```

## タスク分割の基準

- 各タスクは独立して検証可能にする(テストを書く、動かして確認する 等)
- 依存関係があれば明示する
- ファイル作成・スキーマ変更・移行など、取り返しがつきにくい作業は早期に、かつ明示的に

## 作成後

- ユーザーに計画を提示して承認を取る
- 承認後に実装を開始する。実装中に計画と乖離が生じたら、計画書を更新してから進む
