# Reproducible Legacy Baseline on bobs-mini

Date: 2026-07-22

## Status

The complete 1,223-test repository collection has a clean, disjoint baseline
on bobs-mini. Every collected test belongs to exactly one execution lane:

- fast: neither `slow` nor `legacy_quarantine`
- slow: `slow` and not `legacy_quarantine`
- quarantine: `legacy_quarantine`

Manifest selectors are checked against full collection and fail closed when a
recorded node ID disappears. Historical failures are exact node IDs, not file-
or-directory-wide exclusions. Non-resource quarantines use strict xfail, so an
unexpected pass fails the quarantine gate and requires an explicit ledger
change.

## Clean Host Replay

Host checkout: `/Users/bob/Desktop/3body`

Clean environment: `/Users/bob/micromamba/envs/3body-legacy-v1`

Platform: macOS arm64

The environment was created from `environment-legacy.yml` by
`scripts/create_legacy_environment.sh`. The script applies the project
`poetry.lock` in the active conda environment, force-builds `qd_python`, and
checks the binding and QD version tags before returning.

The exact native conda transaction is recorded in
`environment-locks/bobs-osx-arm64.lock`:

```text
SHA-256 4535436197c1358f049720219a9fcb0a25612980b2286767cf7c51fd20056d2f
```

The explicit native lock records pybind11 3.0.3 because heyoka's conda package
requires pybind11 ABI 11. The subsequent locked Poetry layer installs the
project's pybind11 2.13.6 headers, which are the qualified `qd_python` build
input. The explicit conda export does not replace `poetry.lock` or the exact
JAX pip pins in `environment-legacy.yml`; all layers are required.

The baseline runner rejects runtime drift before invoking pytest. Its exact
runtime map is:

| Component | Version |
| --- | --- |
| Python | 3.11.15 |
| QD | 2.3.22 |
| qd_python | 1.0.0 |
| pybind11 | 2.13.6 |
| NumPy | 2.2.6 |
| SciPy | 1.16.1 |
| pytest | 8.4.1 |
| heyoka | 7.12.0 |
| REBOUND | 4.4.10 |
| SymPy | 1.14.0 |
| mpmath | 1.4.1 |
| JAX | 0.9.0.1 |
| jaxlib | 0.9.0.1 |
| ml_dtypes | 0.5.4 |
| opt_einsum | 3.4.0 |

## qd_python Baseline

`qd_python` is built in place against QD 2.3.22 and embeds both its binding
version and qualified QD version. The binding now supplies checked division,
Python absolute value, `is_one`, domain-checked square root/logarithms/inverse
trigonometric functions, base-2 logarithm, rounding, and machine epsilon.

Clean-host result:

```text
25 passed in 0.04s
```

Five stale expected-failure annotations were removed after the repaired
operations passed. Source utility functions imported by tests explicitly opt
out of pytest discovery, preventing helper APIs from being counted as tests.

## Gate Results

Collection and all lanes ran in the clean `3body-legacy-v1` environment.

| Lane | Result | Runtime |
| --- | --- | --- |
| fast | 1,087 passed, 2 skipped, 134 deselected | 74.03 s |
| slow | 45 passed, 2 skipped, 1,176 deselected | 275.29 s |
| quarantine | 79 strict xfailed, 8 skipped, 1,136 deselected | 742.34 s |

There were no ordinary failures and no XPASS results. The three lanes account
for all 1,223 collected tests without overlap.

The slow lane is dominated by three tests measured at 163.27, 53.28, and
42.57 seconds. It produced 1,533 warnings, principally repeated legacy energy-
constraint initialization warnings. The fast lane produced 61 known warnings,
including old pytest return-value and NumPy matmul diagnostics. These warnings
did not change an assertion outcome and remain visible as cleanup debt rather
than hidden gate failures.

## Historical Quarantine

`tests/legacy_baseline_manifest.json` is the authoritative ledger. Its 87 exact
entries comprise:

- 36 pre-publication or superseded WP3 prototype/runtime cases
- 14 superseded reduction expectations
- 10 legacy time-regularization and RATTLE cases
- 4 superseded symbolic KS convention cases
- 9 legacy Kovacic/Morales-Ramis cases
- 5 legacy chaos-indicator cases
- 4 superseded Lagrange-validation cases
- 4 legacy Yoshida-8 integration/timestep cases
- 1 historical architecture-lint expectation

Seventy-nine entries are strict xfails. No inline xfail decorators remain in
the test suite. Eight entries are explicit skips because they
are not stable bounded gates on bobs-mini: one CR3BP escape simulation remained
at full CPU beyond 11 minutes, six legacy Kovacic/Morales-Ramis operations did
not finish within 60 seconds, and one Morales-Ramis operation passed alone in
29.5 seconds but exceeded 120 seconds in the complete lane.

The active structural Kovacic tests that terminate remain in the slow green
lane. The qualified WP4-MR-v2 implementation does not import or depend on this
legacy placeholder implementation.

## Reproduction

From the repository root on bobs-mini:

```bash
MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  ./scripts/create_legacy_environment.sh 3body-legacy-v1

MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  /opt/homebrew/bin/micromamba run -n 3body-legacy-v1 \
  ./scripts/run_legacy_baseline.sh collect

MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  /opt/homebrew/bin/micromamba run -n 3body-legacy-v1 \
  ./scripts/run_legacy_baseline.sh fast

MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  /opt/homebrew/bin/micromamba run -n 3body-legacy-v1 \
  ./scripts/run_legacy_baseline.sh slow

MAMBA_ROOT_PREFIX=/Users/bob/micromamba \
  /opt/homebrew/bin/micromamba run -n 3body-legacy-v1 \
  ./scripts/run_legacy_baseline.sh quarantine
```

## Claim Boundary

This result establishes a reproducible green baseline for the entire legacy
suite: passing behavior is green, slow behavior is isolated, and every known
historical failure has a named, exact, reproducible disposition. It does not
convert quarantined prototypes into qualified science and does not strengthen
their claims.

No frozen WP1, WP2, WP3, or WP4 decision-bearing artifact was regenerated or
reinterpreted. Their sealed qualification decisions remain authoritative and
unchanged; this baseline removes legacy-suite ambiguity around that completed
chain.
