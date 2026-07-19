# WP1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP1Q-v1-937694ba58a8`

**Frozen code snapshot:** `937694ba58a8f3ff1fc94804d642b145e5d8b4a84c7494c7a206c4a65fc642a6`

## Qualified Claim

WP1 is qualified for normalized rotating-frame CR3BP propagation against externally sourced JPL periodic-orbit data across the declared systems, Lyapunov and Halo families, published stability regimes, and float64/high-precision validation tiers. Qualification includes independent arbitrary-precision checkpoint propagation, invariant and reversibility checks, analytic STM/Floquet validation, strict representative differential correction, output-schema enforcement, and a locked holdout suite.

## Evidence Boundary

This qualification does not claim a native production periodic-orbit catalogue, universal correctness outside the declared scope, production-scale Tier 2 throughput, long-horizon 10^4-10^6-period accuracy, regularized close-encounter switching, or validated MEGNO/FLI labels.

## External Corpus

The frozen corpus contains 400 stratified records from 67218 NASA/JPL records. The API payload version is pinned to `1.0` and every raw source file, source record, corpus row, split assignment, and holdout ID is content-addressed.

- Systems: sun-earth, jupiter-europa, saturn-titan, earth-moon
- Families: Lyapunov L1/L2; Halo L1/L2 northern/southern
- Stability strata: marginal, weakly unstable, moderately unstable, strongly unstable
- Split counts: {'calibration': 80, 'development': 240, 'holdout': 80}

The development and calibration splits were executed before the code/spec/corpus lock was created. The holdout evaluator verifies every frozen input hash before reading holdout results.

## Development Decision

**PASS** with case counts `{'float64': 240, 'oracle': 36, 'reconstruction': 40, 'stability': 48}`.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `float64.minimum_cases` | 240 | >= 80 | PASS |
| `float64.integration_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `float64.jacobi_catalog_delta_p95` | 4.884981e-15 | <= 5.000000e-12 | PASS |
| `float64.jacobi_catalog_delta_max` | 4.884981e-15 | <= 5.000000e-11 | PASS |
| `float64.jacobi_max_drift_p95` | 2.062794e-14 | <= 1.000000e-12 | PASS |
| `float64.jacobi_max_drift_max` | 8.308909e-13 | <= 1.000000e-10 | PASS |
| `float64.frame_roundtrip_max` | 3.552714e-15 | <= 5.000000e-13 | PASS |
| `float64.reversibility_error_p95` | 2.942537e-15 | <= 1.000000e-10 | PASS |
| `float64.reversibility_error_max` | 1.149182e-12 | <= 1.000000e-07 | PASS |
| `oracle.minimum_cases` | 36 | >= 24 | PASS |
| `oracle.success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `oracle.high_precision_jacobi_drift_p95` | 1.682426e-30 | <= 1.000000e-25 | PASS |
| `oracle.high_precision_jacobi_drift_max` | 5.858133e-29 | <= 1.000000e-23 | PASS |
| `oracle.checkpoint_state_error_p95` | 2.607198e-10 | <= 1.000000e-09 | PASS |
| `oracle.checkpoint_state_error_max` | 3.194458e-09 | <= 1.000000e-07 | PASS |
| `stability.minimum_cases` | 48 | >= 32 | PASS |
| `stability.success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `stability.relative_index_error_p95` | 3.113060e-05 | <= 1.000000e-04 | PASS |
| `stability.relative_index_error_max` | 7.058792e-05 | <= 5.000000e-03 | PASS |
| `stability.classification_accuracy` | 1.000000e+00 | >= 9.800000e-01 | PASS |
| `stability.monodromy_determinant_error_max` | 1.930869e-07 | <= 1.000000e-04 | PASS |
| `stability.reciprocal_pair_error_max` | 2.009536e-07 | <= 1.000000e-04 | PASS |
| `reconstruction.minimum_cases` | 40 | >= 30 | PASS |
| `reconstruction.success_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `reconstruction.closure_error_p95` | 7.317581e-12 | <= 1.000000e-08 | PASS |
| `reconstruction.closure_error_max` | 1.905024e-11 | <= 1.000000e-07 | PASS |
| `reconstruction.symmetry_residual_p95` | 1.168666e-13 | <= 1.000000e-09 | PASS |
| `coverage.float64.declared_systems` | 4 | == 4 | PASS |
| `coverage.float64.declared_families` | 2 | == 2 | PASS |
| `coverage.float64.stability_regimes` | 4 | == 4 | PASS |
| `coverage.oracle.declared_systems` | 4 | == 4 | PASS |
| `coverage.oracle.declared_families` | 2 | == 2 | PASS |
| `coverage.oracle.stability_regimes` | 4 | == 4 | PASS |
| `coverage.stability.declared_systems` | 4 | == 4 | PASS |
| `coverage.stability.declared_families` | 2 | == 2 | PASS |
| `coverage.stability.stability_regimes` | 4 | == 4 | PASS |
| `coverage.reconstruction.declared_systems` | 4 | == 4 | PASS |
| `coverage.reconstruction.declared_families` | 2 | == 2 | PASS |
| `coverage.reconstruction.stability_regimes` | 4 | == 4 | PASS |

## Calibration Decision

**PASS** with case counts `{'float64': 80, 'oracle': 20, 'reconstruction': 24, 'stability': 24}`.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `float64.minimum_cases` | 80 | >= 20 | PASS |
| `float64.integration_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `float64.jacobi_catalog_delta_p95` | 4.884981e-15 | <= 5.000000e-12 | PASS |
| `float64.jacobi_catalog_delta_max` | 4.884981e-15 | <= 5.000000e-11 | PASS |
| `float64.jacobi_max_drift_p95` | 3.188561e-14 | <= 1.000000e-12 | PASS |
| `float64.jacobi_max_drift_max` | 6.146195e-13 | <= 1.000000e-10 | PASS |
| `float64.frame_roundtrip_max` | 4.440892e-16 | <= 5.000000e-13 | PASS |
| `float64.reversibility_error_p95` | 1.097256e-15 | <= 1.000000e-10 | PASS |
| `float64.reversibility_error_max` | 3.722087e-13 | <= 1.000000e-07 | PASS |
| `oracle.minimum_cases` | 20 | >= 12 | PASS |
| `oracle.success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `oracle.high_precision_jacobi_drift_p95` | 8.017826e-31 | <= 1.000000e-25 | PASS |
| `oracle.high_precision_jacobi_drift_max` | 1.969530e-30 | <= 1.000000e-23 | PASS |
| `oracle.checkpoint_state_error_p95` | 1.206503e-10 | <= 1.000000e-09 | PASS |
| `oracle.checkpoint_state_error_max` | 2.139368e-10 | <= 1.000000e-07 | PASS |
| `stability.minimum_cases` | 24 | >= 16 | PASS |
| `stability.success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `stability.relative_index_error_p95` | 1.328201e-06 | <= 1.000000e-04 | PASS |
| `stability.relative_index_error_max` | 7.350277e-04 | <= 5.000000e-03 | PASS |
| `stability.classification_accuracy` | 1.000000e+00 | >= 9.800000e-01 | PASS |
| `stability.monodromy_determinant_error_max` | 1.507467e-06 | <= 1.000000e-04 | PASS |
| `stability.reciprocal_pair_error_max` | 8.752736e-07 | <= 1.000000e-04 | PASS |
| `reconstruction.minimum_cases` | 24 | >= 16 | PASS |
| `reconstruction.success_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `reconstruction.closure_error_p95` | 2.294877e-12 | <= 1.000000e-08 | PASS |
| `reconstruction.closure_error_max` | 1.968566e-11 | <= 1.000000e-07 | PASS |
| `reconstruction.symmetry_residual_p95` | 8.481785e-14 | <= 1.000000e-09 | PASS |
| `coverage.float64.declared_systems` | 4 | == 4 | PASS |
| `coverage.float64.declared_families` | 2 | == 2 | PASS |
| `coverage.float64.stability_regimes` | 4 | == 4 | PASS |
| `coverage.oracle.declared_systems` | 4 | == 4 | PASS |
| `coverage.oracle.declared_families` | 2 | == 2 | PASS |
| `coverage.oracle.stability_regimes` | 4 | == 4 | PASS |
| `coverage.stability.declared_systems` | 4 | == 4 | PASS |
| `coverage.stability.declared_families` | 2 | == 2 | PASS |
| `coverage.stability.stability_regimes` | 4 | == 4 | PASS |
| `coverage.reconstruction.declared_systems` | 4 | == 4 | PASS |
| `coverage.reconstruction.declared_families` | 2 | == 2 | PASS |
| `coverage.reconstruction.stability_regimes` | 4 | == 4 | PASS |

## Holdout Decision

**PASS** with case counts `{'float64': 80, 'oracle': 36, 'reconstruction': 40, 'stability': 48}`.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `float64.minimum_cases` | 80 | >= 20 | PASS |
| `float64.integration_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `float64.jacobi_catalog_delta_p95` | 4.884981e-15 | <= 5.000000e-12 | PASS |
| `float64.jacobi_catalog_delta_max` | 4.884981e-15 | <= 5.000000e-11 | PASS |
| `float64.jacobi_max_drift_p95` | 1.038059e-13 | <= 1.000000e-12 | PASS |
| `float64.jacobi_max_drift_max` | 7.709389e-13 | <= 1.000000e-10 | PASS |
| `float64.frame_roundtrip_max` | 3.552714e-15 | <= 5.000000e-13 | PASS |
| `float64.reversibility_error_p95` | 2.248474e-15 | <= 1.000000e-10 | PASS |
| `float64.reversibility_error_max` | 3.602110e-13 | <= 1.000000e-07 | PASS |
| `oracle.minimum_cases` | 36 | >= 24 | PASS |
| `oracle.success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `oracle.high_precision_jacobi_drift_p95` | 1.848545e-30 | <= 1.000000e-25 | PASS |
| `oracle.high_precision_jacobi_drift_max` | 2.079040e-29 | <= 1.000000e-23 | PASS |
| `oracle.checkpoint_state_error_p95` | 6.829460e-10 | <= 1.000000e-09 | PASS |
| `oracle.checkpoint_state_error_max` | 3.386373e-09 | <= 1.000000e-07 | PASS |
| `stability.minimum_cases` | 48 | >= 32 | PASS |
| `stability.success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `stability.relative_index_error_p95` | 3.331779e-06 | <= 1.000000e-04 | PASS |
| `stability.relative_index_error_max` | 6.608312e-05 | <= 5.000000e-03 | PASS |
| `stability.classification_accuracy` | 1.000000e+00 | >= 9.800000e-01 | PASS |
| `stability.monodromy_determinant_error_max` | 8.849565e-07 | <= 1.000000e-04 | PASS |
| `stability.reciprocal_pair_error_max` | 8.377643e-07 | <= 1.000000e-04 | PASS |
| `reconstruction.minimum_cases` | 40 | >= 30 | PASS |
| `reconstruction.success_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `reconstruction.closure_error_p95` | 1.173204e-11 | <= 1.000000e-08 | PASS |
| `reconstruction.closure_error_max` | 3.674889e-11 | <= 1.000000e-07 | PASS |
| `reconstruction.symmetry_residual_p95` | 3.496488e-13 | <= 1.000000e-09 | PASS |
| `coverage.float64.declared_systems` | 4 | == 4 | PASS |
| `coverage.float64.declared_families` | 2 | == 2 | PASS |
| `coverage.float64.stability_regimes` | 4 | == 4 | PASS |
| `coverage.oracle.declared_systems` | 4 | == 4 | PASS |
| `coverage.oracle.declared_families` | 2 | == 2 | PASS |
| `coverage.oracle.stability_regimes` | 4 | == 4 | PASS |
| `coverage.stability.declared_systems` | 4 | == 4 | PASS |
| `coverage.stability.declared_families` | 2 | == 2 | PASS |
| `coverage.stability.stability_regimes` | 4 | == 4 | PASS |
| `coverage.reconstruction.declared_systems` | 4 | == 4 | PASS |
| `coverage.reconstruction.declared_families` | 2 | == 2 | PASS |
| `coverage.reconstruction.stability_regimes` | 4 | == 4 | PASS |

## Interpretation

A PASS substantiates the exact qualified claim above. It shows that the same rounded external states propagated by WP1 and by a separately encoded, 224-bit adaptive Taylor oracle agree at declared checkpoints; that invariant, frame, and reversibility gates pass; that analytic state-transition propagation reproduces JPL Floquet stability; and that strict WP1 differential correction recovers nearby periodic Lyapunov/Halo members from perturbed external seeds.

One-period closure is retained as a diagnostic, not treated as a pure integrator error: published decimal initial conditions can amplify rounding along unstable orbits. The oracle checkpoint discrepancy is the integrator-accuracy test.

## Downstream Use

The production writer rejects a missing or failed qualification record and stamps the qualification ID and hashes into HDF5 and Parquet artifacts. Numeric state columns are float64; Tier 2 output also preserves decimal high-precision states.

## Cross-Platform Parity

Bounded Linux/amd64 parity: **PASS**, with 12/12 evidence-bearing tests passing on `navillusserver1` using Python 3.11.15 in `python@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93`.

This is a bounded architecture check of the analytic STM/Floquet path, strict differential correctors, evidence integrity, and high-precision artifact contract. It is not represented as a full Linux replay of the campaign.

## References

- NASA/JPL Three-Body Periodic Orbits API: https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html
- NASA Astrodynamics Convention and Modeling Reference, TP-20220014814: https://ntrs.nasa.gov/citations/20220014814
- Poincare trajectory-design tool stability convention: https://indico.esa.int/event/224/papers/3852/files/225-Poincare_Vaquero.pdf

## Reproducibility

- Base commit: `d7df4eb63650a19aa56da16c569dc461b3bd36d8`
- Lock SHA-256: `ae72214d2149138a677bd1d4c7996347cf0bfa454290d6f1a06aa4daf88c83df`
- Corpus SHA-256: `757565e14d9f9dcc4c489923df1abc32cf09339ea654a154519eed22f061e6f3`
- Qualification record: `validation-external/wp1-validation/reports/wp1_qualification_record.json`
