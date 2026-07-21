#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION="$ROOT/validation-external"
SPEC="$WS_DIR/qualification_spec.json"
CATALOGUE="$WS_DIR/data/native_catalogue.json"
CANDIDATE_LOCK="$WS_DIR/reports/wp1_cat_n3bp_v1_candidate_lock.json"
CORPUS="$WS_DIR/data/qualification_corpus.json"
MANIFEST="$WS_DIR/sources/manifest.json"
RESULTS="$WS_DIR/results"
REPORTS="$WS_DIR/reports"
LOCK="$REPORTS/wp1_cat_n3bp_v1_qualification_lock.json"
FOCUSED_TEST_RECEIPT="$REPORTS/wp1_cat_n3bp_v1_focused_tests.json"
WORKERS="${WP1_CAT_WORKERS:-8}"
export PYTHONPATH="$ROOT:$VALIDATION${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/data" "$RESULTS" "$REPORTS"

run_split() {
  local split="$1"
  local lock_args=()
  if [[ "$split" == "holdout" ]]; then lock_args=(--lock "$LOCK"); fi
  python "$WS_DIR/scripts/run_qualification.py" --spec "$SPEC" --corpus "$CORPUS" \
    --catalogue "$CATALOGUE" --candidate-lock "$CANDIDATE_LOCK" \
    --split "$split" --workers "$WORKERS" --output "$RESULTS/$split.json" \
    "${lock_args[@]}"
  python "$WS_DIR/scripts/evaluate_qualification.py" --spec "$SPEC" --corpus "$CORPUS" \
    --results "$RESULTS/$split.json" --output "$RESULTS/${split}_evaluation.json" \
    "${lock_args[@]}"
}

case "${1:-}" in
  generate)
    python "$WS_DIR/scripts/generate_candidate.py" --spec "$SPEC" \
      --workers "$WORKERS" --output "$CATALOGUE" ;;
  freeze-candidate)
    python "$WS_DIR/scripts/freeze_candidate.py" --spec "$SPEC" --catalogue "$CATALOGUE" \
      --scope validation-external/wp1-catalogue-n3bp-validation/qualification_spec.json \
      --scope validation-external/wp1-catalogue-n3bp-validation/reports/wp1_cat_n3bp_v1_specification_lock.json \
      --scope validation-external/wp1-catalogue-n3bp-validation/scripts/generate_candidate.py \
      --scope validation-external/wp1-catalogue-n3bp-validation/scripts/campaign_common.py \
      --scope validation-external/wp1-catalogue-n3bp-validation/data/native_catalogue.json \
      --scope validation-external/wp1-n3bp-validation/reports \
      --scope src/python/wp1_catalogue_n3bp_v1 --scope tests/wp1_catalogue_n3bp_v1 \
      --scope pyproject.toml --scope poetry.lock --scope environment.yml \
      --output "$CANDIDATE_LOCK" ;;
  build)
    python "$WS_DIR/scripts/build_corpus.py" --spec "$SPEC" --catalogue "$CATALOGUE" \
      --candidate-lock "$CANDIDATE_LOCK" --source-manifest "$MANIFEST" \
      --output "$CORPUS" ;;
  prepare)
    python "$WS_DIR/scripts/run_focused_tests.py" run --spec "$SPEC" \
      --output "$FOCUSED_TEST_RECEIPT"
    run_split development
    run_split calibration ;;
  freeze)
    python "$WS_DIR/scripts/run_focused_tests.py" verify --spec "$SPEC" \
      --output "$FOCUSED_TEST_RECEIPT"
    python "$VALIDATION/freeze_qualification.py" --repo-root "$ROOT" \
      --prefix WP1-CAT-N3BP-v1 --spec "$SPEC" --corpus "$CORPUS" \
      --source-manifest "$MANIFEST" \
      --development "$RESULTS/development_evaluation.json" \
      --calibration "$RESULTS/calibration_evaluation.json" \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/freeze_qualification.py \
      --scope validation-external/verify_qualification.py \
      --scope validation-external/finalize_qualification.py \
      --scope validation-external/finalize_committed_qualification.py \
      --scope validation-external/wp1-catalogue-n3bp-validation \
      --scope validation-external/wp1-n3bp-validation/reports \
      --scope src/python/wp1_catalogue_n3bp_v1 \
      --scope src/python/n3bp_qualification \
      --scope tests/wp1_catalogue_n3bp_v1 \
      --scope validation-external/wp1-catalogue-n3bp-validation/reports/wp1_cat_n3bp_v1_focused_tests.json \
      --scope pyproject.toml --scope poetry.lock --scope environment.yml \
      --output "$LOCK" ;;
  holdout)
    python "$VALIDATION/verify_qualification.py" --repo-root "$ROOT" \
      --prefix WP1-CAT-N3BP-v1 --lock "$LOCK"
    run_split holdout ;;
  finalize)
    python "$VALIDATION/finalize_committed_qualification.py" --repo-root "$ROOT" \
      --prefix WP1-CAT-N3BP-v1 --spec "$SPEC" --corpus "$CORPUS" \
      --source-manifest "$MANIFEST" --lock "$LOCK" \
      --development "$RESULTS/development_evaluation.json" \
      --calibration "$RESULTS/calibration_evaluation.json" \
      --holdout "$RESULTS/holdout_evaluation.json" \
      --record "$REPORTS/wp1_cat_n3bp_v1_qualification_record.json" \
      --report "$REPORTS/wp1_cat_n3bp_v1_qualification_report.md" ;;
  *)
    echo "usage: $0 generate|freeze-candidate|build|prepare|freeze|holdout|finalize" >&2
    exit 2 ;;
esac
