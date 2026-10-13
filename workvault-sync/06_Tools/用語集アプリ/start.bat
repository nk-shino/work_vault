@echo off
rem Glossary launcher. ASCII only: cmd.exe reads .bat files with the system code page.
rem First run sets up the environment, then the app opens in the browser.
cd /d "%~dp0"
python tasks.py
pause
