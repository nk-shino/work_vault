
CPUとメモリを1台分だけ眺める用途
~~~
while ($true) {
    Clear-Host
    Write-Host "更新時刻 $(Get-Date -Format 'HH:mm:ss')"

    $cpu = (Get-CimInstance Win32_Processor).LoadPercentage
    Write-Host "CPU使用率 $cpu %"

    $os = Get-CimInstance Win32_OperatingSystem
    $used  = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 2)
    $total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    Write-Host "メモリ $used GB / $total GB"

    Start-Sleep -Seconds 2
}
~~~

動きが重いと感じたときに原因を探す用途。
CPUを食っている上位のプロセスを繰り返し並べ直すので、どのアプリが張り付いているかを時刻付きで追える。
~~~
while ($true) {
    Clear-Host
    Write-Host "更新時刻 $(Get-Date -Format 'HH:mm:ss')"
    Get-Process |
        Sort-Object CPU -Descending |
        Select-Object -First 10 Name, Id, CPU,
            @{Name='Mem(MB)';Expression={[math]::Round($_.WS/1MB,1)}} |
        Format-Table -AutoSize
    Start-Sleep -Seconds 2
}
~~~

ディスクの空きが心配なときに、使用量と残量を一定間隔で見張る用途。
大きなファイルをコピーしている最中や、容量が減っていく作業のときに役立つ。
~~~
while ($true) {
    Clear-Host
    Write-Host "更新時刻 $(Get-Date -Format 'HH:mm:ss')"
    Get-PSDrive -PSProvider FileSystem |
        Select-Object Name,
            @{N='Used(GB)';E={[math]::Round($_.Used/1GB,1)}},
            @{N='Free(GB)';E={[math]::Round($_.Free/1GB,1)}} |
        Format-Table -AutoSize
    Start-Sleep -Seconds 5
}
~~~

外との通信が気になるときに、今つながっている相手を見張る用途。
確立中の接続を数秒おきに出し直すので、どのプロセスがどこと通信しているかが分かる。
~~~
while ($true) {
    Clear-Host
    Write-Host "更新時刻 $(Get-Date -Format 'HH:mm:ss')"
    Get-NetTCPConnection -State Established |
        Select-Object LocalPort, RemoteAddress, RemotePort, OwningProcess |
        Format-Table -AutoSize
    Start-Sleep -Seconds 3
}
~~~

CPUの使用率だけを本格的に測りたいときは、自分でループを書かずにGet-Counterへ任せる方法。
Continuousを付けると指定した間隔で値を取り続ける。
~~~
Get-Counter '\Processor(_Total)\% Processor Time' -Continuous -SampleInterval 1
~~~

# 実行中モニター表示スクリプト

# 現在時刻 / 経過時間 / 通信速度をリアルタイム表示


```
# ============================================
# 実行中モニター表示スクリプト
# 現在時刻 / 経過時間 / 通信速度をリアルタイム表示
# ============================================

$startTime = Get-Date

# 計測対象のネットワークアダプター名を取得（最初の有効なもの）
$adapter = (Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1).Name
Write-Host "監視対象アダプター: $adapter" -ForegroundColor Cyan

# 前回値の初期化
$prevStats = Get-NetAdapterStatistics -Name $adapter
$prevRx = $prevStats.ReceivedBytes
$prevTx = $prevStats.SentBytes

# メイン処理ループ
$duration = 3600
for ($i = 0; $i -lt $duration; $i++) {

    Start-Sleep -Seconds 1

    # --- 通信速度の計算 ---
    $curStats = Get-NetAdapterStatistics -Name $adapter
    $downSpeed = ($curStats.ReceivedBytes - $prevRx) / 1KB   # KB/s
    $upSpeed   = ($curStats.SentBytes     - $prevTx) / 1KB   # KB/s
    $prevRx = $curStats.ReceivedBytes
    $prevTx = $curStats.SentBytes

    # --- 時刻・経過時間 ---
    $now     = Get-Date
    $elapsed = $now - $startTime

    # --- 1行で上書き表示 ---
    $line = ("[実行中] {0} | 経過: {1:hh\:mm\:ss} | ↓{2,7:N1} KB/s | ↑{3,7:N1} KB/s" -f `
        $now.ToString("HH:mm:ss"), $elapsed, $downSpeed, $upSpeed)

    Write-Host "`r$line" -NoNewline -ForegroundColor Green
}

Write-Host "`n完了しました！" -ForegroundColor Yellow
```
