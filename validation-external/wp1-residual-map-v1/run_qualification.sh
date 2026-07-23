#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp1-residual-map-v1"
MODE="${1:-test}"
SPEC="$CAMPAIGN/qualification_spec.json"
CATALOGUE="$ROOT/validation-external/wp1-catalogue-n3bp-validation/data/native_catalogue.json"
LOCK="$CAMPAIGN/reports/wp1_residual_map_v1_qualification_lock.json"
MAP="$CAMPAIGN/data/residual_structure_map.json"
RESULTS="$CAMPAIGN/results/qualification_results.json"
RECORD="$CAMPAIGN/reports/wp1_residual_map_v1_qualification_record.json"
REPORT="$CAMPAIGN/reports/wp1_residual_map_v1_qualification_report.md"

case "$MODE" in
  test)
    cd "$ROOT"
    python -m pytest -q tests/wp1_residual_map_v1
    ;;
  freeze)
    python "$CAMPAIGN/scripts/freeze_qualification.py" \
      --repo-root "$ROOT" \
      --prefix WP1-RESIDUAL-MAP-v1 \
      --spec "$SPEC" \
      --catalogue "$CATALOGUE" \
      --scope src/python/wp1_residual_map_v1 \
      --scope tests/wp1_residual_map_v1 \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/validation_external_import.py \
      --scope validation-external/wp1-catalogue-n3bp-validation/data/native_catalogue.json \
      --scope validation-external/wp1-catalogue-n3bp-validation/reports/wp1_cat_n3bp_v1_qualification_lock.json \
      --scope validation-external/wp1-catalogue-n3bp-validation/reports/wp1_cat_n3bp_v1_qualification_record.json \
      --scope validation-external/wp4-mr-ni-v2/reports/wp4_mr_v2_qualification_record.json \
      --scope validation-external/wp1-residual-map-v1 \
      --output "$LOCK"
    ;;
  execute)
    python "$CAMPAIGN/scripts/run_qualification.py" \
      --spec "$SPEC" \
      --catalogue "$CATALOGUE" \
      --lock "$LOCK" \
      --map-output "$MAP" \
      --output "$RESULTS"
    ;;
  finalize)
    python "$CAMPAIGN/scripts/finalize_qualification.py" \
      --spec "$SPEC" \
      --lock "$LOCK" \
      --map "$MAP" \
      --results "$RESULTS" \
      --record "$RECORD" \
      --report "$REPORT"
    ;;
  verify)
    python "$ROOT/validation-external/verify_qualification.py" \
      --repo-root "$ROOT" \
      --lock "$LOCK" \
      --prefix WP1-RESIDUAL-MAP-v1
    ;;
  *)
    echo "usage: $0 {test|freeze|execute|finalize|verify}" >&2
    exit 2
    ;;
esac
