---
name: task-account-router
description: タスク開始時・アカウントをまたぐ操作前に、業務用/生活用/サイト構築用のどのアカウントで作業すべきか判定し、実際の使用アカウントと照合する。git commit/push、gh コマンド、デプロイの前と、新規プロジェクト・新規問題対応の開始時に必ず使う。コミット・push・issue・project 操作・新しいリポジトリやプロジェクトを始めるとき、または「アカウント」「名義」「どのアカウント」に関する曖昧な指示が出たときに起動する。
---

# task-account-router（タスク別アカウントの区別）

## 対応表

| 区分 | GitHub アカウント | コミット名義（noreply） | 判断基準 |
|---|---|---|---|
| **業務用** | `nk-shino` | `nk-shino@users.noreply.github.com`（初回は `gh api user --jq '.id'` でIDを引き確認） | Work_Vault 配下の業務成果物・社内リポジトリ（task-board, work_vault 等） |
| **生活用** | `Liff22` | `09220719+Liff22@users.noreply.github.com` | 個人学習・生活記録（Zettelkasten 関連、C:\Projects\name-info-site, UT2Player 等） |
| **サイト構築用** | `liefiction`（ボカロPブログ）/ `kirinukifallstay`（アイデンリリィ・切り抜き） | それぞれの noreply | Web 公開物。C:\Projects\blog は liefiction、アイデンリリィ・切り抜き関連は kirinukifallstay |

**判定の軸は「材料の出どころ」**。成果物の種類で切らない。
出どころが Work_Vault（業務保管庫）なら業務用、個人のプロジェクトなら生活用、
公開サイトならサイト構築用。

**本PC（社用PC・PCS03112）の既定は業務用 `nk-shino`。**
gh にログイン済みのアカウントも nk-shino（`project` スコープ付き）。

## 確認手順（作業を始める前・コミット前・push前に実行）

```bash
git config user.name && git config user.email   # 期待名義と一致するか
gh auth status                                   # Active アカウントとスコープを確認
```

- 期待アカウントと一致しなければ**作業を停止してユーザーに報告する**（黙って続行しない）
- git の名義は config 未設定だと username/hostname から自動生成される
  （警告が出る。このPCでは `篠原 想詩 <ss80751@ad.nkc.co.jp>` になる）。
  **noreply で設定するまで実コミットに含めないこと**
- gh の `project` スコープが無いと看板操作（project item-edit 等）が全部失敗する

## 切替手順

- **git 名義**: `git config --local user.name "<名義>"` / `git config --local user.email "<noreply>"`
  （**`--global` を使わない**。global を書き換えると全リポジトリに名義が漏れる）
- **gh アカウント**: エージェントは `gh auth login` / `gh auth switch` を**実行しない**。
  認証は本人の行為。切替が必要ならユーザーに依頼する
  （複数区分を併用する場合は `GH_CONFIG_DIR` で設定ディレクトリを分ける方式がある。
  私用PC側の実測記録: `Work_Vault/06_Tools/KohdenCode_ワークスペース/20261013_issue-kanban-ops/実行ログ_20261014.md`）
- **project スコープ追加**: `gh auth refresh -s project`（本人実行）

## 発火条件

- コミット前 / push 前
- issue・project 操作前（gh コマンド実行前）
- 新規セッション開始時（このセッションはどの区分かを確認）
- 新規プロジェクト・新規問題対応の開始時

## 失敗パターンキー

`account.wrong-identity`（誤アカウントでのコミット）。発生時は
`.learnings/ERRORS.md` に記録する。
