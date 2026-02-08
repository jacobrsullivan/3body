#!/usr/bin/env bash
set -euo pipefail

repo="/Users/jacobsullivan/.codex/worktrees/8fe0/3body"
cd "$repo"

echo "[wp1-smoke] python verify_setup.py"
python verify_setup.py

echo "[wp1-smoke] import check"
python - <<'PY'
from src.python.integrators.ias15 import IAS15Integrator
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer
from src.python.utils.dynamics import jacobi_constant
print("imports ok")
PY

echo "[wp1-smoke] done"
