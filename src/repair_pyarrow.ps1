$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Project interpreter not found: $Python" }
Set-Location $Root
& $Python -m pip uninstall -y pyarrow numpy
& $Python -m pip cache purge
& $Python -m pip install --no-cache-dir --force-reinstall "numpy==1.26.4" "pyarrow==16.1.0"
& $Python -c "import numpy, pyarrow; print('NumPy:', numpy.__version__); print('PyArrow:', pyarrow.__version__); assert numpy.__version__ == '1.26.4'; assert pyarrow.__version__ == '16.1.0'"
Write-Host "Repair verified. Close every Streamlit terminal, then run:"
Write-Host "& '$Python' -m streamlit run src/ui/app.py"
