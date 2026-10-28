@echo off
setlocal
rem =====================================================
rem  ショートカット一括作成
rem  ドロップしたファイル/フォルダそれぞれのショートカット(.lnk)を
rem  元の場所に「元の名前.lnk」で作成する。
rem  既に同名のショートカットがある場合は上書きせずスキップする。
rem =====================================================

if "%~1"=="" goto usage

set CREATED=0
set SKIPPED=0

:loop
if "%~1"=="" goto summary

set "TARGET=%~1"
set "DIR=%~dp1"
set "LNK=%~dpn1.lnk"

rem パス内のシングルクォートはPowerShell用に2つ重ねてエスケープ
set "TQ=%TARGET:'=''%"
set "DQ=%DIR:'=''%"
set "LQ=%LNK:'=''%"

if exist "%LNK%" goto skipexisting

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%LQ%'); $s.TargetPath='%TQ%'; $s.WorkingDirectory='%DQ%'; $s.Save()" >nul 2>&1

if exist "%LNK%" goto created
echo 失敗: "%TARGET%"
set /a SKIPPED+=1
goto shiftloop

:created
echo 作成: "%LNK%"
set /a CREATED+=1
goto shiftloop

:skipexisting
echo スキップ: "%LNK%" は既に存在します
set /a SKIPPED+=1

:shiftloop
shift
goto loop

:summary
echo.
echo 完了: 作成 %CREATED% 件 / スキップ・失敗 %SKIPPED% 件
pause
exit /b 0

:usage
echo ショートカットを作成したいファイルやフォルダを選んで、
echo このbatファイルへドラッグアンドドロップしてください。
echo.
pause
exit /b 0
