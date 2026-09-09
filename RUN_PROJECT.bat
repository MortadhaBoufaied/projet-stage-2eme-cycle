@echo off
setlocal enabledelayedexpansion

echo === Finance Decision Studio ===
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo Project root: %PROJECT_ROOT%

:: Create virtual environment if missing
if not exist .venv (
    echo [1/4] Creating virtual environment...
    python -m venv .venv
)

:: Activate venv
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Verify Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PY_VER=%%i"
echo    Python !PY_VER!

:: Install dependencies if needed
echo [3/4] Checking dependencies...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install -r requirements.txt --quiet 2>nul

:: Validate setup
echo [4/4] Running smoke check...
python -m src.smoke_check
if errorlevel 1 (
    echo ERROR: Smoke check failed. Fix issues above before continuing.
    pause
    exit /b 1
)

:: Start the app
echo.
echo Starting Finance Decision Studio on http://localhost:8501
echo Press Ctrl+C to stop.
echo.
python -m streamlit run src\ui\app.py --server.port 8501

endlocal
