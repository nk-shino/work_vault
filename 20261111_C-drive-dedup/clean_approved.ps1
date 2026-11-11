$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$log = 'C:\Users\ss80751\kohden-code-workspace\20261111_C-drive-dedup\clean_approved_log.txt'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function FreeGB { [math]::Round((Get-PSDrive C).Free/1GB, 2) }
function DirBytes([string]$p) {
    $b = 0L
    Get-ChildItem -LiteralPath $p -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object { $b += $_.Length }
    return $b
}

$lines = New-Object System.Collections.ArrayList
function Note([string]$s) { [void]$lines.Add($s); Write-Output $s }

$before = FreeGB
Note ("[{0}] free before: {1} GB" -f $stamp, $before)

# 1) Temp older than 7 days (approved)
$temp = Join-Path $env:LOCALAPPDATA 'Temp'
$cutoff = (Get-Date).AddDays(-7)
$b0 = DirBytes $temp
$removed = 0
Get-ChildItem -LiteralPath $temp -Force -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.LastWriteTime -lt $cutoff) {
        try { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop; $removed++ } catch {}
    }
}
$b1 = DirBytes $temp
Note ("[Temp >7d] entries removed: {0} / freed: {1} GB" -f $removed, [math]::Round(($b0-$b1)/1GB,2))

# 2) npm cache (approved)
$npmBefore = DirBytes (Join-Path $env:LOCALAPPDATA 'npm-cache')
& npm cache clean --force 2>$null | Out-Null
$npmAfter = DirBytes (Join-Path $env:LOCALAPPDATA 'npm-cache')
Note ("[npm] freed: {0} GB" -f [math]::Round(($npmBefore-$npmAfter)/1GB,2))

# 3) pip cache (approved)
$pipBefore = DirBytes (Join-Path $env:LOCALAPPDATA 'pip\Cache')
& python -m pip cache purge 2>$null | Out-Null
$pipAfter = DirBytes (Join-Path $env:LOCALAPPDATA 'pip\Cache')
Note ("[pip] freed: {0} GB" -f [math]::Round(($pipBefore-$pipAfter)/1GB,2))

# 4) HuggingFace model cache (approved). Keep token/auth files.
$hf = Join-Path $env:USERPROFILE '.cache\huggingface'
foreach ($sub in @('hub','xet')) {
    $p = Join-Path $hf $sub
    if (Test-Path -LiteralPath $p) {
        $hb = DirBytes $p
        try { Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop } catch {}
        $ha = DirBytes $p
        Note ("[HF {0}] freed: {1} GB" -f $sub, [math]::Round(($hb-$ha)/1GB,2))
    }
}

# 5) Docker is handled separately with narrowly scoped prune commands.

$after = FreeGB
Note ("free after: {0} GB / delta: {1} GB" -f $after, [math]::Round($after-$before,2))
$lines | Add-Content -LiteralPath $log -Encoding UTF8
