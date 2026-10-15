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
# 注意: /XD にフルパスを渡すと「そのパスのみ」除外になり、サブフォルダ内の同名フォルダ(.git など)が
# 除外されずミラーに取り込まれる。フォルダ名を渡すことで全階層で一致させる。
foreach ($d in $xd) { $roboArgs += @("/XD", $d) }

Write-Host "== robocopy: Vault -> mirror =="
& robocopy @roboArgs
$rc = $LASTEXITCODE
if ($rc -ge 8) { throw "robocopy 失敗 exit=$rc" }
Write-Host "robocopy exit=$rc (0-7 は正常)"

# --- 2. 差分確認 (workvault-sync 配下のみ) ---
git -C $RepoPath status --porcelain | Out-Null
if ($LASTEXITCODE -ne 0) { throw "git status 失敗" }

# workvault-sync/ は .gitignore 配下のため、status は追跡済みファイルの変更しか出ない。
# 新規ファイルは ignored 扱いになるため、-om (others+modified, gitignore 適用) とは別に
# 明示的な新規検出を行う。ただし以下は除外する:
#   - ネスト git リポジトリの作業フォルダ (.git を含むもの) → gitlink になり push 不能
#   - 100MB 超の除外対象2ファイル (自動はんだ不良入力.zip / NPM-DGS.PDF)
#   - __pycache__ / *.pyc / .tmp.drive* / .bkp 等の生成物
$nestedGit = @(Get-ChildItem -LiteralPath $MirrorPath -Recurse -Force -Directory -Filter ".git" -ErrorAction SilentlyContinue |
    ForEach-Object { $_.FullName })
$nestedPrefixes = @()
foreach ($g in $nestedGit) {
    $rel = $g.Substring($RepoPath.Length + 1).Replace("\", "/")
    # 末尾の "/.git" を除去した作業ツリーの接頭辞 (スラッシュ区切りに統一)
    $nestedPrefixes += $rel.Substring(0, $rel.Length - 5)
}

function Test-Excluded([string]$relPath) {
    foreach ($p in $nestedPrefixes) { if ($relPath -eq $p -or $relPath.StartsWith($p + "/")) { return $true } }
    if ($relPath -match "workvault-sync/11_USBミラー_E/buckup/15575/BK/自動はんだ不良入力\.zip$") { return $true }
    if ($relPath -match "workvault-sync/09_佐藤さん引継ぎ/佐藤\(勇\)/DGS NPM 説明書/NPM-DGS\.PDF$") { return $true }
    if ($relPath -match "(/|^)(__pycache__|\.tmp\.drive)(/|$)|\.egg-info(/|$)|\.pyc$|\.bkp$|/\.git") { return $true }
    if ($relPath -match "workvault-sync/06_Tools/用語集アプリ/data/glossary\.db$") { return $true }
    return $false
}

# 新規候補: ignored 含む全 untracked (-oi) から追跡済み差分 (-om) を引く
$newCandidates = @(git -C $RepoPath ls-files -oi --exclude-standard -- "workvault-sync" |
    Where-Object { $_ -notmatch "^workvault-sync" -or $true } |
    ForEach-Object { $_ })
# -oi --exclude-standard は gitignore を適用するため、gitignore 配下は出ない。
# そこで --no-standard-excludes 相当として ignored も拾う: 実際は下の二段構え
$tracked = @(git -C $RepoPath ls-files -- "workvault-sync")
$trackedSet = @{}
foreach ($t in $tracked) { $trackedSet[$t] = $true }

$allFiles = @(git -C $RepoPath ls-files -o -- "workvault-sync") # gitignore 配下は出ない
# gitignore を無視して新規を拾うには ls-files -oimo --exclude-standard では不十分。
# PowerShell 側でミラーとインデックスを突合するのが確実。
$indexRel = @{}
foreach ($t in $tracked) { $indexRel[$t] = $true }

$newFiles = @()
Get-ChildItem -LiteralPath $MirrorPath -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
    $rel = $_.FullName.Substring($RepoPath.Length + 1).Replace("\", "/")
    if (-not $indexRel.ContainsKey($rel) -and -not (Test-Excluded $rel)) {
        # 0バイトの未追跡ファイルは毎回候補に上がるため警告して除外する
        # (追跡したい場合は手動で git add -f する: 2026-10-15 autonomous-development-guide.md)
        if ($_.Length -eq 0) { Write-Host "[警告] 0バイトの新規候補をスキップ: $rel" }
        elseif ($_.Length -lt 95MB) { $newFiles += $rel }
    }
}
# egg-info フォルダごと除外した場合のフォルダ扱い: egg-info 配下はファイル単位で除外済み

$modFiles = @(git -C $RepoPath status --porcelain | Where-Object { $_ -match "workvault-sync" })
if (-not $modFiles -and -not $newFiles) {
    Write-Host "== workvault-sync の差分なし。コミット・push はスキップ =="
    exit 0
}

$changes = @()
foreach ($m in $modFiles) { $changes += $m }
foreach ($n in $newFiles) { $changes += "A  $n" }

Write-Host "== 差分 ($($changes.Count) 件 / 新規 $($newFiles.Count) 件) =="
$changes | Select-Object -First 30 | ForEach-Object { Write-Host $_ }
if ($changes.Count -gt 30) { Write-Host "... ほか $($changes.Count - 30) 件" }

if ($DryRun) {
    Write-Host "== DryRun のため終了 =="
    exit 0
}

# --- 3. コミット (追跡済みの変更は add -u、新規は -f で強制追加) ---
git -C $RepoPath add -u -- "workvault-sync"
$addRc = $LASTEXITCODE
if ($addRc -ne 0) {
    Write-Host "git add -u exit=$addRc"
}
if ($newFiles.Count -gt 0) {
    # gitignore 配下の新規は -f が要る。ただし除外判定済みのものだけ渡す
    $newFiles | ForEach-Object { git -C $RepoPath add -f -- $_ }
    if ($LASTEXITCODE -ne 0) { throw "git add -f (新規) 失敗" }
    Write-Host "新規 $($newFiles.Count) 件を強制追加"
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
