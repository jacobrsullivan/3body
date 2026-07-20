#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION="$ROOT/validation-external"
SPATIAL="$VALIDATION/wp3-spatial-validation-v2"
SPEC="$WS_DIR/qualification_spec.json"
CORPUS="$WS_DIR/data/qualification_corpus.json"
RESULTS="$WS_DIR/results"
REPORTS="$WS_DIR/reports"
LOCK="$REPORTS/wp2_up_v2_qualification_lock.json"
export PYTHONPATH="$ROOT:$VALIDATION${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/data" "$RESULTS" "$REPORTS"

run_split() {
  local split="$1"; local lock_args=()
  if [[ "$split" == "holdout" ]]; then lock_args=(--lock "$LOCK"); fi
  python "$WS_DIR/scripts/run_qualification.py" --spec "$SPEC" --corpus "$CORPUS" \
    --spatial-corpus "$SPATIAL/data/qualification_corpus.json" \
    --spatial-results "$SPATIAL/results/$split.json" --split "$split" \
    --output "$RESULTS/$split.json" "${lock_args[@]}"
  python "$WS_DIR/scripts/evaluate_qualification.py" --spec "$SPEC" --corpus "$CORPUS" \
    --results "$RESULTS/$split.json" --output "$RESULTS/${split}_evaluation.json" "${lock_args[@]}"
}

case "${1:-}" in
  build)
    python "$WS_DIR/scripts/build_corpus.py" --spec "$SPEC" \
      --spatial-corpus "$SPATIAL/data/qualification_corpus.json" --output "$CORPUS" ;;
  prepare) run_split development; run_split calibration ;;
  freeze)
    python "$VALIDATION/freeze_qualification.py" --repo-root "$ROOT" --prefix WP2-UPQ-v2 \
      --spec "$SPEC" --corpus "$CORPUS" --source-manifest "$WS_DIR/sources/manifest.json" \
      --development "$RESULTS/development_evaluation.json" --calibration "$RESULTS/calibration_evaluation.json" \
      --scope validation-external/qualification_tools.py --scope validation-external/freeze_qualification.py \
      --scope validation-external/verify_qualification.py --scope validation-external/finalize_qualification.py \
      --scope validation-external/wp2-up-validation-v2 --scope validation-external/wp3-spatial-validation-v2 \
      --scope src/python/upstairs_ks --scope src/python/ks --scope src/python/threebody_flow \
      --scope src/python/threebody_reduction --scope src/python/n3bp_qualification \
      --scope tests/upstairs_ks --scope tests/wp2_up_v2_qualification \
      --scope pyproject.toml --scope poetry.lock --scope environment.yml --output "$LOCK" ;;
  holdout)
    python "$VALIDATION/verify_qualification.py" --repo-root "$ROOT" --prefix WP2-UPQ-v2 --lock "$LOCK"
    run_split holdout ;;
  finalize)
    python "$VALIDATION/finalize_qualification.py" --repo-root "$ROOT" --prefix WP2-UPQ-v2 \
      --spec "$SPEC" --corpus "$CORPUS" --source-manifest "$WS_DIR/sources/manifest.json" --lock "$LOCK" \
      --development "$RESULTS/development_evaluation.json" --calibration "$RESULTS/calibration_evaluation.json" \
      --holdout "$RESULTS/holdout_evaluation.json" --record "$REPORTS/wp2_up_v2_qualification_record.json" \
      --report "$REPORTS/wp2_up_v2_qualification_report.md" ;;
  *) echo "usage: $0 build|prepare|freeze|holdout|finalize" >&2; exit 2 ;;
esac
