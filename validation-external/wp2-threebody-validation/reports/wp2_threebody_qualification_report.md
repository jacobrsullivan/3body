# WP2-3BRQ-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP2-3BRQ-v1-d4c0d5d7e2e3`

## Qualified Claim

If and only if the final qualification record is PASS and its lock verifies, WP2-3BRQ-v1 qualifies the declared downstream composition of two prerequisite PASS artifacts: (1) the exact linear canonical Jacobi transformation and 12-dimensional zero-total-momentum translation quotient for the qualified 18D Newtonian three-body state, (2) a reconstruction-complete nine-coordinate body-frame chart on the generic non-collinear SO(3) Poisson quotient, with generic nonzero-angular-momentum symplectic-leaf dimension eight, and (3) a constrained kinematic lift of all three oriented relative phase states through the qualified zero-Xi canonical KS cotangent lift, including S1^3 gauge invariance, triangle position/velocity closure, and exact full-state reconstruction within the frozen corpus bounds.

## Evidence Boundary

This qualification is a downstream algebraic and trajectory-conformance decision conditional on valid PASS records for WP1Q-N3BP-v1 and WP2KSQ-v1. It covers positive finite masses, collision-free source states, exact canonical momenta p_i=m_i*v_i, the generic non-collinear SO(3) chart, explicitly classified collinear singular strata, and the frozen N3BP source trajectories and random structural bounds. It does not qualify reduced Hamilton equations, a mechanical connection, a Darboux chart for the nine-dimensional Poisson quotient, collinear or collision charts, binary-collision passage, a simultaneous three-body Sundman transformation, three decoupled Kepler oscillators, a globally regularized N3BP Hamiltonian, orbit discovery, correction, stability, or a production periodic-orbit catalogue.

## Decisions

### Development

**PASS** across 3 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `jacobi_roundtrip_scaled_max` | 3.619611e-16 | <= 2.000000e-12 | PASS |
| `jacobi_symplectic_error_max` | 2.220446e-16 | <= 2.000000e-12 | PASS |
| `jacobi_one_form_scaled_max` | 2.220446e-15 | <= 2.000000e-12 | PASS |
| `energy_split_scaled_max` | 3.552714e-15 | <= 2.000000e-12 | PASS |
| `angular_momentum_split_scaled_max` | 9.104506e-16 | <= 2.000000e-12 | PASS |
| `euclidean_roundtrip_scaled_max` | 7.777517e-16 | <= 3.000000e-12 | PASS |
| `euclidean_rigid_invariance_scaled_max` | 1.799173e-15 | <= 3.000000e-12 | PASS |
| `euclidean_energy_scaled_max` | 4.440892e-15 | <= 2.000000e-12 | PASS |
| `pairwise_position_roundtrip_scaled_max` | 4.228718e-16 | <= 3.000000e-12 | PASS |
| `pairwise_velocity_roundtrip_scaled_max` | 5.050905e-16 | <= 3.000000e-12 | PASS |
| `pairwise_xi_abs_max` | 2.664535e-15 | <= 2.000000e-12 | PASS |
| `pairwise_position_closure_scaled_max` | 6.352462e-16 | <= 2.000000e-12 | PASS |
| `pairwise_velocity_closure_scaled_max` | 7.872816e-16 | <= 2.000000e-12 | PASS |
| `pairwise_s1_projection_scaled_max` | 4.089929e-16 | <= 3.000000e-12 | PASS |
| `pairwise_s1_reconstruction_scaled_max` | 8.102148e-16 | <= 3.000000e-12 | PASS |
| `singular_classification_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `generic_sample_count` | 7 | >= 1 | PASS |
| `structural_translation_dimension` | 12 | == 12 | PASS |
| `structural_rotation_poisson_dimension` | 9 | == 9 | PASS |
| `structural_generic_leaf_dimension` | 8 | == 8 | PASS |
| `structural_pairwise_dimension` | 12 | == 12 | PASS |
| `structural_global_sundman_qualified` | 0 | == 0 | PASS |

### Calibration

**PASS** across 3 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `jacobi_roundtrip_scaled_max` | 3.307189e-16 | <= 2.000000e-12 | PASS |
| `jacobi_symplectic_error_max` | 2.220446e-16 | <= 2.000000e-12 | PASS |
| `jacobi_one_form_scaled_max` | 1.776357e-15 | <= 2.000000e-12 | PASS |
| `energy_split_scaled_max` | 2.220446e-15 | <= 2.000000e-12 | PASS |
| `angular_momentum_split_scaled_max` | 1.133570e-15 | <= 2.000000e-12 | PASS |
| `euclidean_roundtrip_scaled_max` | 6.644073e-16 | <= 3.000000e-12 | PASS |
| `euclidean_rigid_invariance_scaled_max` | 8.408462e-16 | <= 3.000000e-12 | PASS |
| `euclidean_energy_scaled_max` | 2.664535e-15 | <= 2.000000e-12 | PASS |
| `pairwise_position_roundtrip_scaled_max` | 3.930909e-16 | <= 3.000000e-12 | PASS |
| `pairwise_velocity_roundtrip_scaled_max` | 5.571998e-16 | <= 3.000000e-12 | PASS |
| `pairwise_xi_abs_max` | 3.552714e-15 | <= 2.000000e-12 | PASS |
| `pairwise_position_closure_scaled_max` | 5.263870e-16 | <= 2.000000e-12 | PASS |
| `pairwise_velocity_closure_scaled_max` | 8.744147e-16 | <= 2.000000e-12 | PASS |
| `pairwise_s1_projection_scaled_max` | 3.940743e-16 | <= 3.000000e-12 | PASS |
| `pairwise_s1_reconstruction_scaled_max` | 6.415748e-16 | <= 3.000000e-12 | PASS |
| `singular_classification_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `generic_sample_count` | 7 | >= 1 | PASS |
| `structural_translation_dimension` | 12 | == 12 | PASS |
| `structural_rotation_poisson_dimension` | 9 | == 9 | PASS |
| `structural_generic_leaf_dimension` | 8 | == 8 | PASS |
| `structural_pairwise_dimension` | 12 | == 12 | PASS |
| `structural_global_sundman_qualified` | 0 | == 0 | PASS |

### Holdout

**PASS** across 5 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `jacobi_roundtrip_scaled_max` | 3.690063e-16 | <= 2.000000e-12 | PASS |
| `jacobi_symplectic_error_max` | 2.220446e-16 | <= 2.000000e-12 | PASS |
| `jacobi_one_form_scaled_max` | 1.549561e-15 | <= 2.000000e-12 | PASS |
| `energy_split_scaled_max` | 2.664535e-15 | <= 2.000000e-12 | PASS |
| `angular_momentum_split_scaled_max` | 1.014126e-15 | <= 2.000000e-12 | PASS |
| `euclidean_roundtrip_scaled_max` | 5.334463e-16 | <= 3.000000e-12 | PASS |
| `euclidean_rigid_invariance_scaled_max` | 1.254589e-15 | <= 3.000000e-12 | PASS |
| `euclidean_energy_scaled_max` | 2.664535e-15 | <= 2.000000e-12 | PASS |
| `pairwise_position_roundtrip_scaled_max` | 4.390951e-16 | <= 3.000000e-12 | PASS |
| `pairwise_velocity_roundtrip_scaled_max` | 5.943305e-16 | <= 3.000000e-12 | PASS |
| `pairwise_xi_abs_max` | 1.776357e-15 | <= 2.000000e-12 | PASS |
| `pairwise_position_closure_scaled_max` | 6.583990e-16 | <= 2.000000e-12 | PASS |
| `pairwise_velocity_closure_scaled_max` | 9.673729e-16 | <= 2.000000e-12 | PASS |
| `pairwise_s1_projection_scaled_max` | 4.371505e-16 | <= 3.000000e-12 | PASS |
| `pairwise_s1_reconstruction_scaled_max` | 5.774377e-16 | <= 3.000000e-12 | PASS |
| `singular_classification_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `generic_sample_count` | 11 | >= 1 | PASS |
| `structural_translation_dimension` | 12 | == 12 | PASS |
| `structural_rotation_poisson_dimension` | 9 | == 9 | PASS |
| `structural_generic_leaf_dimension` | 8 | == 8 | PASS |
| `structural_pairwise_dimension` | 12 | == 12 | PASS |
| `structural_global_sundman_qualified` | 0 | == 0 | PASS |

## Integrity

- Base commit: `2187a4abf3c5346ea0f1147df124dddde373a759`
- Code snapshot: `d4c0d5d7e2e3c7da2b4653da628bedc541f300dffc1a40ea3519f0b8bf2325ec`
- Lock: `7374fb2bd14fcfd9737bf03965703de4ca15e3c14293b91c20a1ce1f4f376049`
- Corpus: `b7be5a0e41c0fc0aef5d617d154aa5d1615d31df9bc8088482f28810f53b2d82`
- Holdout IDs: `a94dd77e2a67bdb6a02ff3103b0eed22cb0beca77cd35697990b60cf9edc97e9`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

This PASS, if achieved, authorizes the bounded reduction and kinematic pairwise-KS representation as qualified inputs to later WP2 research. It does not authorize a production periodic-orbit catalogue claim or any unimplemented three-body regularized dynamics. Any such extension requires a new model specification, independent evidence, frozen gates, and its own qualification record.
