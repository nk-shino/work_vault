# 用語集アプリの検証を1コマンドで回すランナー。
# 実行: powershell -NoProfile -ExecutionPolicy Bypass -File run-verify.ps1 [-KeepData] [-Pytest]
#   既定      : 検証 DB を作り直し、サーバーを再起動し、登録→取込→操作→状態確認→キュー操作まで回す
#   -KeepData : DB を残したまま operate 以降だけ回す
#   -Pytest   : pytest / ruff / mypy も続けて回す
# 検証スクリプトは verify-all.cjs（ブラウザ操作4本 + import のドライバ）。失敗時は非ゼロで終わる。
param(
  [switch]$KeepData,
  [switch]$Pytest
)
$ErrorActionPreference = 'Stop'
$App = 'C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\06_Tools\用語集アプリ'
$P2 = 'C:\Users\ss80751\AppData\Local\Temp\kohden-code\glossary-deai\p2'
$Db = Join-Path $P2 'verify.db'
$Port = 8000

# 1. 既存サーバーを止める。ポートをつかんでいる PID を特定して、その PID だけを止める
$conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($conn) {
  Stop-Process -Id ($conn.OwningProcess | Select-Object -First 1)
  Start-Sleep -Seconds 1
  Write-Output '== 既存サーバーを停止 =='
}

# 2. 既定は DB を作り直す（登録と取込から全部やり直す）
if (-not $KeepData -and (Test-Path $Db)) {
  Remove-Item $Db
  Write-Output '== 検証 DB を作り直し =='
}

# 3. サーバー起動。起動スクリプト自身が /terms の応答まで待つ
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'start-glossary-server-p2.ps1')
$probe = Invoke-WebRequest -Uri ('http://127.0.0.1:{0}/terms' -f $Port) -UseBasicParsing -TimeoutSec 5
if ($probe.StatusCode -ne 200) { throw 'サーバーが起動していません' }
Write-Output '== サーバー起動 =='

# 4. 検証ループ（ブラウザ操作4本 + import）
& node (Join-Path $PSScriptRoot 'verify-all.cjs') 'p2' $(if ($KeepData) { 'keep' })
if ($LASTEXITCODE -ne 0) { throw ('検証ループが失敗しました（exit={0}）。ログの ok: false を確認すること' -f $LASTEXITCODE) }

# 5. -Pytest でテストと静的検査も回す
if ($Pytest) {
  Push-Location $App
  try {
    & (Join-Path $App '.venv\Scripts\python.exe') -m pytest tests/ -p no:warnings -q
    if ($LASTEXITCODE -ne 0) { throw 'pytest が失敗しました' }
    & (Join-Path $App '.venv\Scripts\python.exe') -m ruff check src tests
    if ($LASTEXITCODE -ne 0) { throw 'ruff が失敗しました' }
    & (Join-Path $App '.venv\Scripts\python.exe') -m mypy src
    if ($LASTEXITCODE -ne 0) { throw 'mypy が失敗しました' }
    Write-Output '== pytest / ruff / mypy 合格 =='
  } finally { Pop-Location }
}
Write-Output '== 検証ランナー完了 =='
