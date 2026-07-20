#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

phase="${1:-}"
case "$phase" in
  prepare)
    python -m src.python.wp1_catalogue_v1.cli build-corpus
    python -m src.python.wp1_catalogue_v1.cli generate
    python -m src.python.wp1_catalogue_v1.cli freeze
    python -m src.python.wp1_catalogue_v1.cli evaluate development
    python -m src.python.wp1_catalogue_v1.cli evaluate calibration
    ;;
  holdout)
    python -m src.python.wp1_catalogue_v1.cli verify-lock
    python -m src.python.wp1_catalogue_v1.cli evaluate holdout
    python -m src.python.wp1_catalogue_v1.cli finalize
    ;;
  all)
    "$0" prepare
    "$0" holdout
    ;;
  *)
    echo "usage: $0 {prepare|holdout|all}" >&2
    exit 2
    ;;
esac
