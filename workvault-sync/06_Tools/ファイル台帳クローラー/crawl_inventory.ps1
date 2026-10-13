#Requires -Version 5.1
<#
元ファイルは変更しない。出力先にのみ台帳・取得原本・ログを書き込む。
Windows PowerShell 5.1 / ImportExcel が必要。UTF-8 BOM付きで保存する。
#>
[CmdletBinding()]
param(
    [string]$OutputRoot = 'C:\FileInventory\output',
    [switch]$IncludeUnverified
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Split = $true なら共有直下と直下の各フォルダに分ける。
# Verified は通常実行の対象フラグ。接続確認の結果ではない。
$targets = @(
    @{
        Server   = 'nksv1359'
        Share    = 'share'
        Path     = '\\nksv1359.ad.nkc.co.jp\share'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv1359'
        Share    = 'WWW'
        Path     = '\\nksv1359.ad.nkc.co.jp\WWW'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv569'
        Share    = 'Share'
        Path     = '\\nksv569.ad.nkc.co.jp\Share'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv569'
        Share    = 'WWW'
        Path     = '\\nksv569.ad.nkc.co.jp\WWW'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv250'
        Share    = '富岡（株）_実装'
        Path     = '\\nksv250.ad.nkc.co.jp\富岡（株）_実装'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv523'
        Share    = 'Backup'
        Path     = '\\nksv523.ad.nkc.co.jp\Backup'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv523'
        Share    = 'LOG'
        Path     = '\\nksv523.ad.nkc.co.jp\LOG'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = 'nksv523'
        Share    = '第二工場実装課用'
        Path     = '\\nksv523.ad.nkc.co.jp\第二工場実装課用'
        Split    = $true
        Verified = $true
    }
    @{
        Server   = $env:COMPUTERNAME
        Share    = 'Local'
        Path     = 'C:\Users\ss80751\NK\第二生産部生産一課一係 - ドキュメント'
        Split    = $false
        Verified = $true
    }
)

$started = Get-Date
$runId = $started.ToString('yyyyMMdd_HHmmss_fff')
$month = $started.ToString('yyyyMM')

$script:exitCode = 0
$script:issues = 0
$script:logWriter = $null

$lock = $null
$utf8 = [System.Text.UTF8Encoding]::new($false)

$columns = @(
    '実行ID'
    '取得日時'
    'サーバー'
    '共有'
    '場所'
    '共有ルート'
    '走査ルート'
    '種別'
    '名前'
    '相対パス'
    'フルパス'
    '拡張子'
    '更新日時'
    '容量バイト'
    '容量MB'
)

# 警告・エラーを画面とJSON Lines形式のログに残す。
function Write-Event(
    [string]$Kind,
    [string]$Path,
    [string]$Message
) {
    $script:issues++
    $script:exitCode = [Math]::Max($script:exitCode, 1)

    $line = [ordered]@{
        Time    = (Get-Date).ToString('o')
        RunId   = $runId
        Kind    = $Kind
        Path    = $Path
        Message = $Message
    } | ConvertTo-Json -Compress

    if ($null -ne $script:logWriter) {
        $script:logWriter.WriteLine($line)
    }

    Write-Warning "$Kind [$Path] $Message"
}

# 出力名を短く整え、ハッシュで名前の衝突を抑える。
function Get-Label(
    [string]$Text,
    [string]$Identity = ''
) {
    if (-not $Identity) {
        $Identity = $Text
    }

    $safe = (
        $Text -replace '[<>:"/\\|?*\x00-\x1F]', '_'
    ).Trim().TrimEnd('.')

    if (-not $safe) {
        $safe = 'location'
    }

    if ($safe.Length -gt 36) {
        $safe = $safe.Substring(0, 36)
    }

    $sha = [System.Security.Cryptography.SHA256]::Create()

    try {
        $hash = [BitConverter]::ToString(
            $sha.ComputeHash(
                [Text.Encoding]::UTF8.GetBytes($Identity)
            )
        ).Replace('-', '').Substring(0, 8)
    }
    finally {
        $sha.Dispose()
    }

    return "${safe}_${hash}"
}

# 出力先が走査対象の配下にないか、パスの文字列で確認する。
function Test-Under(
    [string]$Child,
    [string]$Parent
) {
    $a = [IO.Path]::GetFullPath($Child).TrimEnd('\')
    $b = [IO.Path]::GetFullPath($Parent).TrimEnd('\')

    return (
        $a.Equals(
            $b,
            [StringComparison]::OrdinalIgnoreCase
        ) -or
        $a.StartsWith(
            $b + '\',
            [StringComparison]::OrdinalIgnoreCase
        )
    )
}

# ファイルまたはフォルダの情報を取得原本へ1行書き込む。
function Write-InventoryRow(
    $Writer,
    $Item,
    $Target,
    $Job,
    [string]$Kind
) {
    $relative = $Item.FullName.Substring(
        $Job.Root.Length
    ).TrimStart('\')

    if (-not $relative) {
        $relative = '.'
    }

    $bytes = $null
    $mb = $null
    $extension = ''

    if ($Kind -eq 'ファイル') {
        $bytes = $Item.Length
        $mb = [Math]::Round($bytes / 1MB, 2)
        $extension = $Item.Extension
    }

    $record = [ordered]@{
        '実行ID'       = $runId
        '取得日時'     = $started.ToString(
            'yyyy-MM-dd HH:mm:ss.fff zzz'
        )
        'サーバー'     = $Target.Server
        '共有'         = $Target.Share
        '場所'         = $Job.Place
        '共有ルート'   = $Target.Path
        '走査ルート'   = $Job.Root
        '種別'         = $Kind
        '名前'         = $Item.Name
        '相対パス'     = $relative
        'フルパス'     = $Item.FullName
        '拡張子'       = $extension
        '更新日時'     = $Item.LastWriteTime.ToString(
            'yyyy-MM-dd HH:mm:ss'
        )
        '容量バイト'   = $bytes
        '容量MB'       = $mb
    }

    $Writer.WriteLine(
        ($record | ConvertTo-Json -Compress)
    )
}

# 取得原本を読み、月別ブックに日時シートを追加する。
# シート上限を超えた場合は _002、_003 と分割する。
function Save-Workbook(
    [string]$Snapshot,
    [string]$Book,
    $Summary
) {
    $temp = Join-Path (Split-Path $Book) (
        '.work_' +
        [guid]::NewGuid().ToString('N') +
        '.xlsx'
    )

    $package = $null
    $reader = $null

    try {
        if (Test-Path -LiteralPath $Book) {
            Copy-Item -LiteralPath $Book -Destination $temp
        }

        $package = Open-ExcelPackage -Path $temp -Create

        $baseName = $runId
        $suffix = 0

        while (
            $null -ne
            $package.Workbook.Worksheets[$baseName + '_001']
        ) {
            $suffix++
            $baseName = $runId + '_' + $suffix
        }

        $reader = [IO.StreamReader]::new(
            $Snapshot,
            [Text.Encoding]::UTF8
        )

        $part = 0
        $row = 1048577
        $sheetNames = [Collections.Generic.List[string]]::new()

        while (
            ($null -ne ($line = $reader.ReadLine())) -or
            ($part -eq 0)
        ) {
            if ($row -gt 1048576) {
                $part++

                $sheetName = '{0}_{1:000}' -f $baseName, $part
                $ws = $package.Workbook.Worksheets.Add($sheetName)
                $sheetNames.Add($sheetName)

                for ($c = 0; $c -lt $columns.Count; $c++) {
                    $ws.Cells[1, $c + 1].Value = $columns[$c]
                }

                $ws.Cells[
                    1, 1, 1, $columns.Count
                ].Style.Font.Bold = $true

                $ws.View.FreezePanes(2, 1)

                $ws.Cells[
                    1, 1, 1, $columns.Count
                ].AutoFilter = $true

                $ws.Column(1).Width = 25

                for ($c = 2; $c -le $columns.Count; $c++) {
                    $ws.Column($c).Width = 22
                }

                $ws.Column(11).Width = 65
                $row = 2
            }

            # 取得原本が空でも、見出しだけのシートを残す。
            if ($null -eq $line) {
                break
            }

            $obj = $line | ConvertFrom-Json

            for ($c = 0; $c -lt $columns.Count; $c++) {
                # Valueに代入し、ファイル名を数式として扱わない。
                $ws.Cells[$row, $c + 1].Value =
                    $obj.PSObject.Properties[$columns[$c]].Value
            }

            $row++
        }

        $history = $package.Workbook.Worksheets['取得履歴']

        if ($null -eq $history) {
            $history = $package.Workbook.Worksheets.Add(
                '取得履歴'
            )

            $headers = @(
                '実行ID'
                '走査ルート'
                '場所'
                '開始日時'
                '走査終了日時'
                'ファイル数'
                'フォルダ数'
                '記録件数'
                '警告・エラー数'
                '走査結果'
                'シート'
                '取得原本'
            )

            for ($c = 0; $c -lt $headers.Count; $c++) {
                $history.Cells[1, $c + 1].Value = $headers[$c]
            }

            $history.View.FreezePanes(2, 1)
        }

        $r = $history.Dimension.End.Row + 1

        $values = @(
            $runId
            $Summary.Root
            $Summary.Place
            $Summary.Start
            $Summary.End
            $Summary.Files
            $Summary.Folders
            $Summary.Rows
            $Summary.Issues
            $Summary.Status
            ($sheetNames -join ', ')
            $Snapshot
        )

        for ($c = 0; $c -lt $values.Count; $c++) {
            $history.Cells[$r, $c + 1].Value = $values[$c]
        }

        $package.Save()
        $package.Dispose()
        $package = $null

        # 一時ブックの保存が完了してから既存ブックを置換する。
        if (Test-Path -LiteralPath $Book) {
            [IO.File]::Replace($temp, $Book, $null)
        }
        else {
            [IO.File]::Move($temp, $Book)
        }
    }
    finally {
        if ($null -ne $reader) {
            $reader.Dispose()
        }

        if ($null -ne $package) {
            $package.Dispose()
        }

        if (Test-Path -LiteralPath $temp) {
            Remove-Item -LiteralPath $temp -Force
        }
    }
}

try {
    # 出力先はローカルディスクの絶対パスを指定する。
    if ($OutputRoot -notmatch '^[A-Za-z]:\\') {
        throw 'OutputRoot はローカルディスクの絶対パスにしてください。'
    }

    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)

    [IO.Directory]::CreateDirectory($OutputRoot) | Out-Null

    # 同じ出力先を使う処理の同時実行を防ぐ。
    # ロックファイル自体は実行後も残してよい。
    $lock = [IO.File]::Open(
        (Join-Path $OutputRoot 'inventory.lock'),
        [IO.FileMode]::OpenOrCreate,
        [IO.FileAccess]::ReadWrite,
        [IO.FileShare]::None
    )

    $logDir = Join-Path $OutputRoot '_logs'
    [IO.Directory]::CreateDirectory($logDir) | Out-Null

    $script:logWriter = [IO.StreamWriter]::new(
        (Join-Path $logDir "$runId.jsonl"),
        $false,
        $utf8
    )

    $script:logWriter.AutoFlush = $true

    Import-Module ImportExcel -ErrorAction Stop

    foreach ($target in $targets) {
        if (
            -not $target.Verified -and
            -not $IncludeUnverified
        ) {
            continue
        }

        $target.Path = $target.Path.TrimEnd('\')

        if (Test-Under $OutputRoot $target.Path) {
            throw '出力先を走査対象の配下には置けません。'
        }

        $jobs = [Collections.Generic.List[object]]::new()
        $beforeDiscovery = $script:issues

        try {
            $rootInfo = Get-Item -LiteralPath $target.Path -Force

            if (-not $rootInfo.PSIsContainer) {
                throw '走査対象がフォルダではありません。'
            }

            if (
                $rootInfo.Attributes -band
                [IO.FileAttributes]::ReparsePoint
            ) {
                throw '走査ルートが再解析ポイントです。実体のパスを登録してください。'
            }

            if ($target.Split) {
                # 共有直下のファイルは、サブフォルダと別に保存する。
                $jobs.Add(@{
                    Root    = $target.Path
                    Place   = '共有直下'
                    Recurse = $false
                })

                try {
                    foreach ($sub in $rootInfo.GetDirectories()) {
                        if (
                            $sub.Attributes -band
                            [IO.FileAttributes]::ReparsePoint
                        ) {
                            Write-Event 'LINK_SKIP' $sub.FullName `
                                '再解析ポイントを除外しました。'
                        }
                        else {
                            $jobs.Add(@{
                                Root    = $sub.FullName.TrimEnd('\')
                                Place   = $sub.Name
                                Recurse = $true
                            })
                        }
                    }
                }
                catch {
                    Write-Event 'DISCOVERY' $target.Path `
                        $_.Exception.Message
                }
            }
            else {
                # 指定フォルダ全体を1つの場所として保存する。
                $jobs.Add(@{
                    Root    = $target.Path
                    Place   = $rootInfo.Name
                    Recurse = $true
                })
            }
        }
        catch {
            Write-Event 'ROOT' $target.Path $_.Exception.Message
            continue
        }

        $discoveryIssues = $script:issues - $beforeDiscovery

        foreach ($job in $jobs) {
            $before = $script:issues
            $snapshotWriter = $null

            $files = 0
            $folders = 0
            $rows = 0

            try {
                $serverDir = Join-Path $OutputRoot (
                    Get-Label $target.Server
                )

                $shareDir = Join-Path $serverDir (
                    Get-Label $target.Share
                )

                $placeDir = Join-Path $shareDir (
                    Get-Label $job.Place $job.Root
                )

                [IO.Directory]::CreateDirectory(
                    $placeDir
                ) | Out-Null

                $rawDir = Join-Path $placeDir '_snapshots'

                [IO.Directory]::CreateDirectory(
                    $rawDir
                ) | Out-Null

                $snapshot = Join-Path $rawDir "$runId.jsonl"
                $summaryPath = Join-Path $rawDir (
                    "$runId.summary.json"
                )

                $bookName = '{0}_{1}_{2}_{3}.xlsx' -f (
                    $target.Server,
                    $target.Share,
                    (Get-Label $job.Place),
                    $month
                )

                $book = Join-Path $placeDir $bookName

                $snapshotWriter = [IO.StreamWriter]::new(
                    $snapshot,
                    $false,
                    $utf8
                )

                $stack = [Collections.Generic.Stack[string]]::new()
                $stack.Push($job.Root)

                while ($stack.Count -gt 0) {
                    $dir = $stack.Pop()

                    try {
                        $info = [IO.DirectoryInfo]::new($dir)

                        if (
                            $info.Attributes -band
                            [IO.FileAttributes]::ReparsePoint
                        ) {
                            Write-Event 'LINK_SKIP' $dir `
                                '再解析ポイントを除外しました。'

                            continue
                        }

                        # フォルダ自体も記録するため、空フォルダも残る。
                        Write-InventoryRow `
                            $snapshotWriter $info $target $job 'フォルダ'

                        $folders++
                        $rows++
                    }
                    catch {
                        Write-Event 'DIRECTORY' $dir `
                            $_.Exception.Message

                        continue
                    }

                    try {
                        foreach ($fi in $info.GetFiles()) {
                            try {
                                if (
                                    $fi.Attributes -band
                                    [IO.FileAttributes]::ReparsePoint
                                ) {
                                    Write-Event 'LINK_SKIP' $fi.FullName `
                                        '再解析ポイントを除外しました。'

                                    continue
                                }

                                Write-InventoryRow `
                                    $snapshotWriter $fi $target $job 'ファイル'

                                $files++
                                $rows++
                            }
                            catch {
                                Write-Event 'FILE' $fi.FullName `
                                    $_.Exception.Message
                            }
                        }
                    }
                    catch {
                        Write-Event 'DIR_FILES' $dir `
                            $_.Exception.Message
                    }

                    if ($job.Recurse) {
                        try {
                            foreach ($sub in $info.GetDirectories()) {
                                $stack.Push($sub.FullName)
                            }
                        }
                        catch {
                            Write-Event 'DIR_ENUM' $dir `
                                $_.Exception.Message
                        }
                    }
                }

                $snapshotWriter.Dispose()
                $snapshotWriter = $null

                $issueCount = (
                    $script:issues - $before
                ) + $discoveryIssues

                $status = '取得成功'

                if ($issueCount -gt 0) {
                    $status = '一部取得失敗または除外あり'
                }

                $summary = [ordered]@{
                    RunId       = $runId
                    Root        = $job.Root
                    Place       = $job.Place
                    Start       = $started.ToString('o')
                    End         = (Get-Date).ToString('o')
                    Files       = $files
                    Folders     = $folders
                    Rows        = $rows
                    Issues      = $issueCount
                    Status      = $status
                    Book        = $book
                    ExcelStatus = '未保存'
                }

                [IO.File]::WriteAllText(
                    $summaryPath,
                    ($summary | ConvertTo-Json),
                    $utf8
                )

                try {
                    Save-Workbook $snapshot $book $summary

                    $summary.ExcelStatus = '保存成功'

                    Write-Host (
                        "$($job.Root) " +
                        "ファイル $files 件、フォルダ $folders 件 " +
                        "保存先 $book"
                    )
                }
                catch {
                    $summary.ExcelStatus = '保存失敗'
                    $script:exitCode = 2

                    Write-Event 'EXCEL' $book $_.Exception.Message
                }

                [IO.File]::WriteAllText(
                    $summaryPath,
                    ($summary | ConvertTo-Json),
                    $utf8
                )
            }
            catch {
                $script:exitCode = 2

                Write-Event 'OUTPUT_OR_JOB' $job.Root `
                    $_.Exception.Message
            }
            finally {
                if ($null -ne $snapshotWriter) {
                    $snapshotWriter.Dispose()
                }
            }
        }
    }
}
catch {
    $script:exitCode = 2

    if ($null -ne $script:logWriter) {
        Write-Event 'FATAL' $OutputRoot $_.Exception.Message
    }
    else {
        Write-Warning $_.Exception.Message
    }
}
finally {
    if ($null -ne $script:logWriter) {
        $script:logWriter.Dispose()
    }

    if ($null -ne $lock) {
        $lock.Dispose()
    }
}

exit $script:exitCode