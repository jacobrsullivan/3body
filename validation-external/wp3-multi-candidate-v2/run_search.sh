#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION="$ROOT/validation-external"
V1_ROOT="$VALIDATION/wp3-multi-candidate-v1"
SPATIAL_ROOT="$VALIDATION/wp3-spatial-validation-v2"
WP1_ROOT="$VALIDATION/wp1-catalogue-n3bp-validation"
SOURCE_ROOT="$VALIDATION/wp3-v2-exploration"
SPEC="$WS_DIR/search_spec.json"
CORPUS="$V1_ROOT/data/search_corpus.json"
COMMITMENTS="$SOURCE_ROOT/sealed/publication_holdout_commitments.json"
WP1_CATALOGUE="$WP1_ROOT/data/native_catalogue.json"
LOCK="$WS_DIR/reports/wp3_multi_v2_search_lock.json"
RESULTS="$WS_DIR/results/search_results.json"
GATE="$WS_DIR/results/publication_gate.json"

export PYTHONPATH="$ROOT:$VALIDATION${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/results" "$WS_DIR/reports"

case "${1:-}" in
  test)
    python -m pytest tests/wp3_multi_v2 -q
    ;;
  freeze)
    python "$WS_DIR/scripts/freeze_search.py" --repo-root "$ROOT" \
      --prefix WP3-MULTI-CAND-v2 --spec "$SPEC" --corpus "$CORPUS" \
      --commitments "$COMMITMENTS" \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/verify_qualification.py \
      --scope validation-external/validation_external_import.py \
      --scope validation-external/wp3-multi-candidate-v2 \
      --scope validation-external/wp3-multi-candidate-v1/scripts/run_search.py \
      --scope validation-external/wp3-multi-candidate-v1/data/search_corpus.json \
      --scope validation-external/wp3-multi-candidate-v1/reports \
      --scope validation-external/wp3-multi-candidate-v1/results/publication_gate.json \
      --scope validation-external/wp2-multi-validation/reports \
      --scope validation-external/wp1-catalogue-n3bp-validation \
      --scope validation-external/wp3-spatial-validation-v2 \
      --scope validation-external/wp3-v2-exploration/sealed/publication_holdout_commitments.json \
      --scope src/python/ks --scope src/python/n3bp_qualification \
      --scope src/python/threebody_flow --scope src/python/threebody_reduction \
      --scope src/python/wp1_catalogue_n3bp_v1 --scope src/python/wp2_multi_v1 \
      --scope src/python/wp3_exploration_v2/normalization.py \
      --scope src/python/wp3_exploration_v3 --scope src/python/wp3_multi_v1 \
      --scope src/python/wp3_multi_v2 --scope tests/wp3_multi_v2 \
      --scope pyproject.toml --scope poetry.lock --scope environment.yml \
      --output "$LOCK"
    ;;
  execute)
    python "$VALIDATION/verify_qualification.py" --repo-root "$ROOT" \
      --prefix WP3-MULTI-CAND-v2 --lock "$LOCK"
    python "$WS_DIR/scripts/run_search.py" --spec "$SPEC" --corpus "$CORPUS" \
      --spatial-corpus "$SPATIAL_ROOT/data/qualification_corpus.json" \
      --spatial-development "$SPATIAL_ROOT/results/development.json" \
      --spatial-calibration "$SPATIAL_ROOT/results/calibration.json" \
      --wp1-catalogue "$WP1_CATALOGUE" --commitments "$COMMITMENTS" \
      --lock "$LOCK" --output "$RESULTS"
    python "$WS_DIR/scripts/evaluate_publication_gate.py" --spec "$SPEC" \
      --corpus "$CORPUS" --lock "$LOCK" --results "$RESULTS" \
      --commitments "$COMMITMENTS" --output "$GATE"
    ;;
  finalize)
    python "$WS_DIR/scripts/finalize_search.py" --spec "$SPEC" \
      --corpus "$CORPUS" --lock "$LOCK" --results "$RESULTS" --gate "$GATE" \
      --record "$WS_DIR/reports/wp3_multi_v2_search_record.json" \
      --report "$WS_DIR/reports/wp3_multi_v2_search_report.md" \
      --decision "$WS_DIR/reports/wp3_multi_v2_candidate_decision.json"
    ;;
  *)
    echo "usage: $0 test|freeze|execute|finalize" >&2
    exit 2
    ;;
esac
