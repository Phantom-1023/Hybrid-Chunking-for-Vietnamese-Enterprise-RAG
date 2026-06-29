@echo off
setlocal
cd /d "%~dp0.."
echo [INFO] Starting Streamlit demo at http://localhost:8503
python -m streamlit run ui/app.py --server.port 8503 --server.address localhost
endlocal
