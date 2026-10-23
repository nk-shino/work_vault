---
name: vault-commit-routing
description: 「コミット」「保管庫」「workvault」「Work_Vault」という言葉の意味でルーティングを行う。ユーザーが「コミットして」「コミット」とだけ言ったときは必ずこのスキルを使う。GitHub nk-shino/work_vault へのコミット・push と、保管庫(Work_Vault)へのデータ作成・更新・移動を区別して実行する。コミット・push・保管庫への保存・移動・同期のいずれかが絡む言葉が出たら起動する。
---

# vault-commit-routing

コミットと保管庫操作を、ユーザーの言葉で振り分ける。

## 振り分けルール

### 「コミット」と言われた場合 → GitHub へのコミット・push

**リポジトリ: `nk-shino/work_vault`**（`https://github.com/nk-shino/work_vault.git`）
**実体: `C:\Users\ss80751\kohden-code-workspace`**（workvault-sync ミラーを含む親リポジトリ）

1. `git status`, `git diff`, `git log --oneline -10` で現状確認
2. commit-message スキルの Conventional Commits 形式でメッセージを作る
3. 機微ファイル（98_Pass、password、.env、token 等を含むパス）をステージしない
4. コミット後、**push まで行う**: `git push origin HEAD:main`
   - 現在のブランチが feature/* の場合でも `HEAD:main` へ push する（既定の運用）
   - push 失敗時はエラーをそのまま報告し、勝手に force push しない

### 「保管庫」「Work_Vault」「workvault」と言われた場合 → Work_Vault へのデータ作成・更新・移動

**保管庫の実体: `C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault`**

この場合は **vault-change-and-report スキルを起動**し、rules.md の運用に沿って
データの作成・更新・移動を行う。このルートでは git コミットは行わない
（保管庫自体は git 管理外）。

### 両方に触れる指示の場合（例: 「保管庫に置いてコミットして」）

1. 先に vault-change-and-report で保管庫側の操作を行う
2. 次に vault-sync.ps1 でミラーへ反映し、コミット・push する:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\vault-sync.ps1
```

vault-sync.ps1 は保管庫 → workvault-sync ミラー → git commit → GitHub push まで一括で行う。
DryRun オプションで反映内容を先に確認できる。

## 判断に迷うとき

- 「コミット」の対象が Work_Vault 配下のファイルなら → vault-sync.ps1 経由
- コミット対象が workvault-sync 以外（scripts、LNB_Collector 等）なら → 直接 git commit + push
- どちらでも無い/曖昧なら、対象を質問してから動く

## 注意

- **98_Pass 配下の認証情報は絶対にコミットに含めない**（リポジトリは Private だが Vault の方針として禁止）
- **100MB 超の2ファイル**（自動はんだ不良入力.zip、NPM-DGS.PDF）は .gitignore で除外済み。履歴に再登録しない
- workvault-sync ミラーは robocopy /MIR で完全同期される。ミラー側で直接編集しない（保管庫側が正本）
- コミット時は commit-message スキルの形式に従う
