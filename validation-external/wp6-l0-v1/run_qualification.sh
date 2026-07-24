#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp6-l0-v1"
RUNNER="$ROOT/validation-external/successor_qualification.py"
MODE="${1:-test}"
SPEC="$CAMPAIGN/qualification_spec.json"
SPEC_LOCK="$CAMPAIGN/reports/wp6_l0_v1_specification_lock.json"
SOURCES="$CAMPAIGN/sources/manifest.json"
PROOF="$CAMPAIGN/proof/WP6-L0-v1-proof.md"
LOCK="$CAMPAIGN/reports/wp6_l0_v1_qualification_lock.json"
RESULT="$CAMPAIGN/results/qualification_results.json"
RECORD="$CAMPAIGN/reports/wp6_l0_v1_qualification_record.json"
REPORT="$CAMPAIGN/reports/wp6_l0_v1_qualification_report.md"

case "$MODE" in
  test)
    cd "$ROOT"
    python -m pytest -q tests/wp6_l0_v1
    ;;
  freeze)
    python "$RUNNER" freeze --repo-root "$ROOT" --prefix WP6-L0-v1 \
      --spec "$SPEC" --spec-lock "$SPEC_LOCK" --source-manifest "$SOURCES" \
      --proof "$PROOF" --output "$LOCK" --result "$RESULT" \
      --record "$RECORD" --report "$REPORT" \
      --scope src/python/wp6_l0_v1 --scope tests/wp6_l0_v1 \
      --scope validation-external/successor_qualification.py \
      --scope validation-external/qualification_tools.py \
      --scope validation-external/wp6-l0-v1
    ;;
  execute)
    python "$RUNNER" execute --spec "$SPEC" --spec-lock "$SPEC_LOCK" \
      --source-manifest "$SOURCES" --proof "$PROOF" --lock "$LOCK" \
      --source "maciejewski-przybylska-combot-2025=${MPC_2025_PDF:-/private/tmp/3body-wp6-sources/maciejewski-przybylska-combot-2025.pdf}" \
      --source "combot-2015=${COMBOT_2015_PDF:-/private/tmp/3body-wp6-sources/combot-2015.pdf}" \
      --source "maciejewski-przybylska-2011=${MP_2011_PDF:-/private/tmp/3body-wp6-sources/maciejewski-przybylska-2011.pdf}" \
      --output "$RESULT"
    ;;
  finalize)
    python "$RUNNER" finalize --spec "$SPEC" --lock "$LOCK" \
      --result "$RESULT" --record "$RECORD" --report "$REPORT"
    ;;
  verify)
    python "$ROOT/validation-external/verify_qualification.py" \
      --repo-root "$ROOT" --lock "$LOCK" --prefix WP6-L0-v1
    ;;
  *)
    echo "usage: $0 {test|freeze|execute|finalize|verify}" >&2
    exit 2
    ;;
esac
