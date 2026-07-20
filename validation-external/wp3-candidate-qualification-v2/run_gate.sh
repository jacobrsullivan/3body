#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
CAMPAIGN="$ROOT/validation-external/wp3-candidate-qualification-v2"
SEARCH="$ROOT/validation-external/wp3-upstairs-candidate-v2"
RESERVE="$ROOT/validation-external/wp3-v2-exploration/sealed/publication_holdout_commitments.json"
export PYTHONPATH="$ROOT/validation-external:$ROOT${PYTHONPATH:+:$PYTHONPATH}"

python "$CAMPAIGN/scripts/evaluate_trigger.py" \
  --protocol "$CAMPAIGN/qualification_protocol.json" \
  --search-lock "$SEARCH/reports/wp3_upstairs_v2_search_lock.json" \
  --search-record "$SEARCH/reports/wp3_upstairs_v2_search_record.json" \
  --search-results "$SEARCH/results/search_results.json" \
  --search-gate "$SEARCH/results/staged_gate.json" \
  --commitments "$RESERVE" \
  --output "$CAMPAIGN/results/candidate_qualification_decision.json" \
  --report "$CAMPAIGN/reports/candidate_qualification_decision.md"
