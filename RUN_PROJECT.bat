@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.10 or newer is required.& pause & exit /b 1)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m src.smoke_check
if errorlevel 1 (pause & exit /b 1)
python -m streamlit run src\ui\app.py --server.port 8501
