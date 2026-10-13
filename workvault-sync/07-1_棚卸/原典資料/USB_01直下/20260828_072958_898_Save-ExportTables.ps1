# Save-ExportTables.ps1
# 指定された接続先／テーブル一覧で複数テーブルを個別CSVに出力します。
# 実行前にスクリプト内の設定が正しいか確認してください。

# 接続設定（編集済み）
$server   = "EGPROSRV1"
$database = "EGProKOHDEN-Warehouse"
$authType = "Windows"   # Windows / SQL
$user     = ""          # SQL認証時のみ使用
$password = ""          # SQL認証時のみ使用

# 出力設定（編集済み）
$outDir   = "C:\Users\Administrator\Videos"
$tables = @(
  "dbo.T_在庫データ",
  "dbo.T_PanaCIM連携",
  "dbo.T_在庫ログ",
  "dbo.T_実棚卸データ",
  "dbo.T_棚卸原票データ",
  "dbo.T_棚卸制御",
  "dbo.W_在庫ログ",
  "dbo.W_棚卸用在庫ログ",
  "dbo.LOG_棚卸",
  "dbo.LOG_廃棄",
  "dbo.LOG_ロケーション移動",
  "dbo.LOG_出庫",
  "dbo.LOG_棚登録",
  "dbo.LOG_入庫",
  "dbo.T_作業ロス数"
)
$encoding = "UTF8"      # UTF-8（必要なら "Default" に変更して Shift-JIS 相当に）

# 注意: 初回実行前に Invoke-Sqlcmd (SqlServer モジュール) が利用可能か確認してください。
# モジュールがなければ PowerShell 管理者権限で次を実行して取得できます:
# Install-Module -Name SqlServer -Scope CurrentUser -Force

# フォルダ作成
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

function Quote-Ident([string]$name) {
  "[" + ($name -replace "]", "]]") + "]"
}
function Split-SchemaTable([string]$st) {
  $parts = $st.Split('.',2)
  if ($parts.Count -eq 2) { @{ Schema=$parts[0].Trim('[]'); Table=$parts[1].Trim('[]') } }
  else { @{ Schema="dbo"; Table=$parts[0].Trim('[]') } }
}
function Invoke-DbQuery([string]$query) {
  if ($authType -eq "Windows") {
    Invoke-Sqlcmd -ServerInstance $server -Database $database -Query $query -ErrorAction Stop
  } else {
    Invoke-Sqlcmd -ServerInstance $server -Database $database -Username $user -Password $password -Query $query -ErrorAction Stop
  }
}
function Export-TableToCsv([string]$tableName, [string]$outFile) {
  $st = Split-SchemaTable $tableName
  $qn = (Quote-Ident $st.Schema) + "." + (Quote-Ident $st.Table)

  Write-Host "Exporting $qn -> $outFile"
  try {
    $rows = Invoke-DbQuery "SELECT * FROM $qn"
    if ($rows -and $rows.Count -gt 0) {
      $rows | Export-Csv -Path $outFile -NoTypeInformation -Encoding $encoding
    } else {
      # 行が0件でもヘッダだけを出力
      $schemaLit = $st.Schema.Replace("'","''")
      $tableLit  = $st.Table.Replace("'","''")
      $colQuery = @"
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '$schemaLit' AND TABLE_NAME = '$tableLit'
ORDER BY ORDINAL_POSITION
"@
      $cols = Invoke-DbQuery $colQuery | Select-Object -ExpandProperty COLUMN_NAME
      $header = ($cols -join ",")
      Set-Content -Path $outFile -Value $header -Encoding $encoding
    }
    Write-Host "OK: $qn"
  } catch {
    Write-Host "Error exporting $qn : $($_.Exception.Message)" -ForegroundColor Red
  }
}

foreach ($t in $tables) {
  $safe = ($t -replace '[\\/:*?"<>| ]','_')
  $outFile = Join-Path $outDir ("$safe.csv")
  Export-TableToCsv -tableName $t -outFile $outFile
}
Write-Host "All done."
