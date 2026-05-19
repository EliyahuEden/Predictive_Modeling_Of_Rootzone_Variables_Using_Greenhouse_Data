@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
    if errorlevel 1 (
        echo Existing local Python environment uses an unsupported Python version.
        echo Removing .venv so it can be recreated with Python 3.12, the version used to build the model.
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local Python environment...
    set "PY_CMD="
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.12 -c "import sys" >nul 2>nul
        if not errorlevel 1 set "PY_CMD=py -3.12"
    )
    if not defined PY_CMD (
        where python >nul 2>nul
        if not errorlevel 1 (
            python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
            if not errorlevel 1 set "PY_CMD=python"
        )
    )
    if not defined PY_CMD (
        where python3 >nul 2>nul
        if not errorlevel 1 (
            python3 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
            if not errorlevel 1 set "PY_CMD=python3"
        )
    )
    if not defined PY_CMD (
        echo Python 3.12 was not found.
        echo The final model was built with Python 3.12.13 and scikit-learn 1.7.1.
        echo Python 3.14 is not compatible with these pinned model packages on Windows.
        echo Install Python 3.12 from https://www.python.org/downloads/windows/
        echo Make sure to check "Add python.exe to PATH", then run this file again.
        pause
        exit /b 1
    )
    !PY_CMD! -m venv .venv
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
