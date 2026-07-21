#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WS_DIR/../.." && pwd)"
VALIDATION="$ROOT/validation-external"
SPEC="$WS_DIR/qualification_spec.json"
MANIFEST="$WS_DIR/sources/manifest.json"
CATALOGUE="$VALIDATION/wp1-catalogue-n3bp-validation/data/native_catalogue.json"
LOCK="$WS_DIR/reports/wp4_mr_v2_qualification_lock.json"
RESULTS="$WS_DIR/results/qualification_results.json"
TSYGVINTSEV_PDF="${TSYGVINTSEV_PDF:-/tmp/tsygvintsev-2007.pdf}"
BOUCHER_WEIL_PDF="${BOUCHER_WEIL_PDF:-/tmp/boucher-weil-threebody.pdf}"

export PYTHONPATH="$ROOT:$VALIDATION${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WS_DIR/results" "$WS_DIR/reports"

case "${1:-}" in
  test)
    python -m pytest tests/wp4_mr_v2 -q
    ;;
  freeze)
    python "$WS_DIR/scripts/freeze_qualification.py" --repo-root "$ROOT" \
      --prefix WP4-MR-NI-v2 --spec "$SPEC" --source-manifest "$MANIFEST" \
      --catalogue "$CATALOGUE" \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/verify_qualification.py \
      --scope validation-external/validation_external_import.py \
      --scope validation-external/wp4-mr-ni-v1/reports/wp4_mr_v1_specification_assessment.json \
      --scope validation-external/wp4-mr-ni-v2 \
      --scope validation-external/wp1-catalogue-n3bp-validation/data/native_catalogue.json \
      --scope validation-external/wp1-catalogue-n3bp-validation/reports \
      --scope validation-external/wp2-multi-validation/reports \
      --scope validation-external/wp3-multi-candidate-v1/reports \
      --scope src/python/wp4_mr_v2 --scope tests/wp4_mr_v2 \
      --scope pyproject.toml --scope poetry.lock --scope environment.yml \
      --output "$LOCK"
    ;;
  execute)
    python "$VALIDATION/verify_qualification.py" --repo-root "$ROOT" \
      --prefix WP4-MR-NI-v2 --lock "$LOCK"
    python "$WS_DIR/scripts/run_qualification.py" --spec "$SPEC" \
      --source-manifest "$MANIFEST" --catalogue "$CATALOGUE" \
      --tsygvintsev-pdf "$TSYGVINTSEV_PDF" \
      --boucher-weil-pdf "$BOUCHER_WEIL_PDF" \
      --lock "$LOCK" --output "$RESULTS"
    ;;
  finalize)
    python "$WS_DIR/scripts/finalize_qualification.py" --spec "$SPEC" \
      --lock "$LOCK" --results "$RESULTS" \
      --record "$WS_DIR/reports/wp4_mr_v2_qualification_record.json" \
      --report "$WS_DIR/reports/wp4_mr_v2_qualification_report.md"
    ;;
  *)
    echo "usage: $0 test|freeze|execute|finalize" >&2
    exit 2
    ;;
esac
