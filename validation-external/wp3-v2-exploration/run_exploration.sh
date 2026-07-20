#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WS_DIR/../.." && pwd)"
SPATIAL_ROOT="$REPO_ROOT/validation-external/wp3-spatial-validation-v2"
SPEC="$WS_DIR/exploration_spec.json"
CORPUS="$WS_DIR/data/exploration_corpus.json"
COMMITMENTS="$WS_DIR/sealed/publication_holdout_commitments.json"
RESULT="$WS_DIR/results/exploration_results.json"
GATE="$WS_DIR/results/staged_gate.json"
REPORT="$WS_DIR/reports/wp3_v2_exploration_report.md"

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/validation-external${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/data" "$WS_DIR/results" "$WS_DIR/reports"

case "${1:-}" in
  build)
    python "$WS_DIR/scripts/build_corpus.py" --spec "$SPEC" \
      --spatial-corpus "$SPATIAL_ROOT/data/qualification_corpus.json" \
      --commitments "$COMMITMENTS" --output "$CORPUS"
    ;;
  run)
    python "$WS_DIR/scripts/run_exploration.py" --spec "$SPEC" \
      --corpus "$CORPUS" \
      --spatial-corpus "$SPATIAL_ROOT/data/qualification_corpus.json" \
      --spatial-development "$SPATIAL_ROOT/results/development.json" \
      --spatial-calibration "$SPATIAL_ROOT/results/calibration.json" \
      --commitments "$COMMITMENTS" --output "$RESULT" --gate-output "$GATE"
    python "$WS_DIR/scripts/render_report.py" --result "$RESULT" \
      --gate "$GATE" --output "$REPORT"
    ;;
  all)
    "$0" build
    "$0" run
    ;;
  *)
    echo "usage: $0 build|run|all" >&2
    exit 2
    ;;
esac
