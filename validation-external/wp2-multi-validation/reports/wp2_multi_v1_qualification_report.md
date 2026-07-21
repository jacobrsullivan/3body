# WP2-MULTIQ-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP2-MULTIQ-v1-72c81d86644a`

## Qualified Claim

If and only if the final qualification record is PASS and both the specification lock and full qualification lock verify, WP2-MULTIQ-v1 qualifies the declared fixed-energy extended-canonical three-chart, two-spinor KS atlas for the translation-reduced spatial Newtonian three-body problem. The qualified atlas has one T^2 gauge action per chart, one chart-independent Sundman law dt/ds=r12*r23*r31, canonical quotient transitions on collision-free chart overlaps, and smooth fictitious-time continuation through each isolated binary-collision divisor while the third body remains separated.

## Evidence Boundary

The claim covers positive finite masses, zero Xi levels, three central-body charts, collision-free projection to the qualified Newtonian flow, bounded near-collision trajectories, and local passage through every isolated binary channel. It excludes triple collision, any state with two simultaneous pair collisions, nonzero-Xi magnetic reduction, SO(3) reduction, a single unconstrained 24-dimensional three-pair phase space, arbitrary-duration accuracy, completeness outside the frozen corpus, additional first integrals, Liouville or B-integrability, and every WP3/WP4 claim.

## Decisions

### Development

**PASS** across 21 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_identity_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_case_count` | 64 | == 64 | PASS |
| `dimension_and_constraint_count_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `independent_hamiltonian_scaled_max` | 8.881784e-16 | <= 5.000000e-12 | PASS |
| `independent_vector_field_scaled_max` | 5.883925e-16 | <= 5.000000e-10 | PASS |
| `shell_abs_max` | 8.881784e-16 | <= 5.000000e-11 | PASS |
| `xi_abs_max` | 1.942890e-16 | <= 5.000000e-11 | PASS |
| `xi_lie_abs_max` | 3.330669e-16 | <= 5.000000e-09 | PASS |
| `gauge_hamiltonian_scaled_max` | 6.409803e-16 | <= 5.000000e-11 | PASS |
| `gauge_vector_covariance_scaled_max` | 1.110223e-15 | <= 5.000000e-09 | PASS |
| `chart_roundtrip_scaled_max` | 3.330669e-16 | <= 2.000000e-10 | PASS |
| `chart_hamiltonian_scaled_max` | 2.239656e-12 | <= 2.000000e-10 | PASS |
| `chart_time_rate_scaled_max` | 7.897329e-16 | <= 2.000000e-12 | PASS |
| `chart_cocycle_scaled_max` | 1.152428e-11 | <= 2.000000e-09 | PASS |
| `projected_sundman_field_scaled_max` | 9.153406e-16 | <= 2.000000e-08 | PASS |
| `generic_trajectory_scaled_max` | 1.221245e-15 | <= 1.000000e-07 | PASS |
| `near_binary_trajectory_scaled_max` | 2.514555e-14 | <= 5.000000e-06 | PASS |
| `collision_limit_scaled_max` | 5.173075e-05 | <= 3.000000e-04 | PASS |
| `collision_passage_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `collision_passage_hamiltonian_drift_scaled_max` | 5.406793e-17 | <= 2.000000e-08 | PASS |
| `collision_passage_xi_drift_abs_max` | 8.131516e-20 | <= 2.000000e-08 | PASS |
| `collision_passage_reference_scaled_max` | 3.723705e-19 | <= 2.000000e-07 | PASS |
| `triple_collision_rejection_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_unseen_scientific_holdout` | 0 | == 0 | PASS |
| `structural_triple_collision_qualified` | 0 | == 0 | PASS |

### Calibration

**PASS** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_identity_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_case_count` | 64 | == 64 | PASS |
| `dimension_and_constraint_count_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `independent_hamiltonian_scaled_max` | 6.419290e-16 | <= 5.000000e-12 | PASS |
| `independent_vector_field_scaled_max` | 5.217862e-16 | <= 5.000000e-10 | PASS |
| `shell_abs_max` | 4.177378e-16 | <= 5.000000e-11 | PASS |
| `xi_abs_max` | 6.245005e-17 | <= 5.000000e-11 | PASS |
| `xi_lie_abs_max` | 3.074933e-16 | <= 5.000000e-09 | PASS |
| `gauge_hamiltonian_scaled_max` | 3.209509e-16 | <= 5.000000e-11 | PASS |
| `gauge_vector_covariance_scaled_max` | 2.008974e-15 | <= 5.000000e-09 | PASS |
| `chart_roundtrip_scaled_max` | 2.775558e-16 | <= 2.000000e-10 | PASS |
| `chart_hamiltonian_scaled_max` | 5.477156e-12 | <= 2.000000e-10 | PASS |
| `chart_time_rate_scaled_max` | 7.806256e-16 | <= 2.000000e-12 | PASS |
| `chart_cocycle_scaled_max` | 4.162441e-12 | <= 2.000000e-09 | PASS |
| `projected_sundman_field_scaled_max` | 7.477084e-16 | <= 2.000000e-08 | PASS |
| `generic_trajectory_scaled_max` | 6.419213e-16 | <= 1.000000e-07 | PASS |
| `near_binary_trajectory_scaled_max` | 1.616991e-14 | <= 5.000000e-06 | PASS |
| `collision_limit_scaled_max` | 5.001414e-05 | <= 3.000000e-04 | PASS |
| `collision_passage_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `collision_passage_hamiltonian_drift_scaled_max` | 5.616364e-17 | <= 2.000000e-08 | PASS |
| `collision_passage_xi_drift_abs_max` | 1.626303e-19 | <= 2.000000e-08 | PASS |
| `collision_passage_reference_scaled_max` | 3.628956e-19 | <= 2.000000e-07 | PASS |
| `triple_collision_rejection_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_unseen_scientific_holdout` | 0 | == 0 | PASS |
| `structural_triple_collision_qualified` | 0 | == 0 | PASS |

### Holdout

**PASS** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_identity_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_case_count` | 64 | == 64 | PASS |
| `dimension_and_constraint_count_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `independent_hamiltonian_scaled_max` | 1.387779e-16 | <= 5.000000e-12 | PASS |
| `independent_vector_field_scaled_max` | 7.330669e-16 | <= 5.000000e-10 | PASS |
| `shell_abs_max` | 2.628856e-16 | <= 5.000000e-11 | PASS |
| `xi_abs_max` | 2.220446e-16 | <= 5.000000e-11 | PASS |
| `xi_lie_abs_max` | 2.972916e-16 | <= 5.000000e-09 | PASS |
| `gauge_hamiltonian_scaled_max` | 3.330669e-16 | <= 5.000000e-11 | PASS |
| `gauge_vector_covariance_scaled_max` | 5.992791e-16 | <= 5.000000e-09 | PASS |
| `chart_roundtrip_scaled_max` | 3.053113e-16 | <= 2.000000e-10 | PASS |
| `chart_hamiltonian_scaled_max` | 2.059160e-12 | <= 2.000000e-10 | PASS |
| `chart_time_rate_scaled_max` | 7.806256e-16 | <= 2.000000e-12 | PASS |
| `chart_cocycle_scaled_max` | 1.288355e-11 | <= 2.000000e-09 | PASS |
| `projected_sundman_field_scaled_max` | 8.363265e-16 | <= 2.000000e-08 | PASS |
| `generic_trajectory_scaled_max` | 8.475899e-16 | <= 1.000000e-07 | PASS |
| `near_binary_trajectory_scaled_max` | 3.695457e-14 | <= 5.000000e-06 | PASS |
| `collision_limit_scaled_max` | 6.772612e-05 | <= 3.000000e-04 | PASS |
| `collision_passage_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `collision_passage_hamiltonian_drift_scaled_max` | 3.806613e-17 | <= 2.000000e-08 | PASS |
| `collision_passage_xi_drift_abs_max` | 1.897354e-19 | <= 2.000000e-08 | PASS |
| `collision_passage_reference_scaled_max` | 8.069907e-19 | <= 2.000000e-07 | PASS |
| `triple_collision_rejection_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_unseen_scientific_holdout` | 0 | == 0 | PASS |
| `structural_triple_collision_qualified` | 0 | == 0 | PASS |

## Integrity

- Base commit: `40fe3fecaad56c9f96135698e573ae819c5489aa`
- Evidence commit: `4d41cf119e42146ffd3e733985722cd4a907ab13`
- Code snapshot: `72c81d86644ab5a3c2855ab39ce8fc348ea50200afcc0e6ab6a697ad425f0dc8`
- Lock: `4a7dccfff2f457d67aa587680f1f6a8b262a8b70ebf595c9019bdbe00d6b94dd`
- Corpus: `e81e993dc10695e6782ccb2a8d8605353c1dd92b25014eb27b082a1e2ba6afb9`
- Holdout IDs: `e8bb99a37862cd3668737241483743c76555cd5d7fe3112b99dac0a8c9addcfb`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS authorizes a separately locked WP3 search on this exact multi-chart model. It does not transfer the WP3-UP-v3 null result, authorize a candidate, open a publication reserve, or establish integrability.
