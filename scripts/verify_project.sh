#!/usr/bin/env bash
#
# Authoritative repository verification entry point.
#
# Usage:
#   ./scripts/verify_project.sh         # build and run the complete non-slow suite
#   ./scripts/verify_project.sh --all   # include tests marked slow

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-}"

if [[ "$MODE" != "" && "$MODE" != "--all" ]]; then
  echo "Usage: $0 [--all]" >&2
  exit 2
fi

cd "$PROJECT_ROOT"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "CONDA_PREFIX is not set. Activate the pinned Python 3.11 environment." >&2
  exit 2
fi

export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

echo "Project: $PROJECT_ROOT"
echo "Environment: $CONDA_PREFIX"
python --version

PYTHON_BIN=python ./scripts/build_qd_python.sh
./scripts/build_cpp.sh
python verify_setup.py

if [[ "$MODE" == "--all" ]]; then
  python -m pytest -q -p no:cacheprovider
else
  python -m pytest -q -m "not slow" -p no:cacheprovider
fi

echo "Project verification passed."
