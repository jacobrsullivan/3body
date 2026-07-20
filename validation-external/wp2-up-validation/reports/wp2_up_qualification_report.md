# WP2-UPQ-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP2-UPQ-v1-64cdda5ede83`

## Qualified Claim

If and only if the final record is PASS and its lock verifies, WP2-UPQ-v1 qualifies the declared 14-dimensional canonical one-channel KS Hamiltonian for the collision-free translation-reduced Newtonian three-body problem, its S1 action and Xi momentum map, the fixed-energy Hamiltonian K_h, the Sundman relation dt/ds=|q|^2, projection from K_h=Xi=0 to the physical Jacobi flow, and finite continuation of the selected binary-channel vector field at q=0 when the other pair separations remain nonzero.

## Evidence Boundary

The claim covers positive finite masses, the rho=x2-x1 KS channel, zero Xi for physical projection, the frozen external spatial/chaotic checkpoint corpus, and short bounded flow comparisons. It does not qualify either other binary channel, triple collision, simultaneous pairwise regularization, a global three-pair Sundman time, nonzero-Xi physical reduction, orbit discovery, an additional first integral, Liouville integrability, or any WP3/WP4 claim.

## Decisions

### Development

**PASS** across 48 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `reference_hamiltonian_scaled_max` | 0.000000e+00 | <= 2.000000e-12 | PASS |
| `reference_vector_field_scaled_max` | 0.000000e+00 | <= 2.000000e-11 | PASS |
| `shell_hamiltonian_scaled_max` | 2.406964e-13 | <= 2.000000e-12 | PASS |
| `xi_level_abs_max` | 4.440892e-16 | <= 2.000000e-12 | PASS |
| `roundtrip_scaled_max` | 5.778828e-16 | <= 2.000000e-12 | PASS |
| `sundman_projection_scaled_max` | 2.544279e-14 | <= 2.000000e-11 | PASS |
| `canonical_gradient_scaled_max` | 9.970558e-10 | <= 3.000000e-07 | PASS |
| `s1_hamiltonian_scaled_max` | 1.365574e-13 | <= 2.000000e-12 | PASS |
| `s1_projection_scaled_max` | 6.934594e-16 | <= 2.000000e-12 | PASS |
| `s1_vector_covariance_scaled_max` | 2.163229e-14 | <= 2.000000e-11 | PASS |
| `xi_lie_abs_max` | 1.136868e-13 | <= 2.000000e-11 | PASS |
| `angular_momentum_lie_scaled_max` | 5.851791e-15 | <= 2.000000e-11 | PASS |
| `short_flow_projection_scaled_max` | 8.753772e-16 | <= 3.000000e-08 | PASS |
| `short_flow_hamiltonian_drift_scaled_max` | 1.165734e-15 | <= 2.000000e-09 | PASS |
| `short_flow_xi_drift_abs_max` | 1.387779e-16 | <= 2.000000e-09 | PASS |
| `selected_collision_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_simultaneous_regularization_qualified` | 0 | == 0 | PASS |

### Calibration

**PASS** across 24 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `reference_hamiltonian_scaled_max` | 0.000000e+00 | <= 2.000000e-12 | PASS |
| `reference_vector_field_scaled_max` | 0.000000e+00 | <= 2.000000e-11 | PASS |
| `shell_hamiltonian_scaled_max` | 1.345590e-13 | <= 2.000000e-12 | PASS |
| `xi_level_abs_max` | 3.330669e-16 | <= 2.000000e-12 | PASS |
| `roundtrip_scaled_max` | 4.285326e-16 | <= 2.000000e-12 | PASS |
| `sundman_projection_scaled_max` | 6.201896e-14 | <= 2.000000e-11 | PASS |
| `canonical_gradient_scaled_max` | 1.141369e-09 | <= 3.000000e-07 | PASS |
| `s1_hamiltonian_scaled_max` | 3.517187e-13 | <= 2.000000e-12 | PASS |
| `s1_projection_scaled_max` | 4.992498e-16 | <= 2.000000e-12 | PASS |
| `s1_vector_covariance_scaled_max` | 8.149559e-14 | <= 2.000000e-11 | PASS |
| `xi_lie_abs_max` | 2.380318e-13 | <= 2.000000e-11 | PASS |
| `angular_momentum_lie_scaled_max` | 8.971654e-15 | <= 2.000000e-11 | PASS |
| `short_flow_projection_scaled_max` | 6.661338e-16 | <= 3.000000e-08 | PASS |
| `short_flow_hamiltonian_drift_scaled_max` | 2.262079e-15 | <= 2.000000e-09 | PASS |
| `short_flow_xi_drift_abs_max` | 1.179612e-16 | <= 2.000000e-09 | PASS |
| `selected_collision_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_simultaneous_regularization_qualified` | 0 | == 0 | PASS |

### Holdout

**PASS** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `reference_hamiltonian_scaled_max` | 0.000000e+00 | <= 2.000000e-12 | PASS |
| `reference_vector_field_scaled_max` | 0.000000e+00 | <= 2.000000e-11 | PASS |
| `shell_hamiltonian_scaled_max` | 5.928591e-14 | <= 2.000000e-12 | PASS |
| `xi_level_abs_max` | 1.110223e-16 | <= 2.000000e-12 | PASS |
| `roundtrip_scaled_max` | 3.781234e-16 | <= 2.000000e-12 | PASS |
| `sundman_projection_scaled_max` | 1.860588e-14 | <= 2.000000e-11 | PASS |
| `canonical_gradient_scaled_max` | 6.481353e-10 | <= 3.000000e-07 | PASS |
| `s1_hamiltonian_scaled_max` | 6.505907e-14 | <= 2.000000e-12 | PASS |
| `s1_projection_scaled_max` | 5.070659e-16 | <= 2.000000e-12 | PASS |
| `s1_vector_covariance_scaled_max` | 2.253158e-14 | <= 2.000000e-11 | PASS |
| `xi_lie_abs_max` | 1.421085e-14 | <= 2.000000e-11 | PASS |
| `angular_momentum_lie_scaled_max` | 1.087018e-14 | <= 2.000000e-11 | PASS |
| `short_flow_projection_scaled_max` | 1.161393e-15 | <= 3.000000e-08 | PASS |
| `short_flow_hamiltonian_drift_scaled_max` | 4.440892e-16 | <= 2.000000e-09 | PASS |
| `short_flow_xi_drift_abs_max` | 1.665335e-16 | <= 2.000000e-09 | PASS |
| `selected_collision_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `structural_simultaneous_regularization_qualified` | 0 | == 0 | PASS |

## Integrity

- Base commit: `12fc716ba83a0c2af20e50d2c31742bd37bc24b2`
- Code snapshot: `64cdda5ede8378f4d69517c8680555790cd0ebd9eba4a1e0706716aa9244002b`
- Lock: `12a11e64a590e620c3527d4d46ceadad79ad149bc7ffeef32f084e94a853de37`
- Corpus: `3396ddb75a5c67bd2383fe9984fbdaa6974018c4265e1a64cdcee3faca9070bc`
- Holdout IDs: `1e6db3161712fc066202bf917e4ee436714db769ba79f34489de4e5e94ad5b43`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS authorizes this model as the frozen canonical target for a separately locked WP3 upstairs candidate search. It does not authorize candidate interpretation, opening a sealed WP3 reserve, or a WP4 integrability claim.
