---
name: systematic-debugging
description: Four-phase root-cause debugging process. Use when encountering any bug, test failure, error message, or unexpected behavior, BEFORE proposing fixes. Trigger on phrases like "直らない", "エラーが出る", "バグ", "なぜか動かない", "テストが落ちる", or whenever the user reports something behaving incorrectly. Do not use for feature requests or greenfield implementation.
---

# 体系的デバッグ (Systematic Debugging)

## 原則

バグの根本原因を理解する前に修正コードを書くことは、症状の隠蔽であり、再発や新たなバグを生む。**修正は仮説が検証された後にのみ行う。**

## Phase 1: 再現と観察

- エラーを確実に再現する手順を特定する(再現できないものはデバッグできない)
- エラーメッセージ・スタックトレース・ログを**読み切る**。推測で飛ばさない
- 最近の変更(`git diff`, `git log`)を確認する。「以前は動いていた」場合は、その差分が最有力の手がかり
- 期待する動作と実際の動作を 1 文で言語化する

## Phase 2: 仮説の列挙

- 観察した事実から、あり得る原因を 2〜3 個具体的に書き出す
- 各仮説は「検証可能な形」で述べる。「たぶんキャッシュでは?」ではなく「`foo/cache.ts` の TTL が切れて stale データを返しているのでは?」
- 深さ優先で 1 つに固執しない。幅優先で全体像をつかむ

## Phase 3: 仮説の検証

- 最も簡単に確認できる仮説から検証する
- 検証手段: ログ出力の追加、デバッガ、最小再現コードの作成、値の中身を直接確認
- **コードを一切変更せずに観察だけで検証する**ことを最優先する
- 仮説が否定されたら次へ。否定された仮説の記録を残す(同じ道を二度通らない)

## Phase 4: 修正と確認

- 根本原因に対して修正する。症状に対する対症療法(例外を握りつぶす、条件分岐で回避する等)は根本原因が既知で説明できない場合のみ、かつ一時的な措置として明示する
- 修正後、Phase 1 の再現手順で必ず確認する
- 同じ原因が他の場所にも存在しないか確認する
- 回帰テストを追加できる場合は追加する

## よくある落とし穴

- エラーメッセージを最後まで読まずに検索する
- 「直したはず」で再現確認を省略する
- 修正が効かないのに修正を重ねる(=仮説が間違っているサイン。Phase 2 に戻る)
- ランダムな変更を試す(「いじり」はデバッグではない)
