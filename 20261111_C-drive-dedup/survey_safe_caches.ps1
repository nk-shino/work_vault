$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$out = 'C:\Users\ss80751\kohden-code-workspace\20261111_C-drive-dedup\safe_cache_sizes.csv'

# Aggregate-only measurement. No file names are read or reported.
$paths = @(
    "$env:LOCALAPPDATA\Temp"
    "$env:LOCALAPPDATA\npm-cache"
    "$env:LOCALAPPDATA\pnpm"
    "$env:LOCALAPPDATA\ms-playwright"
    "$env:LOCALAPPDATA\Docker"
    "$env:LOCALAPPDATA\Package Cache"
    "$env:LOCALAPPDATA\pip\Cache"
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Code Cache"
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
    "$env:LOCALAPPDATA\Microsoft\vscode-cpptools"
    "$env:APPDATA\Code\Cache"
    "$env:APPDATA\Code\CachedData"
    "$env:USERPROFILE\.bun\install\cache"
    "$env:USERPROFILE\.cache"
    "$env:USERPROFILE\.npm"
    'C:\Windows\Temp'
    'C:\Windows\SoftwareDistribution\Download'
    'C:\Users\ss80751\kohden-code-workspace\.tmp.drivedownload'
    'C:\Users\ss80751\kohden-code-workspace\.tmp.driveupload'
    'C:\Users\ss80751\kohden-code-workspace\.playwright-mcp'
    'C:\Users\ss80751\kohden-code-workspace\_archive'
    'C:\Users\ss80751\kohden-code-workspace\stash3_20261106'
    'C:\Users\ss80751\kohden-code-workspace\trimmed'
)

$rows = @()
foreach ($p in $paths) {
    if (-not (Test-Path -LiteralPath $p)) { continue }
    $n = 0; $b = 0L
    Get-ChildItem -LiteralPath $p -Recurse -Force -File -ErrorAction SilentlyContinue |
        ForEach-Object { $n++; $b += $_.Length }
    $rows += [pscustomobject]@{ Path=$p; Files=$n; GB=[math]::Round($b/1GB,3); MB=[math]::Round($b/1MB,1) }
}

$rows | Sort-Object GB -Descending | Format-Table -AutoSize
$rows | Sort-Object GB -Descending | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8
Write-Output ''
Write-Output ("Total measured: {0} GB" -f [math]::Round((($rows | Measure-Object GB -Sum).Sum),2))
