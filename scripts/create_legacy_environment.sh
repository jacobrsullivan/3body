#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${1:-3body-legacy}"
MAMBA_BIN="${MAMBA_BIN:-/opt/homebrew/bin/micromamba}"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$HOME/micromamba}"

if [[ ! -x "$MAMBA_BIN" ]]; then
  echo "micromamba is not executable at $MAMBA_BIN" >&2
  exit 2
fi
if [[ -e "$MAMBA_ROOT_PREFIX/envs/$ENV_NAME" ]]; then
  echo "Refusing to reuse existing environment: $MAMBA_ROOT_PREFIX/envs/$ENV_NAME" >&2
  echo "Choose a new environment name for a clean baseline bootstrap." >&2
  exit 2
fi

cd "$ROOT_DIR"

"$MAMBA_BIN" create -y -n "$ENV_NAME" -f environment-legacy.yml
"$MAMBA_BIN" run -n "$ENV_NAME" env \
  POETRY_VIRTUALENVS_CREATE=false poetry install --no-root --only main

# Poetry's pybind11 2.13.6 headers are the qualified qd_python build input.
"$MAMBA_BIN" run -n "$ENV_NAME" ./scripts/build_qd_python.sh
