# WP1 bobs-mini Migration and Publication Readiness Plan

Date: 2026-07-19

Repository target: `/Users/bob/Desktop/3body`

## Goal

Make WP1 publish-ready from a clean `3body` checkout on `bobs-mac-mini`, using the Mac mini as the primary workstation and Navillus only as an independent Linux/amd64 verification node.

Publish-ready means:

- a reproducible WP1 environment can be created from documented commands;
- the project test suite collects cleanly and has a clear WP1 acceptance gate;
- QD/C++ precision support is installed, built, and verified;
- Tier 1 and Tier 2 WP1 validation reports are present and regenerated from scripts;
- JPL/external validation results support the claims being made;
- outputs include provenance: commit SHA, environment lock, commands, seeds, and artifact manifest;
- public-facing docs match the actual evidence rather than aspirational project status.

## Implementation Progress: 2026-07-19

This clean bobs-mini checkout now supports a scoped WP1 publication package: environment setup, acceptance gates, qualified Tier 1/Tier 2 artifacts, external JPL cross-checks, and a locked multi-system qualification. Qualification `WP1Q-v1-937694ba58a8` passes 39/39 gates on development, calibration, and first-execution holdout data. It is not publication-ready for the broader claim that WP1 natively generates a production periodic-orbit catalogue.

Completed:

- Cloned `git@github-jacob:jacobrsullivan/3body.git` into `/Users/bob/Desktop/3body`.
- Created `/Users/bob/Desktop/3body/notes`.
- Installed micromamba and created `/Users/bob/micromamba/envs/wp1_env`.
- Reworked dependency ownership so QD and `heyoka.py` come from conda-forge, while Poetry installs the remaining project dependencies.
- Added `numpy>=1.24,<2.3` and QD dependencies to `environment.yml`.
- Removed the PyPI `heyoka` build path from `pyproject.toml`; it requires unavailable C++ heyoka package config files on this host.
- Regenerated `poetry.lock`.
- Built C++ QD checks with `scripts/build_cpp.sh`.
- Fixed stale C++ QD test expectations and qd_python binding build errors.
- Fixed `verify_setup.py` and `tests/python/test_environment.py` to use the actual `build/verify_qd` path and current project docs layout.
- Fixed Python test collection blockers:
  - optionalized WP3 JAX/Flax imports in `src/python/ml/__init__.py`;
  - made `tests/unit` an explicit package;
  - restored missing symbolic helpers in `src/python/symbolic/spinor_basis.py`.
- Replaced `scripts/run_tests.sh` with an explicit WP1 acceptance gate.
- Added `src/python/integrators/heyoka_taylor.py`, a 160-bit `heyoka.real` Taylor integrator for bounded Tier 2 smoke validation.
- Wired Tier 2 Snakemake to use `HeyokaTaylorIntegrator` and to report high-precision Jacobi drift from HDF5 attributes rather than recomputing Tier 2 drift from float states.
- Added a guarded planar Lyapunov differential corrector for small L1/L2 amplitudes (`<= 0.15`), with fallback to the historical approximation outside that safe range.
- Fixed CR3BP rotating-frame reversibility validation to use the correct reversing symmetry `(x,y,z,vx,vy,vz) -> (x,-y,z,-vx,vy,-vz)` instead of a plain velocity flip.
- Narrowed the convergence diagnostic to corrected small-amplitude Lyapunov seeds so it no longer conflates simplified Halo candidates with integrator/closure behavior.

Acceptance gate now passing:

```bash
cd /Users/bob/Desktop/3body
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  ./scripts/run_tests.sh
```

Observed result:

- setup verification passes;
- pytest collection is clean, with 843 tests collected;
- focused WP1 suite passes, with 104 tests passing;
- CTest QD checks pass, with 2/2 tests passing.

Regenerated validation artifacts:

- Formal external qualification completed against 67,218 pinned NASA/JPL
  records and a 400-record multi-system corpus; all three splits pass 39/39
  gates under `WP1Q-v1-937694ba58a8`.
- Holdout completed 80 float64, 36 independent 224-bit oracle, 48
  STM/Floquet, and 40 strict reconstruction cases with 100% method success.
- Bounded Navillus Linux/amd64 parity passes 12/12 evidence-bearing tests.
- Qualified Tier 1 and Tier 2 HDF5/Parquet outputs embed the qualification ID,
  lock hash, and record hash; Tier 2 decimal states survive export exactly.

- Tier 1 minimal Snakemake run completed with 30 orbits at target `1e-14`.
- Tier 1 report: mean drift `2.88e-15`, median drift `4.59e-16`, 95th percentile `1.20e-14`, max drift `2.94e-14`, pass rate `93.3%`.
- Tier 2 bounded Snakemake smoke completed with 3 orbits at target `1e-25`, duration `1.0`, output interval `0.5`, and 160-bit `heyoka.real`.
- Tier 2 report: mean drift `5.27e-28`, median drift `4.83e-28`, 95th percentile `6.36e-28`, max drift `6.53e-28`, pass rate `100.0%`.
- External validation pipeline completed with `--max-jpl 300`.
- JPL sample: 300 sampled candidates from 21,938 fetched records; closure median `2.30e-11`; Jacobi drift median `4.44e-16`.
- Added `validation-external/wp1-validation/scripts/build_jpl_seeded_catalog.py`.
- Built an external/JPL-seeded validation catalogue from the same 300 sampled JPL records:
  - metrics CSV: `validation-external/wp1-validation/results/jpl_seeded_validation.csv`;
  - accepted-only Parquet: `validation-external/wp1-validation/results/jpl_seeded_catalog.parquet`;
  - summary JSON: `validation-external/wp1-validation/results/jpl_seeded_catalog_summary.json`;
  - thresholds: closure `<= 1e-8`, absolute Jacobi drift `<= 1e-12`;
  - accepted rows: 284/300 (`94.7%`);
  - accepted-catalogue closure median `2.01e-11`, 95th percentile `9.73e-10`, max `6.23e-09`;
  - accepted-catalogue absolute Jacobi drift median `4.44e-16`, 95th percentile `9.50e-15`, max `3.64e-14`.
- Report regenerated at `validation-external/wp1-validation/reports/wp1_external_validation_report.md`.
- Added `validation-external/wp1-validation/scripts/generate_artifact_manifest.py`.
- Artifact manifest generated at `validation-external/wp1-validation/reports/wp1_artifact_manifest.json`; it currently hashes 22 artifacts and records commit `13d20836bcadbea15a37e0800609702002d76f75`, dirty worktree status, environment/package versions, and the command `./run_validation.sh --skip-fetch --cores 8 --max-jpl 300`.
- `validation-external/wp1-validation/scripts/generate_report.py` now states the evidence boundary explicitly: JPL-seeded integrator validation is positive evidence, while native-candidate quality remains a blocker for native catalogue claims.
- Reversibility now passes the short-time CR3BP symmetry check: `T=1` median position RMS `2.64e-16`, 95th percentile `3.81e-15`, pass rate `100%`. Longer `T=10` and `T=50` rows remain stress diagnostics in unstable orbit neighborhoods.
- Convergence/closure diagnostic on corrected small-amplitude Lyapunov seeds now reports median closure about `1.02e-12` and median Jacobi drift about `1.5e-16`; the fitted slope is explicitly marked floor-limited rather than treated as an empirical order proof.
- Updated external validation pipeline run on 2026-07-19: `./run_validation.sh --skip-fetch --cores 8 --max-jpl 300` completed end to end, including the new JPL-seeded catalogue and artifact-manifest phases, and regenerated `reports/wp1_external_validation_report.md`.
- Final hygiene check on 2026-07-19: `git diff --check` passed.
- Final fast gate on 2026-07-19: `./scripts/run_tests.sh --fast` passed with setup verification, 104 focused WP1 tests, and 2/2 CTest checks.
- Final canonical gate on 2026-07-19: `./scripts/run_tests.sh` passed with setup verification, 843 tests collected, 104 focused WP1 tests passed, and 2/2 CTest checks.

Remaining publication blockers for broad/native catalogue claims:

- `AdaptiveSymplecticIntegrator` remains a float64 prototype and now rejects tolerances below its float64 floor before stepping. Before this fix, Tier 2 could silently write a false-positive report after failed integrations.
- The new `HeyokaTaylorIntegrator` proves a bounded Tier 2 smoke, not a production-scale Tier 2 catalogue.
- The legacy native candidate comparison is still weak against JPL: median state distance `8.37e-01` and median period error `8.90e-01`. The qualified representative corrector is not yet a family-continuation catalogue generator.
- Current evidence supports the exact scoped claim in `qualification_spec.json`; it does not support "native WP1-generated periodic-orbit catalogue is publish-ready."

Required next fixes before publication claims:

- Scale Tier 2 beyond the current 3-orbit smoke and decide whether the publication scope requires a full Tier 2 catalogue or a documented bounded validation subset.
- Replace or supplement the remaining simplified Halo candidate path with corrected periodic initial conditions. The external/JPL-seeded path now exists and is publishable only under that scoped claim.
- Decide whether to keep the small-amplitude Lyapunov corrector as a documented native subset or extend it through family continuation before making native-generation claims.
- Decide the publication scope: infrastructure/methods paper, validated small catalogue, or full catalogue.

## Host Roles

`bobs-mac-mini`:

- Primary development and validation workstation.
- Apple M4 Pro, 14 cores, 64 GB RAM, large local disk.
- Best place for environment rebuilds, test repair, data wrangling, plotting, and publication packaging.
- Native platform is macOS arm64, so final claims must account for platform-specific numerical behavior.

`navillus`:

- Keep as a secondary Linux/amd64 reference node.
- Do not use it for the full production rerun unless later benchmarks show the runtime is acceptable.
- Use it for bounded reproducibility checks: selected orbit subsets, smoke/acceptance tests, and parity checks against bobs outputs.

## Step 1: Establish Clean Baseline

- Confirm clone location: `/Users/bob/Desktop/3body`.
- Record `git rev-parse HEAD`, branch, remote URL, and clean worktree status.
- Avoid editing through mounted shares; work directly on bobs local APFS disk.
- Add a small setup log under `notes/` as decisions are made.

## Step 2: Build the WP1 Environment on bobs

- Install Miniforge or micromamba for arm64.
- Create `wp1_env` with Python 3.11.
- Install Poetry and project dependencies, respecting `numpy < 2.3`.
- Install CMake and compilers.
- Install or build QD with headers and libraries visible inside the conda environment.
- Build `qd_python` and C++ verification binaries.
- Run `python verify_setup.py`.

Acceptance:

- Python is 3.11.x inside `wp1_env`.
- NumPy satisfies the project constraint.
- CMake is available.
- QD headers and libraries are found.
- `verify_qd` or its replacement passes on bobs.

## Step 3: Repair Test and Acceptance Gates

- Run `pytest --collect-only` and fix collection failures first.
- Fix or isolate non-WP1 import breakage that prevents test collection.
- Replace the misleading "full suite" behavior in `scripts/run_tests.sh` with explicit gates:
  - environment gate;
  - WP1 fast gate;
  - QD/C++ gate;
  - full scientific validation gate.
- Add a single documented WP1 acceptance command for pre-publication checks.

Acceptance:

- Test collection succeeds.
- WP1 fast tests pass locally.
- External validation tests pass locally.
- QD/C++ checks pass or are explicitly marked unavailable with a documented reason.

## Step 4: Fix WP1 Scientific Validation Gaps

- Regenerate Tier 1 validation from scripts, not stale artifacts.
- Keep Tier 2 validation regenerated from scripts; the current bounded Tier 2 smoke passes, while production-scale Tier 2 remains a scope/runtime decision.
- Treat the current JPL result carefully:
  - integrator accuracy on JPL initial conditions is strong;
  - Richardson approximation quality is poor and should not be presented as publish-ready orbit generation.
- Prefer the new external/JPL-seeded catalogue or numerically corrected native periodic initial conditions for publication claims.
- Add convergence, closure error, Jacobi drift, reversibility, and chaos classification tables.

Acceptance:

- Tier 1 and Tier 2 reports exist with command provenance.
- Pass/fail thresholds are declared before running.
- Failed or borderline orbits are included in the report, not hidden.
- Claims distinguish integrator accuracy from candidate initial-condition quality.

## Step 5: Produce Publication Artifacts

- Generate final tables, figures, and machine-readable CSV/Parquet/HDF5 summaries.
- Add artifact manifests with checksums and creation commands.
- Correct README and status docs so they match actual WP1 evidence.
- Prepare a reproducibility appendix:
  - hardware;
  - OS;
  - Python/package versions;
  - QD build details;
  - exact commands;
  - seed policy.

Acceptance:

- A fresh clone plus documented setup can reproduce the small validation suite.
- Publication figures/tables regenerate from tracked scripts and untracked data inputs with manifests.
- Docs no longer claim WP1 completeness unless the acceptance gate supports it.

## Step 6: Cross-Platform Verification Strategy

Run the main production work on bobs. For independent verification, use one of:

- bobs native macOS arm64 plus a Linux container on bobs via Colima;
- bobs native macOS arm64 plus bounded Navillus Linux/amd64 checks;
- all three if runtime is acceptable.

The Linux comparison should validate numerical agreement and reproducibility, not duplicate the entire production workload by default.

## Step 7 Clarification: Navillus Runtime

Yes, a full step-7 rerun on Navillus may be impractically long. Navillus has much less RAM and weaker throughput than bobs. The plan should not require full production-scale validation there.

After the 2026-07-19 bobs run, Navillus should remain bounded. A full Navillus rerun would be expensive and would mostly reproduce known candidate-validation failures until those blockers are fixed. Use Navillus now only for small Linux/amd64 parity checks of the environment, acceptance gate, and the 3-orbit Tier 2 smoke.

Navillus reachability check on 2026-07-19:

- host: `navillusserver1`
- OS: Ubuntu Linux x86_64, kernel `7.0.0-27-generic`
- checkout: `/home/navillus1/dev/3body`
- commit: `13d20836bcadbea15a37e0800609702002d76f75`, branch `main`
- worktree: clean at the base commit, without the bobs-mini repair patches
- visible Python tooling: `/usr/bin/python3` at Python `3.14.4`; no `micromamba`, `mamba`, or `conda` found on PATH

Do not run Navillus parity until either the bobs-mini changes are committed/pushed or a deliberate patch bundle is applied there. The first Navillus parity target should be `./scripts/run_tests.sh --fast` plus the 3-orbit Tier 2 smoke, not the full production workflow.

Recommended Navillus scope:

- environment setup or container smoke test;
- test collection and WP1 fast gate;
- 10 to 30 representative orbit validations;
- a small JPL subset;
- checksum/metadata comparison for shared inputs;
- one longer sentinel run if time allows.

Escalate to a larger Navillus run only if the bounded checks disagree with bobs or if a reviewer/paper claim specifically requires native Linux/amd64 reproduction at scale.

## Immediate Next Commands

From bobs, for the current repaired acceptance gate:

```bash
cd /Users/bob/Desktop/3body
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  ./scripts/run_tests.sh
```

For Tier 1 smoke regeneration:

```bash
cd /Users/bob/Desktop/3body
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
PYTHONPATH=/Users/bob/Desktop/3body \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  snakemake --cores 8 --configfile configs/validation_minimal.yaml --config tier=1
```

For Tier 2 bounded smoke regeneration:

```bash
cd /Users/bob/Desktop/3body
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
PYTHONPATH=/Users/bob/Desktop/3body \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  snakemake --cores 3 --configfile configs/validation_minimal.yaml \
    --config tier=2 n_orbits_per_mu_c=1 duration=1.0 \
    output_interval=0.5 target_accuracy=1e-25 precision_bits=160 --forceall
```

For external validation:

```bash
cd /Users/bob/Desktop/3body/validation-external/wp1-validation
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
PYTHONPATH=/Users/bob/Desktop/3body \
  /opt/homebrew/bin/micromamba run -n wp1_env \
  ./run_validation.sh --cores 8 --max-jpl 300
```
