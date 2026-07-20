# WP1-CAT-v1 qualification report

**Qualification:** `WP1-CAT-v1-5dc7ad44b78f`  
**Status:** **PASS**  
**Lock:** `31da65d3965b98c57c2e05c8906677710e570f996c1fca44f915a0584a75b4dd`

## Qualified claim

WP1-CAT-v1 qualifies deterministic native generation of two bounded Earth-Moon planar Lyapunov family segments in normalized rotating-frame CR3BP: L1 amplitudes 0.001 through 0.080 and L2 amplitudes 0.001 through 0.040, where amplitude is x_L-x on the y=z=vx=vz=0, vy>0 canonical section. Seeds are derived only from the analytic collinear center mode, sequential members are differentially corrected without external orbit seeds, accepted members satisfy frozen closure and symmetry gates, phase-invariant (Jacobi constant, period) deduplication is applied, Floquet stability labels are attached, and recovery is evaluated against disjoint pinned NASA/JPL development, calibration, and holdout rows.

## Evidence boundary

This campaign does not qualify Halo, vertical, resonant, bifurcating, collision, or full three-body families; other mass systems; pseudo-arclength traversal through folds; completeness even inside the declared windows; discovery of disconnected families; long-horizon stability; catalogue uniqueness outside the canonical section; portable throughput guarantees; or a production catalogue of all CR3BP or three-body periodic orbits. External recovery establishes agreement with a sampled pinned JPL corpus only. Throughput is reported as host-specific evidence and is not a gate.

## Evidence summary

- Native candidates: 159 (0 duplicates rejected)
- External data used during native generation: False
- Measured end-to-end rate: 10.503 corrected/stability-labelled orbits/s
- Development: PASS on 180 JPL rows
- Calibration: PASS on 60 JPL rows
- Holdout: PASS on 60 JPL rows

## Gate detail

| Split | Gate | Observed | Requirement | Result |
|---|---|---:|---:|---|
| development | `native.candidate_count` | 159 | >= 159 | PASS |
| development | `native.L1_members` | 80 | >= 80 | PASS |
| development | `native.L2_members` | 79 | >= 79 | PASS |
| development | `native.duplicate_count` | 0 | <= 0 | PASS |
| development | `native.closure_error_p95` | 1.9564249e-12 | <= 1e-09 | PASS |
| development | `native.closure_error_max` | 4.2479548e-12 | <= 1e-08 | PASS |
| development | `native.symmetry_residual_p95` | 3.4037957e-14 | <= 1e-10 | PASS |
| development | `native.L1_jacobi_monotone_fraction` | 1 | >= 0.98 | PASS |
| development | `native.L2_jacobi_monotone_fraction` | 1 | >= 0.98 | PASS |
| development | `native.monodromy_determinant_error_max` | 1.1174748e-09 | <= 0.0001 | PASS |
| development | `native.reciprocal_pair_error_max` | 2.3651257e-09 | <= 0.0001 | PASS |
| development | `external.minimum_cases` | 180 | >= 180 | PASS |
| development | `external.recovery_rate` | 1 | >= 0.98 | PASS |
| development | `external.state_error_p95` | 0.0039774218 | <= 0.006 | PASS |
| development | `external.state_error_max` | 0.0051614352 | <= 0.012 | PASS |
| development | `external.period_relative_error_p95` | 0.0034187476 | <= 0.005 | PASS |
| development | `external.period_relative_error_max` | 0.005270295 | <= 0.01 | PASS |
| development | `external.jacobi_error_p95` | 0.0015953975 | <= 0.003 | PASS |
| development | `external.jacobi_error_max` | 0.00232921 | <= 0.006 | PASS |
| development | `external.stability_relative_error_p95` | 0.016986735 | <= 0.1 | PASS |
| development | `external.stability_relative_error_max` | 0.027119 | <= 0.25 | PASS |
| development | `external.stability_label_accuracy` | 1 | >= 0.98 | PASS |
| calibration | `native.candidate_count` | 159 | >= 159 | PASS |
| calibration | `native.L1_members` | 80 | >= 80 | PASS |
| calibration | `native.L2_members` | 79 | >= 79 | PASS |
| calibration | `native.duplicate_count` | 0 | <= 0 | PASS |
| calibration | `native.closure_error_p95` | 1.9564249e-12 | <= 1e-09 | PASS |
| calibration | `native.closure_error_max` | 4.2479548e-12 | <= 1e-08 | PASS |
| calibration | `native.symmetry_residual_p95` | 3.4037957e-14 | <= 1e-10 | PASS |
| calibration | `native.L1_jacobi_monotone_fraction` | 1 | >= 0.98 | PASS |
| calibration | `native.L2_jacobi_monotone_fraction` | 1 | >= 0.98 | PASS |
| calibration | `native.monodromy_determinant_error_max` | 1.1174748e-09 | <= 0.0001 | PASS |
| calibration | `native.reciprocal_pair_error_max` | 2.3651257e-09 | <= 0.0001 | PASS |
| calibration | `external.minimum_cases` | 60 | >= 60 | PASS |
| calibration | `external.recovery_rate` | 1 | >= 0.98 | PASS |
| calibration | `external.state_error_p95` | 0.0041177184 | <= 0.006 | PASS |
| calibration | `external.state_error_max` | 0.0046917087 | <= 0.012 | PASS |
| calibration | `external.period_relative_error_p95` | 0.0040642404 | <= 0.005 | PASS |
| calibration | `external.period_relative_error_max` | 0.004956397 | <= 0.01 | PASS |
| calibration | `external.jacobi_error_p95` | 0.0018650865 | <= 0.003 | PASS |
| calibration | `external.jacobi_error_max` | 0.0023262625 | <= 0.006 | PASS |
| calibration | `external.stability_relative_error_p95` | 0.019618941 | <= 0.1 | PASS |
| calibration | `external.stability_relative_error_max` | 0.02500526 | <= 0.25 | PASS |
| calibration | `external.stability_label_accuracy` | 1 | >= 0.98 | PASS |
| holdout | `native.candidate_count` | 159 | >= 159 | PASS |
| holdout | `native.L1_members` | 80 | >= 80 | PASS |
| holdout | `native.L2_members` | 79 | >= 79 | PASS |
| holdout | `native.duplicate_count` | 0 | <= 0 | PASS |
| holdout | `native.closure_error_p95` | 1.9564249e-12 | <= 1e-09 | PASS |
| holdout | `native.closure_error_max` | 4.2479548e-12 | <= 1e-08 | PASS |
| holdout | `native.symmetry_residual_p95` | 3.4037957e-14 | <= 1e-10 | PASS |
| holdout | `native.L1_jacobi_monotone_fraction` | 1 | >= 0.98 | PASS |
| holdout | `native.L2_jacobi_monotone_fraction` | 1 | >= 0.98 | PASS |
| holdout | `native.monodromy_determinant_error_max` | 1.1174748e-09 | <= 0.0001 | PASS |
| holdout | `native.reciprocal_pair_error_max` | 2.3651257e-09 | <= 0.0001 | PASS |
| holdout | `external.minimum_cases` | 60 | >= 60 | PASS |
| holdout | `external.recovery_rate` | 1 | >= 0.98 | PASS |
| holdout | `external.state_error_p95` | 0.0030411374 | <= 0.006 | PASS |
| holdout | `external.state_error_max` | 0.0047410927 | <= 0.012 | PASS |
| holdout | `external.period_relative_error_p95` | 0.0029187421 | <= 0.005 | PASS |
| holdout | `external.period_relative_error_max` | 0.0039136932 | <= 0.01 | PASS |
| holdout | `external.jacobi_error_p95` | 0.0010641473 | <= 0.003 | PASS |
| holdout | `external.jacobi_error_max` | 0.0021801383 | <= 0.006 | PASS |
| holdout | `external.stability_relative_error_p95` | 0.011979839 | <= 0.1 | PASS |
| holdout | `external.stability_relative_error_max` | 0.022707213 | <= 0.25 | PASS |
| holdout | `external.stability_label_accuracy` | 1 | >= 0.98 | PASS |

## Interpretation

A PASS qualifies only the two declared, connected, planar family segments and their sampled external recovery. It is evidence for a usable bounded native catalogue component, not evidence of catalogue completeness or general periodic-orbit production.
