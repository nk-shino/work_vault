# 回帰テストハーネス — LNB Collector v6.5-review (環境A/作業用PC専用)
# 本ファイルは配布物に含めない。本番USBには配置しないこと。
$ErrorActionPreference = 'Stop'
$script:Root = 'C:\Users\ss80751\AppData\Local\Temp\kohden-code\LNB_Collector_v6.5-review'
$ScriptPath = Join-Path $script:Root 'Collect_LNB.ps1'

$results = New-Object System.Collections.Generic.List[object]
function Test-Case([string]$Name, [scriptblock]$Body) {
    $ok = $false; $detail = ''
    try { $r = & $Body; if ($r -is [bool]) { $ok = $r } elseif ($null -ne $r) { $ok = $true }; $detail = if ($r -is [bool]) { '' } else { [string]$r } }
    catch { $detail = 'THREW: ' + $_.Exception.Message }
    $script:results.Add([pscustomobject]@{ Name = $Name; Passed = $ok; Detail = $detail })
}
function Assert-Throws([scriptblock]$Body) {
    try { & $Body | Out-Null; return $false } catch { return $true }
}

# ---- Collect_LNB.ps1 から対象関数を AST で抽出してロード(副作用なく) ----
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($ScriptPath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw "Source has parse errors: $($errors[0].Message)" }
$wanted = @('Safe','Suspicious','DocPath','MruPath','CsvText','PathHasReparse','EnsureSafeDir','GetUsbIdentity','ValidateDependency','MakeTable','Sheets')
$funcAsts = $ast.FindAll({ param($a) $a -is [Management.Automation.Language.FunctionDefinitionAst] -and $wanted -contains $a.Name }, $true)
$loader = New-Object System.Collections.Generic.List[string]
foreach ($f in $funcAsts) { $loader.Add($f.Extent.Text) }
# Sheets 定義(ordered hashtable)と Utf8File/WriteAllTextVerified/VerifyUsb/AssertOnUsb の必要部分
$sheetAssign = $ast.FindAll({ param($a) $a -is [Management.Automation.Language.AssignmentStatementAst] -and $a.Left.Extent.Text -eq '$Sheets' }, $true) | Select-Object -First 1
if ($sheetAssign) { $loader.Add($sheetAssign.Extent.Text) }
foreach ($fn in @('Utf8File','WriteAllTextVerified','AssertOnUsb')) {
    $fa = $ast.FindAll({ param($a) $a -is [Management.Automation.Language.FunctionDefinitionAst] -and $a.Name -eq $fn }, $true) | Select-Object -First 1
    if ($fa) { $loader.Add($fa.Extent.Text) }
}
# 検証用スタブ: VerifyUsb (疑似USBとして $script:Root を返す)
$stub = @'
function VerifyUsb { $script:Root = 'X:\'; $script:UsbSerial = 'TESTSERIAL / VOL1234'; if (-not (Test-Path -LiteralPath (Join-Path $script:Root 'LNB_USB_ID.txt'))) { throw 'USB marker missing' } }
'@
$loader.Add($stub)
$init = '$script:Out = $null; $script:RegistrationGuid = $null; $Version="6.5-review"'
$block = ($init + "`n" + ($loader -join "`n"))
Invoke-Expression $block

# ---- 準備: 疑似USBルート(substドライブ X: = 一時フォルダ) ----
$usbRoot = 'X:\'
if (Test-Path 'X:\data') { Remove-Item -Recurse -Force 'X:\data' }
if (Test-Path 'X:\LNB_USB_ID.txt') { Remove-Item -Force 'X:\LNB_USB_ID.txt' }
Set-Content -LiteralPath (Join-Path $usbRoot 'LNB_USB_ID.txt') -Value "LNB-USB-ID-v1`r`nRegistrationGuid=11111111-2222-3333-4444-555555555555`r`nDiskSerial=TESTSERIAL`r`nVolumeSerial=VOL1234`r`nRootMarker=6.5-review`r`n" -Encoding ASCII
$script:Root = $usbRoot

Write-Host '=== T-3 CSV/安全化ユーティリティ回帰 ==='
Test-Case 'T3-01 Safe: null -> empty' { (Safe $null) -ceq '' }
Test-Case 'T3-02 Safe: 改行/タブ除去' { (Safe "a`tb`nc") -ceq 'a b c' }
Test-Case 'T3-03 Safe: 式注入 =cmd 防御' { (Safe '=cmd|'' /C calc''!A0') -ceq "'=cmd|' /C calc'!A0" }
Test-Case 'T3-04 Safe: @x 防御' { (Safe '@SUM(1)') -ceq "'@SUM(1)" }
Test-Case 'T3-05 Safe: +1/-1 防御' { ((Safe '+1') -ceq "'+1") -and ((Safe '-1') -ceq "'-1") }
Test-Case 'T3-06 Safe: 通常文字列は無変更' { (Safe 'C:\D\a.xlsx') -ceq 'C:\D\a.xlsx' }
Test-Case 'T3-07 MruPath: [F][T]* プレフィックス抽出' { (MruPath '[F0000001][T01ABCDEF]*C:\Labels\a.xlsx') -ceq 'C:\Labels\a.xlsx' }
Test-Case 'T3-08 MruPath: 角括弧ファイル名(運用: ラベルxlsx)' { (MruPath '*C:\Labels\a[1].xlsx') -ceq 'C:\Labels\a[1].xlsx' }
Test-Case 'T3-09 MruPath: URL は null' { $null -eq (MruPath 'https://host/a.xlsx') }
Test-Case 'T3-10 DocPath: UNC xlsx 許容' { (DocPath '\\nksv569\share\a.xlsx') }
Test-Case 'T3-11 DocPath: ADS 拒否' { -not (DocPath 'C:\a.txt:stream.xlsx') }
Test-Case 'T3-12 DocPath: 機微名称拒否(password)' { -not (DocPath 'C:\password.xlsx') }
Test-Case 'T3-13 Suspicious: bearer/token 検出' { (Suspicious 'Bearer abc123') -and (Suspicious 'api_key=x') }
Test-Case 'T3-14 CsvText: 空行でもヘッダー保持' { (CsvText @() @('Name','Path')).Trim() -ceq '"Name","Path"' }
Test-Case 'T3-15 CsvText: 値のクォート/注入防御が存続' { $rows = @([pscustomobject]@{ Name = (Safe '=1'); Path = 'a,b' }); $csv = CsvText $rows @('Name','Path'); $parsed = @($csv | ConvertFrom-Csv); ($parsed.Count -eq 1) -and ($parsed[0].Name -ceq "'=1") -and ($parsed[0].Path -ceq 'a,b') }

Write-Host '=== T-4 出力サブシステム回帰(疑似USBルート) ==='
Test-Case 'T4-01 EnsureSafeDir: 正常一段ずつ作成' { $p = Join-Path $usbRoot 'data\LNB_調査\L1_TESTPC_20261013_000000_abc'; EnsureSafeDir $p; Test-Path -LiteralPath $p -PathType Container }
Test-Case 'T4-02 PathHasReparse: ルート内はOK' { PathHasReparse (Join-Path $usbRoot 'data') $usbRoot; $true }
Test-Case 'T4-03 PathHasReparse: ルート外は拒否' { Assert-Throws { PathHasReparse 'C:\Windows\Temp' $usbRoot } }
Test-Case 'T4-04 出力内junctionは拒否(EnsureSafeDir再実行時)' { New-Item -ItemType Junction -Path (Join-Path $usbRoot 'data\LNB_調査\trap') -Target 'C:\Windows\Temp' | Out-Null; Assert-Throws { EnsureSafeDir (Join-Path $usbRoot 'data\LNB_調査\trap\sub') } }
Test-Case 'T4-05 PathHasReparse: junction検知' { Assert-Throws { PathHasReparse (Join-Path $usbRoot 'data\LNB_調査\trap') $usbRoot } }
Test-Case 'T4-06 WriteAllTextVerified: 書込+読戻し一致+BOM' { $f = Join-Path $usbRoot 'data\w.json'; WriteAllTextVerified $f '{"a":1}'; $bytes = [IO.File]::ReadAllBytes($f); ($bytes[0] -eq 0xEF) -and ($bytes[1] -eq 0xBB) -and ($bytes[2] -eq 0xBF) -and ((Get-Content $f -Raw) -ceq '{"a":1}') }
Test-Case 'T4-07 Utf8File/WriteAllTextVerified: 存在確認' { Test-Path -LiteralPath (Join-Path $usbRoot 'data\w.json') -PathType Leaf }
Test-Case 'T4-08 AssertOnUsb: USB外パス拒否' { Assert-Throws { AssertOnUsb 'C:\Users\x\out.xlsx' } }
Test-Case 'T4-09 AssertOnUsb: USB内パスOK' { AssertOnUsb (Join-Path $usbRoot 'LNB_Collector.xlsx'); $true }

Write-Host '=== T-5 USB識別ロジック ==='
Test-Case 'T5-01 GetUsbIdentity: 非ルート配置で停止' { Assert-Throws { GetUsbIdentity } }  # 作業用PCのスクリプト配置は C:\ 配下のため停止するのが正
Test-Case 'T5-02 マーカー書式(CRLF旧正規表現は退行確認として不一致を期待→v6.5修正後は\r?対応で一致)' { $text = [IO.File]::ReadAllText((Join-Path $usbRoot 'LNB_USB_ID.txt'), [Text.Encoding]::ASCII); ($text -match '(?m)^RegistrationGuid=([0-9a-fA-F-]{36})\r?$') -and ($text -match '(?m)^DiskSerial=(.+?)\r?$') -and ($text -match '(?m)^VolumeSerial=(.+?)\r?$') }
Test-Case 'T5-03 マーカー書式: RootMarker=6.5-review(CRLF許容)' { $text = [IO.File]::ReadAllText((Join-Path $usbRoot 'LNB_USB_ID.txt'), [Text.Encoding]::ASCII); $text -match '(?m)^RootMarker=6\.5-review\r?$' }

Write-Host '=== T-7 帳票構成・メタ確定値(改修#5) ==='
Test-Case 'T7-01 Sheets: 10収集シート定義' { (@($Sheets.Keys).Count -eq 10) -and (@($Sheets.Keys) -contains 'excel_recent') -and (@($Sheets.Keys) -contains 'windows_recent') }
Test-Case 'T7-02 Sheets: 列数合計とexcel_recent列' { ($Sheets['excel_recent'] -join ',') -ceq 'OfficeVersion,Path,Source,TimeMeaning' }
Test-Case 'T7-03 MakeTable: 空行でヘッダーのみDataTable' { $dt = MakeTable 't' @() @('A','B'); ($dt.Columns.Count -eq 2) -and ($dt.Rows.Count -eq 0) -and ($dt.TableName -ceq 't') }
Test-Case 'T7-04 MakeTable: 値の文字列化と Safe 済み前提' { $dt = MakeTable 't2' @([pscustomobject]@{ A = 'x'; B = 123 }) @('A','B'); ([string]$dt.Rows[0]['B']) -ceq '123' }

Write-Host ''
$failed = @($script:results | Where-Object { -not $_.Passed })
foreach ($r in $script:results) { $mark = if ($r.Passed) { 'PASS' } else { 'FAIL' }; Write-Host ("[$mark] " + $r.Name + $(if ($r.Detail) { ' -- ' + $r.Detail })) }
Write-Host ("TOTAL: " + $script:results.Count + " / FAIL: " + $failed.Count)
if ($failed.Count) { exit 1 } else { exit 0 }

Write-Host '=== T-7 帳票構成・メタ確定値(改修#5) ==='
Test-Case 'T7-01 Sheets: 10収集シート定義' { (@($Sheets.Keys).Count -eq 10) -and (@($Sheets.Keys) -contains 'excel_recent') -and (@($Sheets.Keys) -contains 'windows_recent') }
Test-Case 'T7-02 Sheets: 列数合計とexcel_recent列' { ($Sheets['excel_recent'] -join ',') -ceq 'OfficeVersion,Path,Source,TimeMeaning' }
Test-Case 'T7-03 MakeTable: 空行でヘッダーのみDataTable' { $dt = MakeTable 't' @() @('A','B'); ($dt.Columns.Count -eq 2) -and ($dt.Rows.Count -eq 0) -and ($dt.TableName -ceq 't') }
Test-Case 'T7-04 MakeTable: 値の文字列化と Safe 済み前提' { $dt = MakeTable 't2' @([pscustomobject]@{ A = 'x'; B = 123 }) @('A','B'); ([string]$dt.Rows[0]['B']) -ceq '123' }

Write-Host ''
$failed = @($script:results | Where-Object { -not $_.Passed })
foreach ($r in $script:results) { $mark = if ($r.Passed) { 'PASS' } else { 'FAIL' }; Write-Host ("[$mark] " + $r.Name + $(if ($r.Detail) { ' -- ' + $r.Detail })) }
Write-Host ("TOTAL: " + $script:results.Count + " / FAIL: " + $failed.Count)
if ($failed.Count) { exit 1 } else { exit 0 }
Write-Host '=== T-7 帳票構成・メタ確定値(改修#5) ==='
Test-Case 'T7-01 Sheets: 10収集シート定義' { (@($Sheets.Keys).Count -eq 10) -and (@($Sheets.Keys) -contains 'excel_recent') -and (@($Sheets.Keys) -contains 'windows_recent') }
Test-Case 'T7-02 Sheets: 列数合計とexcel_recent列' { ($Sheets['excel_recent'] -join ',') -ceq 'OfficeVersion,Path,Source,TimeMeaning' }
Test-Case 'T7-03 MakeTable: 空行でヘッダーのみDataTable' { $dt = MakeTable 't' @() @('A','B'); ($dt.Columns.Count -eq 2) -and ($dt.Rows.Count -eq 0) -and ($dt.TableName -ceq 't') }
Test-Case 'T7-04 MakeTable: 値の文字列化と Safe 済み前提' { $dt = MakeTable 't2' @([pscustomobject]@{ A = 'x'; B = 123 }) @('A','B'); ([string]$dt.Rows[0]['B']) -ceq '123' }

Write-Host ''
$failed = @($script:results | Where-Object { -not $_.Passed })
foreach ($r in $script:results) { $mark = if ($r.Passed) { 'PASS' } else { 'FAIL' }; Write-Host ("[$mark] " + $r.Name + $(if ($r.Detail) { ' -- ' + $r.Detail })) }
Write-Host ("TOTAL: " + $script:results.Count + " / FAIL: " + $failed.Count)
if ($failed.Count) { exit 1 } else { exit 0 }
