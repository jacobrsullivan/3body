#!/usr/bin/env bash
# WP1 External Validation Pipeline
#
# Usage:
#   ./run_validation.sh                        # full pipeline (skips chaos maps)
#   ./run_validation.sh --skip-fetch           # skip JPL fetch (use cached data)
#   ./run_validation.sh --cores 4              # limit worker processes
#   ./run_validation.sh --max-jpl 300          # limit JPL orbits (stratified sample)
#   ./run_validation.sh --include-chaos-maps   # include chaos maps (slow)
#   ./run_validation.sh --include-snakemake    # run Snakemake Tier 1 before report
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$WS_DIR/scripts"
REPO_ROOT="$(cd "$WS_DIR/../.." && pwd)"

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1

ORIGINAL_ARGS=("$@")
SKIP_FETCH=false
INCLUDE_CHAOS=false
INCLUDE_SNAKEMAKE=false
CORES=4
MAX_JPL=300
MU=0.012150585609624

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-fetch) SKIP_FETCH=true; shift ;;
    --include-chaos-maps) INCLUDE_CHAOS=true; shift ;;
    --include-snakemake) INCLUDE_SNAKEMAKE=true; shift ;;
    --cores) CORES="$2"; shift 2 ;;
    --max-jpl) MAX_JPL="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

phase_start() { PHASE_T0=$(date +%s); }
phase_end()   { local elapsed=$(( $(date +%s) - PHASE_T0 )); echo "  done (${elapsed}s)"; echo ""; }

echo "=== WP1 External Validation Pipeline ==="
echo "Workspace : $WS_DIR"
echo "Repo root : $REPO_ROOT"
echo "Cores     : $CORES"
echo "Max JPL   : $MAX_JPL"
echo ""

# ---------- Phase 1: Fetch JPL data ----------
if [ "$SKIP_FETCH" = false ]; then
  echo "[1/11] Fetching JPL periodic orbit data..."
  phase_start
  python "$SCRIPT_DIR/fetch_jpl_periodic_orbits.py" \
    --sys earth-moon \
    --output-dir "$WS_DIR/data/jpl"
  phase_end
else
  echo "[1/11] Skipping JPL fetch (--skip-fetch)"
  echo ""
fi

# ---------- Phase 2: Normalize JPL data ----------
JPL_RAW="$WS_DIR/data/jpl/raw_latest.json"
JPL_NORM="$WS_DIR/data/jpl/normalized.parquet"

if [ -f "$JPL_RAW" ]; then
  echo "[2/11] Normalizing JPL data..."
  phase_start
  python "$SCRIPT_DIR/normalize_jpl_orbits.py" \
    --input "$JPL_RAW" \
    --output "$JPL_NORM" \
    --lu 1.0 --tu 1.0
  phase_end
else
  echo "[2/11] Skipping normalization (no JPL data at $JPL_RAW)"
  echo ""
fi

# ---------- Phase 3: Compare WP1 orbits to JPL ----------
if [ -f "$JPL_NORM" ]; then
  echo "[3/11] Comparing WP1 orbits to JPL catalog (max $MAX_JPL orbits)..."
  phase_start
  python "$SCRIPT_DIR/compare_to_jpl.py" \
    --jpl "$JPL_NORM" \
    --use-periodic-library \
    --mu "$MU" \
    --max-jpl "$MAX_JPL" \
    --output "$WS_DIR/results/jpl_comparison.csv" \
    --summary "$WS_DIR/results/jpl_comparison_summary.json"
  phase_end
else
  echo "[3/11] Skipping JPL comparison (no normalized data)"
  echo ""
fi

# ---------- Phase 4: JPL-seeded validation catalogue ----------
if [ -f "$JPL_NORM" ]; then
  echo "[4/11] Building JPL-seeded WP1 validation catalogue..."
  phase_start
  python "$SCRIPT_DIR/build_jpl_seeded_catalog.py" \
    --jpl "$JPL_NORM" \
    --mu "$MU" \
    --max-jpl "$MAX_JPL" \
    --metrics-output "$WS_DIR/results/jpl_seeded_validation.csv" \
    --catalog-output "$WS_DIR/results/jpl_seeded_catalog.parquet" \
    --summary "$WS_DIR/results/jpl_seeded_catalog_summary.json"
  phase_end
else
  echo "[4/11] Skipping JPL-seeded catalogue (no normalized data)"
  echo ""
fi

# ---------- Phase 5: Extended precision check ----------
echo "[5/11] Running extended precision check..."
phase_start
python "$SCRIPT_DIR/extended_precision_check.py" \
  --use-periodic-library \
  --mu "$MU" \
  --output "$WS_DIR/results/extended_precision_summary.csv"
phase_end

# ---------- Phase 6: Reversibility check ----------
echo "[6/11] Running reversibility check..."
phase_start
python "$SCRIPT_DIR/run_reversibility_check.py" \
  --use-periodic-library --mu "$MU" \
  --output "$WS_DIR/results/reversibility.csv" \
  --summary "$WS_DIR/results/reversibility_summary.json"
phase_end

# ---------- Phase 7: Convergence check ----------
echo "[7/11] Running convergence check..."
phase_start
python "$SCRIPT_DIR/run_convergence_check.py" \
  --use-periodic-library --mu "$MU" \
  --output "$WS_DIR/results/convergence.csv" \
  --summary "$WS_DIR/results/convergence_summary.json"
phase_end

# ---------- Phase 8: Snakemake Tier 1 (opt-in) ----------
if [ "$INCLUDE_SNAKEMAKE" = true ]; then
  echo "[8/11] Running Snakemake Tier 1 validation (cores=$CORES)..."
  phase_start
  # Remove stale parameters.h5 to avoid config mismatch
  rm -f "$REPO_ROOT/data/tier1/parameters.h5"
  cd "$REPO_ROOT"
  snakemake --cores "$CORES" --configfile configs/validation_minimal.yaml
  cd "$WS_DIR"
  phase_end
else
  echo "[8/11] Skipping Snakemake (use --include-snakemake to enable)"
  echo ""
fi

# ---------- Phase 9: Chaos maps (opt-in) ----------
if [ "$INCLUDE_CHAOS" = true ]; then
  echo "[9/11] Generating chaos maps (workers=$CORES)..."
  phase_start
  python "$SCRIPT_DIR/generate_chaos_maps.py" \
    --mu "$MU" \
    --jacobi 3.1 \
    --resolution 200 \
    --t-final 100.0 \
    --workers "$CORES" \
    --output-dir "$WS_DIR/results"
  phase_end
else
  echo "[9/11] Skipping chaos maps (use --include-chaos-maps to enable)"
  echo ""
fi

# ---------- Phase 10: Generate report ----------
echo "[10/11] Generating validation report..."
phase_start
python "$SCRIPT_DIR/generate_report.py" \
  --workspace "$WS_DIR" \
  --output "$WS_DIR/reports/wp1_external_validation_report.md"
phase_end

# ---------- Phase 11: Artifact manifest ----------
PIPELINE_COMMAND="./run_validation.sh"
if [ "${#ORIGINAL_ARGS[@]}" -gt 0 ]; then
  PIPELINE_COMMAND="$PIPELINE_COMMAND ${ORIGINAL_ARGS[*]}"
fi

echo "[11/11] Generating artifact manifest..."
phase_start
python "$SCRIPT_DIR/generate_artifact_manifest.py" \
  --workspace "$WS_DIR" \
  --output "$WS_DIR/reports/wp1_artifact_manifest.json" \
  --command "$PIPELINE_COMMAND"
phase_end

echo "=== Pipeline complete ==="
echo "Report: $WS_DIR/reports/wp1_external_validation_report.md"
echo "Manifest: $WS_DIR/reports/wp1_artifact_manifest.json"
