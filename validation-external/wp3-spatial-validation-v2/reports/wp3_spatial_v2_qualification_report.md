# WP1Q-N3BP-SPATIAL-v2 Qualification Report

**Decision:** PASS

**Qualification ID:** `WP1Q-N3BP-SPATIAL-v2-294429ca5655`

## Qualified Claim

If and only if the final qualification record is PASS and its lock verifies, WP1Q-N3BP-SPATIAL-v2 qualifies bounded collision-free propagation of genuinely spatial chaotic Newtonian three-body states drawn from fresh published Brutus virialized Plummer cases. Qualification includes independently converged arbitrary-precision Taylor checkpoints over each full published trajectory, agreement with published Brutus terminal states within bounds calibrated for source decimal conditioning, and float64 production agreement over a fixed 0.5-unit horizon.

## Evidence Boundary

This campaign covers fresh selected equal-mass and 4:2:1-mass Brutus cases in standard Henon units with G=1, source durations from 5 through 20, the declared checkpoint minimum-separation bound, and a fixed 0.5-unit float64 production horizon. It excludes every v1 qualification row and every still-sealed WP3 publication-reserve row. It does not qualify arbitrary-duration float64 chaotic prediction, collision passage, catalogue completeness, statistical escape distributions, periodicity, regularization, a new first integral, or any WP3 candidate claim.

## Decisions

### Development

**PASS** across 48 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `source_precision_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `spatial_rank_ratio_min` | 5.383452e-02 | >= 5.000000e-02 | PASS |
| `positive_ftle_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `median_ftle` | 8.068938e-01 | >= 2.000000e-02 | PASS |
| `oracle_convergence_position_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_convergence_velocity_scaled_max` | 3.872504e-18 | <= 2.000000e-10 | PASS |
| `oracle_brutus_position_scaled_max` | 5.017341e-08 | <= 1.000000e-06 | PASS |
| `oracle_brutus_velocity_scaled_max` | 1.567708e-06 | <= 1.000000e-05 | PASS |
| `production_oracle_short_position_scaled_max` | 1.079702e-10 | <= 1.000000e-08 | PASS |
| `production_oracle_short_velocity_scaled_max` | 1.816574e-09 | <= 5.000000e-07 | PASS |
| `oracle_relative_energy_drift_max` | 1.478688e-30 | <= 1.000000e-22 | PASS |
| `production_validation_horizon_max` | 5.000000e-01 | <= 5.000000e-01 | PASS |
| `minimum_pair_separation_scaled_min` | 4.538177e-03 | >= 1.000000e-04 | PASS |
| `source_payload_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |

### Calibration

**PASS** across 24 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `source_precision_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `spatial_rank_ratio_min` | 6.193659e-02 | >= 5.000000e-02 | PASS |
| `positive_ftle_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `median_ftle` | 8.544892e-01 | >= 2.000000e-02 | PASS |
| `oracle_convergence_position_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_convergence_velocity_scaled_max` | 3.984356e-16 | <= 2.000000e-10 | PASS |
| `oracle_brutus_position_scaled_max` | 5.408130e-10 | <= 1.000000e-06 | PASS |
| `oracle_brutus_velocity_scaled_max` | 3.798935e-08 | <= 1.000000e-05 | PASS |
| `production_oracle_short_position_scaled_max` | 6.998654e-11 | <= 1.000000e-08 | PASS |
| `production_oracle_short_velocity_scaled_max` | 6.353335e-09 | <= 5.000000e-07 | PASS |
| `oracle_relative_energy_drift_max` | 1.595531e-30 | <= 1.000000e-22 | PASS |
| `production_validation_horizon_max` | 5.000000e-01 | <= 5.000000e-01 | PASS |
| `minimum_pair_separation_scaled_min` | 4.237361e-03 | >= 1.000000e-04 | PASS |
| `source_payload_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |

### Holdout

**PASS** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `source_precision_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `spatial_rank_ratio_min` | 5.537176e-02 | >= 5.000000e-02 | PASS |
| `positive_ftle_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `median_ftle` | 7.275461e-01 | >= 2.000000e-02 | PASS |
| `oracle_convergence_position_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_convergence_velocity_scaled_max` | 4.703689e-17 | <= 2.000000e-10 | PASS |
| `oracle_brutus_position_scaled_max` | 7.141235e-09 | <= 1.000000e-06 | PASS |
| `oracle_brutus_velocity_scaled_max` | 1.722607e-08 | <= 1.000000e-05 | PASS |
| `production_oracle_short_position_scaled_max` | 1.084447e-11 | <= 1.000000e-08 | PASS |
| `production_oracle_short_velocity_scaled_max` | 1.156524e-09 | <= 5.000000e-07 | PASS |
| `oracle_relative_energy_drift_max` | 5.223303e-31 | <= 1.000000e-22 | PASS |
| `production_validation_horizon_max` | 5.000000e-01 | <= 5.000000e-01 | PASS |
| `minimum_pair_separation_scaled_min` | 1.650081e-02 | >= 1.000000e-04 | PASS |
| `source_payload_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |

## Integrity

- Base commit: `9dc20f6714df1243e751372728a2d44b45074d25`
- Code snapshot: `294429ca565523e49072b69b2aaaccbb0a080a095935f0b0d83019ea6ea73670`
- Lock: `9b974df4a808e82e36f1c5fd4ab3fc4e8fc32f6668a969dda257ef347d45a0f0`
- Corpus: `ca73d1378c71f9d386dd00b10b63b0f845497ff583e3d0739ea6e0849a8bd3ff`
- Holdout IDs: `77eca19fb1fbd6cfc32a4c78cdaed923533d7aca3dc81cee5a6d1b238f539665`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS supplies fresh qualified external spatial/chaotic states and an arbitrary-precision N3BP oracle to WP2-3BFLOWQ-v1 and staged WP3 search readiness. It does not authorize interpretation of a WP3 mode or replace the separate reduced/lifted-flow, sealed-publication-holdout, and candidate-specific gates.
