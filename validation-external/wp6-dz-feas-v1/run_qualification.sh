#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp6-dz-feas-v1"
RUNNER="$ROOT/validation-external/wp6_dz_feas_qualification.py"
MODE="${1:-test}"
SOURCE_DIR="${WP6_DZ_SOURCE_DIR:-/private/tmp/3body-wp6-sources}"
SPEC="$CAMPAIGN/qualification_spec.json"
PROTOCOL="$CAMPAIGN/discovery_protocol.json"
SEEDS="$CAMPAIGN/sources/seed_manifest.json"
SPEC_LOCK="$CAMPAIGN/reports/wp6_dz_feas_v1_specification_lock.json"
SOURCES="$CAMPAIGN/sources/discovery_manifest.json"
SEARCH="$CAMPAIGN/search_receipt.json"
LEDGER="$CAMPAIGN/candidate_ledger.json"
AUDIT="$CAMPAIGN/proof/WP6-DZ-FEAS-v1-audit.md"
REFERENCE="$CAMPAIGN/reference/exact_controls.py"
LOCK="$CAMPAIGN/reports/wp6_dz_feas_v1_qualification_lock.json"
RESULT="$CAMPAIGN/results/qualification_results.json"
RECORD="$CAMPAIGN/reports/wp6_dz_feas_v1_qualification_record.json"
REPORT="$CAMPAIGN/reports/wp6_dz_feas_v1_qualification_report.md"

case "$MODE" in
  test)
    cd "$ROOT"
    python -m pytest -q tests/wp6_dz_feas_v1
    ;;
  freeze)
    python "$RUNNER" freeze --repo-root "$ROOT" --prefix WP6-DZ-FEAS-v1 \
      --spec "$SPEC" --protocol "$PROTOCOL" --seed-manifest "$SEEDS" \
      --spec-lock "$SPEC_LOCK" --source-manifest "$SOURCES" \
      --search-receipt "$SEARCH" --candidate-ledger "$LEDGER" \
      --audit "$AUDIT" --reference "$REFERENCE" --output "$LOCK" \
      --result "$RESULT" --record "$RECORD" --report "$REPORT" \
      --scope notes/wp6-dz-feas-v1-plan.md \
      --scope src/python/wp6_dz_feas_v1 \
      --scope tests/wp6_dz_feas_v1 \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/wp6_dz_feas_qualification.py \
      --scope validation-external/wp6-dz-feas-v1 \
      --scope validation-external/wp6-common-level-v1/reports/wp6_common_level_v1_qualification_lock.json \
      --scope validation-external/wp6-common-level-v1/reports/wp6_common_level_v1_qualification_record.json \
      --scope validation-external/wp6-l0-v1/reports/wp6_l0_v1_qualification_lock.json \
      --scope validation-external/wp6-l0-v1/reports/wp6_l0_v1_qualification_record.json \
      --scope validation-external/wp6-fi1-v1/reports/wp6_fi1_v1_qualification_lock.json \
      --scope validation-external/wp6-fi1-v1/reports/wp6_fi1_v1_qualification_record.json \
      --scope validation-external/wp2-so3-leaf-v1/reports/wp2_so3_leaf_v1_qualification_lock.json \
      --scope validation-external/wp2-so3-leaf-v1/reports/wp2_so3_leaf_v1_qualification_record.json
    ;;
  execute)
    python "$RUNNER" execute --spec "$SPEC" --protocol "$PROTOCOL" \
      --seed-manifest "$SEEDS" --spec-lock "$SPEC_LOCK" \
      --source-manifest "$SOURCES" --search-receipt "$SEARCH" \
      --candidate-ledger "$LEDGER" --audit "$AUDIT" \
      --reference "$REFERENCE" --source-dir "$SOURCE_DIR" \
      --lock "$LOCK" --output "$RESULT"
    ;;
  finalize)
    python "$RUNNER" finalize --spec "$SPEC" --lock "$LOCK" \
      --result "$RESULT" --record "$RECORD" --report "$REPORT"
    ;;
  verify)
    python "$ROOT/validation-external/verify_qualification.py" \
      --repo-root "$ROOT" --lock "$LOCK" --prefix WP6-DZ-FEAS-v1
    ;;
  *)
    echo "usage: $0 {test|freeze|execute|finalize|verify}" >&2
    exit 2
    ;;
esac
