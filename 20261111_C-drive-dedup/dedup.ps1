#Requires -Version 5.1
<#
  dedup.ps1 - exact-duplicate quarantine tool (dry-run by default)

  Design: 20261111_C-drive-dedup/設計_重複整理フロー_20261111.md
  - Exact matches only (size + SHA-256)
  - Never deletes: moves duplicates to a quarantine folder and writes a restore script
  - Console output is aggregate only; file paths stay in the local manifest

  Examples:
    powershell -NoProfile -ExecutionPolicy Bypass -File dedup.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File dedup.ps1 -Execute
    powershell -NoProfile -ExecutionPolicy Bypass -File dedup.ps1 -AllowOneDrive
#>
param(
    [string[]]$Roots,
    [int]$MinMB = 1,
    [int]$MinAgeDays = 7,
    [string]$Quarantine = 'C:\_dedup_quarantine\20261111',
    [switch]$Execute,
    [switch]$AllowOneDrive,
    [switch]$IncludeRepos
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

if (-not $Roots -or $Roots.Count -eq 0) {
    $Roots = @(
        (Join-Path $env:USERPROFILE 'Documents')
        (Join-Path $env:USERPROFILE 'Desktop')
        (Join-Path $env:USERPROFILE 'Downloads')
        'C:\work'
    )
    if ($AllowOneDrive) {
        $Roots += (Join-Path $env:USERPROFILE 'OneDrive - NK')
        $Roots += (Join-Path $env:USERPROFILE 'NK')
    }
    if ($IncludeRepos) {
        $Roots += (Join-Path $env:USERPROFILE 'repos')
        $Roots += (Join-Path $env:USERPROFILE 'work_vault-clone')
    }
}
$Roots = $Roots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -Unique

$excludeDir = '\\(\.git|node_modules|\.venv|venv|__pycache__|\.cache|AppData|System Volume Information|\$Recycle\.Bin|\.tmp\.drivedownload|\.tmp\.driveupload)(\\|$)'
$excludeName = '^(\.env|.*credential.*|.*password.*|.*secret.*|.*token.*|.*\.pfx|.*\.p12|.*\.key|.*\.kdbx|.*\.ovpn|98_Pass.*)$'

$qFull = [System.IO.Path]::GetFullPath($Quarantine)
foreach ($r in $Roots) {
    $rFull = [System.IO.Path]::GetFullPath($r)
    if ($qFull.StartsWith($rFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Quarantine folder must not be inside a scanned root: $qFull"
    }
}

$cutoff = (Get-Date).AddDays(-$MinAgeDays)
$minBytes = [int64]$MinMB * 1MB

Write-Output '=== dedup.ps1 ==='
Write-Output ("Mode        : {0}" -f $(if ($Execute) { 'EXECUTE (move to quarantine)' } else { 'DRY RUN (no changes)' }))
Write-Output ("Roots       : {0}" -f ($Roots -join ' | '))
Write-Output ("Min size    : {0} MB / Min age: {1} days" -f $MinMB, $MinAgeDays)
Write-Output ("Quarantine  : {0}" -f $qFull)
Write-Output ''

# ---- enumerate (metadata only) ----
$bySize = @{}
$scanned = 0
$skipped = 0
foreach ($r in $Roots) {
    Get-ChildItem -LiteralPath $r -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
        $f = $_
        if ($f.FullName -match $excludeDir) { $script:skipped++; return }
        if ($f.FullName.StartsWith($qFull, [System.StringComparison]::OrdinalIgnoreCase)) { return }
        if ($f.Attributes -band [IO.FileAttributes]::ReparsePoint) { $script:skipped++; return }
        if (($f.Attributes -band 0x400000) -or ($f.Attributes -band 0x1000)) { $script:skipped++; return }
        if ($f.Length -lt $minBytes) { return }
        if ($f.LastWriteTime -gt $cutoff) { $script:skipped++; return }
        if ($f.Name -match $excludeName) { $script:skipped++; return }
        $script:scanned++
        $k = $f.Length
        if (-not $bySize.ContainsKey($k)) { $bySize[$k] = New-Object System.Collections.ArrayList }
        [void]$bySize[$k].Add($f)
    }
}
Write-Output ("Scanned files : {0} (skipped: {1})" -f $scanned, $skipped)

# ---- hash only size-collision groups ----
$sha = [System.Security.Cryptography.SHA256]::Create()
$byHash = @{}
$hashed = 0
foreach ($g in ($bySize.GetEnumerator() | Where-Object { $_.Value.Count -ge 2 })) {
    foreach ($f in $g.Value) {
        try {
            $fs = [System.IO.File]::OpenRead($f.FullName)
            try { $h = $sha.ComputeHash($fs) } finally { $fs.Dispose() }
            $hex = [BitConverter]::ToString($h).Replace('-', '')
        } catch { continue }
        $script:hashed++
        if (-not $byHash.ContainsKey($hex)) { $byHash[$hex] = New-Object System.Collections.ArrayList }
        [void]$byHash[$hex].Add($f)
    }
}
$groups = @($byHash.GetEnumerator() | Where-Object { $_.Value.Count -ge 2 })
Write-Output ("Hashed files  : {0}" -f $hashed)
Write-Output ("Duplicate sets: {0}" -f $groups.Count)

function Get-KeeperRank([string]$p) {
    if ($p -match '\\Documents\\') { return 0 }
    if ($p -match '\\OneDrive - NK\\') { return 1 }
    if ($p -match '^C:\\work\\') { return 2 }
    if ($p -match '\\Desktop\\') { return 3 }
    if ($p -match '\\Downloads\\') { return 4 }
    return 5
}

$plan = New-Object System.Collections.ArrayList
$reclaim = 0L
$gid = 0
foreach ($g in $groups) {
    $gid++
    $files = @($g.Value)
    $keeper = $files |
        Sort-Object @{Expression={ Get-KeeperRank $_.FullName }}, @{Expression={ $_.LastWriteTime }; Descending=$true}, @{Expression={ $_.FullName.Length }} |
        Select-Object -First 1
    foreach ($f in $files) {
        if ($f.FullName -eq $keeper.FullName) { continue }
        $rel = $f.FullName.Substring(3)
        $dest = Join-Path (Join-Path $qFull 'C') $rel
        $destDir = Split-Path -Parent $dest
        $final = $dest
        $i = 1
        while (Test-Path -LiteralPath $final) {
            $final = [System.IO.Path]::Combine($destDir, ("{0}__dup{1}{2}" -f [System.IO.Path]::GetFileNameWithoutExtension($dest), $i, [System.IO.Path]::GetExtension($dest)))
            $i++
        }
        [void]$plan.Add([pscustomobject]@{
            GroupId=$gid; Hash=$g.Name; Length=$f.Length; Original=$f.FullName
            Kept=$keeper.FullName; MovedTo=$final; LastWrite=$f.LastWriteTime
        })
        $reclaim += $f.Length
    }
}

Write-Output ("Files to move : {0}" -f $plan.Count)
Write-Output ("Reclaimable   : {0} GB" -f [math]::Round($reclaim/1GB,2))
Write-Output ''

if ($plan.Count -eq 0) { Write-Output 'Nothing to do.'; return }

if (-not $Execute) {
    Write-Output 'Dry run only. Re-run with -Execute to move the files to quarantine.'
    Write-Output ('Plan preview (first 10 groups, names hidden):')
    $plan | Select-Object -First 10 GroupId, @{n='MB';e={[math]::Round($_.Length/1MB,2)}}, @{n='From';e={Split-Path -Parent $_.Original}} | Format-Table -AutoSize
    return
}

# ---- execute: verify then move ----
New-Item -ItemType Directory -Path $qFull -Force | Out-Null
$moved = 0
$failed = 0
$manifest = New-Object System.Collections.ArrayList
foreach ($p in $plan) {
    try {
        $fs = [System.IO.File]::OpenRead($p.Original)
        try { $h2 = $sha.ComputeHash($fs) } finally { $fs.Dispose() }
        $hex2 = [BitConverter]::ToString($h2).Replace('-', '')
        if ($hex2 -ne $p.Hash) { $script:failed++; continue }
        New-Item -ItemType Directory -Path (Split-Path -Parent $p.MovedTo) -Force | Out-Null
        Move-Item -LiteralPath $p.Original -Destination $p.MovedTo -Force
        [void]$manifest.Add([pscustomobject]@{
            GroupId=$p.GroupId; Hash=$p.Hash; Length=$p.Length; Original=$p.Original
            Kept=$p.Kept; MovedTo=$p.MovedTo; MovedAt=(Get-Date).ToString('s')
        })
        $script:moved++
    } catch {
        $script:failed++
        Write-Warning ("Move failed: {0}" -f $p.Original)
    }
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$manifestPath = Join-Path $qFull "manifest_$stamp.csv"
$manifest | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8

$restorePath = Join-Path $qFull "restore_$stamp.ps1"
@"
# Restore files moved by dedup.ps1
`$manifest = '$manifestPath'
`$rows = Import-Csv -LiteralPath `$manifest
foreach (`$r in `$rows) {
    if (Test-Path -LiteralPath `$r.MovedTo) {
        New-Item -ItemType Directory -Path (Split-Path -Parent `$r.Original) -Force | Out-Null
        Move-Item -LiteralPath `$r.MovedTo -Destination `$r.Original -Force
        Write-Output ('restored: ' + `$r.Original)
    }
}
"@ | Set-Content -LiteralPath $restorePath -Encoding UTF8

Write-Output ''
Write-Output ("Moved         : {0}" -f $moved)
Write-Output ("Failed        : {0}" -f $failed)
Write-Output ("Manifest      : {0}" -f $manifestPath)
Write-Output ("Restore       : {0}" -f $restorePath)
Write-Output 'Verify the application, then delete the quarantine folder after the retention period.'
