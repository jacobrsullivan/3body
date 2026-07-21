# WP3-MULTI-CAND-v1 Search Report

**Status:** COMPLETE_BOUNDED_NULL_RESULT

**Qualification ID:** `WP3-MULTI-CAND-v1-225359a13711`

**Publication gate:** PASS_BOUNDED_NULL_ONLY

**Interpretation authorization:** BOUNDED_NULL_ONLY

## Bounded Decision

The frozen shared symmetric degree-three library contains no training-eligible direction under the combined physical-Lie, two-generator gauge, and chart-overlap operator.

- Features: 1520
- Observable quotient rank: 1468
- Exact known-module rank removed: 52
- Smallest generalized singular value: `8.989803510526e-02`
- Backend-guarded lower bound: `8.984794583676e-02`
- Candidate threshold: `1.000000000000e-10`

This is a finite-library bounded null, not a no-integral or non-integrability theorem.

## Readiness Gates

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `prerequisite_pass_rate` | 1.0 | >= 1.0 | PASS |
| `specification_lock_verified` | 1 | == 1 | PASS |
| `search_lock_verified` | 1 | == 1 | PASS |
| `sealed_reserve_intact` | 1 | == 1 | PASS |
| `spatial_inputs_hash_verified` | 1 | == 1 | PASS |
| `feature_count` | 1520 | == 1520 | PASS |
| `exact_known_module_rank` | 52 | == 52 | PASS |
| `parameter_weighted_angular_control_count` | 9 | == 9 | PASS |
| `known_module_combined_constraint_rms_max` | 6.329378503610411e-14 | <= 1e-10 | PASS |
| `constraint_value_abs_max` | 2.842170943040401e-14 | <= 1e-10 | PASS |
| `known_angular_chart_overlap_abs_max` | 4.9404924595819466e-15 | <= 1e-10 | PASS |
| `known_module_projection_residual` | 1.0287616155557348e-15 | <= 1e-10 | PASS |
| `all_generalized_modes_evaluated` | 1468 | == 1468 | PASS |
| `decision_runtime_exact` | 1 | == 1 | PASS |
| `fixed_energy_checkpoint_abs_max` | 8.26028134781609e-12 | <= 1e-10 | PASS |
| `chart_projection_state_scaled_max` | 7.993605777301127e-15 | <= 1e-10 | PASS |
| `chart_count` | 3 | == 3 | PASS |
| `gauge_pair_count` | 3 | == 3 | PASS |
| `constraint_block_normalization_error` | 2.7755575615628914e-17 | <= 2e-15 | PASS |
| `minimum_pair_separation_scaled_min` | 0.010884338448493491 | >= 1e-06 | PASS |
| `spectral_decision_partition_consistent` | 1 | == 1 | PASS |

## Evidence Boundary

A no-candidate result states only that the backend-guarded lower bound on the smallest generalized combined-constraint/value singular value exceeds the frozen training threshold in the shared chart-local, body-permutation-symmetric, combined-degree-three-or-less polynomial library over the 16 non-time canonical two-spinor variables and the fixed-energy and symmetric-mass parameters. The combined constraint requires vanishing fictitious-time Lie derivative in all three WP2-MULTIQ-v1 charts, invariance under both independent gauge circles, and equal values on collision-free chart overlaps, after coefficient-exact removal of the complete represented degree-three Xi1/Xi2 ideal and angular-momentum parameter module. The result excludes chart-asymmetric expressions, higher-degree or nonpolynomial functions, parameter-only constants, nonzero-Xi magnetic dynamics, simultaneous or triple collision, unrepresented known-integral modules, and every general no-integral or non-integrability claim. Development and calibration sources have been examined in earlier campaigns, so this is a locked model-rebaseline search rather than fresh blind confirmation. Candidate interpretation is prohibited until the staged publication gate passes and a candidate-specific resolution specification is frozen.

## Integrity

- Evidence commit: `eaa337148b0ffe6ac6a9895131801aa656dcaec3`
- Search lock: `d1a8226dc9bfdd836f24389c8f0c0d6d6eaf56e82f6592f0a2c57140cd294be8`
- Results SHA-256: `63b44017bc0fef52a1d41475f14d63aea384c80d39f4f942befe36683c709e13`
- Publication gate SHA-256: `3ebbe1b48a78d6013db3123e1f0abed9461f99348f7f2393d89165a35a7e5329`
- Publication reserve: **SEALED_UNEXECUTED**
