#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION_ROOT="$REPO_ROOT/validation-external"
SPEC="$WS_DIR/qualification_spec.json"
CORPUS="$WS_DIR/data/qualification_corpus.json"
SOURCE_MANIFEST="$WS_DIR/sources/manifest.json"
RESULTS="$WS_DIR/results"
REPORTS="$WS_DIR/reports"
LOCK="$REPORTS/wp2_ks_qualification_lock.json"

export PYTHONPATH="$REPO_ROOT:$VALIDATION_ROOT:$WS_DIR/scripts:$WS_DIR/evaluation${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

stage="${1:-}"
mkdir -p "$RESULTS" "$REPORTS"

run_split() {
  local split="$1"
  local lock_args=()
  if [[ "$split" == "holdout" ]]; then
    lock_args=(--lock "$LOCK")
  fi
  python "$WS_DIR/evaluation/run_qualification.py" \
    --spec "$SPEC" --corpus "$CORPUS" --split "$split" \
    --output "$RESULTS/$split.json" "${lock_args[@]}"
  python "$WS_DIR/scripts/evaluate_qualification.py" \
    --spec "$SPEC" --corpus "$CORPUS" --results "$RESULTS/$split.json" \
    --output "$RESULTS/${split}_evaluation.json" "${lock_args[@]}"
}

case "$stage" in
  prepare)
    run_split development
    run_split calibration
    ;;
  freeze)
    python "$VALIDATION_ROOT/freeze_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP2KSQ-v1 \
      --spec "$SPEC" --corpus "$CORPUS" --source-manifest "$SOURCE_MANIFEST" \
      --development "$RESULTS/development_evaluation.json" \
      --calibration "$RESULTS/calibration_evaluation.json" \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/freeze_qualification.py \
      --scope validation-external/verify_qualification.py \
      --scope validation-external/finalize_qualification.py \
      --scope validation-external/wp2-ks-validation \
      --scope src/python/ks --scope tests/ks --scope tests/wp2_ks_reference \
      --scope tests/qualification \
      --scope pyproject.toml --scope poetry.lock --scope environment.yml \
      --output "$LOCK"
    ;;
  holdout)
    python "$VALIDATION_ROOT/verify_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP2KSQ-v1 --lock "$LOCK"
    run_split holdout
    ;;
  finalize)
    python "$VALIDATION_ROOT/finalize_qualification.py" \
      --repo-root "$REPO_ROOT" --prefix WP2KSQ-v1 \
      --spec "$SPEC" --corpus "$CORPUS" --source-manifest "$SOURCE_MANIFEST" \
      --lock "$LOCK" \
      --development "$RESULTS/development_evaluation.json" \
      --calibration "$RESULTS/calibration_evaluation.json" \
      --holdout "$RESULTS/holdout_evaluation.json" \
      --record "$REPORTS/wp2_ks_qualification_record.json" \
      --report "$REPORTS/wp2_ks_qualification_report.md"
    ;;
  *)
    echo "usage: $0 prepare|freeze|holdout|finalize" >&2
    exit 2
    ;;
esac
