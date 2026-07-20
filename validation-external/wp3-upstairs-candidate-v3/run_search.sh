#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION_ROOT="$REPO_ROOT/validation-external"
SPATIAL_ROOT="$VALIDATION_ROOT/wp3-spatial-validation-v2"
SOURCE_ROOT="$VALIDATION_ROOT/wp3-v2-exploration"
SPEC="$WS_DIR/search_spec.json"
CORPUS="$WS_DIR/data/search_corpus.json"
SOURCE_CORPUS="$SOURCE_ROOT/data/exploration_corpus.json"
SPATIAL_CORPUS="$SPATIAL_ROOT/data/qualification_corpus.json"
COMMITMENTS="$SOURCE_ROOT/sealed/publication_holdout_commitments.json"
LOCK="$WS_DIR/reports/wp3_upstairs_v3_search_lock.json"
RESULTS="$WS_DIR/results/search_results.json"
GATE="$WS_DIR/results/staged_gate.json"
REPORT="$WS_DIR/reports/wp3_upstairs_v3_search_report.md"

export PYTHONPATH="$REPO_ROOT:$VALIDATION_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/data" "$WS_DIR/results" "$WS_DIR/reports"

case "${1:-}" in
  build)
    python "$WS_DIR/scripts/build_corpus.py" --spec "$SPEC" \
      --source-corpus "$SOURCE_CORPUS" --commitments "$COMMITMENTS" \
      --output "$CORPUS"
    ;;
  freeze)
    python "$WS_DIR/scripts/freeze_search.py" \
      --repo-root "$REPO_ROOT" --prefix WP3-UP-CAND-v3 \
      --spec "$SPEC" --corpus "$CORPUS" --commitments "$COMMITMENTS" \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/wp3-upstairs-candidate-v3 \
      --scope validation-external/wp3-spatial-validation-v2 \
      --scope validation-external/wp3-v2-exploration/data/exploration_corpus.json \
      --scope validation-external/wp3-v2-exploration/sealed/publication_holdout_commitments.json \
      --scope src/python/wp3_upstairs_v3 --scope src/python/upstairs_ks \
      --scope src/python/wp3_exploration_v2/__init__.py \
      --scope src/python/wp3_exploration_v2/normalization.py \
      --scope src/python/wp3_exploration_v3 \
      --scope tests/wp3_upstairs_v3 --scope tests/wp3_exploration_v3 \
      --scope tests/wp3_upstairs_campaign_v3 \
      --output "$LOCK"
    ;;
  search)
    python "$VALIDATION_ROOT/verify_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP3-UP-CAND-v3 --lock "$LOCK"
    python "$WS_DIR/scripts/run_search.py" --spec "$SPEC" --corpus "$CORPUS" \
      --source-corpus "$SOURCE_CORPUS" --spatial-corpus "$SPATIAL_CORPUS" \
      --spatial-development "$SPATIAL_ROOT/results/development.json" \
      --spatial-calibration "$SPATIAL_ROOT/results/calibration.json" \
      --commitments "$COMMITMENTS" --lock "$LOCK" \
      --output "$RESULTS" --gate-output "$GATE"
    ;;
  report)
    python "$WS_DIR/scripts/render_report.py" --spec "$SPEC" \
      --results "$RESULTS" --gate "$GATE" --output "$REPORT"
    ;;
  finalize)
    python "$WS_DIR/scripts/finalize_search.py" --spec "$SPEC" --corpus "$CORPUS" \
      --lock "$LOCK" --results "$RESULTS" --gate "$GATE" \
      --output "$WS_DIR/reports/wp3_upstairs_v3_search_record.json"
    ;;
  *)
    echo "usage: $0 build|freeze|search|report|finalize" >&2
    exit 2
    ;;
esac
