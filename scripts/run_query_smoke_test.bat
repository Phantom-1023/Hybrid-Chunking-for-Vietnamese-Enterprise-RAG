@echo off
setlocal
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
echo [INFO] Running CLI query smoke test...
python main.py --mode query --strategy fixed --question "Minh Tu da dat thanh tich gi trong Asia Next Top Model mua 5?"
endlocal
