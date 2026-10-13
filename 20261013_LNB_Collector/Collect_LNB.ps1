#requires -Version 5.1
[CmdletBinding()]
param([switch]$Register, [switch]$PrepareOnly, [switch]$TestOnly, [ValidateSet('L1','L2','L3')][string]$Line)
$ErrorActionPreference='Stop'; Set-StrictMode -Version 2.0
$Version='6.5-review'; $script:RegistrationGuid=$null; $MarkerName='LNB_USB_ID.txt'; $ToolDir='tools\ImportExcel'; $ExpectedImportExcel='7.8.10'
$Sheets=[ordered]@{
 computer=@('Name','Manufacturer','Model','TotalPhysicalMemory')
 os=@('Caption','Version','BuildNumber','OSArchitecture','LastBootUpTime')
 cpu=@('DeviceID','Name','NumberOfCores','NumberOfLogicalProcessors','MaxClockSpeed')
 memory=@('DeviceLocator','BankLabel','Capacity','Speed')
 disks=@('DeviceID','VolumeName','Size','FreeSpace','FileSystem')
 printers=@('Name','DriverName','PortName','Default','WorkOffline')
 processes=@('ProcessName','Id')
 office=@('ProductIds','Version','Platform')
 excel_recent=@('OfficeVersion','Path','Source','TimeMeaning')
 windows_recent=@('ShortcutName','ShortcutLastWriteTime','TimeMeaning','Target')
}
$script:Rows=[ordered]@{}; foreach($n in $Sheets.Keys){$script:Rows[$n]=@()}
$script:Statuses=New-Object 'System.Collections.Generic.List[object]'; $script:Out=$null; $script:Root=$null; $script:UsbSerial=$null
function Safe([AllowNull()][object]$Value){if($null -eq $Value){return ''};$s=[regex]::Replace([string]$Value,'[\x00-\x1F\x7F]',' ');if($s -match '^\s*[=+@\-]'){$s="'"+$s};return $s}
function Suspicious([string]$s){return ($s -match '(?i)(password|passwd|pwd|token|secret|credential|authorization|bearer|api.?key)|[?#@\x00-\x1F\x7F]|[a-z][a-z0-9+.-]*://')}
function DocPath([AllowNull()][string]$s){if([string]::IsNullOrWhiteSpace($s)){return $false};$p=$s.Trim();if((Suspicious $p)-or $p.StartsWith('\\?\')-or $p.StartsWith('\\.\')){return $false};if($p -match '^[A-Za-z]:\\'){if($p.Substring(2).Contains(':')){return $false}}elseif($p -match '^\\\\[^\\/:]+\\[^\\/:]+\\.+'){if($p.Contains(':')){return $false}}else{return $false};return ($p -match '(?i)\.(xlsx|xls|xlsm|xlsb|xltx|xltm|csv|pdf|doc|docx|txt)$')}
function MruPath([AllowNull()][string]$s){if([string]::IsNullOrWhiteSpace($s)){return $null};$i=$s.LastIndexOf('*');if($i -ge 0){$s=$s.Substring($i+1)};$p=$s.Trim();if(DocPath $p){return $p};return $null}
function CsvText([object[]]$rows,[string[]]$cols){if($rows.Count -gt 0){return ((@($rows|ConvertTo-Csv -NoTypeInformation)-join "`r`n")+"`r`n")};$h=[ordered]@{};foreach($c in $cols){$h[$c]=''};return (((@([pscustomobject]$h|ConvertTo-Csv -NoTypeInformation))[0])+"`r`n")}
function Utf8File([string]$path,[string]$text){if($script:Out){VerifyUsb;PathHasReparse $path $script:Root};[IO.File]::WriteAllText($path,$text,(New-Object System.Text.UTF8Encoding -ArgumentList $true))}
function WriteAllTextVerified([string]$path,[string]$text){Utf8File $path $text;try{[void][IO.File]::ReadAllText($path,[Text.Encoding]::UTF8)}catch{throw ('Write verification failed: '+$path)}}
function PathHasReparse([string]$path,[string]$stop){$full=[IO.Path]::GetFullPath($path);$base=[IO.Path]::GetFullPath($stop).TrimEnd('\');if(-not ($full -eq $base -or $full.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Path escaped approved USB root'};$rel=$full.Substring($base.Length).TrimStart('\');$cur=$base;if($rel){foreach($part in $rel.Split('\')){$cur=Join-Path $cur $part;if(Test-Path -LiteralPath $cur){$i=Get-Item -LiteralPath $cur -Force;if(($i.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0){throw 'Reparse point in output path'}}}}}
function AssertOnUsb([string]$path){if(-not $path.StartsWith($script:Root,[StringComparison]::OrdinalIgnoreCase)){throw 'Output path is not on registered USB'}}
function EnsureSafeDir([string]$path){$full=[IO.Path]::GetFullPath($path);$driveRoot=[IO.Path]::GetPathRoot($script:Root);if(-not $full.StartsWith($driveRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Not on registered USB'};$rel=$full.Substring($driveRoot.Length).TrimEnd('\');$cur=$driveRoot;foreach($part in $rel.Split('\')){if(-not $part){continue};$cur=Join-Path $cur $part;VerifyUsb;PathHasReparse (Split-Path -Parent $cur) $script:Root;if(Test-Path -LiteralPath $cur -ErrorAction Stop){$it=Get-Item -LiteralPath $cur -Force -ErrorAction Stop;if(-not $it.PSIsContainer -or (($it.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0)){throw 'Unsafe existing output component'}}else{[void](New-Item -ItemType Directory -Path $cur -ErrorAction Stop);$it=Get-Item -LiteralPath $cur -Force;if(-not $it.PSIsContainer -or (($it.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0)){throw 'Unsafe newly-created output component'}}}}
function GetUsbIdentity {
 if($PSCommandPath -notmatch '^([A-Za-z]):\\'){throw 'Script must be located at USB drive root'}
 $letter=$Matches[1];$expectedRoot=$letter+':\';$scriptRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSCommandPath)+'\')
 if($scriptRoot.TrimEnd('\') -ine $expectedRoot.TrimEnd('\')){throw 'Place collector directly at USB root'}
 $part=Get-Partition -DriveLetter $letter -ErrorAction Stop;$disk=Get-Disk -Number $part.DiskNumber -ErrorAction Stop
 if([string]$disk.BusType -ne 'USB'){throw 'Drive bus type is not USB'}
 $serial=([string]$disk.SerialNumber).Trim();if(-not $serial){throw 'USB disk has no readable hardware serial number'}
 $vol=Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$letter`:'" -OperationTimeoutSec 10 -ErrorAction Stop; $volSerial=([string]$vol.VolumeSerialNumber).Trim();if(-not $volSerial){throw 'USB volume serial unavailable'}
 return [pscustomobject]@{Root=$expectedRoot;Serial=$serial;VolumeSerial=$volSerial}
}
function RegisterUsb {
 $u=GetUsbIdentity;$marker=Join-Path $u.Root $MarkerName
 if(Test-Path -LiteralPath $marker){throw 'USB marker already exists; refusing overwrite'}
 Write-Host ('USB root: '+$u.Root+' Disk serial: '+$u.Serial+' Volume serial: '+$u.VolumeSerial)
 if((Read-Host 'Register this USB? Type YES') -cne 'YES'){Write-Host 'Cancelled';exit 2}
 $guid=[guid]::NewGuid().ToString('D');$body="LNB-USB-ID-v1`r`nRegistrationGuid=$guid`r`nDiskSerial=$($u.Serial)`r`nVolumeSerial=$($u.VolumeSerial)`r`nRootMarker=6.5-review`r`n"
 $bytes=[Text.Encoding]::ASCII.GetBytes($body);$stream=New-Object IO.FileStream($marker,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush()}finally{$stream.Dispose()}
 Write-Host ('Registration GUID: '+$guid)
 Write-Host 'Registered. Keep the collector at USB root.';exit 0
}
function VerifyUsb {
 $u=GetUsbIdentity;$marker=Join-Path $u.Root $MarkerName
 if(-not (Test-Path -LiteralPath $marker -PathType Leaf -ErrorAction Stop)){throw 'USB marker missing'}
 $text=[IO.File]::ReadAllText($marker,[Text.Encoding]::ASCII)
 if($text -notmatch '(?m)^RegistrationGuid=([0-9a-fA-F-]{36})$'){throw 'Registration GUID missing or malformed'};$script:RegistrationGuid=$Matches[1];if($text -notmatch '(?m)^DiskSerial=(.+)$' -or $Matches[1].Trim() -cne $u.Serial){throw 'USB disk serial does not match marker'};if($text -notmatch '(?m)^VolumeSerial=(.+)$' -or $Matches[1].Trim() -cne $u.VolumeSerial){throw 'USB volume serial does not match marker'}
 $script:Root=$u.Root;$script:UsbSerial=($u.Serial+' / '+$u.VolumeSerial)
}
function ValidateDependency {
 $moduleRoot=Join-Path $script:Root $ToolDir;$manifest=Join-Path $moduleRoot 'ImportExcel.psd1'
 if(-not (Test-Path -LiteralPath $manifest -PathType Leaf)){throw 'Approved ImportExcel 7.8.10 module folder missing'}
 $moduleItem=Get-Item -LiteralPath $moduleRoot -Force -ErrorAction Stop;if(($moduleItem.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0){throw 'ImportExcel module root is a reparse point'}
 $tree=Get-ChildItem -LiteralPath $moduleRoot -Force -Recurse -ErrorAction Stop
 foreach($i in $tree){if(($i.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0){throw 'Reparse point in ImportExcel module tree'}}
 $data=Import-PowerShellDataFile -Path $manifest
 if([string]$data.ModuleVersion -ne $ExpectedImportExcel){throw 'ImportExcel manifest version mismatch'}
 Import-Module -Name $manifest -Force -ErrorAction Stop
 $cmd=Get-Command Export-Excel -ErrorAction Stop
 $modulePath=[IO.Path]::GetFullPath($cmd.Module.Path);$allowed=[IO.Path]::GetFullPath($moduleRoot+'\')
 if(-not $modulePath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Export-Excel did not resolve from USB module folder'}
 if((Get-Command Export-Excel).Module.Version.ToString() -ne $ExpectedImportExcel){throw 'Loaded ImportExcel command version mismatch'}
}
function SelfTest {
 $t=New-Object 'System.Collections.Generic.List[object]'
 $cases=@(
  @{N='Local doc';B={DocPath 'C:\D\a.xlsx'}},@{N='UNC doc';B={DocPath '\\host\share\a.xlsx'}},@{N='URL rejected';B={-not (DocPath 'https://host/a.xlsx')}},@{N='device rejected';B={-not (DocPath '\\.\C:\a.xlsx')}},@{N='query rejected';B={-not (DocPath 'C:\a.xlsx?secret=x')}},@{N='suspicious name rejected';B={-not (DocPath 'C:\password.xlsx')}},@{N='ADS rejected';B={-not (DocPath 'C:\a.txt:stream.xlsx')}},@{N='extension rejected';B={-not (DocPath 'C:\a.exe')}},@{N='MRU marker parse';B={(MruPath '[F123][T456]*C:\D\a.xlsx') -ceq 'C:\D\a.xlsx'}},@{N='MRU filename brackets';B={(MruPath '*C:\D\a[1].xlsx') -ceq 'C:\D\a[1].xlsx'}},@{N='CSV formula defense';B={(Safe "`t=1+1") -ceq "' =1+1"}},@{N='CSV header on empty';B={(CsvText @() @('Name','Path')).Trim() -ceq '"Name","Path"'}},@{N='CSV escaped value';B={$csv=[pscustomobject]@{A=(Safe '=1');B='a,b'}|ConvertTo-Csv -NoTypeInformation;$parsed=@($csv|ConvertFrom-Csv);$parsed.Count -eq 1 -and $parsed[0].A -ceq "'=1" -and $parsed[0].B -ceq 'a,b'}}
 )
 foreach($c in $cases){$ok=$false;try{$ok=[bool](& $c.B)}catch{$ok=$false};$t.Add([pscustomobject]@{Name=$c.N;Passed=$ok})}
 $tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$tokens,[ref]$errors);$t.Add([pscustomobject]@{Name='PowerShell parser';Passed=($errors.Count -eq 0)})
 return @($t.ToArray())
}
function WriteState {
 if(-not $script:Out){return}
 try { VerifyUsb; PathHasReparse $script:Out $script:Root;
  $obj=@($script:Statuses.ToArray());WriteAllTextVerified (Join-Path $script:Out 'status.json') (ConvertTo-Json -InputObject $obj -Depth 6)
  foreach($n in $Sheets.Keys){$r=@($script:Rows[$n]);WriteAllTextVerified (Join-Path $script:Out ($n+'.csv')) (CsvText $r $Sheets[$n]);WriteAllTextVerified (Join-Path $script:Out ($n+'.json')) (ConvertTo-Json -InputObject $r -Depth 6)}
 }catch{throw}
}
function Stage([string]$name,[scriptblock]$action){$start=(Get-Date).ToString('o');$st='Success';$detail='';$rowList=New-Object 'System.Collections.Generic.List[object]';try{foreach($item in (& $action)){$rowList.Add($item);if($rowList.Count -ge 501){break}};$rows=@($rowList.ToArray())}catch{$st='Failed';$detail=$_.Exception.GetType().Name;$rows=@($rowList.ToArray())};if($rows.Count -gt 500){$rows=@($rows|Select-Object -First 500);if($st -eq 'Success'){$st='Truncated'};$detail+=' capped at 500 (501st row observed; enumeration stopped)'};if($st -eq 'Success' -and $rows.Count -eq 0){$st='NoData'};$safeRows=New-Object 'System.Collections.Generic.List[object]';foreach($r in $rows){$h=[ordered]@{};foreach($c in $Sheets[$name]){$p=$r.PSObject.Properties[$c];$v=if($null -eq $p){''}else{$p.Value};$h[$c]=Safe $v};$safeRows.Add([pscustomobject]$h)};$script:Rows[$name]=@($safeRows.ToArray());$override=if($name -eq 'excel_recent'){$script:scriptMruStatus}elseif($name -eq 'office'){$script:officeStatus}elseif($name -eq 'windows_recent'){$script:recentStatus}else{$null};$ovdetail=if($name -eq 'excel_recent'){$script:scriptMruDetail}elseif($name -eq 'office'){$script:officeDetail}elseif($name -eq 'windows_recent'){$script:recentDetail}else{$null};if($override -and $override -notin @('Success','NoData')){$st=$override;$detail=$ovdetail};$script:Statuses.Add([pscustomobject]@{Stage=$name;Status=$st;Rows=$safeRows.Count;Started=$start;Finished=(Get-Date).ToString('o');Detail=$detail});WriteState;Write-Host ($name+': '+$st+' rows='+$safeRows.Count)}
function ExcelRecent {
 $rows=New-Object 'System.Collections.Generic.List[object]';$errors=0;$filtered=0;$limited=$false
 foreach($v in @('16.0','15.0','14.0')){$base='HKCU:\Software\Microsoft\Office\'+$v+'\Excel';$keys=New-Object 'System.Collections.Generic.List[string]';$keys.Add($base+'\File MRU');try{$user=$base+'\User MRU';if(Test-Path -LiteralPath $user -ErrorAction Stop){$kids=@(Get-ChildItem -LiteralPath $user -ErrorAction Stop|Select-Object -First 65);if($kids.Count -gt 64){$limited=$true};foreach($k in @($kids|Select-Object -First 64)){$keys.Add((Join-Path $k.PSPath 'File MRU'))}}}catch{$errors++};foreach($key in $keys){if($rows.Count -ge 500){$limited=$true;break};try{if(-not(Test-Path -LiteralPath $key -ErrorAction Stop)){continue};$props=Get-ItemProperty -LiteralPath $key -ErrorAction Stop;$vals=@($props.PSObject.Properties|Where-Object{$_.Name -match '^File\d+$'}|Select-Object -First 501);if($vals.Count -gt 500){$limited=$true};foreach($val in @($vals|Select-Object -First 500)){if($rows.Count -ge 500){$limited=$true;break};$path=MruPath ([string]$val.Value);if($null -eq $path){$filtered++;continue};$rows.Add([pscustomobject]@{OfficeVersion=$v;Path=$path;Source='HKCU Excel File MRU';TimeMeaning='MRU; actual use time unavailable'})}}catch{$errors++}}}
 if($errors -gt 0){$script:scriptMruStatus=if($rows.Count){'Partial'}else{'Failed'}}elseif($limited){$script:scriptMruStatus='Truncated'};$script:scriptMruDetail="ReadErrors=$errors;Filtered=$filtered;LimitReached=$limited;targets never accessed";return $rows.ToArray()
}
function Recent {
 $base=$env:APPDATA;if(-not $base -or $base.StartsWith('\\') -or $base -notmatch '^[A-Za-z]:\\'){$script:recentStatus='Skipped';$script:recentDetail='APPDATA not local';return}
 $drive=New-Object IO.DriveInfo -ArgumentList ([IO.Path]::GetPathRoot($base));if($drive.DriveType -ne [IO.DriveType]::Fixed){$script:recentStatus='Skipped';$script:recentDetail='APPDATA drive not fixed';return}
 $dir=Join-Path $base 'Microsoft\Windows\Recent';$root=[IO.Path]::GetPathRoot($dir);$cur=$root;foreach($part in $dir.Substring($root.Length).Split('\')){if(-not $part){continue};$cur=Join-Path $cur $part;if(Test-Path -LiteralPath $cur -ErrorAction Stop){$it=Get-Item -LiteralPath $cur -Force -ErrorAction Stop;if(($it.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0){$script:recentStatus='Skipped';$script:recentDetail='Reparse point in Recent ancestor';return}}}
 if(-not(Test-Path -LiteralPath $dir -PathType Container -ErrorAction Stop)){return};$cut=(Get-Date).AddDays(-30);$items=@(Get-ChildItem -LiteralPath $dir -Filter '*.lnk' -File -ErrorAction Stop|Where-Object{$_.LastWriteTime -ge $cut}|Sort-Object LastWriteTime -Descending|Select-Object -First 501);if($items.Count -gt 500){$script:recentStatus='Truncated'};foreach($f in @($items|Select-Object -First 500)){$name=$f.Name;if(Suspicious $name){$name='[REDACTED]'};[pscustomobject]@{ShortcutName=$name;ShortcutLastWriteTime=$f.LastWriteTime.ToString('o');TimeMeaning='Shortcut modification time, not confirmed document use';Target='Not resolved'}}
}
function OfficeInfo {$list=New-Object 'System.Collections.Generic.List[object]';$err=0;foreach($key in @('HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration')){try{if(-not(Test-Path -LiteralPath $key -ErrorAction Stop)){continue};$p=Get-ItemProperty -LiteralPath $key;$list.Add([pscustomobject]@{ProductIds=$p.ProductReleaseIds;Version=$p.ClientVersionToReport;Platform=$p.Platform})}catch{$err++}};if($err){$script:officeStatus=if($list.Count){'Partial'}else{'Failed'}};$script:officeDetail='Click-to-Run metadata only; read errors='+$err;return $list.ToArray()}
function MakeTable([string]$name,[object[]]$rows,[string[]]$cols){$dt=New-Object System.Data.DataTable;$dt.TableName=$name;foreach($c in $cols){[void]$dt.Columns.Add($c,[string])};foreach($r in $rows){$dr=$dt.NewRow();foreach($c in $cols){$dr[$c]=[string]$r.$c};[void]$dt.Rows.Add($dr)};return ,$dt}
function CreateWorkbook([object[]]$selfTests,[object]$meta){$xlsx=Join-Path $script:Out 'LNB_Collector.xlsx';AssertOnUsb $xlsx;$all=[ordered]@{};foreach($n in $Sheets.Keys){$all[$n]=@($script:Rows[$n])};$all['Metadata']=@($meta);$all['SelfTest']=$selfTests;$all['Status']=@($script:Statuses.ToArray());$first=$true;foreach($n in $all.Keys){$cols=if($Sheets.Contains($n)){$Sheets[$n]}elseif($n -eq 'Metadata'){@('ToolVersion','Line','Computer','Account','UsbSerial','RegistrationGuid','Started','Finished','Completion','Limitations')}elseif($n -eq 'SelfTest'){@('Name','Passed')}else{@('Stage','Status','Rows','Started','Finished','Detail')};$dt=MakeTable $n $all[$n] $cols;VerifyUsb;PathHasReparse $xlsx $script:Root;if($first -and (Test-Path -LiteralPath $xlsx)){throw 'XLSX exists; refusing overwrite'};if($first){Export-Excel -InputObject $dt -Path $xlsx -WorksheetName $n -NoNumberConversion '*' -ErrorAction Stop;$first=$false}else{VerifyUsb;PathHasReparse $xlsx $script:Root;Export-Excel -InputObject $dt -Path $xlsx -WorksheetName $n -NoNumberConversion '*' -ErrorAction Stop}}
 VerifyUsb;PathHasReparse $xlsx $script:Root;$pkg=Open-ExcelPackage -Path $xlsx -ErrorAction Stop;try{$actual=@($pkg.Workbook.Worksheets|ForEach-Object{$_.Name});if($actual.Count -ne 13){throw 'Workbook sheet count is not 13'};foreach($n in $all.Keys){$ws=$pkg.Workbook.Worksheets[$n];if($null -eq $ws -or $null -eq $ws.Dimension){throw ('Missing/empty worksheet: '+$n)};$expectedRows=@($all[$n]).Count+1;$expectedCols=if($Sheets.Contains($n)){$Sheets[$n].Count}elseif($n -eq 'Metadata'){10}elseif($n -eq 'SelfTest'){2}else{6};if($ws.Dimension.End.Row -ne $expectedRows -or $ws.Dimension.End.Column -ne $expectedCols){throw ('Worksheet dimensions mismatch: '+$n)}};$statusWs=$pkg.Workbook.Worksheets['Status'];$xlsxRow=@($script:Statuses.ToArray()).Count+1;$statusWs.Cells[$xlsxRow,2].Value='Success';$statusWs.Cells[$xlsxRow,3].Value='13';$statusWs.Cells[$xlsxRow,5].Value=(Get-Date).ToString('o');$statusWs.Cells[$xlsxRow,6].Value='13 worksheets reopened and dimensions verified';$pkg.Save()}finally{$pkg.Dispose()};VerifyUsb;PathHasReparse $xlsx $script:Root;$pkg=Open-ExcelPackage -Path $xlsx -ErrorAction Stop;try{if($pkg.Workbook.Worksheets.Count -ne 13){throw 'Final workbook reopen sheet count mismatch'};$statusWs=$pkg.Workbook.Worksheets['Status'];if([string]$statusWs.Cells[$xlsxRow,2].Value -ne 'Success'){throw 'Final workbook xlsx status not Success'}}finally{$pkg.Dispose()}
}
try {
 if($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1){throw 'Windows PowerShell 5.1 Desktop required'}
 if($Register){RegisterUsb}
 $script:scriptMruStatus='Success';$script:scriptMruDetail='';$script:officeStatus='Success';$script:officeDetail='';$script:recentStatus='Success';$script:recentDetail='';$tests=@(SelfTest);$failed=@($tests|Where-Object{-not $_.Passed}).Count;if($TestOnly){$tests|ConvertTo-Json -Depth 4;if($failed){exit 3};exit 0};if($failed){throw 'Self-test/parser failed; collection refused'}
 VerifyUsb
 ValidateDependency
 if($PrepareOnly){Write-Host 'USB registration and approved ImportExcel 7.8.10 module checks passed. No collection/output was performed.';exit 0}
 if(-not $Line){$Line=Read-Host 'Line L1/L2/L3'};if($Line -notin @('L1','L2','L3')){exit 2}
 Write-Host ("USB serial: $UsbSerial; Line: $Line; PC: $env:COMPUTERNAME; output root: $Root\data\LNB_調査")
 if((Read-Host 'Check approved account/timing and type YES to collect') -cne 'YES'){exit 2}
  $base=Join-Path $Root ('data\LNB_調査\'+$Line+'_'+$env:COMPUTERNAME+'_'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'_'+[guid]::NewGuid().ToString('N'))
  if(Test-Path -LiteralPath $base){throw 'Output run directory already exists; refusing reuse'};EnsureSafeDir $base;VerifyUsb;PathHasReparse $base $script:Root;$script:Out=$base;$created=Get-Item -LiteralPath $base -Force -ErrorAction Stop;if(($created.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0){throw 'Output run directory became a reparse point'}
 $id=[Security.Principal.WindowsIdentity]::GetCurrent();$principal=New-Object Security.Principal.WindowsPrincipal -ArgumentList $id;$admin=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
 $meta=[ordered]@{ToolVersion=$Version;Line=$Line;Computer=$env:COMPUTERNAME;Account=$id.Name;UsbSerial=$UsbSerial;RegistrationGuid=$script:RegistrationGuid;Started=(Get-Date).ToString('o');Finished='';Completion='Running';Limitations='MRU is not proof of actual use or timestamp; paths sensitive; no browser/credentials/content/args/window title; USB serial/volume/GUID marker is not cryptographic authentication'}
  Utf8File (Join-Path $Out 'selftest.json') (ConvertTo-Json -InputObject $tests -Depth 4);WriteState
  $metaCopy=[pscustomobject]@{ToolVersion=$meta.ToolVersion;Line=$meta.Line;Computer=$meta.Computer;Account=$meta.Account;UsbSerial=$meta.UsbSerial;RegistrationGuid=$meta.RegistrationGuid;Started=$meta.Started;Finished='';Completion='Running';Limitations=$meta.Limitations}
  Stage computer {Get-CimInstance Win32_ComputerSystem -OperationTimeoutSec 10|Select-Object Name,Manufacturer,Model,TotalPhysicalMemory}
  Stage os {Get-CimInstance Win32_OperatingSystem -OperationTimeoutSec 10|Select-Object Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime}
  Stage cpu {Get-CimInstance Win32_Processor -OperationTimeoutSec 10|Select-Object DeviceID,Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed}
  Stage memory {Get-CimInstance Win32_PhysicalMemory -OperationTimeoutSec 10|Select-Object DeviceLocator,BankLabel,Capacity,Speed}
  Stage disks {Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' -OperationTimeoutSec 10|Select-Object DeviceID,VolumeName,Size,FreeSpace,FileSystem}
  Stage printers {Get-CimInstance Win32_Printer -OperationTimeoutSec 10|Select-Object Name,DriverName,PortName,Default,WorkOffline}
  Stage processes {Get-Process|Select-Object -First 501|Select-Object ProcessName,Id}
  $script:scriptMruStatus='Success';$script:scriptMruDetail='';Stage excel_recent {ExcelRecent}
  $script:officeStatus='Success';$script:officeDetail='';Stage office {OfficeInfo}
  $script:recentStatus='Success';$script:recentDetail='';Stage windows_recent {Recent}
  WriteState
  $warnings=@($script:Statuses|Where-Object{$_.Status -in @('Failed','Partial','Truncated','Skipped')}).Count;$meta.Finished=(Get-Date).ToString('o');$meta.Completion=if($warnings){'CompletedWithWarnings'}else{'Completed'};$metaCopy.Finished=$meta.Finished;$metaCopy.Completion=$meta.Completion
  try{$script:Statuses.Add([pscustomobject]@{Stage='xlsx';Status='Pending';Rows=0;Started=$meta.Finished;Finished='';Detail='Workbook creation and 13-sheet verification pending'});CreateWorkbook $tests $metaCopy;$xs=$script:Statuses|Where-Object{$_.Stage -eq 'xlsx'}|Select-Object -Last 1;$xs.Status='Success';$xs.Rows=13;$xs.Finished=(Get-Date).ToString('o');$xs.Detail='13 worksheets reopened and dimensions verified'}catch{$script:Statuses.Add([pscustomobject]@{Stage='xlsx';Status='Failed';Rows=0;Started=$meta.Finished;Finished=(Get-Date).ToString('o');Detail=$_.Exception.GetType().Name});WriteState;throw}
 WriteState
 $warnings=@($script:Statuses|Where-Object{$_.Status -in @('Failed','Partial','Truncated','Skipped')}).Count;$meta.Completion=if($warnings){'CompletedWithWarnings'}else{'Completed'}
  Utf8File (Join-Path $Out 'summary.json') (ConvertTo-Json -InputObject ([ordered]@{Metadata=$meta;Warnings=$warnings;Statuses=@($script:Statuses.ToArray())}) -Depth 7)
  Utf8File (Join-Path $Out 'COMPLETE.txt') ($meta.Completion+"`r`n"+$meta.Finished);try{[void][IO.File]::ReadAllText((Join-Path $Out 'COMPLETE.txt'))}catch{throw 'COMPLETE.txt write verification failed'}
 Write-Host ($meta.Completion+': '+$Out);if($warnings){exit 10};exit 0
 } catch {Write-Host ('Stopped: '+$_.Exception.GetType().Name+'; '+$_.Exception.Message);if($script:Out){try{$script:Statuses.Add([pscustomobject]@{Stage='fatal';Status='Failed';Rows=0;Started=(Get-Date).ToString('o');Finished=(Get-Date).ToString('o');Detail=$_.Exception.GetType().Name});try{WriteState}catch{};Write-Host ('Partial data may exist at '+$script:Out+'; absence of COMPLETE.txt means incomplete')}catch{}};exit 5}
