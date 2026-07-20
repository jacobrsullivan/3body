#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-}" in
  freeze|run|verify)
    python -m src.python.wp4_upstairs_v3.cli "$1"
    ;;
  *)
    echo "usage: $0 {freeze|run|verify}" >&2
    exit 2
    ;;
esac
