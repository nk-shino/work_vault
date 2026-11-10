---
name: github-issue-board
description: GitHub issue 起票・コメント・マイルストーン/ラベル/Project V2 フィールド（期限・優先度）の設定・看板(Project V2)への追加・Status列(Todo/In Progress/Done)の移動・タスク完了時のDone移動を統一手順で行う。issue を作るとき、期限や優先度を割り当てるとき、マイルストーンで計画を管理するとき、タスクの進行状況を看板に反映するとき、タスク完了を報告するときに使う。「issue 起票して」「看板に載せて」「Done に移して」「タスク終わった」「期限を設定して」「マイルストーンを作って」でも起動する。
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

## 手順5: コメントのみ追加(期限割当・進捗報告)

close を伴わないコメントは REST で行う。**投稿前に issue タイトルを照合する**
(番号の取り違え・別リポジトリへの誤投稿を防ぐ。実測で #60 のキーワード不一致を検出できた)。

```python
# 1) 照合: GET /repos/{repo}/issues/{n} → title に期待キーワードが含まれるか
# 2) 投稿: POST /repos/{repo}/issues/{n}/comments  {"body": "..."}
# 認証: git credential fill (protocol=https host=github.com) の password= を token として使用
```

- 期限割当コメントの定型: `【期限割当 YYYY-MM-DD】` で始め、**根拠**・**完了条件**・
  依存や制約(立入不可日・休暇等)を書く
- issue タイトルに既存の目標(例「12月頃」)がある場合は、前倒しするなら
  その旨と調整可をコメントに明記する(既存目標を黙って上書きしない)
- 既存本文を変更する場合は **GET → 追記 → PATCH**。マーカー文字列
  (例 `2026-11-09 PM再定義`)を本文に含めて冪等化し、再実行で二重追記しない

## 手順6: マイルストーン・ラベル・カスタムフィールド(PM運用)

計画の再定義(期限・優先度・コストの可視化)は次の組み合わせで行う。
すべて nk-shino/task-board で 2026-11-09 に実測済み。

1. **マイルストーン**(REST): `POST /repos/{repo}/milestones`
   `{"title":"M1: 11-14 鹿島受け入れ確認","due_on":"2026-11-14T23:59:59Z","state":"open"}`
   → issue へは `PATCH /repos/{repo}/issues/{n}` に `{"milestone": <number>}`
2. **ラベル**(REST): `POST /repos/{repo}/labels` `{"name","color","description"}`
   → issue へは `POST /repos/{repo}/issues/{n}/labels` `{"labels":["priority/urgent", ...]}`
   推奨体系: `priority/urgent|high|normal`(赤・橙・緑)・`cost/high|low`・`theme/*`
3. **カスタムフィールド**(GraphQL): Project に無ければ作成する
   ```graphql
   mutation($p:ID!){ createProjectV2Field(input:{projectId:$p, dataType:DATE, name:"期限"}){
     projectV2Field{ ... on ProjectV2Field { id name } } } }
   mutation($p:ID!){ createProjectV2Field(input:{projectId:$p, dataType:SINGLE_SELECT, name:"優先度",
     singleSelectOptions:[{name:"緊急",color:RED},{name:"高",color:ORANGE},{name:"中",color:GRAY}]}){
     projectV2Field{ ... on ProjectV2SingleSelectField { id name options{ id name } } } } }
   ```
4. **アイテムへの値設定**: アイテムIDは
   `project(id:){ items(first:100){ nodes{ id content{ ... on Issue { number } } } } }`
   で issue 番号から引く(未掲載なら `addProjectV2ItemById`)。
   ```graphql
   # 期限: 変数型は Date!  (String! だと variableMismatch)
   mutation($p:ID!,$i:ID!,$f:ID!,$v:Date!){ updateProjectV2ItemFieldValue(input:{
     projectId:$p, itemId:$i, fieldId:$f, value:{date:$v}}){ projectV2Item{ id } } }
   # 優先度: 変数型は String!  (ID! だと variableMismatch)
   mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){ updateProjectV2ItemFieldValue(input:{
     projectId:$p, itemId:$i, fieldId:$f, value:{singleSelectOptionId:$o}}){ projectV2Item{ id } } }
   ```

### GraphQL 型の落とし穴(2026-11-09 実測・4回失敗して確定)

| 症状 | 正解 |
|---|---|
| `Type mismatch on variable $v and argument date (String! / Date)` | 変数型を `Date!` にする |
| `Type mismatch on variable $o and argument singleSelectOptionId (ID! / String)` | 変数型を `String!` にする |
| `No such type ProjectV2ItemFieldDate` | アイテム値の型名は `ProjectV2ItemFieldDateValue` / `ProjectV2ItemFieldSingleSelectValue` |
| `No such type ProjectV2CommonField` | `field` は `... on ProjectV2Field { name }` と `... on ProjectV2SingleSelectField { name }` を併記 |
| `Field 'items' doesn't exist on ProjectV2FieldConfigurationConnection` | `items` は `fields` の兄弟(ProjectV2 直下)。`fields{ nodes{...} }` を閉じてから書く |
| `linkProjectV2ToRepository` で `projectV2` を選択して selectionMismatch | payload は `repository{...}` と `clientMutationId` のみ選択可 |

検証は書き込み後に読み取りで行う(issue 側: milestone・labels・本文マーカー /
Project 側: フィールド定義と各アイテムの `期限`・`優先度`・`Status` の値)。

## ルール

- issue 無しで着手しない。看板に無い作業は先に起票する
- 1 issue = 1完了条件のまとまり。複数の成果物は関連 issue に分ける
- API 失敗時は HTTP ステータスと本文をそのまま報告する
  (黙ってリトライを続けない。3回失敗したら停止)
- `.learnings/ERRORS.md` に `issue.api-<種類>` の Pattern-Key で失敗を記録する
