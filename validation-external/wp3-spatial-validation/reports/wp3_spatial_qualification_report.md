# WP1Q-N3BP-SPATIAL-v1 Qualification Report

**Decision:** FAIL

**Qualification ID:** `WP1Q-N3BP-SPATIAL-v1-8216e5f53247`

## Qualified Claim

If and only if the final qualification record is PASS and its lock verifies, WP1Q-N3BP-SPATIAL-v1 qualifies bounded collision-free propagation of genuinely spatial chaotic Newtonian three-body states drawn from the published Brutus virialized Plummer corpus. Qualification includes independently converged arbitrary-precision Taylor checkpoints over each full published trajectory, agreement with published Brutus terminal states within bounds calibrated for the source's decimal initial-state conditioning, float64 production agreement through the first frozen checkpoint, invariant non-planarity, and finite-time variational growth within the frozen corpus bounds.

## Evidence Boundary

This campaign covers the selected equal-mass and 4:2:1-mass Brutus cases in standard Henon units with G=1, source durations from 5 through 20, the declared minimum-separation bound, and the frozen checkpoint grid. The float64 production claim ends at the first nonzero checkpoint, source duration divided by eight (0.625 through 2.5 time units); full-horizon float64 errors remain reported diagnostics because pathwise error is exponentially conditioned on these chaotic trajectories. It does not qualify arbitrary-duration float64 chaotic prediction, collision passage, catalogue completeness, statistical escape distributions, periodicity, regularization, a new first integral, or any WP3 candidate claim. A positive finite-time variational exponent is a bounded chaos diagnostic, not a theorem about asymptotic Lyapunov exponents.

## Decisions

### Development

**PASS** across 48 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `source_precision_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `spatial_rank_ratio_min` | 5.341823e-02 | >= 5.000000e-02 | PASS |
| `positive_ftle_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `median_ftle` | 8.403736e-01 | >= 2.000000e-02 | PASS |
| `oracle_convergence_position_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_convergence_velocity_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_brutus_position_scaled_max` | 5.717698e-08 | <= 1.000000e-06 | PASS |
| `oracle_brutus_velocity_scaled_max` | 5.865698e-07 | <= 1.000000e-05 | PASS |
| `production_oracle_short_position_scaled_max` | 7.108093e-10 | <= 1.000000e-08 | PASS |
| `production_oracle_short_velocity_scaled_max` | 1.105718e-07 | <= 5.000000e-07 | PASS |
| `oracle_relative_energy_drift_max` | 1.783992e-30 | <= 1.000000e-22 | PASS |
| `production_validation_horizon_max` | 2.500000e+00 | <= 2.500000e+00 | PASS |
| `minimum_pair_separation_scaled_min` | 1.632107e-03 | >= 1.000000e-04 | PASS |
| `source_payload_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |

### Calibration

**PASS** across 24 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `source_precision_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `spatial_rank_ratio_min` | 5.145305e-02 | >= 5.000000e-02 | PASS |
| `positive_ftle_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `median_ftle` | 9.803752e-01 | >= 2.000000e-02 | PASS |
| `oracle_convergence_position_scaled_max` | 5.942014e-16 | <= 2.000000e-10 | PASS |
| `oracle_convergence_velocity_scaled_max` | 7.347145e-16 | <= 2.000000e-10 | PASS |
| `oracle_brutus_position_scaled_max` | 3.601653e-07 | <= 1.000000e-06 | PASS |
| `oracle_brutus_velocity_scaled_max` | 3.777281e-06 | <= 1.000000e-05 | PASS |
| `production_oracle_short_position_scaled_max` | 1.652271e-09 | <= 1.000000e-08 | PASS |
| `production_oracle_short_velocity_scaled_max` | 8.564477e-09 | <= 5.000000e-07 | PASS |
| `oracle_relative_energy_drift_max` | 2.968600e-30 | <= 1.000000e-22 | PASS |
| `production_validation_horizon_max` | 2.500000e+00 | <= 2.500000e+00 | PASS |
| `minimum_pair_separation_scaled_min` | 5.577240e-03 | >= 1.000000e-04 | PASS |
| `source_payload_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |

### Holdout

**FAIL** across 12 cases.

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `case_success_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `source_precision_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |
| `spatial_rank_ratio_min` | 5.786956e-02 | >= 5.000000e-02 | PASS |
| `positive_ftle_rate` | 1.000000e+00 | >= 9.000000e-01 | PASS |
| `median_ftle` | 8.489720e-01 | >= 2.000000e-02 | PASS |
| `oracle_convergence_position_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_convergence_velocity_scaled_max` | 0.000000e+00 | <= 2.000000e-10 | PASS |
| `oracle_brutus_position_scaled_max` | 2.247555e-11 | <= 1.000000e-06 | PASS |
| `oracle_brutus_velocity_scaled_max` | 2.262726e-10 | <= 1.000000e-05 | PASS |
| `production_oracle_short_position_scaled_max` | 1.442216e-08 | <= 1.000000e-08 | FAIL |
| `production_oracle_short_velocity_scaled_max` | 1.552436e-06 | <= 5.000000e-07 | FAIL |
| `oracle_relative_energy_drift_max` | 2.859343e-30 | <= 1.000000e-22 | PASS |
| `production_validation_horizon_max` | 2.250000e+00 | <= 2.500000e+00 | PASS |
| `minimum_pair_separation_scaled_min` | 3.931478e-03 | >= 1.000000e-04 | PASS |
| `source_payload_hash_rate` | 1.000000e+00 | >= 1.000000e+00 | PASS |

## Integrity

- Base commit: `dd0631f9afecafc1d769aa3d4b7215bdc38f4283`
- Code snapshot: `8216e5f53247c810fe1c79797150a63b7eeac263c61cc74a3b248e91752bdd93`
- Lock: `47e7e4d9f2e07803e5e6e68507d4e3151bf1b65dbf48d0ec86302ca9a44c3819`
- Corpus: `e2e30abd56810db0b500b73d76eae05873617bceaf807b810983766b3152c321`
- Holdout IDs: `b23100d28705be35d7b05fd2f1da866b2327cbb91eca4e03d9bf861cc8c3f692`

The holdout runner verified every frozen input before selecting the reserved cases. The final status is fail-closed: any failed mandatory gate produces FAIL.

## Downstream Policy

A PASS supplies qualified external spatial/chaotic states and an arbitrary-precision N3BP oracle to staged WP3 search readiness. It does not authorize interpretation of a WP3 mode or replace the separate reduced/lifted-flow, sealed-publication-holdout, and candidate-specific gates.
