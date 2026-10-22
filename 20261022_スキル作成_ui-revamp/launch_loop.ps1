$ErrorActionPreference = 'Stop'
$skillCreator = 'C:\Users\ss80751\.cache\kohden-code\builtin-skills\1.18.33-nk.9\skill-creator'
$topic = 'C:\Users\ss80751\kohden-code-workspace\20261022_スキル作成_ui-revamp'
New-Item -ItemType Directory -Force -Path "$topic\run_results" | Out-Null
$a = @(
  '-X','utf8','-m','scripts.run_loop',
  '--eval-set', "$topic\eval_set.json",
  '--skill-path', 'C:\Users\ss80751\.config\kohden-code\skills\ui-revamp',
  '--model', 'internal-litellm/kohden-hosted/main',
  '--max-iterations', '5',
  '--num-workers', '4',
  '--results-dir', "$topic\run_results",
  '--verbose'
)
$p = Start-Process -FilePath 'python' -ArgumentList $a -WorkingDirectory $skillCreator -WindowStyle Hidden -RedirectStandardOutput "$topic\run_results\loop.log" -RedirectStandardError "$topic\run_results\loop.err" -PassThru
"PID=$($p.Id)" | Set-Content "$topic\run_results\loop.pid"
Write-Output "STARTED PID=$($p.Id)"
