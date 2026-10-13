#Requires -Version 5.1
<#
  共有フォルダ ファイル台帳クローラー（全件版 Phase 1）
  読み取り専用。ファイル列挙とプロパティ読み取りのみ。
  書き込み・移動・削除・コピー・属性変更は一切行わない。
#>
param(
    [string]$OutputDir = (Join-Path $PSScriptRoot 'inventory')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

# --- 時刻 ---
$runStart      = Get-Date
$scanTimestamp  = $runStart.ToString('yyyy-MM-dd HH:mm:ss')
$fileTag        = $runStart.ToString('yyyyMMdd_HHmmss')

# ============================================================
# 走査対象
# 共有名まで含めたパスで指定する。
# サーバー名だけでは共有を展開できず 0 件になる。
# ============================================================
$crawlTargets = @(
    '\\nksv1359\share'
    '\\nksv1359\WWW'
    '\\nksv569\Share'
    '\\nksv569\WWW'
    '\\nksv523\Backup'
    '\\nksv523\LOG'
    '\\nksv250\業務統括部Cloud_棚卸関連'
    '\\nksv250\VX_棚卸関連'
    '\\nksv250\CDX統括部情報システム部_在庫Sim'
    'C:\Users\ss80751\NK'
)

# ============================================================
# 出力先の準備
# ============================================================
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}
$csvPath = Join-Path $OutputDir "inventory_${fileTag}.csv"
$logPath = Join-Path $OutputDir "inventory_${fileTag}_errors.log"

# ============================================================
# 走査本体
# .NET の EnumerateFiles は途中のディレクトリでアクセス拒否が
# 出ると残り全部を黙って捨てる。IgnoreInaccessible でも防げない。
# Stack による自前再帰でディレクトリ単位に try/catch する。
# ============================================================
$allRows  = [System.Collections.Generic.List[PSCustomObject]]::new()
$errLines = [System.Collections.Generic.List[string]]::new()
$targetSummary = [System.Collections.Generic.List[string]]::new()

$sw = [System.Diagnostics.Stopwatch]::StartNew()
Write-Host "走査開始: $scanTimestamp"
Write-Host "出力先:   $csvPath"
Write-Host ''

foreach ($root in $crawlTargets) {
    Write-Host "  $root ... " -NoNewline

    if (-not (Test-Path -LiteralPath $root)) {
        $errLines.Add("SKIP`t$root`tパスが存在しないかアクセスできません")
        $targetSummary.Add("  $root`t0`tスキップ")
        Write-Host 'スキップ (パスなし)'
        continue
    }

    $countBefore = $allRows.Count
    $dirCount    = 0
    $stack = [System.Collections.Generic.Stack[string]]::new()
    $stack.Push($root)

    while ($stack.Count -gt 0) {
        $dirPath = $stack.Pop()
        $dirCount++
        $dirObj  = [System.IO.DirectoryInfo]::new($dirPath)

        # ファイル取得
        try {
            foreach ($fi in $dirObj.GetFiles()) {
                try {
                    $allRows.Add([PSCustomObject]@{
                        SourceShare   = $root
                        Name          = $fi.Name
                        Extension     = $fi.Extension
                        LastWriteTime = $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
                        DaysOld       = ($runStart - $fi.LastWriteTime).Days
                        DirectoryName = $fi.DirectoryName
                        Length        = $fi.Length
                        SizeMB        = [math]::Round($fi.Length / 1MB, 2)
                        ScanTimestamp = $scanTimestamp
                    })
                }
                catch {
                    $errLines.Add("FILE`t$($fi.FullName)`t$($_.Exception.Message)")
                }
            }
        }
        catch {
            $errLines.Add("DIR_FILES`t$dirPath`t$($_.Exception.Message)")
        }

        # サブディレクトリ展開
        try {
            foreach ($sub in $dirObj.GetDirectories()) {
                $stack.Push($sub.FullName)
            }
        }
        catch {
            $errLines.Add("DIR_ENUM`t$dirPath`t$($_.Exception.Message)")
        }
    }

    $added = $allRows.Count - $countBefore
    $targetSummary.Add("  $root`t$added 件`t$dirCount フォルダ")
    Write-Host "$added 件 ($dirCount フォルダ)"
}

$sw.Stop()
$elapsedMin = [math]::Round($sw.Elapsed.TotalMinutes, 1)

Write-Host ''
Write-Host '--- 走査結果 ---'
foreach ($line in $targetSummary) { Write-Host $line }
Write-Host ''
Write-Host "合計: $($allRows.Count) 件 / $elapsedMin 分"

# ============================================================
# 並べ替え (LastWriteTime 降順)
# yyyy-MM-dd HH:mm:ss 形式なので文字列の降順で正しい時系列になる
# ============================================================
if ($allRows.Count -gt 0) {
    $sorted = $allRows | Sort-Object LastWriteTime -Descending
}
else {
    $sorted = @()
    Write-Host '走査結果が 0 件のため CSV は空ヘッダーのみ出力します'
}

# ============================================================
# CSV 出力 (Shift-JIS / cp932)
# PS 5.1 では -Encoding Default が Shift-JIS。
# PS 7+ では Default が UTF-8 に変わるため cp932 を明示する。
# ============================================================
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $cp932 = [System.Text.Encoding]::GetEncoding(932)
    $csvText = ($sorted | ConvertTo-Csv -NoTypeInformation) -join "`r`n"
    [System.IO.File]::WriteAllText($csvPath, $csvText + "`r`n", $cp932)
}
else {
    $sorted | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding Default
}

Write-Host "CSV: $csvPath"

# ============================================================
# エラーログ
# ============================================================
if ($errLines.Count -gt 0) {
    $logHeader = @(
        "走査時刻: $scanTimestamp"
        "合計エラー: $($errLines.Count) 件"
        '種別	パス	メッセージ'
        '----	----	----------'
    )
    ($logHeader + $errLines) | Out-File -LiteralPath $logPath -Encoding UTF8
    Write-Host "エラーログ: $logPath ($($errLines.Count) 件)"
}
else {
    Write-Host 'エラー: なし'
}

Write-Host ''
Write-Host "完了 ($elapsedMin 分)"