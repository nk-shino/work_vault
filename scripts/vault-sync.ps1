# Work_Vault 同期スクリプト
# Vault 実体 -> workspace/workvault-sync ミラー -> git commit -> GitHub push
#
# 使い方:
#   powershell -NoProfile -ExecutionPolicy Bypass -File vault-sync.ps1            # 同期+コミット+push
#   powershell -NoProfile -ExecutionPolicy Bypass -File vault-sync.ps1 -DryRun    # 反映内容の確認のみ
#
# 配置場所: C:\Users\ss80751\kohden-code-workspace\scripts\vault-sync.ps1
#           (ミラー配下に置くと robocopy /MIR の EXTRA 判定で消えるため scripts/ に置く)
#
# 前提: ミラー先に .git があり origin が設定済み(初回のみ setup 済みであること)
# 注意: 98_Pass を含める方針。リポジトリは Private 運用のこと。

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$VaultPath  = "C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault"
$MirrorPath = "C:\Users\ss80751\kohden-code-workspace\workvault-sync"

if (-not (Test-Path -LiteralPath $VaultPath))  { throw "Vault が見つからない: $VaultPath" }
if (-not (Test-Path -LiteralPath (Join-Path $MirrorPath ".git"))) { throw "ミラーの .git が無い: $MirrorPath" }

# --- 1. robocopy で反映 (削除も同期) ---
# /MIR 完全ミラー  /XD 同期対象外  /R:1 /W:1 再試行1回  /NFL /NDL ログ簡略  /NP 進捗非表示
# 注意: .git はミラー側にしか無いため /XD で保護する。外すと /MIR が .git を削除する
$xd = @(".obsidian", ".git", ".trash", ".tmp.drivedownload", ".tmp.driveupload")
$roboArgs = @($VaultPath, $MirrorPath, "/MIR", "/R:1", "/W:1", "/NP", "/NFL", "/NDL", "/NJH")
foreach ($d in $xd) { $roboArgs += @("/XD", (Join-Path $VaultPath $d)) }

Write-Host "== robocopy: Vault -> mirror =="
& robocopy @roboArgs
$rc = $LASTEXITCODE
if ($rc -ge 8) { throw "robocopy 失敗 exit=$rc" }
Write-Host "robocopy exit=$rc (0-7 は正常)"

# --- 2. 差分確認 ---
git -C $MirrorPath status --porcelain | Out-Null
if ($LASTEXITCODE -ne 0) { throw "git status 失敗" }
$changes = @(git -C $MirrorPath status --porcelain)
if (-not $changes) {
    Write-Host "== 差分なし。コミット・push はスキップ =="
    exit 0
}

Write-Host "== 差分 ($($changes.Count) 件) =="
$changes | ForEach-Object { Write-Host $_ }

if ($DryRun) {
    Write-Host "== DryRun のため終了 =="
    exit 0
}

# --- 3. コミット ---
git -C $MirrorPath add -A
if ($LASTEXITCODE -ne 0) { throw "git add 失敗" }

$date = Get-Date -Format "yyyy-MM-dd HH:mm"
$msg  = "sync(workvault): $date 差分 $($changes.Count) 件"
git -C $MirrorPath commit -m $msg
if ($LASTEXITCODE -ne 0) { throw "git commit 失敗" }

# --- 4. push ---
git -C $MirrorPath push origin HEAD 2>&1 | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) { throw "git push 失敗 (ネットワーク/認証を確認)" }

Write-Host "== 同期完了: commit/push 済み =="
