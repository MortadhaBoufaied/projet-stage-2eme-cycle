@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo ERROR: Project interpreter not found: %PY%
  echo Run this script from the project containing .venv and src.
  exit /b 1
)
cd /d "%ROOT%"
echo Using: %PY%
"%PY%" -m pip uninstall -y pyarrow numpy
"%PY%" -m pip cache purge
"%PY%" -m pip install --no-cache-dir --force-reinstall "numpy==1.26.4" "pyarrow==16.1.0"
if errorlevel 1 exit /b 1
"%PY%" -c "import numpy, pyarrow; print('NumPy:', numpy.__version__); print('PyArrow:', pyarrow.__version__); assert numpy.__version__ == '1.26.4'; assert pyarrow.__version__ == '16.1.0'"
if errorlevel 1 exit /b 1
echo Repair verified. Close every Streamlit terminal, then run:
echo "%PY%" -m streamlit run src\ui\app.py
endlocal
