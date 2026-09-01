#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.smoke_check
python -m streamlit run src/ui/app.py --server.port 8501
