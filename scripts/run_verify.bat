@echo off
setlocal
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
echo [INFO] Running verify mode...
python main.py --mode verify
endlocal
