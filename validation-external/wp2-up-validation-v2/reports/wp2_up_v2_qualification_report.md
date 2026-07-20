# WP2-UPQ-v2 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP2-UPQ-v2-3baea4a70768`

## Qualified Claim

If and only if the final record is PASS and its lock verifies, WP2-UPQ-v2 qualifies the declared 14-dimensional canonical one-channel KS Hamiltonian for the translation-reduced Newtonian three-body problem, including its canonical gradient, S1 action, Xi momentum map, fixed-energy K_h shell, Sundman projection, and smooth fictitious-time passage through the selected rho=x2-x1 binary collision while the other separations remain nonzero.

## Evidence Boundary

The claim covers positive finite masses, the selected rho channel, zero Xi physical projection, external Brutus checkpoint conformance, an independently autodifferentiated Hamiltonian reference, and bounded collision passage. The split called holdout reserves WP2-UP transformation execution only; the upstream spatial states were already public in the repository and this is not an unseen scientific holdout. The claim excludes the other binary channels, triple collision, simultaneous regularization, a global three-pair Sundman time, nonzero-Xi physical reduction, additional first integrals, Liouville integrability, and every WP3/WP4 claim.

## Decisions

### Development

**PASS** across 48 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `upstream_input_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `autodiff_hamiltonian_scaled_max` | 8.881784e-16 | <= 2.000000e-12 | PASS |
| `autodiff_vector_field_scaled_max` | 5.155276e-15 | <= 2.000000e-10 | PASS |
| `shell_hamiltonian_scaled_max` | 2.406964e-13 | <= 2.000000e-12 | PASS |
| `xi_level_abs_max` | 4.440892e-16 | <= 2.000000e-12 | PASS |
| `roundtrip_scaled_max` | 5.778828e-16 | <= 2.000000e-12 | PASS |
| `sundman_projection_scaled_max` | 2.544279e-14 | <= 2.000000e-11 | PASS |
| `canonical_gradient_scaled_max` | 9.970558e-10 | <= 3.000000e-07 | PASS |
| `s1_hamiltonian_scaled_max` | 1.365574e-13 | <= 2.000000e-12 | PASS |
| `s1_projection_scaled_max` | 6.934594e-16 | <= 2.000000e-12 | PASS |
| `s1_vector_covariance_scaled_max` | 2.163229e-14 | <= 2.000000e-11 | PASS |
| `xi_lie_abs_max` | 1.136868e-13 | <= 2.000000e-11 | PASS |
| `projected_angular_momentum_lie_scaled_max` | 1.216733e-14 | <= 2.000000e-11 | PASS |
| `short_flow_projection_scaled_max` | 1.332268e-15 | <= 3.000000e-08 | PASS |
| `collision_shell_abs_max` | 2.775558e-17 | <= 2.000000e-12 | PASS |
| `collision_limit_scaled_max` | 1.613253e-06 | <= 2.000000e-04 | PASS |
| `collision_passage_hamiltonian_drift_scaled_max` | 9.111428e-17 | <= 2.000000e-09 | PASS |
| `collision_passage_xi_drift_abs_max` | 5.089946e-49 | <= 2.000000e-09 | PASS |
| `collision_limit_monotone_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `collision_passage_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_ks_kinetic_identity_pass` | 1 | == 1 | PASS |
| `structural_simultaneous_regularization_qualified` | 0 | == 0 | PASS |
| `structural_unseen_scientific_holdout` | 0 | == 0 | PASS |

### Calibration

**PASS** across 24 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `upstream_input_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `autodiff_hamiltonian_scaled_max` | 2.692291e-15 | <= 2.000000e-12 | PASS |
| `autodiff_vector_field_scaled_max` | 1.244242e-14 | <= 2.000000e-10 | PASS |
| `shell_hamiltonian_scaled_max` | 1.345590e-13 | <= 2.000000e-12 | PASS |
| `xi_level_abs_max` | 3.330669e-16 | <= 2.000000e-12 | PASS |
| `roundtrip_scaled_max` | 4.285326e-16 | <= 2.000000e-12 | PASS |
| `sundman_projection_scaled_max` | 6.201896e-14 | <= 2.000000e-11 | PASS |
| `canonical_gradient_scaled_max` | 1.141369e-09 | <= 3.000000e-07 | PASS |
| `s1_hamiltonian_scaled_max` | 3.517187e-13 | <= 2.000000e-12 | PASS |
| `s1_projection_scaled_max` | 4.992498e-16 | <= 2.000000e-12 | PASS |
| `s1_vector_covariance_scaled_max` | 8.149559e-14 | <= 2.000000e-11 | PASS |
| `xi_lie_abs_max` | 2.380318e-13 | <= 2.000000e-11 | PASS |
| `projected_angular_momentum_lie_scaled_max` | 1.007884e-14 | <= 2.000000e-11 | PASS |
| `short_flow_projection_scaled_max` | 1.137234e-15 | <= 3.000000e-08 | PASS |
| `collision_shell_abs_max` | 2.775558e-17 | <= 2.000000e-12 | PASS |
| `collision_limit_scaled_max` | 7.818896e-07 | <= 2.000000e-04 | PASS |
| `collision_passage_hamiltonian_drift_scaled_max` | 7.691123e-17 | <= 2.000000e-09 | PASS |
| `collision_passage_xi_drift_abs_max` | 6.554668e-51 | <= 2.000000e-09 | PASS |
| `collision_limit_monotone_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `collision_passage_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_ks_kinetic_identity_pass` | 1 | == 1 | PASS |
| `structural_simultaneous_regularization_qualified` | 0 | == 0 | PASS |
| `structural_unseen_scientific_holdout` | 0 | == 0 | PASS |

### Holdout

**PASS** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `prerequisite_pass_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `upstream_input_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `autodiff_hamiltonian_scaled_max` | 2.220446e-16 | <= 2.000000e-12 | PASS |
| `autodiff_vector_field_scaled_max` | 3.910468e-15 | <= 2.000000e-10 | PASS |
| `shell_hamiltonian_scaled_max` | 5.928591e-14 | <= 2.000000e-12 | PASS |
| `xi_level_abs_max` | 1.110223e-16 | <= 2.000000e-12 | PASS |
| `roundtrip_scaled_max` | 3.781234e-16 | <= 2.000000e-12 | PASS |
| `sundman_projection_scaled_max` | 1.860588e-14 | <= 2.000000e-11 | PASS |
| `canonical_gradient_scaled_max` | 6.481353e-10 | <= 3.000000e-07 | PASS |
| `s1_hamiltonian_scaled_max` | 6.505907e-14 | <= 2.000000e-12 | PASS |
| `s1_projection_scaled_max` | 5.070659e-16 | <= 2.000000e-12 | PASS |
| `s1_vector_covariance_scaled_max` | 2.253158e-14 | <= 2.000000e-11 | PASS |
| `xi_lie_abs_max` | 1.421085e-14 | <= 2.000000e-11 | PASS |
| `projected_angular_momentum_lie_scaled_max` | 1.087018e-14 | <= 2.000000e-11 | PASS |
| `short_flow_projection_scaled_max` | 7.771561e-16 | <= 3.000000e-08 | PASS |
| `collision_shell_abs_max` | 2.775558e-17 | <= 2.000000e-12 | PASS |
| `collision_limit_scaled_max` | 5.941946e-07 | <= 2.000000e-04 | PASS |
| `collision_passage_hamiltonian_drift_scaled_max` | 7.003425e-17 | <= 2.000000e-09 | PASS |
| `collision_passage_xi_drift_abs_max` | 9.187629e-52 | <= 2.000000e-09 | PASS |
| `collision_limit_monotone_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `collision_passage_finite_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `symbolic_ks_kinetic_identity_pass` | 1 | == 1 | PASS |
| `structural_simultaneous_regularization_qualified` | 0 | == 0 | PASS |
| `structural_unseen_scientific_holdout` | 0 | == 0 | PASS |

## Integrity

- Base commit: `d44d087fd5fb340176150cdbdcd9e73deac4eaeb`
- Code snapshot: `3baea4a7076834d68de35d28b942aecbdcdb8605967761c354dc5eb30a20c54e`
- Lock: `b75a581be8e01a10682f5e4fa552af02d625a73c1675db64578d701291f0fd54`
- Corpus: `f3de2e4ba870e1319c36862f2964760736e72189e12cd87499352132e1939e80`
- Holdout IDs: `01ff35ae5c0b7d5187cfbe20bc2b40138fe6e0e6660e78aa1b250946a7e8fb98`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS supersedes WP2-UPQ-v1 for a separately locked WP3 upstairs search. It does not authorize a candidate, opening the sealed publication reserve, or a WP4/integrability claim.
