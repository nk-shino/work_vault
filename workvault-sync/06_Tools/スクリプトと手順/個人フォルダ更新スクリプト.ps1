# 個人フォルダの古いファイルを、修正済みの版で上書きする
#
# 用途: \\nksv569...\★個人フォルダ\篠原 の中身が古く、別ディレクトリに
#       修正済みの版がある場合に、新しいほうで置き換える。
#
# 自宅からは共有へ届かないため未検証。社用PCで実行すること。
#
# 既定は -WhatIf 相当の下見モード。実際に上書きするには -Apply を付ける。
# 理由: 個人フォルダは唯一の実体である可能性があり、取り違えた上書きは戻せない。

param(
    [string]$Target = "\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\★個人フォルダ\篠原",
    [string]$Source = "",          # 修正済みの版があるフォルダ
    [switch]$Apply,                # 付けたときだけ実際に上書きする
    [int]$MinDiffSeconds = 2       # この秒数より新しければ「更新あり」とみなす
)

if (-not $Source) {
    Write-Output "更新元フォルダを -Source で指定すること。例:"
    Write-Output '  .\個人フォルダ更新スクリプト.ps1 -Source "D:\作業\篠原_修正版"'
    exit 1
}
foreach ($p in @($Target, $Source)) {
    if (-not (Test-Path $p)) { Write-Output "到達できない: $p"; exit 1 }
}

# 上書き前の退避先。日付つきで残すので、取り違えても戻せる。
$backup = Join-Path $env:USERPROFILE ("個人フォルダ退避_" + (Get-Date -Format "yyyy-MM-dd_HHmm"))

$newer = @(); $onlySrc = @(); $same = @(); $older = @()

Get-ChildItem $Source -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($Source.Length).TrimStart('\')
    $dstFile = Join-Path $Target $rel
    if (-not (Test-Path $dstFile)) {
        $onlySrc += $rel
    } else {
        $d = ($_.LastWriteTime - (Get-Item $dstFile).LastWriteTime).TotalSeconds
        if ($d -gt $MinDiffSeconds)      { $newer   += $rel }
        elseif ($d -lt -$MinDiffSeconds) { $older   += $rel }
        else                             { $same    += $rel }
    }
}

Write-Output ""
Write-Output "更新元 : $Source"
Write-Output "更新先 : $Target"
Write-Output ""
Write-Output ("  更新元のほうが新しい : {0,5} 件  ← 上書き対象" -f $newer.Count)
Write-Output ("  更新元にしか無い     : {0,5} 件  ← 新規コピー対象" -f $onlySrc.Count)
Write-Output ("  同じ                 : {0,5} 件" -f $same.Count)
Write-Output ("  更新先のほうが新しい : {0,5} 件  ← 触らない" -f $older.Count)
Write-Output ""

if ($older.Count -gt 0) {
    # ここが一番危ない。更新先のほうが新しいということは、現地で直された可能性がある。
    Write-Output "更新先のほうが新しいファイル（上書きしない。目視して判断すること）:"
    $older | Select-Object -First 20 | ForEach-Object { Write-Output "    $_" }
    if ($older.Count -gt 20) { Write-Output ("    … 他 {0} 件" -f ($older.Count - 20)) }
    Write-Output ""
}

if (-not $Apply) {
    Write-Output "下見モード。実際に上書きするには -Apply を付ける。"
    Write-Output "上書き対象の先頭20件:"
    ($newer + $onlySrc) | Select-Object -First 20 | ForEach-Object { Write-Output "    $_" }
    exit 0
}

if ($newer.Count -eq 0 -and $onlySrc.Count -eq 0) {
    Write-Output "上書きするものが無い。終了。"
    exit 0
}

# 上書きされる側を先に退避する
Write-Output "退避先: $backup"
foreach ($rel in $newer) {
    $s = Join-Path $Target $rel
    $d = Join-Path $backup $rel
    New-Item -ItemType Directory -Force (Split-Path $d) | Out-Null
    Copy-Item $s $d -Force
}

$done = 0
foreach ($rel in ($newer + $onlySrc)) {
    $s = Join-Path $Source $rel
    $d = Join-Path $Target $rel
    New-Item -ItemType Directory -Force (Split-Path $d) | Out-Null
    Copy-Item $s $d -Force
    $done++
}

Write-Output ""
Write-Output ("上書き {0} 件 / 退避 {1} 件 -> {2}" -f $done, $newer.Count, $backup)
Write-Output "戻すときは退避先から Copy-Item で書き戻す。"
exit 0
