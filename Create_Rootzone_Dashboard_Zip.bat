@echo off
setlocal

set "ROOTZONE_PROJECT_ROOT=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop'; " ^
  "$root = $env:ROOTZONE_PROJECT_ROOT; " ^
  "$src = Join-Path $root 'scripts\rootzone_full_etl_pipeline'; " ^
  "$dist = Join-Path $root 'dist'; " ^
  "$pkg = Join-Path $dist 'rootzone_dashboard_app'; " ^
  "$zip = Join-Path $dist 'rootzone_dashboard_app.zip'; " ^
  "New-Item -ItemType Directory -Force -Path $dist | Out-Null; " ^
  "if (Test-Path $pkg) { Remove-Item -Recurse -Force $pkg }; " ^
  "New-Item -ItemType Directory -Force -Path $pkg | Out-Null; " ^
  "$files = @('rootzone_web_app.py','rootzone_full_etl.py','dashboard_template.html','fertilizer_dose_presets.json','requirements.txt','run_windows.bat','run_mac_linux.sh','Dockerfile','docker-compose.yml','.dockerignore','.gitignore','netlify.toml','DEPLOYMENT.md','README.md','micro_climate_3day_unified_model.joblib','v8_unified_model_48h_no_rh_shared_model.joblib','v8_unified_model_48h_no_rh_model_meta.json'); " ^
  "foreach ($file in $files) { Copy-Item -LiteralPath (Join-Path $src $file) -Destination $pkg -Force }; " ^
  "Copy-Item -LiteralPath (Join-Path $src 'netlify_site') -Destination $pkg -Recurse -Force; " ^
  "if (Test-Path $zip) { Remove-Item -Force $zip }; " ^
  "Compress-Archive -Path $pkg -DestinationPath $zip -Force; " ^
  "Write-Host 'Created package:' $zip"

if errorlevel 1 (
    echo Failed to create the package.
    pause
    exit /b 1
)

pause
