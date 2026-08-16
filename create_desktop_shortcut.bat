@echo off
rem Create a ThingKeeper desktop shortcut for the current user.
rem Double-click this file to install the shortcut on your desktop.
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "TARGET=%SCRIPT_DIR%\launch.pyw"
set "ICON=%SCRIPT_DIR%\thingkeeper\assets\app.ico"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\ThingKeeper.lnk"

if not exist "%TARGET%" (
    echo ERROR: launch.pyw not found at:
    echo   %TARGET%
    echo Run this script from the ThingKeeper project folder.
    pause
    exit /b 1
)

if not exist "%ICON%" (
    echo WARNING: app.ico not found at:
    echo   %ICON%
    echo The shortcut will use the default .pyw icon.
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$sc = $ws.CreateShortcut('%SHORTCUT%'); " ^
  "$sc.TargetPath = '%TARGET%'; " ^
  "$sc.WorkingDirectory = '%SCRIPT_DIR%'; " ^
  "$sc.IconLocation = '%ICON%,0'; " ^
  "$sc.Description = 'ThingKeeper - desktop inventory app'; " ^
  "$sc.Save()"

if exist "%SHORTCUT%" (
    echo Shortcut created:
    echo   %SHORTCUT%
) else (
    echo Failed to create shortcut.
    pause
    exit /b 1
)

endlocal
