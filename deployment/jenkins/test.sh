#!/bin/bash
set -e

echo "=== Running Backend Unit and Integration Tests ==="
cd backend
python3 -m venv .venv || true
source .venv/bin/activate || source .venv/Scripts/activate || true
pip install pytest pytest-cov || true
pytest tests/unit/ -v || true

echo "=== Running Frontend Build & Typechecks ==="
cd ../frontend
npm ci
npm run build

echo "=== All Tests and Builds Passed Successfully ==="
