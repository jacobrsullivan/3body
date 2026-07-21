# WP1-CAT-N3BP-v1 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP1-CAT-N3BP-v1-605c6dbd59d1`

## Qualified Claim

If and only if the final qualification record is PASS and both the specification lock and full qualification lock verify, WP1-CAT-N3BP-v1 qualifies the declared native correction-and-continuation path to generate a 169-member catalogue of one connected planar bABabaBAba Newtonian three-body family on the frozen two-dimensional mass grid. Every member is stored in the qualified full 18-dimensional barycentric inertial state contract, closes over one corrected period, carries bounded invariant and reduced-planar Floquet diagnostics, and is evaluated one-to-one at the same masses against the pinned Li-Li-Liao/SJTU catalogue without using those evaluation rows as continuation seeds.

## Evidence Boundary

Generation starts from one explicitly disclosed rounded equal-mass root published by Li, Li, and Liao; v1 therefore qualifies native correction, two-parameter continuation, full-state catalogue production, and external family-surface conformance, not independent discovery of the root. The external table is public and the holdout is execution-reserved rather than blind. The claim excludes other topologies or disconnected families, spatial orbit generation, relative-periodic orbits, collision passage, folds or bifurcations, pseudo-arclength continuation, nonlinear or spatial stability, completeness, arbitrary masses or scale, and a general production catalogue for the full three-body problem.

## Decisions

### Development

**PASS** across 84 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `rebound_case_count` | 4 | == 4 | PASS |
| `candidate_count` | 169 | == 169 | PASS |
| `candidate_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `external_seed_count` | 1 | == 1 | PASS |
| `evaluation_row_used_as_seed_count` | 0 | == 0 | PASS |
| `closure_position_scaled_max` | 3.822160e-11 | <= 2.000000e-08 | PASS |
| `closure_velocity_scaled_max` | 1.469823e-10 | <= 2.000000e-08 | PASS |
| `relative_energy_drift_max` | 4.095625e-11 | <= 2.000000e-09 | PASS |
| `linear_momentum_drift_scaled_max` | 3.034649e-15 | <= 2.000000e-11 | PASS |
| `angular_momentum_drift_scaled_max` | 2.580583e-12 | <= 2.000000e-09 | PASS |
| `minimum_pair_separation_scaled_min` | 1.118913e-01 | >= 1.000000e-02 | PASS |
| `exact_mass_match_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `external_parameter_error_p95` | 2.973034e-11 | <= 2.000000e-06 | PASS |
| `external_parameter_error_max` | 3.081044e-11 | <= 1.000000e-05 | PASS |
| `external_period_relative_error_p95` | 1.557269e-11 | <= 2.000000e-07 | PASS |
| `external_period_relative_error_max` | 2.198912e-11 | <= 1.000000e-06 | PASS |
| `planar_stability_classified_rate` | 1.000000e+00 | >= 9.500000e-01 | PASS |
| `planar_stability_label_agreement` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `monodromy_symplectic_defect_max` | 1.012530e-06 | <= 2.000000e-05 | PASS |
| `monodromy_reciprocal_pair_error_max` | 8.090058e-09 | <= 2.000000e-04 | PASS |
| `dop853_rebound_position_error_scaled_max` | 3.601708e-10 | <= 3.000000e-08 | PASS |
| `dop853_rebound_velocity_error_scaled_max` | 5.481512e-09 | <= 3.000000e-08 | PASS |
| `partition_disjoint_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `one_to_one_match_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `duplicate_count` | 0 | <= 0 | PASS |
| `structural_blind_holdout` | 0 | == 0 | PASS |
| `structural_independent_root_discovery` | 0 | == 0 | PASS |
| `structural_general_n3bp_catalogue` | 0 | == 0 | PASS |

### Calibration

**PASS** across 42 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `rebound_case_count` | 4 | == 4 | PASS |
| `candidate_count` | 169 | == 169 | PASS |
| `candidate_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `external_seed_count` | 1 | == 1 | PASS |
| `evaluation_row_used_as_seed_count` | 0 | == 0 | PASS |
| `closure_position_scaled_max` | 3.122304e-11 | <= 2.000000e-08 | PASS |
| `closure_velocity_scaled_max` | 1.427991e-10 | <= 2.000000e-08 | PASS |
| `relative_energy_drift_max` | 3.830450e-11 | <= 2.000000e-09 | PASS |
| `linear_momentum_drift_scaled_max` | 2.961781e-15 | <= 2.000000e-11 | PASS |
| `angular_momentum_drift_scaled_max` | 1.961343e-12 | <= 2.000000e-09 | PASS |
| `minimum_pair_separation_scaled_min` | 1.113346e-01 | >= 1.000000e-02 | PASS |
| `exact_mass_match_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `external_parameter_error_p95` | 2.961695e-11 | <= 2.000000e-06 | PASS |
| `external_parameter_error_max` | 3.206384e-11 | <= 1.000000e-05 | PASS |
| `external_period_relative_error_p95` | 1.672939e-11 | <= 2.000000e-07 | PASS |
| `external_period_relative_error_max` | 2.236865e-11 | <= 1.000000e-06 | PASS |
| `planar_stability_classified_rate` | 1.000000e+00 | >= 9.500000e-01 | PASS |
| `planar_stability_label_agreement` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `monodromy_symplectic_defect_max` | 1.012530e-06 | <= 2.000000e-05 | PASS |
| `monodromy_reciprocal_pair_error_max` | 8.090058e-09 | <= 2.000000e-04 | PASS |
| `dop853_rebound_position_error_scaled_max` | 2.768891e-10 | <= 3.000000e-08 | PASS |
| `dop853_rebound_velocity_error_scaled_max` | 4.165553e-09 | <= 3.000000e-08 | PASS |
| `partition_disjoint_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `one_to_one_match_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `duplicate_count` | 0 | <= 0 | PASS |
| `structural_blind_holdout` | 0 | == 0 | PASS |
| `structural_independent_root_discovery` | 0 | == 0 | PASS |
| `structural_general_n3bp_catalogue` | 0 | == 0 | PASS |

### Holdout

**PASS** across 42 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `rebound_case_count` | 4 | == 4 | PASS |
| `candidate_count` | 169 | == 169 | PASS |
| `candidate_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `external_seed_count` | 1 | == 1 | PASS |
| `evaluation_row_used_as_seed_count` | 0 | == 0 | PASS |
| `closure_position_scaled_max` | 3.111116e-11 | <= 2.000000e-08 | PASS |
| `closure_velocity_scaled_max` | 1.427991e-10 | <= 2.000000e-08 | PASS |
| `relative_energy_drift_max` | 4.214181e-11 | <= 2.000000e-09 | PASS |
| `linear_momentum_drift_scaled_max` | 2.916006e-15 | <= 2.000000e-11 | PASS |
| `angular_momentum_drift_scaled_max` | 2.198218e-12 | <= 2.000000e-09 | PASS |
| `minimum_pair_separation_scaled_min` | 1.122098e-01 | >= 1.000000e-02 | PASS |
| `exact_mass_match_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `external_parameter_error_p95` | 2.792542e-11 | <= 2.000000e-06 | PASS |
| `external_parameter_error_max` | 3.759151e-11 | <= 1.000000e-05 | PASS |
| `external_period_relative_error_p95` | 1.889308e-11 | <= 2.000000e-07 | PASS |
| `external_period_relative_error_max` | 2.009075e-11 | <= 1.000000e-06 | PASS |
| `planar_stability_classified_rate` | 1.000000e+00 | >= 9.500000e-01 | PASS |
| `planar_stability_label_agreement` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `monodromy_symplectic_defect_max` | 1.012530e-06 | <= 2.000000e-05 | PASS |
| `monodromy_reciprocal_pair_error_max` | 8.090058e-09 | <= 2.000000e-04 | PASS |
| `dop853_rebound_position_error_scaled_max` | 3.300840e-10 | <= 3.000000e-08 | PASS |
| `dop853_rebound_velocity_error_scaled_max` | 4.890270e-09 | <= 3.000000e-08 | PASS |
| `partition_disjoint_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `one_to_one_match_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `duplicate_count` | 0 | <= 0 | PASS |
| `structural_blind_holdout` | 0 | == 0 | PASS |
| `structural_independent_root_discovery` | 0 | == 0 | PASS |
| `structural_general_n3bp_catalogue` | 0 | == 0 | PASS |

## Integrity

- Base commit: `3418eebbf4f14a48a9cae9d4cddd586f5f87f92a`
- Evidence commit: `0418166f8bef699850c72b0c8acdec0c8cebb54e`
- Code snapshot: `605c6dbd59d1b30b7fb174b0b4d59451bb6027bb49452e7c5b3de925102d5429`
- Lock: `fde5e484ada224c64083b5695750bf1ec780a99b5ccd61e7324fc89b0ee0f191`
- Corpus: `e97a0a51f363e2fe2aee1f3db90e2751a4d0bc79483333cecbc908447c2c9374`
- Holdout IDs: `5c51f0f0cabf776e48cc478397911cf69a3cd0dcd2a239667c14d773cee776b0`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS supplies a bounded full-state periodic trajectory family for future WP2/WP3 experiments. It does not widen WP2's model qualification and must not be cited as evidence for catalogue completeness or root discovery.
