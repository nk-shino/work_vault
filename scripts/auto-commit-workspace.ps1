<#
.SYNOPSIS
    Work_Vault以外のGitリポジトリ（既定: kohden-code-workspace）の未コミット差分を自動コミットする。

.DESCRIPTION
    チャットセッションごとに散らばるコミットを集約するための自動コミット。
    - 変更が無ければ何もせず終了（exit 0）
    - コミットメッセージは変更ファイル一覧から自動生成
    - 実行記録は scripts/logs/auto-commit.log へ追記
    - pushは行わない（vault-sync.ps1 が管理するリポジトリのみpush対象）

.NOTES
    タスクスケジューラから実行されることを想定。
    手動実行: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\auto-commit-workspace.ps1 [-DryRun]
#>
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$workspace = "C:\Users\ss80751\kohden-code-workspace"
$logDir    = Join-Path $workspace "scripts\logs"
$logFile   = Join-Path $logDir "auto-commit.log"
$stamp     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param([string]$Message)
    if (-not (Test-Path -LiteralPath $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -LiteralPath $logFile -Value "[$stamp] $Message" -Encoding UTF8
}

Set-Location -LiteralPath $workspace

# git の安全確認: リポジトリであること
git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: not a git repo: $workspace"
    exit 1
}

# 差分の取得（追跡+未追跡）
$status = git status --porcelain
if (-not $status) {
    Write-Log "no changes"
    exit 0
}

# 機微ファイルの除外（.gitignore済みのはずだが念のため再確認して除外）
$sensitivePatterns = @('98_Pass', 'password', 'passwd', 'secret', 'credential', '\.env', 'token')
$files = @()
foreach ($line in $status) {
    $f = $line.Substring(3).Trim('"')
    $isSensitive = $false
    foreach ($p in $sensitivePatterns) {
        if ($f -match $p) { $isSensitive = $true; break }
    }
    if ($isSensitive) {
        Write-Log "SKIP (sensitive name): $f"
        continue
    }
    $files += $f
}

if (-not $files) {
    Write-Log "no committable files (all skipped)"
    exit 0
}

# コミットメッセージ生成: ディレクトリ単位で要約
$dirs = $files | ForEach-Object { Split-Path $_ -Parent } | Where-Object { $_ } | Sort-Object -Unique
$summary = if ($dirs.Count -gt 0) { ($dirs | Select-Object -First 3) -join ', ' } else { ($files | Select-Object -First 3) -join ', ' }
$message = "chore(auto): workspace auto-commit ({0} files) - {1}" -f $files.Count, $summary

if ($DryRun) {
    Write-Host "DRY-RUN: would commit $($files.Count) files with message:"
    Write-Host $message
    $files | ForEach-Object { Write-Host "  $_" }
    exit 0
}

git add -A
git commit --quiet -m $message
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: git commit failed"
    exit 1
}

$hash = git rev-parse --short HEAD
Write-Log "committed $hash : $message"
Write-Host "committed $hash : $message"
exit 0
