@echo off
rem ThingKeeper launcher - reliable double-click entry point.
rem Uses pythonw.exe (no console window). If you want to see errors,
rem run launch.pyw from a terminal with:  python launch.pyw
setlocal
set PYTHONW=pythonw.exe
where %PYTHONW% >nul 2>&1
if errorlevel 1 (
    set PYTHONW=py.exe
)
start "" %PYTHONW% "%~dp0launch.pyw"
endlocal
