#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp4-lift-ni-v3"
MODE="${1:-test}"
SPEC="$CAMPAIGN/qualification_spec.json"
SOURCES="$ROOT/validation-external/wp4-lift-ni-v2/sources/manifest.json"
ADDENDUM="$CAMPAIGN/proof/WP4-LIFT-NI-v3-addendum.md"
LOCK="$CAMPAIGN/reports/wp4_lift_ni_v3_qualification_lock.json"
RESULTS="$CAMPAIGN/results/qualification_results.json"
RECORD="$CAMPAIGN/reports/wp4_lift_ni_v3_qualification_record.json"
REPORT="$CAMPAIGN/reports/wp4_lift_ni_v3_qualification_report.md"

case "$MODE" in
  test)
    cd "$ROOT"
    python -m pytest -q tests/wp4_lift_ni_v3
    ;;
  freeze)
    python "$CAMPAIGN/scripts/freeze_qualification.py" \
      --repo-root "$ROOT" \
      --prefix WP4-LIFT-NI-v3 \
      --spec "$SPEC" \
      --source-manifest "$SOURCES" \
      --proof-addendum "$ADDENDUM" \
      --scope src/python/ks/canonical.py \
      --scope src/python/wp2_multi_v1 \
      --scope src/python/wp4_lift_ni_v2 \
      --scope src/python/wp4_lift_ni_v3 \
      --scope tests/wp4_lift_ni_v3 \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/validation_external_import.py \
      --scope validation-external/wp2-multi-validation/qualification_spec.json \
      --scope validation-external/wp2-multi-validation/reports/wp2_multi_v1_qualification_lock.json \
      --scope validation-external/wp2-multi-validation/reports/wp2_multi_v1_qualification_record.json \
      --scope validation-external/wp4-mr-repl-v1/qualification_spec.json \
      --scope validation-external/wp4-mr-repl-v1/reports/wp4_mr_repl_v1_qualification_lock.json \
      --scope validation-external/wp4-mr-repl-v1/reports/wp4_mr_repl_v1_qualification_record.json \
      --scope validation-external/wp4-lift-ni-v2/proof/WP4-LIFT-NI-v2-proof.md \
      --scope validation-external/wp4-lift-ni-v2/reference/sympy_reference.py \
      --scope validation-external/wp4-lift-ni-v2/scripts/run_qualification.py \
      --scope validation-external/wp4-lift-ni-v2/sources/manifest.json \
      --scope validation-external/wp4-lift-ni-v2/reports/wp4_lift_ni_v2_qualification_lock.json \
      --scope validation-external/wp4-lift-ni-v2/reports/wp4_lift_ni_v2_qualification_record.json \
      --scope validation-external/wp4-lift-ni-v3 \
      --output "$LOCK"
    ;;
  execute)
    python "$CAMPAIGN/scripts/run_qualification.py" \
      --spec "$SPEC" \
      --source-manifest "$SOURCES" \
      --proof-addendum "$ADDENDUM" \
      --marsden-weinstein-pdf "${MARSDEN_WEINSTEIN_PDF:-/tmp/marsden-weinstein-1974.pdf}" \
      --tsygvintsev-pdf "${TSYGVINTSEV_PDF:-/tmp/tsygvintsev-2007.pdf}" \
      --boucher-weil-pdf "${BOUCHER_WEIL_PDF:-/tmp/boucher-weil.pdf}" \
      --dullin-montgomery-pdf "${DULLIN_MONTGOMERY_PDF:-/tmp/dullin-montgomery-2025.pdf}" \
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
      --prefix WP4-LIFT-NI-v3
    ;;
  *)
    echo "usage: $0 {test|freeze|execute|finalize|verify}" >&2
    exit 2
    ;;
esac
