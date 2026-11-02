# AutoShutdown_20261016_1900 の毎日トリガーを 21:00 へ戻し、自分自身を削除する。
# 実行予定: 2026-10-24 00:05(起動していなければ次回起動時・StartWhenAvailable)
$t = Get-ScheduledTask -TaskName "AutoShutdown_20261016_1900"
$trg = $t.Triggers | Where-Object { $_.CimClass.CimClassName -eq "MSFT_TaskDailyTrigger" }
$trg.StartBoundary = "2026-10-24T21:00:00"
Set-ScheduledTask -TaskName "AutoShutdown_20261016_1900" -Trigger $t.Triggers
Unregister-ScheduledTask -TaskName "Restore_AutoShutdown_20261024" -Confirm:$false
