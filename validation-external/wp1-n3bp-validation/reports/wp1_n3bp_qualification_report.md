# WP1Q-N3BP-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP1Q-N3BP-v1-892335b25187`

## Qualified Claim

If and only if the final qualification record is PASS and its lock verifies, WP1Q-N3BP-v1 qualifies the declared float64 production path to propagate an 18-dimensional inertial Cartesian state for three positive Newtonian point masses, without softening, over the bounded collision-free intervals and mass/separation ranges in the frozen corpus. Qualification covers explicit state/parameter contracts, barycentric normalization, conservation diagnostics, three-dimensional Euclidean/Galilean/body-permutation covariance, analytic Lagrange relative equilibria, the published rounded figure-eight, pinned published unequal-mass full-state periodic-orbit seeds, and checkpoint agreement with the independently implemented external REBOUND IAS15 propagator.

## Evidence Boundary

This qualification establishes bounded full-state Newtonian propagation, not native periodic-orbit discovery or correction. The published external catalogue is planar; spatial numerical coverage is supplied only by rotated analytic Lagrange cases and 3D covariance tests. The claim excludes collisions, trajectories whose minimum pair separation is below the frozen bound, regularization, softened gravity, zero/negative masses, long-term stability classification, arbitrary-duration accuracy, catalogue completeness, CR3BP equivalence, KS reduction, pairwise KS, full symplectic three-body reduction, and WP3/WP4 claims.

## Decisions

### Development

**PASS** across 5 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `dop853_rebound_position_error_scaled_max` | 2.704795e-11 | <= 2.000000e-08 | PASS |
| `dop853_rebound_velocity_error_scaled_max` | 1.141684e-08 | <= 2.000000e-08 | PASS |
| `lagrange_analytic_position_error_scaled_max` | 1.838894e-14 | <= 2.000000e-09 | PASS |
| `lagrange_analytic_velocity_error_scaled_max` | 1.441994e-14 | <= 2.000000e-09 | PASS |
| `periodic_closure_position_scaled_max` | 2.050961e-08 | <= 2.000000e-07 | PASS |
| `periodic_closure_velocity_scaled_max` | 3.274115e-08 | <= 2.000000e-07 | PASS |
| `relative_energy_drift_max` | 4.224677e-12 | <= 2.000000e-10 | PASS |
| `linear_momentum_drift_scaled_max` | 1.966974e-15 | <= 2.000000e-11 | PASS |
| `angular_momentum_drift_scaled_max` | 1.895213e-13 | <= 2.000000e-10 | PASS |
| `center_of_mass_position_drift_scaled_max` | 6.039571e-15 | <= 2.000000e-11 | PASS |
| `center_of_mass_velocity_drift_scaled_max` | 1.966974e-15 | <= 2.000000e-11 | PASS |
| `minimum_pair_separation_scaled_min` | 1.292315e-02 | >= 1.000000e-02 | PASS |
| `structural_translation_boost_error_max` | 2.220446e-15 | <= 2.000000e-12 | PASS |
| `structural_rotation_error_max` | 2.736073e-15 | <= 2.000000e-12 | PASS |
| `structural_permutation_error_max` | 0.000000e+00 | <= 2.000000e-12 | PASS |
| `structural_internal_force_balance_error_max` | 5.321697e-16 | <= 2.000000e-12 | PASS |
| `structural_barycenter_residual_max` | 3.521527e-16 | <= 2.000000e-12 | PASS |
| `sjtu_closure_position_scaled_max` | 5.819915e-12 | <= 2.000000e-08 | PASS |
| `sjtu_closure_velocity_scaled_max` | 1.304498e-10 | <= 2.000000e-08 | PASS |

### Calibration

**PASS** across 3 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `dop853_rebound_position_error_scaled_max` | 1.882061e-11 | <= 2.000000e-08 | PASS |
| `dop853_rebound_velocity_error_scaled_max` | 3.831405e-10 | <= 2.000000e-08 | PASS |
| `lagrange_analytic_position_error_scaled_max` | 6.525517e-15 | <= 2.000000e-09 | PASS |
| `lagrange_analytic_velocity_error_scaled_max` | 5.759216e-15 | <= 2.000000e-09 | PASS |
| `periodic_closure_position_scaled_max` | 1.000684e-11 | <= 2.000000e-07 | PASS |
| `periodic_closure_velocity_scaled_max` | 5.606064e-11 | <= 2.000000e-07 | PASS |
| `relative_energy_drift_max` | 2.965521e-12 | <= 2.000000e-10 | PASS |
| `linear_momentum_drift_scaled_max` | 2.130456e-15 | <= 2.000000e-11 | PASS |
| `angular_momentum_drift_scaled_max` | 5.673907e-14 | <= 2.000000e-10 | PASS |
| `center_of_mass_position_drift_scaled_max` | 7.172335e-15 | <= 2.000000e-11 | PASS |
| `center_of_mass_velocity_drift_scaled_max` | 2.130456e-15 | <= 2.000000e-11 | PASS |
| `minimum_pair_separation_scaled_min` | 8.400652e-02 | >= 1.000000e-02 | PASS |
| `structural_translation_boost_error_max` | 7.812485e-15 | <= 2.000000e-12 | PASS |
| `structural_rotation_error_max` | 4.687491e-15 | <= 2.000000e-12 | PASS |
| `structural_permutation_error_max` | 0.000000e+00 | <= 2.000000e-12 | PASS |
| `structural_internal_force_balance_error_max` | 7.892679e-16 | <= 2.000000e-12 | PASS |
| `structural_barycenter_residual_max` | 4.600371e-16 | <= 2.000000e-12 | PASS |
| `sjtu_closure_position_scaled_max` | 1.000684e-11 | <= 2.000000e-08 | PASS |
| `sjtu_closure_velocity_scaled_max` | 5.606064e-11 | <= 2.000000e-08 | PASS |

### Holdout

**PASS** across 5 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `dop853_rebound_position_error_scaled_max` | 2.333874e-11 | <= 2.000000e-08 | PASS |
| `dop853_rebound_velocity_error_scaled_max` | 6.317431e-10 | <= 2.000000e-08 | PASS |
| `lagrange_analytic_position_error_scaled_max` | 8.737383e-15 | <= 2.000000e-09 | PASS |
| `lagrange_analytic_velocity_error_scaled_max` | 6.859867e-15 | <= 2.000000e-09 | PASS |
| `periodic_closure_position_scaled_max` | 1.055875e-11 | <= 2.000000e-07 | PASS |
| `periodic_closure_velocity_scaled_max` | 8.003358e-11 | <= 2.000000e-07 | PASS |
| `relative_energy_drift_max` | 3.921826e-12 | <= 2.000000e-10 | PASS |
| `linear_momentum_drift_scaled_max` | 2.084088e-15 | <= 2.000000e-11 | PASS |
| `angular_momentum_drift_scaled_max` | 1.516307e-13 | <= 2.000000e-10 | PASS |
| `center_of_mass_position_drift_scaled_max` | 6.665559e-15 | <= 2.000000e-11 | PASS |
| `center_of_mass_velocity_drift_scaled_max` | 2.084088e-15 | <= 2.000000e-11 | PASS |
| `minimum_pair_separation_scaled_min` | 6.572045e-02 | >= 1.000000e-02 | PASS |
| `structural_translation_boost_error_max` | 8.460806e-15 | <= 2.000000e-12 | PASS |
| `structural_rotation_error_max` | 4.471853e-15 | <= 2.000000e-12 | PASS |
| `structural_permutation_error_max` | 0.000000e+00 | <= 2.000000e-12 | PASS |
| `structural_internal_force_balance_error_max` | 1.399833e-15 | <= 2.000000e-12 | PASS |
| `structural_barycenter_residual_max` | 5.922173e-16 | <= 2.000000e-12 | PASS |
| `sjtu_closure_position_scaled_max` | 1.055875e-11 | <= 2.000000e-08 | PASS |
| `sjtu_closure_velocity_scaled_max` | 8.003358e-11 | <= 2.000000e-08 | PASS |

## Integrity

- Base commit: `cb3ac8e5e6580065b077cb0aeb3bc2487e04f55c`
- Code snapshot: `892335b25187621c71e0433f2eb87088878e9dce66f2d6784951a669ec184718`
- Lock: `99b69816fa7096e059d6cb965c2b5eacea191f6af234cb9dc320f7a2dd9fd937`
- Corpus: `041129a2b3d3d2f8007652b4bd5e49d2e724a5b6bc02f477b2ae2ae5d085a51a`
- Holdout IDs: `ffa1879075ae5f7a0e5e5a1453b51f6eb4935e8f90395afae04a55e43d94f72e`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

This PASS is necessary but insufficient for full three-body reduction or pairwise KS. Those paths may be rebuilt only when this record and WP2KSQ-v1 are both PASS with valid locks, and the rebuilt path must then satisfy its own downstream qualification.
