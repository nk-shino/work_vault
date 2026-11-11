$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$root = 'C:\Users\ss80751\kohden-code-workspace\20261111_C-drive-dedup'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# Approved scope (user approved 2026-11-11: business data + OneDrive/vault)
$roots = @(
    'C:\work'
    'C:\whisper'
    'C:\Users\ss80751\Documents'
    'C:\Users\ss80751\Desktop'
    'C:\Users\ss80751\Downloads'
    'C:\Users\ss80751\OneDrive - NK'
    'C:\Users\ss80751\NK'
    'C:\Users\ss80751\work_vault-clone'
    'C:\Users\ss80751\OneDrive'
) | Where-Object { Test-Path -LiteralPath $_ }

$excludePattern = '\\(\.git|node_modules|\.venv|venv|__pycache__|\.cache|AppData|System Volume Information|\$Recycle\.Bin|\.tmp\.drivedownload|\.tmp\.driveupload)(\\|$)'

Write-Output "Approved roots:"
$roots | ForEach-Object { Write-Output "  $_" }
Write-Output ''

# ---------- Phase A: size by root ----------
$sizeRows = @()
foreach ($r in $roots) {
    $files = 0
    $bytes = 0L
    Get-ChildItem -LiteralPath $r -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch $excludePattern -and -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } |
        ForEach-Object { $files++; $bytes += $_.Length }
    $sizeRows += [pscustomobject]@{
        Root = $r; Files = $files; GB = [math]::Round($bytes / 1GB, 2); MB = [math]::Round($bytes / 1MB, 1)
    }
}
$sizeRows | Sort-Object GB -Descending | Format-Table -AutoSize
$sizeRows | Sort-Object GB -Descending | Export-Csv -LiteralPath (Join-Path $root "sizes_$stamp.csv") -NoTypeInformation -Encoding UTF8

# ---------- Phase B: exact duplicate detection ----------
$minBytes = 262144
$attrOffline = 0x1000
$attrRecall = 0x400000

$bySize = @{}
$scanned = 0
$skippedCloud = 0

foreach ($r in $roots) {
    Get-ChildItem -LiteralPath $r -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
        $f = $_
        if ($f.FullName -match $excludePattern) { return }
        if ($f.Attributes -band [IO.FileAttributes]::ReparsePoint) { return }
        if (($f.Attributes -band $attrRecall) -or ($f.Attributes -band $attrOffline)) { $script:skippedCloud++; return }
        if ($f.Length -lt $minBytes) { return }
        $script:scanned++
        $key = $f.Length
        if (-not $bySize.ContainsKey($key)) { $bySize[$key] = New-Object System.Collections.ArrayList }
        [void]$bySize[$key].Add($f)
    }
}

$candidates = $bySize.GetEnumerator() | Where-Object { $_.Value.Count -ge 2 }
Write-Output "Files >= $minBytes bytes scanned: $scanned / duplicate-size candidates: $(($candidates | Measure-Object).Count) size groups"

$sha = [System.Security.Cryptography.SHA256]::Create()
$hashRows = @()
$n = 0
foreach ($g in $candidates) {
    foreach ($f in $g.Value) {
        $n++
        if ($n % 200 -eq 0) { Write-Output "  hashing $n ..." }
        try {
            $fs = [System.IO.File]::OpenRead($f.FullName)
            try { $h = $sha.ComputeHash($fs) } finally { $fs.Dispose() }
            $hex = [BitConverter]::ToString($h).Replace('-', '')
            $hashRows += [pscustomobject]@{
                Hash = $hex; Length = $f.Length; FullName = $f.FullName
                LastWrite = $f.LastWriteTime; Created = $f.CreationTime
            }
        } catch {}
    }
}

$dupGroups = $hashRows | Group-Object Hash | Where-Object { $_.Count -ge 2 }
$detail = @()
$summary = @()
$wastedTotal = 0L
foreach ($g in $dupGroups) {
    $len = $g.Group[0].Length
    $wasted = $len * ($g.Count - 1)
    $wastedTotal += $wasted
    $summary += [pscustomobject]@{
        Hash = $g.Name; MBEach = [math]::Round($len / 1MB, 2); Copies = $g.Count
        WastedMB = [math]::Round($wasted / 1MB, 2)
    }
    foreach ($row in $g.Group) {
        $detail += [pscustomobject]@{
            Hash = $g.Name; MBEach = [math]::Round($len / 1MB, 2); Copies = $g.Count
            WastedMB = [math]::Round($wasted / 1MB, 2); FullName = $row.FullName
            LastWrite = $row.LastWrite; Created = $row.Created; Length = $row.Length
        }
    }
}

Write-Output ''
Write-Output "Identical groups: $(($dupGroups | Measure-Object).Count) / reclaimable: $([math]::Round($wastedTotal/1GB,2)) GB"
Write-Output "Cloud placeholders skipped: $skippedCloud"
Write-Output ''
$summary | Sort-Object WastedMB -Descending | Select-Object -First 30 | Format-Table -AutoSize

$summary | Sort-Object WastedMB -Descending | Export-Csv -LiteralPath (Join-Path $root "dup_groups_$stamp.csv") -NoTypeInformation -Encoding UTF8
$detail | Sort-Object WastedMB -Descending | Export-Csv -LiteralPath (Join-Path $root "dup_files_$stamp.csv") -NoTypeInformation -Encoding UTF8
Write-Output "Outputs: dup_groups_$stamp.csv / dup_files_$stamp.csv"
