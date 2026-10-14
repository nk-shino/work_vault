#Requires -Version 5.1
# ============================================================================
#  extract-ocr-text.ps1  -  台帳 inventory.csv から画像だけを OCR してテキスト化
# ----------------------------------------------------------------------------
#  【完全ローカル処理・外部送信なし】
#    OCR は Windows 標準の WinRT OCR (Windows.Media.Ocr) のみを使用する。
#    Tesseract / ImageMagick / Poppler / クラウド OCR 等は使わない。
#    画像・抽出テキスト・その他のいかなるデータも外部へ送信しない。
#  【入力元へ書き込まない】
#    inventory.csv / 画像ファイルは読み取り専用。一切変更しない。
#    出力は -OutputRoot 配下 (ocr_yyyyMMdd_HHmmss) にのみ書き込む。
#  【PDF 非対応】
#    Poppler 等が未導入のため PDF は OCR できない。
#    skipped.csv に reason=pdf-not-supported で一覧化するのみ。
#    Office 埋め込み画像も非対応 (reason=office-embedded-not-supported)。
# ============================================================================
<#
.SYNOPSIS
    台帳 inventory.csv を入力に、画像ファイルだけを OCR して日本語テキストを抽出する。

.DESCRIPTION
    Windows 標準の WinRT OCR (Windows.Media.Ocr.OcrEngine) を PowerShell 5.1 から
    呼び出して、対象画像を 1 件ずつ OCR する (完全ローカル処理・外部送信なし)。

    除外ルール (skipped.csv に記録し本文は出力しない):
      - config の sensitiveNamePatterns がパスに部分一致 -> reason=sensitive-path
      - Sensitive 列が true                              -> reason=sensitive-path
      - PDF (.pdf)                                       -> reason=pdf-not-supported
      - Office 形式                                      -> reason=office-embedded-not-supported
      - 対象外の拡張子                                   -> reason=unsupported-extension
      - MinSizeBytes 未満の画像                          -> reason=too-small

    マスクルール:
      OCR 本文の行が機微キーワードを含む場合、その行全体を [REDACTED] に置換し
      redactions.csv に記録する (マスク対象の本文は書かない)。

    config について:
      使用するキーは sensitiveNamePatterns のみ。
      outputRoot は台帳スクリプト (_inventory) 向けの設定のため本スクリプトでは
      使用しない (OCR 出力の既定は _ocr)。

.PARAMETER InventoryCsv
    台帳スクリプトが出した inventory.csv のパス (必須)。

.PARAMETER OutputRoot
    出力ルート。既定: Work_Vault 08_サーバー_nksv523\_ocr

.PARAMETER ConfigPath
    sensitiveNamePatterns を読む config のパス。

.PARAMETER MaxFiles
    動作確認用の件数制限。0 = 無制限。

.PARAMETER MinSizeBytes
    これ未満の画像はアイコン等とみなし reason=too-small でスキップ。

.PARAMETER Filter
    フルパスに対する部分一致 (大文字小文字を区別しない) で対象を絞る。

.EXAMPLE
    .\extract-ocr-text.ps1 -InventoryCsv C:\work\inventory.csv

.EXAMPLE
    .\extract-ocr-text.ps1 -InventoryCsv C:\work\inventory.csv -MaxFiles 5 -MinSizeBytes 0
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InventoryCsv,

    [string]$OutputRoot = 'C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\08_サーバー_nksv523\_ocr',

    [string]$ConfigPath = 'C:\Users\ss80751\kohden-code-workspace\scripts\config\inventory-targets.json',

    [ValidateRange(0, [int]::MaxValue)]
    [int]$MaxFiles = 0,

    [ValidateRange(0, [long]::MaxValue)]
    [long]$MinSizeBytes = 10240,

    [string]$Filter = ''
)

$ErrorActionPreference = 'Stop'

# ============================================================================
# 定数
# ============================================================================

# OCR 対象の画像拡張子
$imageExtensions = @('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff')

# Office 埋め込み画像を含みうる形式 (今回は対象外。一覧化のみ)
$officeExtensions = @('.doc', '.docx', '.xls', '.xlsx', '.xlsm', '.xlsb', '.ppt', '.pptx')

# OCR 本文のマスク対象キーワード (部分一致・大文字小文字を区別しない)
$bodyKeywords = @(
    'パスワード', 'ﾊﾟｽﾜｰﾄﾞ', 'password', 'passwd', 'pwd',
    '認証', 'token', 'api_key', 'apikey',
    '秘密鍵', 'マイナンバー', '個人番号'
)

# ============================================================================
# WinRT 非同期ヘルパー (PowerShell 5.1 用・自前実装)
# ============================================================================

# WinRT 型をロードし、IAsyncOperation`1 を Task 化する AsTask をリフレクションで取得する
function Initialize-WinRtTypes {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime

    $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Globalization.Language, Windows.Foundation, ContentType=WindowsRuntime]

    $script:AsTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object {
            $_.Name -eq 'AsTask' -and
            $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        } |
        Select-Object -First 1

    if (-not $script:AsTaskGeneric) {
        throw 'WindowsRuntimeSystemExtensions.AsTask(IAsyncOperation`1) が見つかりませんでした。'
    }
}

# IAsyncOperation を同期待ちして結果を返す
function Invoke-WinRtAwait {
    param(
        [Parameter(Mandatory = $true)]$AsyncOperation,
        [Parameter(Mandatory = $true)][type]$ResultType
    )
    $asTask = $script:AsTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($AsyncOperation))
    try {
        $netTask.Wait(-1) | Out-Null
    }
    catch [System.AggregateException] {
        # WinRT 非同期の失敗は AggregateException に包まれるため中身を投げ直す
        throw $_.Exception.InnerException
    }
    return $netTask.Result
}

# OCR エンジン生成: ja で作成し、不可ならユーザープロファイル言語へフォールバック
function Initialize-OcrEngine {
    $engine = $null
    $usedLanguage = ''

    try {
        $ja = New-Object -TypeName 'Windows.Globalization.Language' -ArgumentList 'ja'
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($ja)
        if ($engine) { $usedLanguage = 'ja' }
    }
    catch {
        Write-Verbose "TryCreateFromLanguage(ja) 失敗: $($_.Exception.Message)"
    }

    if (-not $engine) {
        Write-Verbose 'ユーザープロファイル言語へフォールバック'
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
        if ($engine) { $usedLanguage = [string]$engine.RecognizerLanguage.LanguageTag }
    }

    if (-not $engine) {
        throw 'WinRT OCR エンジンを作成できませんでした (ja もユーザープロファイル言語も不可)。言語パックのインストールを確認してください。'
    }

    return [pscustomobject]@{ Engine = $engine; Language = $usedLanguage }
}

# 画像ファイルを読み込み BitmapDecoder で SoftwareBitmap にする
# 注: StorageFile::OpenAsync が返す汎用インターフェース (IRandomAccessStreamWithContentType)
#     は PowerShell 5.1 では型付けされず AsTask に渡せないため、.NET で読んだバイト列を
#     AsRandomAccessStream で WinRT ストリーム化して BitmapDecoder に渡す。
function Get-SoftwareBitmapFromPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $netStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $wrStream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($netStream)
        $decoder = Invoke-WinRtAwait -AsyncOperation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($wrStream)) -ResultType ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Invoke-WinRtAwait -AsyncOperation ($decoder.GetSoftwareBitmapAsync()) -ResultType ([Windows.Graphics.Imaging.SoftwareBitmap])
        return $bitmap
    }
    finally {
        $netStream.Dispose()
    }
}

# ============================================================================
# 準備
# ============================================================================

# 入力 CSV の存在確認
if (-not (Test-Path -LiteralPath $InventoryCsv -PathType Leaf)) {
    throw "入力 CSV が見つかりません: $InventoryCsv"
}

# config 読み込み (使用するのは sensitiveNamePatterns のみ)
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "設定ファイルが見つかりません: $ConfigPath"
}
$config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$sensitivePatterns = @()
if ($config.sensitiveNamePatterns) {
    $sensitivePatterns = @($config.sensitiveNamePatterns)
}
Write-Host ("config sensitiveNamePatterns: {0} 件" -f $sensitivePatterns.Count)

# WinRT / OCR エンジン初期化
Initialize-WinRtTypes
$ocr = Initialize-OcrEngine
Write-Host ("WinRT OCR エンジン: 言語 = {0}" -f $ocr.Language)

# 出力フォルダ (実行ごとにタイムスタンプ付きサブフォルダ)
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runRoot = Join-Path $OutputRoot ("ocr_{0}" -f $stamp)
$textDir = Join-Path $runRoot 'text'
foreach ($dir in @($runRoot, $textDir)) {
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# 台帳読み込み
$rows = @(Import-Csv -LiteralPath $InventoryCsv -Encoding UTF8)
Write-Host ("台帳行数: {0}" -f $rows.Count)

# ============================================================================
# 事前フィルタ
# ============================================================================

$targets = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$allTargets = New-Object System.Collections.Generic.List[object]

foreach ($row in $rows) {
    $fullPath = [string]$row.FullPath
    $ext = ('.' + ([string]$row.Extension).TrimStart('.').ToLowerInvariant())
    if ([string]::IsNullOrWhiteSpace($ext) -or $ext -eq '.') {
        $ext = [System.IO.Path]::GetExtension($fullPath).ToLowerInvariant()
    }
    $size = 0L
    [void][long]::TryParse([string]$row.SizeBytes, [ref]$size)
    $sensitive = ('' + $row.Sensitive).Trim().ToLowerInvariant() -eq 'true'

    # 機微パス (config パターン部分一致 / Sensitive 列) は最優先で除外
    if ($sensitive) {
        $skipped.Add([pscustomobject]@{ SourcePath = $fullPath; Reason = 'sensitive-path'; SizeBytes = $size })
        continue
    }
    $hit = $sensitivePatterns | Where-Object { $fullPath.IndexOf($_, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 } | Select-Object -First 1
    if ($hit) {
        $skipped.Add([pscustomobject]@{ SourcePath = $fullPath; Reason = 'sensitive-path'; SizeBytes = $size })
        continue
    }

    # PDF は非対応
    if ($ext -eq '.pdf') {
        $skipped.Add([pscustomobject]@{ SourcePath = $fullPath; Reason = 'pdf-not-supported'; SizeBytes = $size })
        continue
    }

    # Office 埋め込み画像は非対応
    if ($officeExtensions -contains $ext) {
        $skipped.Add([pscustomobject]@{ SourcePath = $fullPath; Reason = 'office-embedded-not-supported'; SizeBytes = $size })
        continue
    }

    # 画像拡張子のみ対象
    if ($imageExtensions -notcontains $ext) {
        $skipped.Add([pscustomobject]@{ SourcePath = $fullPath; Reason = 'unsupported-extension'; SizeBytes = $size })
        continue
    }

    # アイコン等の小さい画像はスキップ
    if ($size -lt $MinSizeBytes) {
        $skipped.Add([pscustomobject]@{ SourcePath = $fullPath; Reason = 'too-small'; SizeBytes = $size })
        continue
    }

    # フィルタ指定時は部分一致のみ
    if ($Filter -and $fullPath.IndexOf($Filter, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
        continue
    }

    $targets.Add([pscustomobject]@{ FullPath = $fullPath; Extension = $ext; SizeBytes = $size })
    $allTargets.Add([pscustomobject]@{ FullPath = $fullPath; Extension = $ext; SizeBytes = $size })
}

if ($MaxFiles -gt 0 -and $targets.Count -gt $MaxFiles) {
    $targets = New-Object System.Collections.Generic.List[object]
    $targets.AddRange(@($allTargets | Select-Object -First $MaxFiles))
}

Write-Host ("OCR 対象: {0} 件 / スキップ: {1} 件" -f $targets.Count, $skipped.Count)

# ============================================================================
# OCR ループ
# ============================================================================

$indexRows    = New-Object System.Collections.Generic.List[object]
$redactionRows = New-Object System.Collections.Generic.List[object]
$errorRows    = New-Object System.Collections.Generic.List[object]
$usedBaseNames = New-Object 'System.Collections.Generic.HashSet[string]'
$seq = 0

foreach ($target in $targets) {
    $fullPath = $target.FullPath
    $seq++
    Write-Host ("[{0}/{1}] {2}" -f $seq, $targets.Count, $fullPath)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw 'ファイルが存在しません'
        }

        # 画像を開いて OCR
        $bitmap = Get-SoftwareBitmapFromPath -Path $fullPath
        try {
            $result = Invoke-WinRtAwait -AsyncOperation ($ocr.Engine.RecognizeAsync($bitmap)) -ResultType ([Windows.Media.Ocr.OcrResult])
        }
        finally {
            $bitmap.Dispose()
        }

        # 行単位でマスク処理
        $outLines = New-Object System.Collections.Generic.List[string]
        $lineNo = 0
        $redactedCount = 0
        foreach ($line in ($result.Text -split "`r?`n")) {
            $lineNo++
            $matched = $null
            foreach ($kw in $bodyKeywords) {
                if ($line.IndexOf($kw, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    $matched = $kw
                    break
                }
            }
            if ($matched) {
                $outLines.Add('[REDACTED]')
                $redactedCount++
                $redactionRows.Add([pscustomobject]@{
                    SourcePath     = $fullPath
                    LineNumber     = $lineNo
                    MatchedKeyword = $matched
                })
            }
            else {
                $outLines.Add($line)
            }
        }

        # 出力ファイル名: 連番_元ファイル名 (衝突時は _2 を付加)
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fullPath)
        $safe = ($baseName -replace '[\\/:*?"<>|]', '_').Trim()
        if (-not $safe) { $safe = 'untitled' }
        $candidate = '{0:D4}_{1}' -f $seq, $safe
        $suffix = 2
        while (-not $usedBaseNames.Add($candidate)) {
            $candidate = '{0:D4}_{1}_{2}' -f $seq, $safe, $suffix
            $suffix++
        }
        $outFile = Join-Path $textDir ($candidate + '.txt')

        $content = ($outLines -join "`r`n")
        [System.IO.File]::WriteAllText($outFile, $content, (New-Object System.Text.UTF8Encoding($true)))

        $sw.Stop()
        $charCount = ($outLines -join '').Length
        $indexRows.Add([pscustomobject]@{
            SourcePath    = $fullPath
            OutputFile    = $outFile
            CharCount     = $charCount
            LineCount     = $outLines.Count
            ElapsedMs     = $sw.ElapsedMilliseconds
            RedactedLines = $redactedCount
        })
        Write-Host ("    OK: {0} 文字 / {1} 行 ({2} ms)" -f $charCount, $outLines.Count, $sw.ElapsedMilliseconds)
    }
    catch {
        $sw.Stop()
        $msg = $_.Exception.Message
        if ($_.Exception.InnerException) { $msg = $_.Exception.InnerException.Message }
        $errorRows.Add([pscustomobject]@{ SourcePath = $fullPath; Message = $msg })
        Write-Warning ("OCR 失敗 (続行): {0} : {1}" -f $fullPath, $msg)
    }
}

# ============================================================================
# CSV / サマリ出力
# ============================================================================

$utf8 = 'UTF8'
$indexRows    | Export-Csv -LiteralPath (Join-Path $runRoot 'index.csv')    -Encoding $utf8 -NoTypeInformation
$skipped      | Export-Csv -LiteralPath (Join-Path $runRoot 'skipped.csv')  -Encoding $utf8 -NoTypeInformation
$redactionRows | Export-Csv -LiteralPath (Join-Path $runRoot 'redactions.csv') -Encoding $utf8 -NoTypeInformation
$errorRows    | Export-Csv -LiteralPath (Join-Path $runRoot 'errors.csv')   -Encoding $utf8 -NoTypeInformation

# 空リストの Export-Csv は空ファイル (ヘッダなし) になるためヘッダのみを書く
if ($indexRows.Count -eq 0) {
    Set-Content -LiteralPath (Join-Path $runRoot 'index.csv') -Value 'SourcePath,OutputFile,CharCount,LineCount,ElapsedMs,RedactedLines' -Encoding $utf8
}
if ($skipped.Count -eq 0) {
    Set-Content -LiteralPath (Join-Path $runRoot 'skipped.csv') -Value 'SourcePath,Reason,SizeBytes' -Encoding $utf8
}
if ($redactionRows.Count -eq 0) {
    Set-Content -LiteralPath (Join-Path $runRoot 'redactions.csv') -Value 'SourcePath,LineNumber,MatchedKeyword' -Encoding $utf8
}
if ($errorRows.Count -eq 0) {
    Set-Content -LiteralPath (Join-Path $runRoot 'errors.csv') -Value 'SourcePath,Message' -Encoding $utf8
}

$reasonGroups = @($skipped | Group-Object -Property Reason | Sort-Object Name)
$skipSummary = ($reasonGroups | ForEach-Object { '{0}: {1} 件' -f $_.Name, $_.Count }) -join ' / '
if (-not $skipSummary) { $skipSummary = 'なし' }
$totalRedacted = $redactionRows.Count

$summary = @"
# OCR 抽出結果サマリ

- 実行日時: {0}
- 入力CSV: {1}
- 台帳行数: {2} 行
- 対象件数: {3} 件 (OCR 実行)
- 成功件数: {4} 件
- スキップ件数: {5} 件 ({6})
- エラー件数: {7} 件
- マスク行数: {8} 行
- 出力先: {9}
- OCR 言語: {10}

## 備考
- 完全ローカル処理・外部送信なし (WinRT OCR のみ使用)
- 入力元 (台帳 CSV・画像) には書き込んでいない
- PDF は Poppler 未導入のため非対応 (skipped.csv に reason=pdf-not-supported で一覧化)
- Office 埋め込み画像は非対応 (reason=office-embedded-not-supported)
- 機微キーワードを含む行は [REDACTED] に置換済み (内容は redactions.csv にも記録しない)
"@ -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $InventoryCsv, $rows.Count, $targets.Count, $indexRows.Count, $skipped.Count, $skipSummary, $errorRows.Count, $totalRedacted, $runRoot, $ocr.Language

[System.IO.File]::WriteAllText((Join-Path $runRoot 'summary.md'), $summary, (New-Object System.Text.UTF8Encoding($true)))

Write-Host ''
Write-Host ("完了: 成功 {0} / スキップ {1} / エラー {2} / マスク {3} 行" -f $indexRows.Count, $skipped.Count, $errorRows.Count, $totalRedacted)
Write-Host ("出力先: {0}" -f $runRoot)
