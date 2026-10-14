param(
    [string]$OutputRoot = "C:\Users\Public\Documents\lnb_baseline",
    [string[]]$SharePaths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-OfficeInfo {
    $registryPaths = @(
        "HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration"
    )

    $items = @()
    foreach ($path in $registryPaths) {
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }

        $config = Get-ItemProperty -LiteralPath $path

        $productIds = if ($config.PSObject.Properties["ProductReleaseIds"]) { $config.ProductReleaseIds } else { $null }
        $version = if ($config.PSObject.Properties["ClientVersionToReport"]) { $config.ClientVersionToReport } else { $null }
        $platform = if ($config.PSObject.Properties["Platform"]) { $config.Platform } else { $null }
        $installPath = if ($config.PSObject.Properties["InstallPath"]) { $config.InstallPath } else { $null }

        $items += [pscustomobject]@{
            RegistryPath = $path
            ProductIds   = $productIds
            Version      = $version
            Platform     = $platform
            InstallPath  = $installPath
        }
    }

    return $items
}

function Get-ExcelWorkbookSnapshot {
    $books = @()
    try {
        $excel = [Runtime.InteropServices.Marshal]::GetActiveObject("Excel.Application")
        foreach ($book in $excel.Workbooks) {
            $books += [pscustomobject]@{
                Name     = $book.Name
                FullName = $book.FullName
                ReadOnly = $book.ReadOnly
            }
        }
    }
    catch {
        # Excel is not running or COM is unavailable.
    }

    return $books
}

function Get-ProcessSnapshot {
    $list = @()
    foreach ($p in (Get-Process)) {
        if (-not ($p.MainWindowTitle -or $p.ProcessName -match "excel|panacim|egpro|lnb|zed")) {
            continue
        }

        $startTime = $null
        try {
            $startTime = $p.StartTime
        }
        catch {
            $startTime = $null
        }

        $list += [pscustomobject]@{
            Name            = $p.ProcessName
            Id              = $p.Id
            StartTime       = $startTime
            MainWindowTitle = $p.MainWindowTitle
        }
    }

    return $list
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = Join-Path $OutputRoot "lnb_pc_baseline_$timestamp"

if (-not (Test-Path -LiteralPath $OutputRoot)) {
    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
}
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$computer = Get-CimInstance -ClassName Win32_ComputerSystem |
    Select-Object Manufacturer, Model, TotalPhysicalMemory, UserName

$os = Get-CimInstance -ClassName Win32_OperatingSystem |
    Select-Object Caption, Version, BuildNumber, OSArchitecture, LastBootUpTime

$cpu = Get-CimInstance -ClassName Win32_Processor |
    Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed


$memoryModules = @(
    Get-CimInstance -ClassName Win32_PhysicalMemory |
        Select-Object BankLabel, Capacity, Speed, Manufacturer, PartNumber
)

$logicalDisks = @(
    Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3" |
        Select-Object DeviceID, VolumeName, Size, FreeSpace, FileSystem
)

$processes = @(Get-ProcessSnapshot)

$office = @(Get-OfficeInfo)
$excelBooks = @(Get-ExcelWorkbookSnapshot)

$shareChecks = @(foreach ($path in $SharePaths) {
    [pscustomobject]@{
        Path   = $path
        Exists = Test-Path -LiteralPath $path
    }
})

$snapshot = [pscustomobject]@{
    CollectedAt   = (Get-Date).ToString("o")
    Computer      = $computer
    OS            = $os
    CPU           = $cpu
    MemoryModules = $memoryModules
    LogicalDisks  = $logicalDisks
    Office        = $office
    Processes     = $processes
    ExcelBooks    = $excelBooks
    ShareChecks   = $shareChecks
}

$jsonPath = Join-Path $outputDir "snapshot.json"
$diskCsvPath = Join-Path $outputDir "logical_disks.csv"
$procCsvPath = Join-Path $outputDir "processes.csv"
$summaryPath = Join-Path $outputDir "summary.txt"

$snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
$logicalDisks | Export-Csv -LiteralPath $diskCsvPath -NoTypeInformation -Encoding UTF8
$processes | Export-Csv -LiteralPath $procCsvPath -NoTypeInformation -Encoding UTF8

@(
    "CollectedAt: $($snapshot.CollectedAt)",
    "OutputDir: $outputDir",
    "Machine: $($computer.Manufacturer) / $($computer.Model)",
    "OS: $($os.Caption) $($os.Version) ($($os.OSArchitecture))",
    "OfficeRecords: $($office.Count)",
    "ProcessesCaptured: $($processes.Count)",
    "ExcelBooksCaptured: $($excelBooks.Count)",
    "ShareChecks: $($shareChecks.Count)"
) | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host "Baseline collection completed: $outputDir"
