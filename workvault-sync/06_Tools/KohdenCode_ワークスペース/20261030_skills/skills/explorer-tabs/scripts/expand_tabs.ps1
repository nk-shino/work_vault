# expand_tabs.ps1 — Explorer タブ展開
# 対象パス群を1つのエクスプローラーウィンドウへ新しいタブとして追加し、前面に出す。
# 使い方: powershell -NoProfile -ExecutionPolicy Bypass -File expand_tabs.ps1 -ListFile <UTF-8テキスト(1行1パス)> [-NewWindow]
# 出力: 1行1対象 "OK(tab)|OK(opened with window)|SKIP(focus failed): <パス>" + 最終行 WINDOW_HWND=<hwnd>
param(
    [string]$ListFile,
    [string[]]$Paths,
    [switch]$NewWindow
)
$ErrorActionPreference = 'Stop'

# --- 対象の収集と解決 ---
$items = @()
if ($ListFile) {
    $items += Get-Content -LiteralPath $ListFile -Encoding UTF8 | Where-Object { $_.Trim() -ne '' }
}
if ($Paths) { $items += $Paths }
if ($items.Count -eq 0) { throw 'no target paths (use -ListFile or -Paths)' }

$resolved = @()
foreach ($p in $items) {
    $rp = Resolve-Path -LiteralPath $p.Trim() -ErrorAction Stop
    $resolved += $rp.Path
}

# ファイルは親フォルダへ(アドレスバーにファイルパスを入れると関連アプリが起動するため)
$targets = @()
foreach ($p in $resolved) {
    if (Test-Path -LiteralPath $p -PathType Container) { $targets += $p }
    else { $targets += (Split-Path -Parent $p) }
}
$targets = @($targets | Select-Object -Unique)
if ($targets.Count -eq 0) { throw 'no resolvable targets' }

Add-Type -Namespace Win32 -Name FGW -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
[DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, IntPtr ProcessId);
[DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
[DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
'@
Add-Type -AssemblyName System.Windows.Forms

$shell = New-Object -ComObject Shell.Application

function Get-ExplorerWindows {
    $list = @()
    foreach ($w in $shell.Windows()) {
        try {
            if ($w.HWND -and $w.HWND -ne 0 -and "$($w.FullName)" -match 'explorer\.exe$') { $list += $w }
        } catch { }
    }
    return $list
}

function Enable-Window([IntPtr]$h) {
    if ([Win32.FGW]::IsIconic($h)) { [void][Win32.FGW]::ShowWindow($h, 9) }  # SW_RESTORE
    # 1) 入力スレッドを一時アタッチしてから前面化(フォアグラウンドロック回避の定石)
    $fg = $null
    try { $fg = [Win32.FGW]::GetForegroundWindow() } catch { }
    $myThread = [Win32.FGW]::GetCurrentThreadId()
    $attached = $false
    if ($fg -and $fg -ne [IntPtr]::Zero) {
        $fgThread = [Win32.FGW]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
        if ($fgThread -ne 0 -and $fgThread -ne $myThread) {
            $attached = [Win32.FGW]::AttachThreadInput($myThread, $fgThread, $true)
        }
    }
    [void][Win32.FGW]::SetForegroundWindow($h)
    if ($attached) { [void][Win32.FGW]::AttachThreadInput($myThread, $fgThread, $false) }
    Start-Sleep -Milliseconds 250
    if ([Win32.FGW]::GetForegroundWindow() -eq $h) { return $true }
    # 2) ALTタップでフォアグラウンドロックを解除してから再試行
    [Win32.FGW]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)   # ALT down
    [Win32.FGW]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)   # ALT up
    [void][Win32.FGW]::SetForegroundWindow($h)
    Start-Sleep -Milliseconds 250
    if ([Win32.FGW]::GetForegroundWindow() -eq $h) { return $true }
    # 3) 最小化→復元(復元時はフォアグラウンドになれる)
    [void][Win32.FGW]::ShowWindow($h, 6)   # SW_MINIMIZE
    [void][Win32.FGW]::ShowWindow($h, 9)   # SW_RESTORE
    Start-Sleep -Milliseconds 300
    return ([Win32.FGW]::GetForegroundWindow() -eq $h)
}

# --- 既存ウィンドウの確認(無ければ新規起動) ---
$wins = @(Get-ExplorerWindows)
$launched = $false
if ($wins.Count -eq 0 -or $NewWindow) {
    Start-Process explorer.exe -ArgumentList ('"{0}"' -f $targets[0])
    $launched = $true
    $deadline = (Get-Date).AddSeconds(6)
    do {
        Start-Sleep -Milliseconds 400
        $wins = @(Get-ExplorerWindows)
    } while ($wins.Count -eq 0 -and (Get-Date) -lt $deadline)
    if ($wins.Count -eq 0) { throw 'explorer window did not appear' }
}

$win = $wins[$wins.Count - 1]   # 最近のウィンドウ
$hwnd = [IntPtr]$win.HWND

# --- クリップボードの退避 ---
$oldClip = $null
try { $oldClip = Get-Clipboard -Raw } catch { }

# --- タブ追加ループ ---
$results = @()
$skipFirst = $launched
foreach ($t in $targets) {
    if ($skipFirst) {
        $skipFirst = $false
        $results += "OK(opened with window): $t"
        continue
    }
    if (-not (Enable-Window $hwnd)) { $results += "SKIP(focus failed): $t"; continue }
    Set-Clipboard -Value $t
    Start-Sleep -Milliseconds 150
    [System.Windows.Forms.SendKeys]::SendWait('^t')   # 新規タブ(Win11)
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait('^l')   # アドレスバーへフォーカス
    Start-Sleep -Milliseconds 250
    [System.Windows.Forms.SendKeys]::SendWait('^v')   # パス貼り付け(日本語パスはキー入力でなく貼り付けで)
    Start-Sleep -Milliseconds 250
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Milliseconds 600
    $results += "OK(tab): $t"
}

if ($null -ne $oldClip) { try { Set-Clipboard -Value $oldClip } catch { } }
[void](Enable-Window $hwnd)   # 最後に前面へ

$results | ForEach-Object { Write-Output $_ }
Write-Output ("WINDOW_HWND=" + $win.HWND)
