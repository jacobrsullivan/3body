#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp4-mr-repl-v1"
MODE="${1:-test}"
SPEC="$CAMPAIGN/qualification_spec.json"
SOURCES="$CAMPAIGN/sources/manifest.json"
PROOF="$CAMPAIGN/proof/WP4-MR-REPL-v1-proof.md"
LOCK="$CAMPAIGN/reports/wp4_mr_repl_v1_qualification_lock.json"
RESULTS="$CAMPAIGN/results/qualification_results.json"
RECORD="$CAMPAIGN/reports/wp4_mr_repl_v1_qualification_record.json"
REPORT="$CAMPAIGN/reports/wp4_mr_repl_v1_qualification_report.md"

case "$MODE" in
  test)
    cd "$ROOT"
    python -m pytest -q tests/wp4_mr_repl_v1
    ;;
  freeze)
    python "$CAMPAIGN/scripts/freeze_qualification.py" \
      --repo-root "$ROOT" \
      --prefix WP4-MR-REPL-v1 \
      --spec "$SPEC" \
      --source-manifest "$SOURCES" \
      --proof "$PROOF" \
      --scope src/python/wp4_mr_repl_v1 \
      --scope tests/wp4_mr_repl_v1 \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/validation_external_import.py \
      --scope validation-external/wp2-multi-validation/reports/wp2_multi_v1_qualification_lock.json \
      --scope validation-external/wp2-multi-validation/reports/wp2_multi_v1_qualification_record.json \
      --scope validation-external/wp4-mr-ni-v2/reports/wp4_mr_v2_qualification_lock.json \
      --scope validation-external/wp4-mr-ni-v2/reports/wp4_mr_v2_qualification_record.json \
      --scope validation-external/wp4-lift-ni-v2/reports/wp4_lift_ni_v2_qualification_lock.json \
      --scope validation-external/wp4-lift-ni-v2/reports/wp4_lift_ni_v2_qualification_record.json \
      --scope validation-external/wp4-mr-repl-v1 \
      --output "$LOCK"
    ;;
  execute)
    python "$CAMPAIGN/scripts/run_qualification.py" \
      --spec "$SPEC" \
      --source-manifest "$SOURCES" \
      --proof "$PROOF" \
      --tsygvintsev-pdf "${TSYGVINTSEV_2001_PDF:-/tmp/tsygvintsev-2001.pdf}" \
      --boucher-weil-pdf "${BOUCHER_WEIL_PDF:-/tmp/boucher-weil.pdf}" \
      --morales-ramis-pdf "${MORALES_RAMIS_2001_PDF:-/tmp/morales-ramis-2001.pdf}" \
      --lock "$LOCK" \
      --output "$RESULTS"
    ;;
  finalize)
    python "$CAMPAIGN/scripts/finalize_qualification.py" \
      --spec "$SPEC" \
      --lock "$LOCK" \
      --results "$RESULTS" \
      --record "$RECORD" \
      --report "$REPORT"
    ;;
  verify)
    python "$ROOT/validation-external/verify_qualification.py" \
      --repo-root "$ROOT" \
      --lock "$LOCK" \
      --prefix WP4-MR-REPL-v1
    ;;
  *)
    echo "usage: $0 {test|freeze|execute|finalize|verify}" >&2
    exit 2
    ;;
esac
