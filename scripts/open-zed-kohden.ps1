param()

$zedPath = Join-Path $env:LOCALAPPDATA "Programs\Zed\Zed.exe"
$workspace = "C:\Users\ss80751\kohden-code-workspace"
$weekday = (Get-Date).DayOfWeek

if ($weekday -in @([System.DayOfWeek]::Saturday, [System.DayOfWeek]::Sunday)) {
    Write-Verbose "Weekend detected ($weekday). Skipping Zed launch." -Verbose
    exit 0
}

if (-not (Test-Path -LiteralPath $zedPath)) {
    Write-Error "Zed executable not found at $zedPath"
    exit 1
}

if (-not (Test-Path -LiteralPath $workspace)) {
    Write-Error "Workspace path not found: $workspace"
    exit 1
}

# Avoid launching multiple windows if Zed already has the workspace open.
$existing = Get-Process -Name "Zed" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Verbose "Zed is already running. Skipping additional launch." -Verbose
    exit 0
}

Start-Process -FilePath $zedPath -ArgumentList "--new-window", $workspace
