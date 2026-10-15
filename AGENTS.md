# Default workspace
This is the default workspace. The rules below are a default starting point; adapt them to how the user actually works.

- When starting a new topic, create a `YYYYMMDD_<topic>/` folder and work inside it
- Put generated files in the matching topic folder rather than directly at the root of this folder
- When continuing an existing topic, work inside the matching `YYYYMMDD_*` folder
- This folder is a git repository: commit your changes at each natural stopping point of the work without waiting for the user to ask. If git refuses to commit because `user.name`/`user.email` are unset, ask the user for their name and their company email address (`@mbN.nkc.co.jp`, where N is a single digit such as 1–5), then set them with `git config --global`
- Maintain `.gitignore` appropriately for what the work creates: never commit installed dependencies or virtual environments such as `node_modules/` or `.venv/`
- Work that belongs in its own repository fits better outside this workspace: suggest creating a separate folder elsewhere and opening it as a separate project in Kohden Code
- Kohden Code が実行した内容は、日付ごとに実行ログとして個別に記録する。ログは `YYYYMMDD_<topic>/実行ログ_YYYYMMDD.md` に置き、「ユーザーの指示1件＝エントリ1件」として「指示/実施/成果物/状態(コミット番号含む)」を記す。既存の日のログがあればそこに追記する

## Work_Vault リモートトラッキング運用

- 保管庫 `C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault` は `workvault-sync/` ミラー経由で GitHub `nk-shino/work_vault`（Private）に追跡される
- 同期は `scripts/vault-sync.ps1`（タスクスケジューラ `Vault-sync-commit-push` がログオン5分後＋毎日17:30に自動実行）。手動実行は `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\vault-sync.ps1 [-DryRun]`
- Vault 側の変更を AI が検知したら同期を待たず手動同期してよい（`vault-sync.ps1` 実行→差分コミット→push まで自動）。手順・検証・除外条件・トラブルシュートは **`vault-sync` スキル**（`~/.config/kohden-code/skills/vault-sync/SKILL.md`）に従う。同期後は `git ls-files` で新規が追跡に入ったか必ず検証する（2026-10-14、新規フォルダが無音で欠落した失敗 ERR-20261014-001 の再発防止）
- GitHub issue は `scripts/github-issue.py`（起票）と `scripts/github-issue-close.py`（コメント付きクローズ）で操作する。gh CLI は未ログインだが git credential のトークンで API を叩ける。使い方: `python scripts/github-issue.py nk-shino/work_vault "<title>" <body.md>`
- **issue 起票・看板(Project V2)への追加・Status 移動(Todo/In Progress/Done)・タスク完了時の Done 移動は `github-issue-board` スキル**（`~/.config/kohden-code/skills/github-issue-board/SKILL.md`）の統一手順で行う。全セッション共通。完了時は forced-logging による記録検証 → issue へ完了コメント → Done 移動の順。close はユーザーの確認後
- 100MB 超の2ファイル（`自動はんだ不良入力.zip`・`NPM-DGS.PDF`）は `.gitignore` 済み。履歴に再登録しないこと（push が拒否される）
- `98_Pass`（認証情報）を含むためリポジトリは必ず Private 維持。public 化やスコープ拡大をしてはいけない

## 文書作成の言い回し(管理文書・報告書)

- 管理文書・報告書・原稿を作成するとき、日常会話寄りの語や比喩表現を使わない。ビジネス標準の言い回しに置き換える
- 例: 律速→ネック、動き出す→着手できる、飛ばす→省略する、打ち切る→切り上げる、手がかり→情報、勝手に→許可なく、そもそも→開始時点から、直す→修正する、なじむ→適合する
- 比喩(「異常を正常と読む文書」「道具です」等)は、意味が直接伝わる表現(「異常を正常と判断してしまう恐れ」「準備です」)に言い換える
- AI生成文と判断されやすい記述を避ける(実測に基づく主指標): ①文長のリズムが均質(長短の混在がない) ②「〜ではなく〜です」型の対比の反復 ③体言止めの多用。該当したら文を組み替える
- 詳細な点検手順と置換表は `01_Templates/プロンプト/DeAIプロンプト.md`(保管庫)を参照。作成時に自己点検し、置換した語が残っていないか確認してから提出する

## アカウント照合と記録検証（2026-10-14 導入・issue看板運用 04）

- **アカウント照合は `task-account-router` スキル**（`~/.config/kohden-code/skills/task-account-router/SKILL.md`）で行う。コミット・push・issue・project 操作の前に、git 名義と gh ログインアカウント（本PCの既定 = 業務用 `nk-shino`）が期待値と一致するか確認する。一致しなければ作業を停止してユーザーに報告する（黙って続行しない）
- **記録検証は `forced-logging` スキル**（`~/.config/kohden-code/skills/forced-logging/SKILL.md`）で行う。完了報告の前に、実行ログ（`YYYYMMDD_<topic>/実行ログ_YYYYMMDD.md`・指示1件=エントリ1件）が実際に書かれたかを確認する。ログ未記載のまま完了報告・コミットをしない
- 失敗は `.learnings/ERRORS.md` に Pattern-Key 付きで記録する（Recurrence-Count>=2・resolved・別セッション発生の3条件を満たしたらスキル化を検討）
- 上記の括書きの理由: このPCの git config は未設定で、名義が username/hostname から自動生成される（`篠原 想詩 <ss80751@ad.nkc.co.jp>`）。**noreply 名義での `--local` 設定が確定するまで、この節の既定に従う**

## About this file

This file holds general rules for this workspace, not notes about the current task. When these rules do not fit how the user works, or an agent made a mistake or worked inefficiently, suggest updating them so things go better next time, and edit the file once the user agrees.
