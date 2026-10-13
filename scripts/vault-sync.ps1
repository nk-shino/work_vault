# Work_Vault 同期スクリプト
# Vault 実体 -> workspace/workvault-sync ミラー -> git commit -> GitHub push
#
# 使い方:
#   powershell -NoProfile -ExecutionPolicy Bypass -File vault-sync.ps1            # 同期+コミット+push
#   powershell -NoProfile -ExecutionPolicy Bypass -File vault-sync.ps1 -DryRun    # 反映内容の確認のみ
#
# 配置場所: C:\Users\ss80751\kohden-code-workspace\scripts\vault-sync.ps1
#
# 構成: ミラーは親リポジトリ(kohden-code-workspace)の配下で追跡する。
#       workvault-sync/ 自体に .git は作らない(robocopy /MIR が .git を消すため)。
#       リモート: https://github.com/nk-shino/work_vault.git (Private 運用・98_Pass を含む)
#       GitHub 100MB 制限のため、自動はんだ不良入力.zip と NPM-DGS.PDF は .gitignore で除外。
#
# 使い方(親リポジトリ側から):
#   git -C C:\Users\ss80751\kohden-code-workspace push origin HEAD:main

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$VaultPath  = "C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault"
$MirrorPath = "C:\Users\ss80751\kohden-code-workspace\workvault-sync"
$RepoPath   = "C:\Users\ss80751\kohden-code-workspace"

if (-not (Test-Path -LiteralPath $VaultPath))  { throw "Vault が見つからない: $VaultPath" }
if (-not (Test-Path -LiteralPath $MirrorPath)) { throw "ミラーが無い: $MirrorPath" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) { throw "親リポジトリの .git が無い: $RepoPath" }

# --- 1. robocopy で反映 (削除も同期) ---
# /MIR 完全ミラー  /XD 同期対象外  /R:1 /W:1 再試行1回  /NFL /NDL ログ簡略  /NP 進捗非表示
# 注意: .git はミラー側に作らない。追跡は親リポジトリ(kohden-code-workspace)が行う
$xd = @(".obsidian", ".git", ".trash", ".tmp.drivedownload", ".tmp.driveupload")
$roboArgs = @($VaultPath, $MirrorPath, "/MIR", "/R:1", "/W:1", "/NP", "/NFL", "/NDL", "/NJH")
foreach ($d in $xd) { $roboArgs += @("/XD", (Join-Path $VaultPath $d)) }

Write-Host "== robocopy: Vault -> mirror =="
& robocopy @roboArgs
$rc = $LASTEXITCODE
if ($rc -ge 8) { throw "robocopy 失敗 exit=$rc" }
Write-Host "robocopy exit=$rc (0-7 は正常)"

# --- 2. 差分確認 (workvault-sync 配下のみ) ---
git -C $RepoPath status --porcelain | Out-Null
if ($LASTEXITCODE -ne 0) { throw "git status 失敗" }
$changes = @(git -C $RepoPath status --porcelain | Where-Object { $_ -match "workvault-sync" })
if (-not $changes) {
    Write-Host "== workvault-sync の差分なし。コミット・push はスキップ =="
    exit 0
}

Write-Host "== 差分 ($($changes.Count) 件) =="
$changes | ForEach-Object { Write-Host $_ }

if ($DryRun) {
    Write-Host "== DryRun のため終了 =="
    exit 0
}

# --- 3. コミット (変更済み分は追跡対象なので通常の add が通る。新規除外判定は -f 不要) ---
git -C $RepoPath add -u -- "workvault-sync"
$addRc = $LASTEXITCODE
if ($addRc -ne 0) {
    # gitignore に完全一致する新規パスは追跡対象外として跳ねられる。既に追跡中のファイルは通る
    Write-Host "git add -u exit=$addRc (新規除外ファイルはスキップ)"
}

$date = Get-Date -Format "yyyy-MM-dd HH:mm"
$msg  = "sync(workvault): $date 差分 $($changes.Count) 件"
git -C $RepoPath commit -m $msg
if ($LASTEXITCODE -ne 0) { throw "git commit 失敗 (差分が staging されなかった可能性)" }

# --- 4. push (PowerShell が stderr をエラー扱いするため $ErrorActionPreference を一時緩和) ---
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
git -C $RepoPath push origin HEAD:main 2>&1 | ForEach-Object { Write-Host $_ }
$pushRc = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($pushRc -ne 0) { throw "git push 失敗 (ネットワーク/認証を確認)" }

Write-Host "== 同期完了: commit/push 済み =="
