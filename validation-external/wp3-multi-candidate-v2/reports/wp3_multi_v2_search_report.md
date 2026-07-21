# WP3-MULTI-CAND-v2 Search Report

**Status:** CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION

**Qualification ID:** `WP3-MULTI-CAND-v2-ab9626e19010`

**Publication gate:** BLOCKED_PENDING_CANDIDATE_RESOLUTION

**Interpretation authorization:** PROHIBITED

## Bounded Decision

The spectral decision contains 1 unresolved candidate subspace(s).

No candidate expression is interpreted or reported. Candidate resolution must be separately specified and frozen before reserve execution.

## Readiness Gates

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `prerequisite_pass_rate` | 1.0 | >= 1.0 | PASS |
| `specification_lock_verified` | 1 | == 1 | PASS |
| `search_lock_verified` | 1 | == 1 | PASS |
| `sealed_reserve_intact` | 1 | == 1 | PASS |
| `qualified_spatial_inputs_verified` | 1 | == 1 | PASS |
| `development_group_count` | 156 | == 156 | PASS |
| `calibration_group_count` | 78 | == 78 | PASS |
| `development_physical_point_count` | 288 | == 288 | PASS |
| `calibration_physical_point_count` | 144 | == 144 | PASS |
| `declared_feature_count` | 285 | == 285 | PASS |
| `active_feature_count` | 249 | == 249 | PASS |
| `exact_structural_zero_count` | 36 | == 36 | PASS |
| `exact_known_module_rank` | 1 | == 1 | PASS |
| `known_module_lie_rms_max` | 1.1574150862424421e-13 | <= 1e-10 | PASS |
| `known_module_projection_residual` | 1.9500075320535145e-15 | <= 1e-10 | PASS |
| `angular_momentum_squared_relative_error_max` | 2.7644553313166398e-14 | <= 1e-10 | PASS |
| `energy_control_relative_lie_max` | 4.726491797480005e-14 | <= 1e-10 | PASS |
| `body_permutation_spread_max` | 0.0 | <= 1e-12 | PASS |
| `rotation_spread_max` | 0.0 | <= 1e-12 | PASS |
| `gauge_orbit_spread_max` | 0.0 | <= 1e-10 | PASS |
| `chart_overlap_spread_max` | 0.0 | <= 1e-10 | PASS |
| `fixed_energy_checkpoint_abs_max` | 8.26028134781609e-12 | <= 1e-10 | PASS |
| `chart_projection_state_scaled_max` | 2.6268878986856614e-15 | <= 1e-10 | PASS |
| `wp2_pushforward_tangent_relative_error_max` | 3.182754013940238e-11 | <= 1e-10 | PASS |
| `wp2_time_rate_relative_error_max` | 8.604228440844963e-14 | <= 1e-10 | PASS |
| `minimum_pair_separation_scaled_min` | 0.010884338448493491 | >= 1e-06 | PASS |
| `minimum_denominator_abs` | 0.0012644779505763687 | >= 1e-10 | PASS |
| `all_generalized_modes_evaluated` | 75 | == 75 | PASS |
| `decision_runtime_exact` | 1 | == 1 | PASS |
| `spectral_decision_partition_consistent` | 1 | == 1 | PASS |

## Evidence Boundary

A no-candidate result states only that the backend-guarded lower bound on the smallest generalized Lie/value singular value exceeds the frozen threshold in the 285-function Reynolds-averaged library. Numerators are combined-degree-two-or-less monomials in the ten Gram scalars of two relative position and two canonical momentum vectors, with fixed-energy and symmetric-mass parameters, divided by one, the global pair-distance product, or barycentric moment of inertia. This reaches physical polynomial degree four and permits the declared rational poles. It excludes non-scalar SO(3) representations, higher numerator degree, other denominators, non-meromorphic functions, chart-asymmetric functions, nonzero-Xi dynamics, simultaneous or triple collision, and every general no-integral or non-integrability claim. The development and calibration data were used by earlier campaigns. Candidate interpretation remains prohibited until the staged publication gate passes and candidate resolution is separately frozen.

## Integrity

- Evidence commit: `378525cadf806ffe9ab17cf663e5d0f9e50adfc3`
- Search lock: `f23005c9ba6c9bbd9948abb9354f95bf12757bd4020c9bfd7a7a0b331678f5ff`
- Results SHA-256: `c5c3da9f3c30f7758bc6e90a7c751505e21acafe7485e8cdfb363fd59103da61`
- Publication gate SHA-256: `3a4ac1ad72dfab88d15d5f3497dc9a3c119a53abd6ff0cf2e26039cb1baeaada`
- Publication reserve: **SEALED_UNEXECUTED**
