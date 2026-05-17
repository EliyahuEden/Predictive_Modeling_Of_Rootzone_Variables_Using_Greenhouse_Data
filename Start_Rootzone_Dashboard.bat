@echo off
setlocal

set "APP_DIR=%~dp0scripts\rootzone_full_etl_pipeline"

if not exist "%APP_DIR%\run_windows.bat" (
    echo Rootzone dashboard runner was not found:
    echo %APP_DIR%\run_windows.bat
    pause
    exit /b 1
)

call "%APP_DIR%\run_windows.bat"
