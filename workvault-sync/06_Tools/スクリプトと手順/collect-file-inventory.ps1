#Requires -Version 5.1
<#
.SYNOPSIS
    社内ファイルサーバ/共有の「ファイル台帳」をメタデータのみで収集する。

.DESCRIPTION
    安全上の約束（厳守）:
      * 探索先は読み取り専用。新規作成・更新・削除・属性変更を一切行わない。
      * ファイル本文を一切読まない。ハッシュ計算も行わない（第1段はメタデータのみ）。
      * 出力は -OutputRoot（Work_Vault 配下）にのみ書き込む。
      * 機微情報に該当する名前のファイルは Sensitive=true とし、
        パス・サイズ・更新日時以外を記録しない。

    対象定義とタグ語彙は scripts/config/inventory-targets.json を正本とする。
    語彙の意味は Work_Vault/10_業務全般/システム関係マップ/03_オブジェクト台帳.md を参照。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\collect-file-inventory.ps1 -WhatIfScan
    対象一覧と到達可否だけを表示して終了する（走査しない）。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\collect-file-inventory.ps1 -TargetId local-dept-docs
    指定した target だけを走査する。
#>
[CmdletBinding()]
param(
    [string]   $ConfigPath,
    [string]   $OutputRoot,
    [string[]] $TargetId,
    [switch]   $WhatIfScan,
    [int]      $MaxDepth = 0
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# 設定読み込み
# ---------------------------------------------------------------------------
# $PSScriptRoot は param 既定値の評価時に空になることがあるため、本体で解決する
if (-not $ConfigPath -or $ConfigPath.Trim() -eq '') {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
    $ConfigPath = Join-Path $scriptDir 'config\inventory-targets.json'
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "設定ファイルが見つかりません: $ConfigPath"
}

$config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

if (-not $OutputRoot -or $OutputRoot.Trim() -eq '') {
    $OutputRoot = $config.outputRoot
}
if (-not $OutputRoot) {
    throw '出力先が決まりません。-OutputRoot を指定するか config の outputRoot を設定してください。'
}

# 対象 target の決定
$targets = @($config.targets | Where-Object { $_.enabled })
if ($TargetId -and $TargetId.Count -gt 0) {
    $targets = @($targets | Where-Object { $TargetId -contains $_.id })
}
if ($targets.Count -eq 0) {
    throw '有効な target がありません。config の enabled と -TargetId を確認してください。'
}

# ---------------------------------------------------------------------------
# 照合用テーブルの事前構築（1ファイルあたりの判定を速くするため）
# ---------------------------------------------------------------------------
$excludeDirSet = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($n in @($config.excludeDirNames)) { [void]$excludeDirSet.Add($n) }

$excludeFilePatterns = @($config.excludeFilePatterns)

# 拡張子 -> カテゴリ
$extToCategory = @{}
foreach ($rule in @($config.categoryRules)) {
    foreach ($ext in @($rule.extensions)) {
        $extToCategory[$ext.ToLowerInvariant()] = $rule.category
    }
}

# タグ名 -> 検索語配列
function ConvertTo-TagTable {
    param($TagObject)
    $table = New-Object System.Collections.ArrayList
    if ($null -eq $TagObject) { return , $table }
    foreach ($prop in $TagObject.PSObject.Properties) {
        [void]$table.Add([PSCustomObject]@{
            Tag   = $prop.Name
            Terms = @($prop.Value)
        })
    }
    return , $table
}

$systemTagTable    = ConvertTo-TagTable -TagObject $config.systemTags
$equipmentTagTable = ConvertTo-TagTable -TagObject $config.equipmentTags
$sensitivePatterns = @($config.sensitiveNamePatterns)

function Get-MatchedTags {
    param(
        [string] $Text,
        $TagTable
    )
    $hits = New-Object System.Collections.ArrayList
    foreach ($entry in $TagTable) {
        foreach ($term in $entry.Terms) {
            if ($Text.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                [void]$hits.Add($entry.Tag)
                break
            }
        }
    }
    if ($hits.Count -eq 0) { return '' }
    return ($hits -join ';')
}

function Test-Sensitive {
    param([string] $Text)
    foreach ($p in $sensitivePatterns) {
        if ($Text.IndexOf($p, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
    }
    return $false
}

function Test-ExcludedFileName {
    param([string] $Name)
    foreach ($pattern in $excludeFilePatterns) {
        if ($Name -like $pattern) { return $true }
    }
    return $false
}

# ---------------------------------------------------------------------------
# -WhatIfScan : 走査せず対象確認のみ
# ---------------------------------------------------------------------------
if ($WhatIfScan) {
    Write-Host ''
    Write-Host '=== 対象確認のみ（走査しません） ===' -ForegroundColor Cyan
    Write-Host ("設定ファイル : {0}" -f $ConfigPath)
    Write-Host ("出力先       : {0}" -f $OutputRoot)
    Write-Host ''

    $preview = foreach ($t in $targets) {
        $reachable = $false
        try { $reachable = Test-Path -LiteralPath $t.path } catch { $reachable = $false }
        [PSCustomObject]@{
            Id        = $t.id
            到達      = if ($reachable) { 'OK' } else { 'NG' }
            Path      = $t.path
            Note      = $t.note
        }
    }
    $preview | Format-Table -AutoSize | Out-String -Width 400 | Write-Host

    $disabled = @($config.targets | Where-Object { -not $_.enabled })
    if ($disabled.Count -gt 0) {
        Write-Host '--- 既定で対象外 ---' -ForegroundColor DarkGray
        foreach ($d in $disabled) {
            Write-Host ("  {0,-22} {1}" -f $d.id, $d.note) -ForegroundColor DarkGray
        }
    }
    Write-Host ''
    Write-Host '本スキャンは -WhatIfScan を外して実行してください。' -ForegroundColor Yellow
    return
}

# ---------------------------------------------------------------------------
# 出力先の準備
# ---------------------------------------------------------------------------
$stamp   = Get-Date -Format 'yyyyMMdd_HHmmss'
$scanDir = Join-Path $OutputRoot ("scan_" + $stamp)
New-Item -ItemType Directory -Path $scanDir -Force | Out-Null

$inventoryCsv = Join-Path $scanDir 'inventory.csv'
$firstSeenCsv = Join-Path $scanDir 'first-seen.csv'
$duplicateCsv = Join-Path $scanDir 'duplicates.csv'
$summaryCsv   = Join-Path $scanDir 'targets-summary.csv'
$errorCsv     = Join-Path $scanDir 'errors.csv'
$summaryMd    = Join-Path $scanDir 'summary.md'

Write-Host ''
Write-Host ("出力先: {0}" -f $scanDir) -ForegroundColor Cyan
Write-Host ''

# 集計用
$errors        = New-Object System.Collections.ArrayList
$targetSummary = New-Object System.Collections.ArrayList
$dirAgg        = @{}   # ディレクトリ -> 集計
$dupAgg        = @{}   # "name|size" -> パス一覧
$categoryCount = @{}
$systemCount   = @{}
$totalFiles    = 0
$totalBytes    = [int64]0
$sensitiveCount = 0
$inventoryHeaderWritten = $false

$scanStartedAt = Get-Date

# ---------------------------------------------------------------------------
# 走査本体
# ---------------------------------------------------------------------------
foreach ($t in $targets) {

    $tStart = Get-Date
    Write-Host ("[開始] {0}  {1}" -f $t.id, $t.path) -ForegroundColor Green

    $reachable = $false
    try { $reachable = Test-Path -LiteralPath $t.path } catch { $reachable = $false }

    if (-not $reachable) {
        Write-Host ("  到達できません。スキップします。") -ForegroundColor Yellow
        [void]$errors.Add([PSCustomObject]@{
            TargetId = $t.id; Path = $t.path; Message = '到達できません（Test-Path = False）'
        })
        [void]$targetSummary.Add([PSCustomObject]@{
            TargetId = $t.id; Path = $t.path; Reachable = $false
            FileCount = 0; TotalSizeBytes = 0; ElapsedSeconds = 0; ErrorCount = 1
        })
        continue
    }

    $rootLen     = $t.path.TrimEnd('\').Length
    $records     = New-Object System.Collections.ArrayList
    $tFiles      = 0
    $tBytes      = [int64]0
    $tErrorCount = 0

    $gciErr = $null
    $items = Get-ChildItem -LiteralPath $t.path -Recurse -File -Force `
                           -ErrorAction SilentlyContinue -ErrorVariable gciErr

    foreach ($e in @($gciErr)) {
        $tErrorCount++
        [void]$errors.Add([PSCustomObject]@{
            TargetId = $t.id
            Path     = if ($e.TargetObject) { [string]$e.TargetObject } else { $t.path }
            Message  = $e.Exception.Message
        })
    }

    foreach ($f in $items) {
        try {
            $full = $f.FullName

            # 相対パスの分解（除外判定と深さ算出で再利用）
            $relative = $full.Substring([Math]::Min($rootLen, $full.Length)).TrimStart('\')
            $segments = $relative.Split('\')
            $depth    = $segments.Count - 1

            if ($MaxDepth -gt 0 -and $depth -gt $MaxDepth) { continue }

            # 除外フォルダ配下か
            $skip = $false
            for ($i = 0; $i -lt $segments.Count - 1; $i++) {
                if ($excludeDirSet.Contains($segments[$i])) { $skip = $true; break }
            }
            if ($skip) { continue }

            # 除外ファイル名か
            if (Test-ExcludedFileName -Name $f.Name) { continue }

            $isSensitive = Test-Sensitive -Text $full

            if ($isSensitive) {
                # 機微: 所在のみ。タグ・カテゴリを付けない
                $category = ''
                $sysTags  = ''
                $eqTags   = ''
                $sensitiveCount++
            }
            else {
                $ext      = $f.Extension.ToLowerInvariant()
                $category = if ($extToCategory.ContainsKey($ext)) { $extToCategory[$ext] } else { 'その他' }
                $sysTags  = Get-MatchedTags -Text $full -TagTable $systemTagTable
                $eqTags   = Get-MatchedTags -Text $full -TagTable $equipmentTagTable

                if ($categoryCount.ContainsKey($category)) { $categoryCount[$category]++ } else { $categoryCount[$category] = 1 }
                if ($sysTags -ne '') {
                    foreach ($tag in $sysTags.Split(';')) {
                        if ($systemCount.ContainsKey($tag)) { $systemCount[$tag]++ } else { $systemCount[$tag] = 1 }
                    }
                }
            }

            [void]$records.Add([PSCustomObject]@{
                TargetId       = $t.id
                FullPath       = $full
                Directory      = $f.DirectoryName
                Name           = $f.Name
                Extension      = $f.Extension
                SizeBytes      = $f.Length
                LastWriteTime  = $f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
                CreationTime   = $f.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')
                Category       = $category
                SystemTags     = $sysTags
                EquipmentTags  = $eqTags
                Sensitive      = $isSensitive
                Depth          = $depth
            })

            $tFiles++
            $tBytes += $f.Length

            # ディレクトリ集計（初出ディレクトリの記録用）
            $dkey = $f.DirectoryName
            if (-not $dirAgg.ContainsKey($dkey)) {
                $dirAgg[$dkey] = [PSCustomObject]@{
                    TargetId       = $t.id
                    Directory      = $dkey
                    FileCount      = 0
                    TotalSizeBytes = [int64]0
                    FirstSeenAt    = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
                    SystemTags     = (New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase))
                    EquipmentTags  = (New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase))
                }
            }
            $agg = $dirAgg[$dkey]
            $agg.FileCount++
            $agg.TotalSizeBytes += $f.Length
            if ($sysTags -ne '') { foreach ($tag in $sysTags.Split(';')) { [void]$agg.SystemTags.Add($tag) } }
            if ($eqTags  -ne '') { foreach ($tag in $eqTags.Split(';'))  { [void]$agg.EquipmentTags.Add($tag) } }

            # 重複候補（名前 + サイズ。ハッシュは取らない）
            $ckey = ($f.Name + '|' + $f.Length)
            if (-not $dupAgg.ContainsKey($ckey)) {
                $dupAgg[$ckey] = New-Object System.Collections.ArrayList
            }
            [void]$dupAgg[$ckey].Add($full)
        }
        catch {
            $tErrorCount++
            [void]$errors.Add([PSCustomObject]@{
                TargetId = $t.id
                Path     = $f.FullName
                Message  = $_.Exception.Message
            })
        }
    }

    # target 単位で書き出してメモリを解放する
    if ($records.Count -gt 0) {
        if ($inventoryHeaderWritten) {
            $records | Export-Csv -LiteralPath $inventoryCsv -Encoding UTF8 -NoTypeInformation -Append
        }
        else {
            $records | Export-Csv -LiteralPath $inventoryCsv -Encoding UTF8 -NoTypeInformation
            $inventoryHeaderWritten = $true
        }
    }
    $records.Clear()

    $elapsed = ((Get-Date) - $tStart).TotalSeconds
    $totalFiles += $tFiles
    $totalBytes += $tBytes

    [void]$targetSummary.Add([PSCustomObject]@{
        TargetId       = $t.id
        Path           = $t.path
        Reachable      = $true
        FileCount      = $tFiles
        TotalSizeBytes = $tBytes
        ElapsedSeconds = [math]::Round($elapsed, 1)
        ErrorCount     = $tErrorCount
    })

    Write-Host ("[完了] {0}  {1:N0} 件 / {2:N1} MB / {3:N1} 秒 / エラー {4} 件" -f `
        $t.id, $tFiles, ($tBytes / 1MB), $elapsed, $tErrorCount) -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 集計ファイルの出力
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '集計を書き出しています...' -ForegroundColor Cyan

# first-seen.csv
$firstSeenRows = foreach ($k in $dirAgg.Keys) {
    $a = $dirAgg[$k]
    [PSCustomObject]@{
        TargetId       = $a.TargetId
        Directory      = $a.Directory
        FileCount      = $a.FileCount
        TotalSizeBytes = $a.TotalSizeBytes
        FirstSeenAt    = $a.FirstSeenAt
        SystemTags     = (($a.SystemTags)    -join ';')
        EquipmentTags  = (($a.EquipmentTags) -join ';')
    }
}
if ($firstSeenRows) {
    $firstSeenRows | Sort-Object TargetId, Directory |
        Export-Csv -LiteralPath $firstSeenCsv -Encoding UTF8 -NoTypeInformation
}

# duplicates.csv
$dupRows = foreach ($k in $dupAgg.Keys) {
    $paths = $dupAgg[$k]
    if ($paths.Count -ge 2) {
        $parts = $k -split '\|'
        [PSCustomObject]@{
            Name      = $parts[0]
            SizeBytes = $parts[1]
            Count     = $paths.Count
            Paths     = ($paths -join '|')
        }
    }
}
if ($dupRows) {
    $dupRows | Sort-Object -Property Count -Descending |
        Export-Csv -LiteralPath $duplicateCsv -Encoding UTF8 -NoTypeInformation
}

# targets-summary.csv / errors.csv
$targetSummary | Export-Csv -LiteralPath $summaryCsv -Encoding UTF8 -NoTypeInformation
if ($errors.Count -gt 0) {
    $errors | Export-Csv -LiteralPath $errorCsv -Encoding UTF8 -NoTypeInformation
}

# summary.md
$dupCount   = if ($dupRows) { @($dupRows).Count } else { 0 }
$dirCount   = $dirAgg.Keys.Count
$scanEnded  = Get-Date
$totalSecs  = [math]::Round(($scanEnded - $scanStartedAt).TotalSeconds, 1)

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('# ファイル台帳 収集結果')
[void]$sb.AppendLine('')
[void]$sb.AppendLine(('- 実行日時: ' + $scanStartedAt.ToString('yyyy-MM-dd HH:mm:ss') + ' 〜 ' + $scanEnded.ToString('HH:mm:ss') + ' (' + $totalSecs + ' 秒)'))
[void]$sb.AppendLine(('- 設定ファイル: `' + $ConfigPath + '`'))
[void]$sb.AppendLine(('- 出力先: `' + $scanDir + '`'))
[void]$sb.AppendLine('')
[void]$sb.AppendLine('**本文は読んでいない。メタデータのみ。ハッシュ計算もしていない。**')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## 全体')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('| 項目 | 値 |')
[void]$sb.AppendLine('|---|---:|')
[void]$sb.AppendLine(('| ファイル件数 | ' + ('{0:N0}' -f $totalFiles) + ' |'))
[void]$sb.AppendLine(('| 合計容量 | ' + ('{0:N1}' -f ($totalBytes / 1GB)) + ' GB |'))
[void]$sb.AppendLine(('| ディレクトリ件数 | ' + ('{0:N0}' -f $dirCount) + ' |'))
[void]$sb.AppendLine(('| 重複候補（名前+サイズ一致） | ' + ('{0:N0}' -f $dupCount) + ' 組 |'))
[void]$sb.AppendLine(('| 機微判定ファイル | ' + ('{0:N0}' -f $sensitiveCount) + ' 件 |'))
[void]$sb.AppendLine(('| エラー | ' + ('{0:N0}' -f $errors.Count) + ' 件 |'))
[void]$sb.AppendLine('')
[void]$sb.AppendLine('機微判定ファイルは**所在のみ記録**し、名前をこの要約に書かない。')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## 対象別')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('| Target | 到達 | 件数 | 容量(MB) | 秒 | エラー |')
[void]$sb.AppendLine('|---|---|---:|---:|---:|---:|')
foreach ($s in $targetSummary) {
    [void]$sb.AppendLine(('| ' + $s.TargetId + ' | ' + $(if ($s.Reachable) { 'OK' } else { '**NG**' }) + ' | ' + `
        ('{0:N0}' -f $s.FileCount) + ' | ' + ('{0:N1}' -f ($s.TotalSizeBytes / 1MB)) + ' | ' + `
        $s.ElapsedSeconds + ' | ' + $s.ErrorCount + ' |'))
}
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## カテゴリ別')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('| カテゴリ | 件数 |')
[void]$sb.AppendLine('|---|---:|')
foreach ($k in ($categoryCount.Keys | Sort-Object { $categoryCount[$_] } -Descending)) {
    [void]$sb.AppendLine(('| ' + $k + ' | ' + ('{0:N0}' -f $categoryCount[$k]) + ' |'))
}
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## システムタグ別')
[void]$sb.AppendLine('')
if ($systemCount.Keys.Count -eq 0) {
    [void]$sb.AppendLine('該当なし。')
}
else {
    [void]$sb.AppendLine('| タグ | 件数 |')
    [void]$sb.AppendLine('|---|---:|')
    foreach ($k in ($systemCount.Keys | Sort-Object { $systemCount[$_] } -Descending)) {
        [void]$sb.AppendLine(('| ' + $k + ' | ' + ('{0:N0}' -f $systemCount[$k]) + ' |'))
    }
}
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## 次にやること')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('1. `targets-summary.csv` で到達できなかった対象を確認する。')
[void]$sb.AppendLine('2. `duplicates.csv` で正本候補を絞る（**名前とサイズが同じだけで、中身の一致は未確認**）。')
[void]$sb.AppendLine('3. `first-seen.csv` のタグ付きディレクトリから、関係マップへ反映する対象を選ぶ。')
[void]$sb.AppendLine('4. 絞り込んだ画像のみ `extract-ocr-text.ps1` に渡す。')

[System.IO.File]::WriteAllText($summaryMd, $sb.ToString(), (New-Object System.Text.UTF8Encoding $true))

# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '=== 完了 ===' -ForegroundColor Cyan
Write-Host ("ファイル件数 : {0:N0}" -f $totalFiles)
Write-Host ("合計容量     : {0:N1} GB" -f ($totalBytes / 1GB))
Write-Host ("機微判定     : {0:N0} 件（所在のみ記録）" -f $sensitiveCount)
Write-Host ("エラー       : {0:N0} 件" -f $errors.Count)
Write-Host ("出力先       : {0}" -f $scanDir)
Write-Host ''
