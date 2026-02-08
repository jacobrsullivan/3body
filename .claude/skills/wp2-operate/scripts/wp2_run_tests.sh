#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

MODE="${1:-}"

if ! command -v pytest >/dev/null 2>&1; then
  echo "pytest not found in PATH. Activate your Python environment and try again." >&2
  exit 2
fi

if [[ "${MODE}" == "--fast" ]]; then
  pytest \
    tests/geometry/test_connection.py \
    tests/geometry/test_jm_metric.py \
    tests/lifts/test_s1_bundle.py \
    -v
else
  pytest \
    tests/unit/reduction/ \
    tests/geometry/ \
    tests/lifts/ \
    -v
fi
