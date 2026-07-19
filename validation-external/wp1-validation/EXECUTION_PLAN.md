# External WP1 Validation Execution Plan (Runbook)

This runbook executes the external validation workflow for WP1 in a reproducible way.

## Formal Qualification Decision (2026-07-19)

The formal campaign is complete with decision `PASS` under qualification ID
`WP1Q-v1-937694ba58a8`. Development, calibration, and the locked first-execution
holdout each passed 39/39 gates. The exact source snapshot, corpus, split
results, lock, report, and machine record are versioned in this workspace.

Verify the immutable lock and final record without rerunning or overwriting the
original holdout evidence:

```bash
cd /Users/bob/Desktop/3body
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
PYTHONPATH=/Users/bob/Desktop/3body \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  python validation-external/wp1-validation/scripts/verify_qualification_lock.py \
    --repo-root /Users/bob/Desktop/3body \
    --lock validation-external/wp1-validation/reports/wp1_qualification_lock.json \
    --corpus-manifest validation-external/wp1-validation/data/qualification/corpus_manifest.json

MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
PYTHONPATH=/Users/bob/Desktop/3body \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  python -c "from src.python.validation.qualification import load_qualification_record; print(load_qualification_record()['status'])"
```

The formal evidence is in:

- `reports/wp1_qualification_report.md`
- `reports/wp1_qualification_record.json`
- `reports/wp1_qualification_lock.json`
- `reports/wp1_qualified_artifact_audit.json`
- `results/qualification/`
- `data/qualification/`

The qualified claim and exclusions are normative in `qualification_spec.json`.
The older Earth-Moon workflow below remains a useful secondary diagnostic, but
it is not the formal multi-system qualification decision.

## Workspace
- Base directory: `/Users/bob/Desktop/3body/validation-external/wp1-validation`
- Config: `/Users/bob/Desktop/3body/validation-external/wp1-validation/config.yaml`

## Phase 1 — Preflight & Dependencies
```bash
cd /Users/bob/Desktop/3body
python verify_setup.py
python -c "import rebound; print(rebound.__version__)"

python -c "import snakemake" || python -m pip install snakemake
python -c "import heyoka; print(heyoka.__version__)"  # installed from environment.yml

pytest tests/test_integrators.py::test_ias15_energy_conservation -v
pytest tests/validation/test_chaos_indicators.py -v
```

## Phase 2 — Pipeline Hardening (Already Implemented)
Changes applied:
- Fixed orbit ID parsing in `Snakefile`.
- Fixed integrator selection in `Snakefile`.
- Added `solve_vy_from_jacobi(...)` helper.
- Added `generate_initial_states_for_mu_c(...)` sampler.
- Updated `generate_parameters` to emit full `states` array.
- Updated `integrate_orbit` to read `states` directly.
- Added unit tests for new helpers.

## Phase 3 — Smoke Run
```bash
cd /Users/bob/Desktop/3body
snakemake --cores 8 --config tier=1 n_mu=2 n_C=2 n_orbits_per_mu_c=5
```
Expected outputs:
- `data/tier1/parameters.h5`
- `data/tier1/analysis/validation_report.txt`

## Phase 4 — Full Tier Runs
```bash
cd /Users/bob/Desktop/3body
snakemake --cores 16 --config tier=1
snakemake --cores 16 --config tier=2
```
Log output:
- `/Users/bob/Desktop/3body/validation-external/wp1-validation/logs/`

## Phase 5 — JPL Reference Data
Fetch and normalize JPL periodic orbits:
```bash
python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/fetch_jpl_periodic_orbits.py \
  --system earth-moon

python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/normalize_jpl_orbits.py \
  --input /Users/bob/Desktop/3body/validation-external/wp1-validation/data/jpl/raw_latest.json \
  --output /Users/bob/Desktop/3body/validation-external/wp1-validation/data/jpl/normalized.parquet
```

## Phase 6 — Comparative Validation
```bash
python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/compare_to_jpl.py \
  --jpl /Users/bob/Desktop/3body/validation-external/wp1-validation/data/jpl/normalized.parquet \
  --use-periodic-library \
  --output /Users/bob/Desktop/3body/validation-external/wp1-validation/results/jpl_comparison.csv \
  --summary /Users/bob/Desktop/3body/validation-external/wp1-validation/results/jpl_comparison_summary.json

python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/build_jpl_seeded_catalog.py \
  --jpl /Users/bob/Desktop/3body/validation-external/wp1-validation/data/jpl/normalized.parquet \
  --max-jpl 300 \
  --metrics-output /Users/bob/Desktop/3body/validation-external/wp1-validation/results/jpl_seeded_validation.csv \
  --catalog-output /Users/bob/Desktop/3body/validation-external/wp1-validation/results/jpl_seeded_catalog.parquet \
  --summary /Users/bob/Desktop/3body/validation-external/wp1-validation/results/jpl_seeded_catalog_summary.json

python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/extended_precision_check.py \
  --use-periodic-library \
  --output /Users/bob/Desktop/3body/validation-external/wp1-validation/results/extended_precision_summary.csv
```

Current JPL-seeded catalogue thresholds are closure `<= 1e-8` and absolute Jacobi drift `<= 1e-12`. The 2026-07-19 bobs-mini run accepted 284/300 sampled seeds.

## Phase 7 — Chaos Maps
```bash
python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/generate_chaos_maps.py \
  --resolution 1000 \
  --output-dir /Users/bob/Desktop/3body/validation-external/wp1-validation/results
```

## Phase 8 — Reporting
```bash
python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/generate_report.py \
  --workspace /Users/bob/Desktop/3body/validation-external/wp1-validation \
  --output /Users/bob/Desktop/3body/validation-external/wp1-validation/reports/wp1_external_validation_report.md

python /Users/bob/Desktop/3body/validation-external/wp1-validation/scripts/generate_artifact_manifest.py \
  --workspace /Users/bob/Desktop/3body/validation-external/wp1-validation \
  --output /Users/bob/Desktop/3body/validation-external/wp1-validation/reports/wp1_artifact_manifest.json \
  --command "./run_validation.sh --skip-fetch --cores 8 --max-jpl 300"
```

## Notes
- The Snakefile now supports config overrides for `n_mu`, `n_C`, and `n_orbits_per_mu_c`.
- If `--config mu=<value>` is provided, the pipeline will fix `mu` to that single value.
- The JPL API endpoint can be overridden in `fetch_jpl_periodic_orbits.py` via `--base-url`.
