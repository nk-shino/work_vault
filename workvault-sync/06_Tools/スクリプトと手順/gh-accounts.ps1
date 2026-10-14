# 起票先アカウントを区分ごとに分ける。
#
# なぜ設定ディレクトリを分けるのか:
#   gh は -R でリポジトリを選べるが、認証はアクティブアカウントのまま使われる。
#   宛先を変えたつもりで名義が変わらない。gh auth switch はホスト単位で
#   グローバルに切り替わるので、切り替え忘れが静かに誤名義のコミットになる。
#   設定ディレクトリを分けると、指定を間違えたときは「未認証」で止まる。
#   誤ったアカウントへ静かに起票されるより、止まるほうがよい。
#
# トークンは gh の keyring に入る。このスクリプトにも設定ファイルにも書かない。
#
# 使い方。Windows PowerShell 5.1 は実効ポリシーが Restricted（全スコープ Undefined）で
# .ps1 を一切読み込まない。pwsh 7 側は RemoteSigned なので直接呼べる。
# どちらで開いても動く形にするため、-ExecutionPolicy Bypass を付けて呼ぶ。
# この保管庫の他のスクリプト（collect-file-inventory.ps1 等）も同じ形で呼んでいる。
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\gh-accounts.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\gh-accounts.ps1 -Setup work
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\gh-accounts.ps1 -Run work -- issue list
#
# pwsh 7 からでも Bypass は必要。このファイルが H: にあるためである。
# H: は Google ドライブの仮想ドライブで、RemoteSigned はここを「リモート」と判定し、
# 署名が無いと読み込みを拒否する（ダウンロード印は付いていない。置き場そのものが理由）。
# 同じ内容を C: に置くと pwsh 7 は Bypass なしで通る。
#
# つまり 5.1 と pwsh 7、H: と C: の4通りすべてで通る呼び方は Bypass 付きの1つだけ。
#
# このファイルは BOM 付き UTF-8 で保存する。BOM が無いと 5.1 が cp932 として読み、
# 日本語の文字列リテラルが壊れて構文エラーになる。エラーは文字コードを指さない。

param(
  [string]$Setup,
  [string]$Run,
  [Parameter(ValueFromRemainingArguments = $true)] [string[]]$Rest
)

# 区分 -> 期待アカウント。ここが唯一の対応表。
$Accounts = [ordered]@{
  work     = 'soushi.shinohara22'   # 業務。Work_Vault 由来
  life     = 'Liff22'               # 生活。Zettelkasten 由来
  kirinuki = 'kirinukifallstay'     # サイト構築。切り抜き・アイデンリリィ
}

function Get-Dir([string]$k) { Join-Path $HOME ".config\gh-$k" }

function Show-State {
  "{0,-10} {1,-22} {2,-12} {3}" -f '区分', '期待アカウント', 'project', '実際'
  foreach ($k in $Accounts.Keys) {
    $d = Get-Dir $k
    if (-not (Test-Path $d)) { "{0,-10} {1,-22} {2,-12} {3}" -f $k, $Accounts[$k], '-', '設定ディレクトリ未作成'; continue }
    $old = $env:GH_CONFIG_DIR; $env:GH_CONFIG_DIR = $d
    $s = (gh auth status 2>&1) -join "`n"
    $env:GH_CONFIG_DIR = $old
    if ($s -notmatch 'Logged in') { "{0,-10} {1,-22} {2,-12} {3}" -f $k, $Accounts[$k], '-', '未ログイン'; continue }
    $who  = if ($s -match 'account (\S+)') { $matches[1] } else { '不明' }
    $proj = if ($s -match "scopes:.*'project'") { 'あり' } else { '**無し**' }
    $mark = if ($who -eq $Accounts[$k]) { '' } else { '  ← 一致しない' }
    "{0,-10} {1,-22} {2,-12} {3}{4}" -f $k, $Accounts[$k], $proj, $who, $mark
  }
}

if ($Setup -eq 'all') {
  # 3区分を順に。1つ失敗しても残りは試す（どれが通ったかは最後の一覧で分かる）。
  foreach ($k in $Accounts.Keys) { & $PSCommandPath -Setup $k }
  exit 0
}

if ($Setup) {
  if (-not $Accounts.Contains($Setup)) { throw "区分が不正: $Setup（work / life / kirinuki / all）" }
  $d = Get-Dir $Setup
  New-Item -ItemType Directory -Force -Path $d | Out-Null
  $env:GH_CONFIG_DIR = $d
  Write-Output "=== $Setup ($($Accounts[$Setup])) ==="
  Write-Output "GH_CONFIG_DIR = $d"
  Write-Output "ブラウザが開く。$($Accounts[$Setup]) でログインすること。別アカウントで入ると後の照合で止まる。"
  gh auth login
  # project スコープは既定で付かない。無いと看板操作が全部失敗する。
  gh auth refresh -s project
  Write-Output ""
  # コミット名義は推測しない。ログインしたアカウントから引く。
  $noreply = gh api user --jq '"\(.id)+\(.login)@users.noreply.github.com"' 2>$null
  if ($noreply) { Write-Output "このアカウントのコミット用メール: $noreply" }
  Write-Output "リポジトリ側で設定する: git config --local user.email `"$noreply`""
  Write-Output "**--global は使わない。**他の区分のリポジトリに名義が漏れる。"
  $env:GH_CONFIG_DIR = $null
  Write-Output ""
  Show-State
  exit 0
}

if ($Run) {
  if (-not $Accounts.Contains($Run)) { throw "区分が不正: $Run（work / life / kirinuki）" }
  $d = Get-Dir $Run
  if (-not (Test-Path $d)) { throw "$Run は未設定。先に .\gh-accounts.ps1 -Setup $Run を実行する" }
  $env:GH_CONFIG_DIR = $d
  # 叩く前に名義を照合する。黙って続行しない（task-account-router の発火条件）。
  $s = (gh auth status 2>&1) -join "`n"
  $who = if ($s -match 'account (\S+)') { $matches[1] } else { '' }
  if ($who -ne $Accounts[$Run]) {
    $env:GH_CONFIG_DIR = $null
    throw "名義が一致しない。期待 $($Accounts[$Run]) / 実際 '$who'。作業を中止した"
  }
  $args2 = $Rest | Where-Object { $_ -ne '--' }
  & gh @args2
  $code = $LASTEXITCODE
  $env:GH_CONFIG_DIR = $null
  exit $code
}

Show-State
