---
name: vault-sync
description: Work_Vault 保管庫を GitHub nk-shino/work_vault へ同期する。保管庫の内容を GitHub に反映・push するとき、workvault-sync ミラーの状態を確認するとき、同期漏れ(新規ファイル未反映)を疑うとき、vault-sync.ps1 の実行結果を検証するときに使う。「同期して」「push して」「保管庫を GitHub に上げて」でも起動する。
---

# vault-sync

Work_Vault(`C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault`)を
GitHub `nk-shino/work_vault`(Private)へ同期する手順。
同期本体は `scripts/vault-sync.ps1`(タスクスケジューラ `Vault-sync-commit-push` が
ログオン5分後＋毎日17:30に自動実行)。手動実行・検証・欠落調査がこのスキルの主目的。

## 前提

- ミラー: `C:\Users\ss80751\kohden-code-workspace\workvault-sync\`
  - `.gitignore` により**全体が除外配下**。追跡済みファイルの変更のみ status に出る
- スクリプト: `scripts/vault-sync.ps1`(`-DryRun` で反映内容の確認のみ)
- リモート: `https://github.com/nk-shino/work_vault.git`(98_Pass を含むため**必ず Private 維持**)

## 手順

1. **DryRun で確認**: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/vault-sync.ps1 -DryRun`
   - 「差分 N 件 / 新規 M 件」の表示を読む。**新規 M 件が 0 で、実際には新規作成したものがある場合は欠落の疑い**
2. **実行**: `-DryRun` を外して実行。robocopy → 新規の `git add -f` → commit → push まで自動
3. **検証(省略しない)**:
   ```bash
   git ls-files workvault-sync | grep -c "新規作成したフォルダ名"   # 追跡に入ったか
   ```
   0 件なら同期漏れ。スクリプトの「新規 0 件」表示を信じない
4. **欠落時の救済**: ミラーから該当フォルダを直接 `git add -f` する。
   その前に**ネスト `.git` の有無を確認**し、あれば除去(下記の禁止参照)

## 除外されるもの(追跡に入らない)

| 対象 | 理由 |
| --- | --- |
| ネスト git リポジトリの作業ツリー(`PanaCIM_LNB`、`参照のみ・読み込み後に削除`) | gitlink になり push 不能。中身を上げる場合は `.git` を除去してから |
| `自動はんだ不良入力.zip` / `NPM-DGS.PDF` | 100MB 超で GitHub 拒否。履歴に再登録しない(push が止まる) |
| `__pycache__` / `*.pyc` / `.egg-info` / `.tmp.drive*` / `*.bkp` | 生成物 |
| `06_Tools/用語集アプリ/data/glossary.db` | 実行時生成の DB |
| `98_Pass` は追跡対象**内**(rules.md §2 の退避先)。リポジトリの Private 維持が前提 | |

## 禁止

- **force-push しない**。rebase 後の通常 push で解決する
- 100MB 超の2ファイルを履歴に再登録しない(push が拒否される)
- ネスト `.git` を含むフォルダを `add -f` しない(gitlink になる)
- リポジトリの public 化・スコープ拡大をしない(98_Pass を含む)

## トラブルシュート

| 症状 | 対処 |
| --- | --- |
| push が non-fast-forward で拒否 | `git fetch origin` → `git pull --rebase origin main` → `git push origin HEAD:main` |
| `index.lock` が残る | git プロセス終了を `tasklist //FI "IMAGENAME eq git.exe"` で確認してから lock を削除。プロセスを名前で kill しない |
| 「差分なし」なのに新規があるはず | `git ls-files` で突合。スクリプトの新規検出(`Test-Excluded`)に除外されないか確認 |
| gh CLI で clone/push できない | gh 未ログイン。`git` + git credential トークンで直接操作する |

## 根拠(2026-10-14 の失敗から)

`git add -u` の時代、新規フォルダ(PanaCIM_LNB 57件)が無音で欠落し、
「差分 N 件で同期完了」と報告されていた(ERR-20261014-001)。
現行版はミラー実ファイルと `git ls-files` の突合で新規を検出し `-f` で追加するが、
**実行後の検証(手順3)は省略しないこと**。
