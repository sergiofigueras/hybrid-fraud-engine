#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m compileall -q fraud_engine training
pytest -q
python -m training.demo

echo
echo "Project verification completed successfully."
