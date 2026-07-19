#!/usr/bin/env bash
# Frozen WP1 external qualification campaign.
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WS_DIR/../.." && pwd)"
SCRIPT_DIR="$WS_DIR/scripts"
SPEC="$WS_DIR/qualification_spec.json"
SOURCE_DIR="$WS_DIR/data/qualification/raw"
CORPUS_DIR="$WS_DIR/data/qualification"
RESULTS_DIR="$WS_DIR/results/qualification"
REPORTS_DIR="$WS_DIR/reports"
CORPUS="$CORPUS_DIR/corpus.parquet"
CORPUS_MANIFEST="$CORPUS_DIR/corpus_manifest.json"
HOLDOUT_IDS="$CORPUS_DIR/holdout_ids.json"
LOCK="$REPORTS_DIR/wp1_qualification_lock.json"

export PYTHONPATH="$REPO_ROOT:$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/wp1-matplotlib}"

STAGE=""
WORKERS=4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage) STAGE="$2"; shift 2 ;;
    --workers) WORKERS="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$STAGE" ]]; then
  echo "Usage: $0 --stage fetch|development|calibration|prepare|freeze|holdout|finalize|all|reproduce [--workers N]" >&2
  exit 2
fi

mkdir -p "$SOURCE_DIR" "$CORPUS_DIR" "$RESULTS_DIR" "$REPORTS_DIR"

run_split() {
  local split="$1"
  python "$SCRIPT_DIR/run_qualification_float64.py" \
    --spec "$SPEC" --corpus "$CORPUS" --split "$split" \
    --workers "$WORKERS" --output "$RESULTS_DIR/${split}_float64.csv"
  python "$SCRIPT_DIR/run_qualification_oracle.py" \
    --spec "$SPEC" --corpus "$CORPUS" --split "$split" \
    --output "$RESULTS_DIR/${split}_oracle.csv"
  python "$SCRIPT_DIR/run_qualification_stability.py" \
    --spec "$SPEC" --corpus "$CORPUS" --split "$split" \
    --workers "$WORKERS" --output "$RESULTS_DIR/${split}_stability.csv"
  python "$SCRIPT_DIR/run_qualification_reconstruction.py" \
    --spec "$SPEC" --corpus "$CORPUS" --split "$split" \
    --float64-results "$RESULTS_DIR/${split}_float64.csv" \
    --workers "$WORKERS" --output "$RESULTS_DIR/${split}_reconstruction.csv"
}

evaluate_split() {
  local split="$1"
  if [[ "$split" == "holdout" ]]; then
    python "$SCRIPT_DIR/evaluate_qualification.py" \
      --spec "$SPEC" --corpus-manifest "$CORPUS_MANIFEST" \
      --lock "$LOCK" --split "$split" \
      --float64 "$RESULTS_DIR/${split}_float64.csv" \
      --oracle "$RESULTS_DIR/${split}_oracle.csv" \
      --stability "$RESULTS_DIR/${split}_stability.csv" \
      --reconstruction "$RESULTS_DIR/${split}_reconstruction.csv" \
      --output "$RESULTS_DIR/${split}_evaluation.json"
  else
    python "$SCRIPT_DIR/evaluate_qualification.py" \
      --spec "$SPEC" --corpus-manifest "$CORPUS_MANIFEST" \
      --split "$split" \
      --float64 "$RESULTS_DIR/${split}_float64.csv" \
      --oracle "$RESULTS_DIR/${split}_oracle.csv" \
      --stability "$RESULTS_DIR/${split}_stability.csv" \
      --reconstruction "$RESULTS_DIR/${split}_reconstruction.csv" \
      --output "$RESULTS_DIR/${split}_evaluation.json"
  fi
}

fetch_sources() {
  python "$SCRIPT_DIR/fetch_qualification_corpus.py" \
    --spec "$SPEC" --output-dir "$SOURCE_DIR"
}

prepare_campaign() {
  python "$SCRIPT_DIR/build_qualification_corpus.py" \
    --spec "$SPEC" --source-manifest "$SOURCE_DIR/manifest.json" \
    --output "$CORPUS" --manifest "$CORPUS_MANIFEST" \
    --holdout-ids "$HOLDOUT_IDS"
  run_split development
  evaluate_split development
  run_split calibration
  evaluate_split calibration
}

freeze_campaign() {
  python "$SCRIPT_DIR/freeze_qualification.py" \
    --repo-root "$REPO_ROOT" --spec "$SPEC" \
    --corpus-manifest "$CORPUS_MANIFEST" --holdout-ids "$HOLDOUT_IDS" \
    --results-dir "$RESULTS_DIR" --output "$LOCK"
}

run_holdout() {
  python "$SCRIPT_DIR/verify_qualification_lock.py" \
    --repo-root "$REPO_ROOT" --lock "$LOCK" \
    --corpus-manifest "$CORPUS_MANIFEST"
  run_split holdout
  evaluate_split holdout
}

finalize_campaign() {
  python "$SCRIPT_DIR/generate_qualification_report.py" \
    --spec "$SPEC" --lock "$LOCK" --corpus-manifest "$CORPUS_MANIFEST" \
    --development "$RESULTS_DIR/development_evaluation.json" \
    --calibration "$RESULTS_DIR/calibration_evaluation.json" \
    --holdout "$RESULTS_DIR/holdout_evaluation.json" \
    --report "$REPORTS_DIR/wp1_qualification_report.md" \
    --record "$REPORTS_DIR/wp1_qualification_record.json"
}

case "$STAGE" in
  fetch) fetch_sources ;;
  development) run_split development; evaluate_split development ;;
  calibration) run_split calibration; evaluate_split calibration ;;
  prepare) prepare_campaign ;;
  freeze) freeze_campaign ;;
  holdout) run_holdout ;;
  finalize) finalize_campaign ;;
  all)
    fetch_sources
    prepare_campaign
    freeze_campaign
    run_holdout
    finalize_campaign
    ;;
  reproduce)
    run_split development
    evaluate_split development
    run_split calibration
    evaluate_split calibration
    run_holdout
    finalize_campaign
    ;;
  *) echo "Unknown stage: $STAGE" >&2; exit 2 ;;
esac
