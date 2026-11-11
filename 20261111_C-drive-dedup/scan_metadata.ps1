$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$root = 'C:\Users\ss80751\kohden-code-workspace\20261111_C-drive-dedup'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# Metadata-only scan. No file contents are read.
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

Write-Output 'Approved roots:'
$roots | ForEach-Object { Write-Output "  $_" }
Write-Output ''

# ---------- Phase A: size by root (metadata only) ----------
$sizeRows = @()
foreach ($r in $roots) {
    $files = 0; $bytes = 0L
    Get-ChildItem -LiteralPath $r -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch $excludePattern -and -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } |
        ForEach-Object { $files++; $bytes += $_.Length }
    $sizeRows += [pscustomobject]@{ Root=$r; Files=$files; GB=[math]::Round($bytes/1GB,2); MB=[math]::Round($bytes/1MB,1) }
}
$sizeRows | Sort-Object GB -Descending | Format-Table -AutoSize
$sizeRows | Sort-Object GB -Descending | Export-Csv -LiteralPath (Join-Path $root "sizes_$stamp.csv") -NoTypeInformation -Encoding UTF8

# ---------- Phase B: probable duplicates by name + size (no content read) ----------
$minBytes = 262144
$keys = @{}
$scanned = 0
foreach ($r in $roots) {
    Get-ChildItem -LiteralPath $r -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
        $f = $_
        if ($f.FullName -match $excludePattern) { return }
        if ($f.Attributes -band [IO.FileAttributes]::ReparsePoint) { return }
        if ($f.Length -lt $minBytes) { return }
        $script:scanned++
        $k = ('{0}|{1}' -f $f.Name.ToLowerInvariant(), $f.Length)
        if (-not $keys.ContainsKey($k)) { $keys[$k] = New-Object System.Collections.ArrayList }
        [void]$keys[$k].Add($f)
    }
}

$groups = $keys.GetEnumerator() | Where-Object { $_.Value.Count -ge 2 }
$detail = @(); $summary = @(); $wastedTotal = 0L
foreach ($g in $groups) {
    $files = @($g.Value)
    $len = $files[0].Length
    $wasted = $len * ($files.Count - 1)
    $wastedTotal += $wasted
    $summary += [pscustomobject]@{
        Name = $files[0].Name; MBEach = [math]::Round($len/1MB,2); Copies = $files.Count
        WastedMB = [math]::Round($wasted/1MB,2)
        Newest = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
        Oldest = ($files | Sort-Object LastWriteTime | Select-Object -First 1).LastWriteTime
    }
    foreach ($f in $files) {
        $detail += [pscustomobject]@{
            Name=$f.Name; MBEach=[math]::Round($len/1MB,2); Copies=$files.Count; WastedMB=[math]::Round($wasted/1MB,2)
            FullName=$f.FullName; LastWrite=$f.LastWriteTime; Created=$f.CreationTime; Length=$f.Length
        }
    }
}

Write-Output ''
Write-Output "Files >= $minBytes B scanned: $scanned"
Write-Output "Name+size groups with 2+ copies: $(($groups | Measure-Object).Count)"
Write-Output "Upper bound of reclaim (probable): $([math]::Round($wastedTotal/1GB,2)) GB"
Write-Output ''
Write-Output 'Top 40 probable duplicate groups:'
$summary | Sort-Object WastedMB -Descending | Select-Object -First 40 | Format-Table -AutoSize

$summary | Sort-Object WastedMB -Descending | Export-Csv -LiteralPath (Join-Path $root "probable_groups_$stamp.csv") -NoTypeInformation -Encoding UTF8
$detail | Sort-Object WastedMB -Descending | Export-Csv -LiteralPath (Join-Path $root "probable_files_$stamp.csv") -NoTypeInformation -Encoding UTF8
Write-Output "Outputs: probable_groups_$stamp.csv / probable_files_$stamp.csv"
