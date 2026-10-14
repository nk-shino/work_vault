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
- 100MB 超の2ファイル（`自動はんだ不良入力.zip`・`NPM-DGS.PDF`）は `.gitignore` 済み。履歴に再登録しないこと（push が拒否される）
- `98_Pass`（認証情報）を含むためリポジトリは必ず Private 維持。public 化やスコープ拡大をしてはいけない

## About this file

This file holds general rules for this workspace, not notes about the current task. When these rules do not fit how the user works, or an agent made a mistake or worked inefficiently, suggest updating them so things go better next time, and edit the file once the user agrees.
