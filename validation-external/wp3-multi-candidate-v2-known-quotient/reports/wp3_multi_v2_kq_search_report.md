# WP3-MULTI-CAND-v2 Observable Known-Quotient Report

**Status:** COMPLETE_BOUNDED_NULL_RESULT

**Publication gate:** PASS_BOUNDED_NULL_ONLY

**Qualification ID:** `WP3-MULTI-CAND-v2-KQ-v1-514be9de7232`

## Domain Certificates

| Domain | Value rank | Smallest values | Relative spread | Guarded lower bound | Null certified |
|---|---:|---|---:|---:|:---:|
| calibration | [75] | gesdd=8.172400e-03, gesvd=8.172400e-03, numpy=8.172400e-03 | 2.039877e-13 | 8.172396e-03 | PASS |
| challenge | [75] | gesdd=1.862450e-01, gesvd=1.862450e-01, numpy=1.862450e-01 | 6.795640e-14 | 1.862450e-01 | PASS |
| development | [75] | gesdd=5.063730e-02, gesvd=5.063730e-02, numpy=5.063730e-02 | 1.055141e-13 | 5.063722e-02 | PASS |

## Readiness Gates

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `prerequisites_verified` | 1 | == 1 | PASS |
| `specification_lock_verified` | 1 | == 1 | PASS |
| `implementation_lock_verified` | 1 | == 1 | PASS |
| `publication_reserve_intact` | 1 | == 1 | PASS |
| `source_matrix_byte_identity` | 1 | == 1 | PASS |
| `development_group_count` | 156 | == 156 | PASS |
| `calibration_group_count` | 78 | == 78 | PASS |
| `development_physical_point_count` | 288 | == 288 | PASS |
| `calibration_physical_point_count` | 144 | == 144 | PASS |
| `challenge_case_count` | 192 | == 192 | PASS |
| `declared_feature_count` | 285 | == 285 | PASS |
| `structural_zero_feature_count` | 36 | == 36 | PASS |
| `active_feature_count` | 249 | == 249 | PASS |
| `challenge_feature_physical_l2_relative_difference_max` | 1.0547118733938987e-14 | <= 1e-12 | PASS |
| `minimum_pair_separation_scaled_min` | 0.010884338448493491 | >= 0.001 | PASS |
| `minimum_denominator_abs` | 0.0012644779505763687 | >= 0.001 | PASS |
| `energy_control_relative_lie_max` | 4.726491797480005e-14 | <= 1e-10 | PASS |
| `body_permutation_spread_max` | 0.0 | <= 1e-12 | PASS |
| `rotation_spread_max` | 0.0 | <= 1e-12 | PASS |
| `gauge_orbit_spread_max` | 0.0 | <= 1e-10 | PASS |
| `chart_overlap_spread_max` | 0.0 | <= 1e-10 | PASS |
| `wp2_pushforward_tangent_relative_error_max` | 3.182754013940238e-11 | <= 1e-10 | PASS |
| `wp2_time_rate_relative_error_max` | 8.604228440844963e-14 | <= 1e-10 | PASS |
| `decision_runtime_exact` | 1 | == 1 | PASS |
| `spectral_candidate_partition_consistent` | 1 | == 1 | PASS |
| `development_backend_value_rank_consistent` | 1 | == 1 | PASS |
| `development_known_observable_rank` | 1 | == 1 | PASS |
| `development_known_response_projection_residual_max` | 5.704828214671233e-14 | <= 1e-10 | PASS |
| `development_mode_known_response_projection_max` | 3.261280134836401e-16 | <= 1e-10 | PASS |
| `development_known_lie_rms_per_coefficient_scale` | 1.1574150862424421e-13 | <= 1e-10 | PASS |
| `development_backend_smallest_generalized_relative_spread` | 1.0551409380573413e-13 | <= 1e-06 | PASS |
| `calibration_backend_value_rank_consistent` | 1 | == 1 | PASS |
| `calibration_known_observable_rank` | 1 | == 1 | PASS |
| `calibration_known_response_projection_residual_max` | 4.318061743228591e-14 | <= 1e-10 | PASS |
| `calibration_mode_known_response_projection_max` | 2.6367796834847463e-16 | <= 1e-10 | PASS |
| `calibration_known_lie_rms_per_coefficient_scale` | 1.1413433335220155e-14 | <= 1e-10 | PASS |
| `calibration_backend_smallest_generalized_relative_spread` | 2.0398772695486598e-13 | <= 1e-06 | PASS |
| `challenge_backend_value_rank_consistent` | 1 | == 1 | PASS |
| `challenge_known_observable_rank` | 1 | == 1 | PASS |
| `challenge_known_response_projection_residual_max` | 1.6049442087644652e-13 | <= 1e-10 | PASS |
| `challenge_mode_known_response_projection_max` | 3.3306690738754716e-16 | <= 1e-10 | PASS |
| `challenge_known_lie_rms_per_coefficient_scale` | 9.650582784301678e-15 | <= 1e-10 | PASS |
| `challenge_backend_smallest_generalized_relative_spread` | 6.795639734457193e-14 | <= 1e-06 | PASS |

## Claim Boundary

A COMPLETE_BOUNDED_NULL_RESULT states only that every frozen backend-guarded lower bound on the smallest generalized Lie/value singular value exceeds 1e-10 after quotienting the known L^2 observable in the declared 285-function Reynolds library, on the frozen development, calibration, and 192-state challenge domains. The library and exclusions are identical to WP3-MULTI-CAND-v2: combined-degree-two-or-less Gram/parameter numerators, the three declared denominators, physical polynomial degree at most four, scalar SO(3) representations, nonzero-separation states, and the qualified zero-Xi physical model. It is not a general no-integral or non-integrability theorem and does not cover higher degree, other denominators, non-meromorphic functions, non-scalar representations, nonzero Xi, or collision strata. Any candidate result remains uninterpretable until a separately locked candidate-resolution campaign passes.

## Integrity

- Evidence commit: `579711581aa138d989196c2a034ac1942b48bbae`
- Search lock: `c06fda96cd54574aa3a19b1a519268960450ea0b967c134516fed3ea67fcd9a7`
- Results SHA-256: `240b9daef5afa087aae911691966fb1428e1d0edaa920f10abdac027806ecbcc`
- Publication gate SHA-256: `925372c32c390bd17725cb8ea30481a435ee5bf1df23254178c4428e4ce26be2`
- Record payload SHA-256: `33a0d12d65e5b4a1ac14e9b891ede025fad1f6b6ae003add087c8d9e2ff370e5`
- Publication reserve: **SEALED_UNEXECUTED**
