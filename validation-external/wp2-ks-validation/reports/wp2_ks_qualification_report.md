# WP2KSQ-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP2KSQ-v1-dc4b342e3bd2`

## Qualified Claim

If and only if the final qualification record is PASS and its lock verifies, WP2KSQ-v1 qualifies the declared canonical Kustaanheimo-Stiefel construction for isolated negative-energy Kepler motion: the Hopf position map, canonical cotangent lift, common-phase S1 action, Xi momentum map, zero-level quotient, fixed-energy Sundman rule dt/ds=|u|^2, regular four-dimensional isotropic oscillator, physical-time reconstruction, and smooth radial-collision passage in regular variables. Within the frozen corpus bounds, projected collision-free trajectories reproduce independently encoded analytic Kepler conics and the external REBOUND IAS15 implementation at the declared checkpoints.

## Evidence Boundary

This qualification is limited to an isolated two-body Hamiltonian with reduced_mass>0, kappa>0, fixed E<0, Xi=0, elliptic eccentricity 0<=e<=0.97, the parameter ranges in the frozen corpus, and the explicitly tested radial-collision continuation. It does not qualify E>=0, nonzero-Xi magnetic reduction, perturbed Kepler motion, a pair embedded in a three-body field, pairwise or simultaneous three-body KS, full three-body reduction, orbit discovery, additional first integrals, or any WP3/WP4 claim.

## Decisions

### Development

**PASS** across 2 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `analytic_state_error_max` | 3.108624e-15 | <= 5.000000e-10 | PASS |
| `rebound_state_error_max` | 6.661338e-15 | <= 2.000000e-08 | PASS |
| `closure_position_error_max` | 1.948434e-15 | <= 2.000000e-10 | PASS |
| `closure_velocity_error_max` | 2.449294e-16 | <= 2.000000e-09 | PASS |
| `regularized_hamiltonian_abs_max` | 1.110223e-16 | <= 5.000000e-12 | PASS |
| `momentum_map_abs_max` | 1.110223e-16 | <= 5.000000e-12 | PASS |
| `physical_energy_abs_error_max` | 3.330669e-16 | <= 2.000000e-09 | PASS |
| `period_relative_error_max` | 1.568344e-16 | <= 5.000000e-13 | PASS |
| `structural_radius_error_max` | 1.776357e-15 | <= 2.000000e-12 | PASS |
| `structural_s1_invariance_error_max` | 1.776357e-15 | <= 2.000000e-12 | PASS |
| `structural_cotangent_roundtrip_error_max` | 1.519618e-15 | <= 2.000000e-11 | PASS |
| `structural_poisson_error_max` | 1.776357e-15 | <= 2.000000e-11 | PASS |

### Calibration

**PASS** across 2 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `analytic_state_error_max` | 1.243450e-14 | <= 5.000000e-10 | PASS |
| `rebound_state_error_max` | 2.931666e-11 | <= 2.000000e-08 | PASS |
| `closure_position_error_max` | 4.041273e-16 | <= 2.000000e-10 | PASS |
| `closure_velocity_error_max` | 3.953392e-15 | <= 2.000000e-09 | PASS |
| `regularized_hamiltonian_abs_max` | 2.220446e-16 | <= 5.000000e-12 | PASS |
| `momentum_map_abs_max` | 4.440892e-16 | <= 5.000000e-12 | PASS |
| `physical_energy_abs_error_max` | 3.552714e-15 | <= 2.000000e-09 | PASS |
| `period_relative_error_max` | 2.827160e-16 | <= 5.000000e-13 | PASS |
| `structural_radius_error_max` | 1.776357e-15 | <= 2.000000e-12 | PASS |
| `structural_s1_invariance_error_max` | 1.790235e-15 | <= 2.000000e-12 | PASS |
| `structural_cotangent_roundtrip_error_max` | 1.554312e-15 | <= 2.000000e-11 | PASS |
| `structural_poisson_error_max` | 1.776357e-15 | <= 2.000000e-11 | PASS |

### Holdout

**PASS** across 5 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `analytic_state_error_max` | 8.881784e-15 | <= 5.000000e-10 | PASS |
| `rebound_state_error_max` | 7.840173e-12 | <= 2.000000e-08 | PASS |
| `closure_position_error_max` | 1.269571e-15 | <= 2.000000e-10 | PASS |
| `closure_velocity_error_max` | 2.264420e-15 | <= 2.000000e-09 | PASS |
| `regularized_hamiltonian_abs_max` | 6.217249e-15 | <= 5.000000e-12 | PASS |
| `momentum_map_abs_max` | 8.881784e-16 | <= 5.000000e-12 | PASS |
| `physical_energy_abs_error_max` | 2.886580e-15 | <= 2.000000e-09 | PASS |
| `period_relative_error_max` | 5.505775e-16 | <= 5.000000e-13 | PASS |
| `structural_radius_error_max` | 1.776357e-15 | <= 2.000000e-12 | PASS |
| `structural_s1_invariance_error_max` | 2.220446e-15 | <= 2.000000e-12 | PASS |
| `structural_cotangent_roundtrip_error_max` | 1.332268e-15 | <= 2.000000e-11 | PASS |
| `structural_poisson_error_max` | 2.700408e-15 | <= 2.000000e-11 | PASS |
| `radial_collision_q_norm_max` | 1.006150e-16 | <= 2.000000e-14 | PASS |
| `radial_symmetry_error_max` | 4.018601e-22 | <= 2.000000e-11 | PASS |
| `radial_regularized_hamiltonian_abs_max` | 2.220446e-16 | <= 5.000000e-12 | PASS |

## Integrity

- Base commit: `cb3ac8e5e6580065b077cb0aeb3bc2487e04f55c`
- Code snapshot: `dc4b342e3bd2f9fa3c234c6ee056aa4e2926d7d12bb6ea2a5604c99e9a268d93`
- Lock: `6224c0167ec264695e5c1a9cceb635f710444b6da8b35841967c86f0ca7586bd`
- Corpus: `0afa4a9f754ac8b8018c3766be02b0791ddfc5ef4593f067fd88786518d5ad1e`
- Holdout IDs: `52fb28f4c2f8bcd1dd6d3efb903d166738bad0165deddf7496758e02c1aa68f6`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

This PASS is necessary but insufficient for full three-body reduction or pairwise KS. Those paths may be rebuilt only when this record and WP1Q-N3BP-v1 are both PASS with valid locks, and the rebuilt path must then satisfy its own downstream qualification.
