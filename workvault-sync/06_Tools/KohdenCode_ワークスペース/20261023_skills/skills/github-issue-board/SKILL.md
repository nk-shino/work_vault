---
name: github-issue-board
description: GitHub issue 起票・看板(Project V2)への追加・Status列(Todo/In Progress/Done)の移動・タスク完了時のDone移動を統一手順で行う。issue を作るとき、タスクの進行状況を看板に反映するとき、タスク完了を報告するときに使う。「issue 起票して」「看板に載せて」「Done に移して」「タスク終わった」でも起動する。
---

# github-issue-board(issue起票と看板運用)

## 適用範囲

全セッション共通。GitHub への issue 操作・看板操作は必ずこの手順を使う。

## 前提(このPCの環境)

- gh CLI は未ログイン。**git credential のトークン(repo + project スコープ付き)で
  GitHub REST/GraphQL API を直接叩く**
- 標準リポジトリ: `nk-shino/work_vault`(Private)
- 補助スクリプト(ワークスペース): `scripts/github-issue.py`(起票)、
  `scripts/github-issue-close.py`(コメント付きクローズ)

## 対応アカウントの確認(コミット・push・起票の前に1回)

`task-account-router` スキルの照合に従う。GitHub 名義は `nk-shino`(業務用)。
照合に失敗したら作業を停止してユーザーに報告する。

## 手順1: issue の起票

1. 本文を一時ファイルに書く(題と本文は日本語。受け入れ基準を含める):
   ```markdown
   ## ゴール
   (何が分かれば/何ができれば完了か)
   ## 受け入れ基準
   - (確認可能な条件)
   ## 既知情報
   - [事実|推定|未確認] (出典つきで)
   ```
2. 起票は git credential トークンで REST API を叩く
   (スクリプトがある場合はそれを使う):
   ```bash
   python scripts/github-issue.py nk-shino/work_vault "<title>" body.md
   ```
   スクリプト無し環境では同等の urllib/requests 呼び出しをその場で書く
   (`POST /repos/{repo}/issues`、Authorization: token)。
3. 出力された issue 番号と URL をユーザーに報告する。

## 手順2: 看板(Project V2)への追加と Status 設定

看板は GraphQL API で操作する(REST の projects エンドポイントは obsolete)。

1. 起票した issue を看板に追加:
   ```graphql
   mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p, contentId:$c}){ item{ id } } }
   ```
   `contentId` は issue の GraphQL node ID
   (`GET /repos/{repo}/issues/{n}` の `node_id`)。`projectId` は下の表。
2. 追加直後は Status が空欄。**Todo を明示設定する**:
   ```graphql
   mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){
     updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f,
       value:{singleSelectOptionId:$o}}){ projectV2Item{ id } } }
   ```

### 看板とオプションID(2026-10-13 実測・nk-shino 名義)

| Project | 番号 | projectId | Status fieldId | optionId |
|---|---|---|---|---|
| task-board 看板 | 4 | PVT_kwHOFGAcOc4Bm-ma | PVTSSF_lAHOFGAcOc4Bm-mazhllT6o | 下記 |
| 業務タスク管理 | 3 | PVT_kwHOFGAcOc4Bm-Nc | (同方式で取得) | 同上 |

Status の optionId(共通):
- Todo: `f75ad846` / In Progress: `47fc9ee4` / Done: `98236657`

**fieldId は projectId ごとに別物なので、必ず上の query で取得してから使う**
(2つの ID を混同すると NOT_FOUND になる。実測で確認済み)。

**どの看板を使うか迷ったらユーザーに1回だけ質問し、以降そのセッションは固定。**
ID が 404/不正エラーになる場合は `gh auth login` が済んでいない可能性が高いので
ユーザーに案内して停止する。

## 手順3: 進行状況の移動

- 着手時: In Progress(47fc9ee4)へ移動し、issue に計画をコメント
- 質問・承認待ち: issue コメントに「待っているもの」を書いて Status は
  In Progress のまま(勝手に Done にしない)
- 修正指摘への対応: 対応してコメントし、In Progress に戻す

## 手順4: タスク完了時(必須)

1. **Done へ移動する前に**: 実行ログ・成果物が実際に書かれたことを
   `forced-logging` スキルで検証する。未記載なら先に書く
2. issue に完了コメントを書く(何を・結果・確認方法・コミット番号)
3. Status を Done(`98236657`)へ移動する
4. issue の close はユーザーの確認が済んでから
   (`python scripts/github-issue-close.py nk-shino/work_vault <番号> comment.md`。
   勝手に close しない。ユーザーが「閉じて」と言った時だけ)

## 実測済みの動作(2026-10-13、issue #5 で全手順を検証済み)

- 起票: REST `POST /repos/nk-shino/work_vault/issues` → OK
- 看板追加: GraphQL `addProjectV2ItemById` → OK(追加直後は Status 空欄)
- Status 設定: `updateProjectV2ItemFieldValue` + fieldId + optionId →
  Todo→Done の移動と再取得確認まで成功
- close: REST `PATCH` → OK
- 注意: GraphQL mutation の戻り値で `field { name }` を選択すると
  selectionMismatch になる。検証は item 取り直しで行う

## ルール

- issue 無しで着手しない。看板に無い作業は先に起票する
- 1 issue = 1完了条件のまとまり。複数の成果物は関連 issue に分ける
- API 失敗時は HTTP ステータスと本文をそのまま報告する
  (黙ってリトライを続けない。3回失敗したら停止)
- `.learnings/ERRORS.md` に `issue.api-<種類>` の Pattern-Key で失敗を記録する
