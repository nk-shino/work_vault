$procs = Get-CimInstance Win32_Process -Filter "Name='EXCEL.EXE'"
$targets = @()
foreach ($p in $procs) {
    $auto = $p.CommandLine -match "/automation"
    Write-Output ("PID={0} Created={1} Auto={2} Cmd={3}" -f $p.ProcessId, $p.CreationDate, $auto, $p.CommandLine)
    if ($auto) { $targets += $p.ProcessId }
}
foreach ($t in $targets) {
    Write-Output ("Stopping PID {0}" -f $t)
    Stop-Process -Id $t -Force -ErrorAction Continue
}
Start-Sleep -Seconds 2
$left = Get-Process EXCEL -ErrorAction SilentlyContinue
if ($left) { Write-Output ("Remaining: " + ($left.Id -join ",")) } else { Write-Output "Remaining: none" }
