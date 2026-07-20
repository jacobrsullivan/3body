#!/usr/bin/env bash
set -euo pipefail
WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WS_DIR/../.." && pwd)"
UP="$ROOT/validation-external/wp3-upstairs-candidate"
V2="$ROOT/validation-external/wp3-v2-exploration"
export PYTHONPATH="$ROOT:$ROOT/validation-external${PYTHONPATH:+:$PYTHONPATH}"
python "$WS_DIR/scripts/evaluate_trigger.py" \
  --protocol "$WS_DIR/qualification_protocol.json" \
  --search-lock "$UP/reports/wp3_upstairs_search_lock.json" \
  --search-results "$UP/results/search_results.json" \
  --search-gate "$UP/results/staged_gate.json" \
  --commitments "$V2/sealed/publication_holdout_commitments.json" \
  --output "$WS_DIR/results/candidate_qualification_decision.json" \
  --report "$WS_DIR/reports/candidate_qualification_decision.md"
