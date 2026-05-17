@echo off
setlocal

cd /d "%~dp0"

set "HOST=127.0.0.1"
set "PORT=8765"
set "URL=http://%HOST%:%PORT%"

netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if not errorlevel 1 (
    echo Rootzone dashboard is already running.
    start "" "%URL%"
    pause
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local Python environment...
    set "PY_CMD="
    where py >nul 2>nul && set "PY_CMD=py -3"
    if not defined PY_CMD where python >nul 2>nul && set "PY_CMD=python"
    if not defined PY_CMD (
        echo Python was not found. Install Python 3.11 or newer, then run this file again.
        pause
        exit /b 1
    )
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo Could not create the local Python environment.
        pause
        exit /b 1
    )
)

echo Installing/updating required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Could not update pip.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Could not install required packages.
    pause
    exit /b 1
)

start "" "%URL%"
echo Rootzone dashboard is running at %URL%
echo Keep this window open while using the dashboard. Press Ctrl+C to stop it.
".venv\Scripts\python.exe" rootzone_web_app.py --host %HOST% --port %PORT%
pause
