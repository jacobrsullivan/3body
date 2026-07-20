#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CAMPAIGN="$ROOT/validation-external/wp3-exploration"
PYTHON_BIN="${PYTHON_BIN:-python}"

mkdir -p "$CAMPAIGN/results" "$CAMPAIGN/reports"

"$PYTHON_BIN" "$CAMPAIGN/scripts/evaluate_publication_gate.py" \
  --spec "$CAMPAIGN/publication_gate_spec.json" \
  --manifest "$CAMPAIGN/publication_evidence_manifest.json" \
  --output "$CAMPAIGN/results/publication_gate.json"

"$PYTHON_BIN" "$CAMPAIGN/scripts/run_exploration.py" \
  --spec "$CAMPAIGN/exploration_spec.json" \
  --corpus "$CAMPAIGN/data/exploration_corpus.json" \
  --gate-result "$CAMPAIGN/results/publication_gate.json" \
  --output "$CAMPAIGN/results/exploration_results.json"

"$PYTHON_BIN" "$CAMPAIGN/scripts/render_report.py" \
  --results "$CAMPAIGN/results/exploration_results.json" \
  --gate-result "$CAMPAIGN/results/publication_gate.json" \
  --output "$CAMPAIGN/reports/wp3_exploration_report.md"
