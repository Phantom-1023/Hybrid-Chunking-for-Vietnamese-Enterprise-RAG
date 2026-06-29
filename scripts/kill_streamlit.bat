@echo off
setlocal
echo [INFO] Finding Streamlit-related Python processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and ($_.CommandLine -match 'streamlit' -or $_.CommandLine -match 'ui/app.py' -or $_.CommandLine -match 'ui\\app.py') }; if (-not $procs) { Write-Output '[INFO] No Streamlit Python process found.'; exit 0 }; $procs | ForEach-Object { Write-Output ('[INFO] Killing PID=' + $_.ProcessId + ' CMD=' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo [DONE] kill_streamlit complete.
endlocal
