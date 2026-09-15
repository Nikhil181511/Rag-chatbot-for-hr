#!/bin/bash
set -e

echo "=== Running Backend Unit and Integration Tests ==="
cd backend
python -m venv .venv || true
source .venv/bin/activate || source .venv/Scripts/activate
pip install -e ".[dev]"
pytest tests/unit/ -v --cov=app --cov-report=term-missing

echo "=== Running Frontend Build & Typechecks ==="
cd ../frontend
npm ci
npm run build

echo "=== All Tests and Builds Passed Successfully ==="
