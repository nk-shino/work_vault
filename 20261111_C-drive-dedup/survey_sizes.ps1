$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$root = 'C:\Users\ss80751\kohden-code-workspace\20261111_C-drive-dedup'

function Get-DirStat {
    param([string]$Path)
    $files = 0
    $bytes = 0L
    Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
        ForEach-Object { $files++; $bytes += $_.Length }
    [pscustomobject]@{
        Path  = $Path
        Files = $files
        MB    = [math]::Round($bytes / 1MB, 1)
        GB    = [math]::Round($bytes / 1GB, 2)
    }
}

$targets = @(
    'C:\Users\ss80751\Desktop'
    'C:\Users\ss80751\Documents'
    'C:\Users\ss80751\Downloads'
    'C:\Users\ss80751\Pictures'
    'C:\Users\ss80751\Videos'
    'C:\Users\ss80751\Music'
    'C:\Users\ss80751\OneDrive'
    'C:\Users\ss80751\OneDrive - NK'
    'C:\Users\ss80751\NK'
    'C:\Users\ss80751\repos'
    'C:\Users\ss80751\node_modules'
    'C:\Users\ss80751\work_vault-clone'
    'C:\Users\ss80751\.cache'
    'C:\Users\ss80751\.config'
    'C:\Users\ss80751\.local'
    'C:\Users\ss80751\.bun'
    'C:\Users\ss80751\AppData\Local'
    'C:\Users\ss80751\AppData\Roaming'
    'C:\Users\ss80751\AppData\Local\Temp'
    'C:\work'
    'C:\whisper'
    'C:\FileInventory'
    'C:\inetpub'
    'C:\ProgramData'
)

$results = foreach ($t in $targets) {
    if (Test-Path -LiteralPath $t) { Get-DirStat -Path $t }
}

$results | Sort-Object GB -Descending | Format-Table -AutoSize
$results | Sort-Object GB -Descending | Export-Csv -LiteralPath (Join-Path $root 'sizes_top.csv') -NoTypeInformation -Encoding UTF8

Write-Output ''
Write-Output '--- Second level: Documents / Downloads / work / OneDrive - NK ---'
$second = @()
foreach ($parent in @('C:\Users\ss80751\Documents','C:\Users\ss80751\Downloads','C:\work','C:\Users\ss80751\OneDrive - NK','C:\Users\ss80751\Desktop')) {
    if (-not (Test-Path -LiteralPath $parent)) { continue }
    Get-ChildItem -LiteralPath $parent -Force -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $second += Get-DirStat -Path $_.FullName
    }
}
$second | Sort-Object GB -Descending | Select-Object -First 40 | Format-Table -AutoSize
$second | Sort-Object GB -Descending | Export-Csv -LiteralPath (Join-Path $root 'sizes_second.csv') -NoTypeInformation -Encoding UTF8
