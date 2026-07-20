# WP2-3BFLOWQ-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP2-3BFLOWQ-v1-90fab6dac1ca`

## Qualified Claim

If and only if the final qualification record is PASS and its lock verifies, WP2-3BFLOWQ-v1 qualifies an independently replicated canonical Jacobi reduction, the exact 12-dimensional physical-time Jacobi Hamiltonian vector field, its generic non-collinear nine-coordinate SO(3)-quotient derivative with body-frame reconstruction dynamics, and a constrained physical-time pairwise KS lift whose projection, Xi levels, S1-cubed covariance, and triangle position/velocity closure derivatives conform to the qualified Newtonian three-body flow.

## Evidence Boundary

This qualification covers positive finite masses, collision-free states, the generic non-collinear body-frame chart, zero-Xi pairwise KS sections, and the frozen external spatial/chaotic checkpoint corpus. The pairwise KS flow is a redundant constrained physical-time lift, not three independent Kepler systems. The claim excludes a global Sundman transformation, collision passage, a globally regularized three-body Hamiltonian, a Darboux assertion for the SO(3) quotient, nonzero-Xi magnetic reduction, orbit discovery, and every WP3 invariant claim.

## Decisions

### Development

**PASS** across 16 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_canonical_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `independent_jacobi_state_scaled_max` | 0.000000e+00 | <= 3.000000e-12 | PASS |
| `independent_jacobi_roundtrip_scaled_max` | 2.316017e-16 | <= 3.000000e-12 | PASS |
| `independent_body_frame_scaled_max` | 0.000000e+00 | <= 3.000000e-12 | PASS |
| `canonical_tangent_scaled_max` | 5.024835e-15 | <= 3.000000e-12 | PASS |
| `hamiltonian_lie_scaled_max` | 1.421085e-14 | <= 1.000000e-10 | PASS |
| `reduced_quotient_fd_scaled_max` | 3.424382e-08 | <= 3.000000e-07 | PASS |
| `reconstruction_frame_fd_scaled_max` | 2.072744e-08 | <= 3.000000e-07 | PASS |
| `pairwise_projection_fd_scaled_max` | 1.941743e-08 | <= 5.000000e-07 | PASS |
| `pairwise_xi_derivative_abs_max` | 2.269296e-13 | <= 2.000000e-11 | PASS |
| `pairwise_position_closure_derivative_max` | 8.881784e-16 | <= 2.000000e-12 | PASS |
| `pairwise_velocity_closure_derivative_max` | 1.136868e-13 | <= 2.000000e-12 | PASS |
| `pairwise_s1_covariance_scaled_max` | 1.785478e-14 | <= 3.000000e-12 | PASS |
| `structural_global_sundman_qualified` | 0 | == 0 | PASS |

### Calibration

**PASS** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_canonical_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `independent_jacobi_state_scaled_max` | 0.000000e+00 | <= 3.000000e-12 | PASS |
| `independent_jacobi_roundtrip_scaled_max` | 2.371508e-16 | <= 3.000000e-12 | PASS |
| `independent_body_frame_scaled_max` | 0.000000e+00 | <= 3.000000e-12 | PASS |
| `canonical_tangent_scaled_max` | 1.195393e-14 | <= 3.000000e-12 | PASS |
| `hamiltonian_lie_scaled_max` | 1.136868e-13 | <= 1.000000e-10 | PASS |
| `reduced_quotient_fd_scaled_max` | 2.926734e-08 | <= 3.000000e-07 | PASS |
| `reconstruction_frame_fd_scaled_max` | 1.176610e-08 | <= 3.000000e-07 | PASS |
| `pairwise_projection_fd_scaled_max` | 1.372219e-08 | <= 5.000000e-07 | PASS |
| `pairwise_xi_derivative_abs_max` | 2.819966e-14 | <= 2.000000e-11 | PASS |
| `pairwise_position_closure_derivative_max` | 4.440892e-16 | <= 2.000000e-12 | PASS |
| `pairwise_velocity_closure_derivative_max` | 1.136868e-13 | <= 2.000000e-12 | PASS |
| `pairwise_s1_covariance_scaled_max` | 5.908434e-13 | <= 3.000000e-12 | PASS |
| `structural_global_sundman_qualified` | 0 | == 0 | PASS |

### Holdout

**PASS** across 6 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_canonical_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `independent_jacobi_state_scaled_max` | 0.000000e+00 | <= 3.000000e-12 | PASS |
| `independent_jacobi_roundtrip_scaled_max` | 2.220446e-16 | <= 3.000000e-12 | PASS |
| `independent_body_frame_scaled_max` | 0.000000e+00 | <= 3.000000e-12 | PASS |
| `canonical_tangent_scaled_max` | 1.687333e-15 | <= 3.000000e-12 | PASS |
| `hamiltonian_lie_scaled_max` | 8.881784e-16 | <= 1.000000e-10 | PASS |
| `reduced_quotient_fd_scaled_max` | 8.327083e-09 | <= 3.000000e-07 | PASS |
| `reconstruction_frame_fd_scaled_max` | 4.611782e-09 | <= 3.000000e-07 | PASS |
| `pairwise_projection_fd_scaled_max` | 1.994674e-08 | <= 5.000000e-07 | PASS |
| `pairwise_xi_derivative_abs_max` | 1.748601e-15 | <= 2.000000e-11 | PASS |
| `pairwise_position_closure_derivative_max` | 2.486410e-16 | <= 2.000000e-12 | PASS |
| `pairwise_velocity_closure_derivative_max` | 3.552714e-15 | <= 2.000000e-12 | PASS |
| `pairwise_s1_covariance_scaled_max` | 3.436595e-15 | <= 3.000000e-12 | PASS |
| `structural_global_sundman_qualified` | 0 | == 0 | PASS |

## Integrity

- Base commit: `89937dd03eba779580bcdd78476d90843d4822a5`
- Code snapshot: `90fab6dac1caa9bb9f99e57cec33c72637d2eb6fd1c24c08faa76d5cd0a9e89f`
- Lock: `e7c5cdb2f23daa6796340bbccb3412be6ec9c1dea241cfeff7144649b2f05c81`
- Corpus: `b84c537bbf5e53be38c1b17fc8669fc3b28b2bd673652e28b7ac62d8d305283c`
- Holdout IDs: `38b3b9a422c3b819194706d180dc8f241f7bf26b60075323e449b0c28cda7fa5`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS closes the independent-reduction and qualified-reduced-or-lifted-vector-field infrastructure items for staged WP3 search readiness. It does not authorize a conserved-quantity, hidden-integrability, regularized-collision, or publication claim.
