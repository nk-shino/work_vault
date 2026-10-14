# ============================================================
#  CSV自動バックアップ v2.1 (ASCII互換版)
# ============================================================
# 実行: powershell -ExecutionPolicy Bypass -File .\CsvBackup.ps1

# ====================================
# 設定（ここを書き換えてください）
# ====================================
$WatchFolder = "T:\"   # 監視対象フォルダ
$BackupRoot  = "C:\日本光電富岡_ユーザースクリプト\SMT_SND"               # バックアップ先ルート
# ====================================

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Windows.Forms

# ----------------------------------------------------------

# XAML定義 (WPF GUI)
# ----------------------------------------------------------

[xml]$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="CSV Auto Backup v2.1" Height="370" Width="540"
    WindowStartupLocation="CenterScreen" ResizeMode="CanMinimize"
    Background="#1e1e2e" Foreground="#cdd6f4">

    <Window.Resources>
        <Style TargetType="Button">
            <Setter Property="Background" Value="#45475a"/>
            <Setter Property="Foreground" Value="#cdd6f4"/>
            <Setter Property="BorderBrush" Value="#585b70"/>
            <Setter Property="Padding" Value="12,6"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}"
                                BorderBrush="{TemplateBinding BorderBrush}"
                                BorderThickness="1" CornerRadius="4"
                                Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center"
                                              VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter Property="Background" Value="#585b70"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Grid Margin="16">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <!-- ステータス -->
        <StackPanel Grid.Row="0" Orientation="Horizontal" Margin="0,0,0,8">
            <Ellipse x:Name="StatusLed" Width="12" Height="12"
                     Fill="#a6e3a1" Margin="0,0,8,0" VerticalAlignment="Center"/>
            <TextBlock x:Name="StatusText" Text="Watching" FontSize="15"
                       FontWeight="SemiBold" VerticalAlignment="Center"/>
        </StackPanel>

        <!-- パス情報 -->
        <StackPanel Grid.Row="1" Margin="0,0,0,4">
            <TextBlock FontSize="11" Foreground="#9399b2"
                       Text="Watch:" Margin="0,0,0,1"/>
            <TextBlock FontSize="11" Foreground="#bac2de"
                       x:Name="TxtWatch" TextTrimming="CharacterEllipsis"/>
        </StackPanel>
        <StackPanel Grid.Row="2" Margin="0,0,0,8">
            <TextBlock FontSize="11" Foreground="#9399b2"
                       Text="Backup:" Margin="0,0,0,1"/>
            <TextBlock FontSize="11" Foreground="#bac2de"
                       x:Name="TxtBackup" TextTrimming="CharacterEllipsis"/>
        </StackPanel>

        <!-- ログ -->
        <ListBox Grid.Row="3" x:Name="LogList"
                 Background="#181825" Foreground="#a6adc8"
                 BorderBrush="#313244" FontSize="11.5"
                 FontFamily="Consolas, Meiryo UI"
                 ScrollViewer.HorizontalScrollBarVisibility="Auto"/>

        <!-- ボタン -->
        <StackPanel Grid.Row="4" Orientation="Horizontal"
                    HorizontalAlignment="Right" Margin="0,10,0,0">
            <Button x:Name="BtnOpen" Content="Open Backup Folder"
                    Margin="0,0,8,0"/>
            <Button x:Name="BtnClose" Content="Exit"/>
        </StackPanel>
    </Grid>
</Window>
"@

# ----------------------------------------------------------

# GUI構築
# ----------------------------------------------------------

$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)

$statusLed  = $window.FindName("StatusLed")
$statusText = $window.FindName("StatusText")
$txtWatch   = $window.FindName("TxtWatch")
$txtBackup  = $window.FindName("TxtBackup")
$logList    = $window.FindName("LogList")
$btnOpen    = $window.FindName("BtnOpen")
$btnClose   = $window.FindName("BtnClose")

$txtWatch.Text  = $WatchFolder
$txtBackup.Text = $BackupRoot

# ----------------------------------------------------------

# ログ出力関数
# ----------------------------------------------------------

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("HH:mm:ss")
    $entry = "$timestamp  $Message"
    $window.Dispatcher.Invoke([Action]{
        $logList.Items.Add($entry) | Out-Null
        while ($logList.Items.Count -gt 200) {
            $logList.Items.RemoveAt(0)
        }
        $logList.ScrollIntoView($logList.Items[$logList.Items.Count - 1])
    })
}

# ----------------------------------------------------------

# バックアップ処理（コア）
# ----------------------------------------------------------

function Backup-CsvFile {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) { return }
    if ([IO.Path]::GetExtension($FilePath).ToLower() -ne ".csv") { return }

    # ファイルロック解除待ち（最大15秒）
    $retry = 0
    while ($retry -lt 30) {
        try {
            $stream = [IO.File]::Open($FilePath, 'Open', 'Read', 'Read')
            $stream.Close()
            break
        } catch {
            Start-Sleep -Milliseconds 500
            $retry++
        }
    }
    if ($retry -ge 30) {
        Write-Log "[WARN] Lock timeout: $([IO.Path]::GetFileName($FilePath))"
        return
    }

    $fileName   = [IO.Path]::GetFileName($FilePath)
    $baseName   = [IO.Path]::GetFileNameWithoutExtension($FilePath)
    $dateFolder = (Get-Date).ToString("yyyy-MM-dd")
    $destDir    = Join-Path $BackupRoot $dateFolder

    if (-not (Test-Path $destDir)) {
        New-Item -Path $destDir -ItemType Directory -Force | Out-Null
    }

    $destPath = Join-Path $destDir $fileName

    if (Test-Path $destPath) {
        $srcLastWrite  = (Get-Item $FilePath).LastWriteTime
        $destLastWrite = (Get-Item $destPath).LastWriteTime

        if ($srcLastWrite -eq $destLastWrite) {
            return
        }

        $ts       = $srcLastWrite.ToString("yyyyMMdd_HHmmss")
        $newName  = "${baseName}_${ts}.csv"
        $destPath = Join-Path $destDir $newName

        if (Test-Path $destPath) { return }
    }

    try {
        Copy-Item -Path $FilePath -Destination $destPath -Force
        Write-Log "[OK] $fileName -> $dateFolder\$([IO.Path]::GetFileName($destPath))"
    } catch {
        Write-Log "[ERR] $fileName -- $($_.Exception.Message)"
    }
}

# ----------------------------------------------------------

# フォルダ内の全CSVをバックアップ
# ----------------------------------------------------------

function Backup-AllCsvFiles {
    if (-not (Test-Path $WatchFolder)) { return }
    $files = Get-ChildItem -Path $WatchFolder -Filter "*.csv" -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        Backup-CsvFile -FilePath $f.FullName
    }
}

# ----------------------------------------------------------

# デバウンス用キュー＋タイマー
# ----------------------------------------------------------

$script:pendingFiles = New-Object 'System.Collections.Generic.HashSet[string]' (
    [StringComparer]::OrdinalIgnoreCase
)

$debounceTimer = New-Object System.Windows.Threading.DispatcherTimer
$debounceTimer.Interval = [TimeSpan]::FromSeconds(1.5)
$debounceTimer.Add_Tick({
    $debounceTimer.Stop()

    $filesToProcess = @($script:pendingFiles)
    $script:pendingFiles.Clear()

    foreach ($filePath in $filesToProcess) {
        Backup-CsvFile -FilePath $filePath
    }
})

function Enqueue-File {
    param([string]$FilePath)
    $window.Dispatcher.Invoke([Action]{
        $script:pendingFiles.Add($FilePath) | Out-Null
        $debounceTimer.Stop()
        $debounceTimer.Start()
    })
}

# ----------------------------------------------------------

# FileSystemWatcher 設定
# ----------------------------------------------------------

$watcher = $null

function Start-Watcher {
    $script:watcher = New-Object System.IO.FileSystemWatcher
    $script:watcher.Path                  = $WatchFolder
    $script:watcher.Filter                = "*.csv"
    $script:watcher.IncludeSubdirectories = $false
    $script:watcher.NotifyFilter          = [IO.NotifyFilters]::FileName -bor
                                            [IO.NotifyFilters]::LastWrite -bor
                                            [IO.NotifyFilters]::Size
    $script:watcher.EnableRaisingEvents   = $false

    Register-ObjectEvent -InputObject $script:watcher -EventName Created -Action {
        Enqueue-File -FilePath $Event.SourceEventArgs.FullPath
    } | Out-Null

    Register-ObjectEvent -InputObject $script:watcher -EventName Changed -Action {
        Enqueue-File -FilePath $Event.SourceEventArgs.FullPath
    } | Out-Null

    Register-ObjectEvent -InputObject $script:watcher -EventName Renamed -Action {
        Enqueue-File -FilePath $Event.SourceEventArgs.FullPath
    } | Out-Null

    $script:watcher.EnableRaisingEvents = $true
}

# ----------------------------------------------------------

# 補助ポーリング Timer（60秒間隔）
# ----------------------------------------------------------

$pollTimer = New-Object System.Windows.Threading.DispatcherTimer
$pollTimer.Interval = [TimeSpan]::FromSeconds(60)
$pollTimer.Add_Tick({
    if (Test-Path $WatchFolder) {
        if ($statusText.Text -ne "Watching") {
            $statusLed.Fill  = [Windows.Media.Brushes]::LightGreen
            $statusText.Text = "Watching"
            if ($null -eq $script:watcher -or -not $script:watcher.EnableRaisingEvents) {
                Start-Watcher
                Write-Log "[INFO] FileSystemWatcher restarted"
            }
        }
        Backup-AllCsvFiles
    } else {
        if ($statusText.Text -ne "Folder not found") {
            $statusLed.Fill  = [Windows.Media.Brushes]::Orange
            $statusText.Text = "Folder not found"
            Write-Log "[WARN] Watch folder not found (retrying...)"
        }
        if ($null -ne $script:watcher -and $script:watcher.EnableRaisingEvents) {
            $script:watcher.EnableRaisingEvents = $false
            $script:watcher.Dispose()
            $script:watcher = $null
        }
    }
})

# ----------------------------------------------------------

# ボタンイベント
# ----------------------------------------------------------

$btnOpen.Add_Click({
    $todayDir = Join-Path $BackupRoot (Get-Date).ToString("yyyy-MM-dd")
    $openDir  = if (Test-Path $todayDir) { $todayDir } else { $BackupRoot }
    if (-not (Test-Path $openDir)) {
        New-Item -Path $openDir -ItemType Directory -Force | Out-Null
    }
    Start-Process "explorer.exe" $openDir
})

$btnClose.Add_Click({
    $window.Close()
})

# ----------------------------------------------------------

# ウィンドウ終了時のクリーンアップ
# ----------------------------------------------------------

$window.Add_Closed({
    $pollTimer.Stop()
    $debounceTimer.Stop()
    if ($null -ne $script:watcher) {
        $script:watcher.EnableRaisingEvents = $false
        $script:watcher.Dispose()
    }
    Get-EventSubscriber | Unregister-Event -Force -ErrorAction SilentlyContinue
})

# ----------------------------------------------------------

# 起動シーケンス
# ----------------------------------------------------------

Write-Log "[START] CSV Auto Backup v2.1"
Write-Log "  Watch:  $WatchFolder"
Write-Log "  Backup: $BackupRoot"

if (-not (Test-Path $BackupRoot)) {
    New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null
}

if (Test-Path $WatchFolder) {
    $existing = Get-ChildItem -Path $WatchFolder -Filter "*.csv" -File -ErrorAction SilentlyContinue
    if ($existing.Count -gt 0) {
        Write-Log "[INFO] Found $($existing.Count) existing file(s) - backing up"
        Backup-AllCsvFiles
    }
    Start-Watcher
    Write-Log "[INFO] FileSystemWatcher started"
} else {
    Write-Log "[WARN] Watch folder not found (will retry via polling)"
    $statusLed.Fill  = [Windows.Media.Brushes]::Orange
    $statusText.Text = "Folder not found"
}

$pollTimer.Start()
Write-Log "[INFO] Polling started (60s interval)"

$window.ShowDialog() | Out-Null