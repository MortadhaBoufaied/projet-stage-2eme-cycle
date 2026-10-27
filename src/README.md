# Source package

Canonical package with no nested `src` directory.

- `agents`: credit, demand, and recommendation engines
- `services`: schemas, training, model registry, company profiles, policy application
- `data_generator`: optional synthetic development data
- `ui`: Streamlit workspace
- `smoke_check.py`: end-to-end validation

Run from the project root with `python -m src.smoke_check` and `python -m streamlit run src/ui/app.py`.
## NumPy / PyArrow compatibility repair
If Streamlit reports `pyarrow requires NumPy 2.0 or newer, found 1.26.4`, activate the project virtual environment and run one of:

- Command Prompt: `src\repair_pyarrow.bat`
- PowerShell: `powershell -ExecutionPolicy Bypass -File src\repair_pyarrow.ps1`
- Manual: `python -m pip install --no-cache-dir --force-reinstall -r src/requirements-compat.txt`

Then fully stop and restart Streamlit. The compatibility file pins NumPy 1.26.4 with PyArrow 16.1.0 so Streamlit DataFrame rendering loads a matching binary build.
