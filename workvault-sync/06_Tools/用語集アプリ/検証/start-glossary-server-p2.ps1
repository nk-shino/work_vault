$ErrorActionPreference = 'Stop'
$root = 'C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\06_Tools\用語集アプリ'
$py = Join-Path $root '.venv\Scripts\python.exe'
$dbdir = 'C:\Users\ss80751\AppData\Local\Temp\kohden-code\glossary-deai\p2'
New-Item -ItemType Directory -Force -Path $dbdir | Out-Null
$db = Join-Path $dbdir 'verify.db'
$logdir = 'C:\Users\ss80751\AppData\Local\Temp\kohden-code\glossary-deai\logs'
$p = Start-Process -FilePath $py -ArgumentList 'tasks.py','serve','--db',"`"$db`"" -WorkingDirectory $root -RedirectStandardOutput (Join-Path $logdir 'serve-p2.out.log') -RedirectStandardError (Join-Path $logdir 'serve-p2.err.log') -WindowStyle Hidden -PassThru
Write-Output ("STARTED PID={0}" -f $p.Id)

$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/terms' -UseBasicParsing -TimeoutSec 3
    if ($resp.StatusCode -eq 200) { $ok = $true; break }
  } catch {}
}
Write-Output ("HTTP /terms {0}" -f $(if ($ok) { 'OK' } else { 'FAIL' }))
if (-not $ok) { Get-Content (Join-Path $logdir 'serve-p2.err.log') -Tail 20 | Write-Output }
