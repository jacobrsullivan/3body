#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION_ROOT="$REPO_ROOT/validation-external"
SPATIAL_ROOT="$VALIDATION_ROOT/wp3-spatial-validation-v2"
SPEC="$WS_DIR/qualification_spec.json"
CORPUS="$WS_DIR/data/qualification_corpus.json"
SPATIAL_CORPUS="$SPATIAL_ROOT/data/qualification_corpus.json"
SOURCE_MANIFEST="$WS_DIR/sources/manifest.json"
RESULTS="$WS_DIR/results"
REPORTS="$WS_DIR/reports"
LOCK="$REPORTS/wp2_up_qualification_lock.json"

export PYTHONPATH="$REPO_ROOT:$VALIDATION_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/data" "$RESULTS" "$REPORTS"

run_split() {
  local split="$1"
  local lock_args=()
  if [[ "$split" == "holdout" ]]; then
    lock_args=(--lock "$LOCK")
  fi
  python "$WS_DIR/scripts/run_qualification.py" \
    --spec "$SPEC" --corpus "$CORPUS" --spatial-corpus "$SPATIAL_CORPUS" \
    --spatial-results "$SPATIAL_ROOT/results/$split.json" --split "$split" \
    --output "$RESULTS/$split.json" "${lock_args[@]}"
  python "$WS_DIR/scripts/evaluate_qualification.py" \
    --spec "$SPEC" --corpus "$CORPUS" --results "$RESULTS/$split.json" \
    --output "$RESULTS/${split}_evaluation.json" "${lock_args[@]}"
}

case "${1:-}" in
  build)
    python "$WS_DIR/scripts/build_corpus.py" --spec "$SPEC" \
      --spatial-corpus "$SPATIAL_CORPUS" --output "$CORPUS"
    ;;
  prepare)
    run_split development
    run_split calibration
    ;;
  freeze)
    python "$VALIDATION_ROOT/freeze_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP2-UPQ-v1 \
      --spec "$SPEC" --corpus "$CORPUS" --source-manifest "$SOURCE_MANIFEST" \
      --development "$RESULTS/development_evaluation.json" \
      --calibration "$RESULTS/calibration_evaluation.json" \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/freeze_qualification.py \
      --scope validation-external/verify_qualification.py \
      --scope validation-external/finalize_qualification.py \
      --scope validation-external/wp2-up-validation \
      --scope src/python/upstairs_ks --scope src/python/ks \
      --scope src/python/threebody_flow --scope tests/upstairs_ks \
      --scope tests/wp2_up_qualification --scope pyproject.toml \
      --scope poetry.lock --scope environment.yml --output "$LOCK"
    ;;
  holdout)
    python "$VALIDATION_ROOT/verify_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP2-UPQ-v1 --lock "$LOCK"
    run_split holdout
    ;;
  finalize)
    python "$VALIDATION_ROOT/finalize_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP2-UPQ-v1 \
      --spec "$SPEC" --corpus "$CORPUS" --source-manifest "$SOURCE_MANIFEST" \
      --lock "$LOCK" --development "$RESULTS/development_evaluation.json" \
      --calibration "$RESULTS/calibration_evaluation.json" \
      --holdout "$RESULTS/holdout_evaluation.json" \
      --record "$REPORTS/wp2_up_qualification_record.json" \
      --report "$REPORTS/wp2_up_qualification_report.md"
    ;;
  *)
    echo "usage: $0 build|prepare|freeze|holdout|finalize" >&2
    exit 2
    ;;
esac
