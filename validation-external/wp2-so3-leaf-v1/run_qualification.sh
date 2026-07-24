#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp2-so3-leaf-v1"
RUNNER="$ROOT/validation-external/successor_qualification.py"
MODE="${1:-test}"
SPEC="$CAMPAIGN/qualification_spec.json"
SPEC_LOCK="$CAMPAIGN/reports/wp2_so3_leaf_v1_specification_lock.json"
SOURCES="$CAMPAIGN/sources/manifest.json"
PROOF="$CAMPAIGN/proof/WP2-SO3-LEAF-v1-proof.md"
LOCK="$CAMPAIGN/reports/wp2_so3_leaf_v1_qualification_lock.json"
RESULT="$CAMPAIGN/results/qualification_results.json"
RECORD="$CAMPAIGN/reports/wp2_so3_leaf_v1_qualification_record.json"
REPORT="$CAMPAIGN/reports/wp2_so3_leaf_v1_qualification_report.md"

case "$MODE" in
  test)
    cd "$ROOT"
    python -m pytest -q tests/so3_reduction_v1
    ;;
  freeze)
    python "$RUNNER" freeze --repo-root "$ROOT" --prefix WP2-SO3-LEAF-v1 \
      --spec "$SPEC" --spec-lock "$SPEC_LOCK" --source-manifest "$SOURCES" \
      --proof "$PROOF" --output "$LOCK" --result "$RESULT" \
      --record "$RECORD" --report "$REPORT" \
      --scope src/python/so3_reduction_v1 --scope tests/so3_reduction_v1 \
      --scope src/python/threebody_reduction \
      --scope src/python/threebody_flow \
      --scope validation-external/successor_qualification.py \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/wp2-so3-leaf-v1 \
      --scope validation-external/wp2-threebody-validation/reports/wp2_threebody_qualification_lock.json \
      --scope validation-external/wp2-threebody-validation/reports/wp2_threebody_qualification_record.json \
      --scope validation-external/wp2-threebody-flow-validation/reports/wp2_threebody_flow_qualification_lock.json \
      --scope validation-external/wp2-threebody-flow-validation/reports/wp2_threebody_flow_qualification_record.json
    ;;
  execute)
    python "$RUNNER" execute --spec "$SPEC" --spec-lock "$SPEC_LOCK" \
      --source-manifest "$SOURCES" --proof "$PROOF" --lock "$LOCK" \
      --source "ciftci-waalkens-2010=${CIFTCI_WAALKENS_2010_PDF:-/private/tmp/3body-wp6-sources/ciftci-waalkens-2010.pdf}" \
      --source "moeckel-montgomery-2012=${MOECKEL_MONTGOMERY_2012_PDF:-/private/tmp/3body-wp6-sources/moeckel-montgomery-2012.pdf}" \
      --output "$RESULT"
    ;;
  finalize)
    python "$RUNNER" finalize --spec "$SPEC" --lock "$LOCK" \
      --result "$RESULT" --record "$RECORD" --report "$REPORT"
    ;;
  verify)
    python "$ROOT/validation-external/verify_qualification.py" \
      --repo-root "$ROOT" --lock "$LOCK" --prefix WP2-SO3-LEAF-v1
    ;;
  *)
    echo "usage: $0 {test|freeze|execute|finalize|verify}" >&2
    exit 2
    ;;
esac
