@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.CommandLine -like '*rootzone_web_app.py*' }; if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; Write-Host 'Rootzone dashboard stopped.' } else { Write-Host 'Rootzone dashboard was not running.' }"

pause
