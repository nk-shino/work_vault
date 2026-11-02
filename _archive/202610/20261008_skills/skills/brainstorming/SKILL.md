---
name: brainstorming
description: Socratic design refinement before writing code. Use when the user wants to discuss ideas, before starting a non-trivial feature ("〜を作りたい", "どうすればいい", "設計相談", "アイデア"), when requirements are vague, or when multiple implementation approaches exist. Do not use for small unambiguous tasks or simple questions with clear answers.
---

# ブレインストーミング (Socratic 設計相談)

## 目的

コードを書く前に、要件と設計の理解を揃える。曖昧なまま実装すると手戻りが最も高くつく。

## 進め方

### 1. 現状の理解

- 関連するコード・ドキュメントを先に調査する。ユーザーに聞く前に自分で調べられることは調べる
- 既存の設計パターン・制約を把握する

### 2. 一度に 1 つずつ質問する

- 要件の穴を特定し、**最も重要な問いから 1 つずつ**尋ねる。質問の投げっぱなしはしない
- 選択肢がある場合は、選択肢 + 推奨 + 理由を提示する(質問ツールや箇条書きを活用)
- 聞くべきこと: 目的・成功条件、スコープ(やらないこと)、制約(技術/運用/期限)、既存システムとの整合

### 3. 設計案の提示

- 2〜3 案を比較できる場合は比較する(観点: 影響範囲、保守性、工数、リスク)
- 提案にはトレードオフを明示する。「銀弾」は存在しない
- 小さく始められる分割点を探す

### 4. 合意の確認

- ユーザーの回答を受けて設計を更新し、最終案を短く要約して確認を取る
- 誤解したまま進まない。「認識合わせ: 〜という理解で合っていますか?」

## 終了条件

設計が固まったら:

- 小さいタスクなら、そのまま実装へ進む
- 中〜大規模なら `writing-plans` スキルで実装計画書の作成に進む
