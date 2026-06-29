@echo off
echo [WARNING] Emergency cleanup: this kills all python.exe/pythonw.exe processes for current user.
echo [WARNING] Use only when the machine is lagging badly or Python processes are stuck.
timeout /t 5
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process python,pythonw -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ('[INFO] Killing PID=' + $_.Id); Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }"
echo [DONE] emergency Python cleanup complete.
