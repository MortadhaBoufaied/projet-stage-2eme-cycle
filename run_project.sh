#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== Finance Decision Studio ==="
echo "Project root: $PROJECT_ROOT"

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "   Python $PYTHON_VERSION"

# Install dependencies if needed
echo "[3/4] Checking dependencies..."
python -m pip install --upgrade pip --quiet 2>/dev/null || true
python -m pip install -r requirements.txt --quiet 2>/dev/null || true

# Validate setup
echo "[4/4] Running smoke check..."
python -m src.smoke_check

# Start the app
echo ""
echo "Starting Finance Decision Studio on http://localhost:8501"
echo "Press Ctrl+C to stop."
echo ""
python -m streamlit run src/ui/app.py --server.port 8501
