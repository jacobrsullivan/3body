# WP3 Exploratory Screening Report

**Campaign:** `WP3-EXP-v1`

**Interpretation status:** `EXPLORATORY_ONLY`

**Publication gate:** `BLOCKED` (3/11 gates)

This report ranks numerical near-null directions only. It makes no conservation, independence, involution, or integrability claim.

## Data Boundary

- Training points: 365
- Calibration points: 219
- Qualified trajectory sources use only upstream development/calibration cases.
- Deterministic spatial collocation probes the exact vector field but is not external trajectory evidence.
- Every upstream holdout case remains excluded from WP3 execution.

## Known Controls

| Control | Train Lie RMS | Calibration Lie RMS | Train max drift | Calibration max drift |
|---|---:|---:|---:|---:|
| `angular_momentum_squared` | 2.644e-14 | 6.922e-14 | 5.440e-16 | 2.879e-17 |
| `energy` | 1.551e-14 | 2.444e-14 | 1.545e-11 | 3.140e-12 |

## Screening Modes

Search each mass-length-time dimension sector independently. Coefficients from different physical dimensions are never combined.

Numerical nullity after projecting known controls across 9 sectors: `0` at relative tolerance `1.0e-10`.

The table reports only the leading direction in each dimension sector.

| Sector | Features | Standardized singular value | Train Lie RMS | Calibration Lie RMS | Cal/train RMS | Train max drift | Calibration max drift |
|---|---:|---:|---:|---:|---:|---:|---:|
| `M+0_L+2_T+0` | 3 | 9.284e-01 | 9.213e-01 | 1.539e+00 | 1.7x | 4.593e-01 | 6.659e-02 |
| `M+0_L+4_T+0` | 6 | 3.645e-01 | 7.047e-01 | 1.617e+00 | 2.3x | 5.372e-02 | 8.982e-03 |
| `M+1_L+2_T-2` | 5 | 1.154e-01 | 1.091e+00 | 1.884e+00 | 1.7x | 4.410e-01 | 1.549e-01 |
| `M+1_L+2_T-1` | 4 | 6.157e-01 | 1.655e+00 | 4.518e+00 | 2.7x | 9.071e-01 | 6.642e-01 |
| `M+1_L+4_T-1` | 12 | 2.462e-01 | 1.166e+00 | 5.256e+00 | 4.5x | 1.133e-01 | 2.035e-02 |
| `M+2_L+2_T-2` | 3 | 3.593e-01 | 1.696e+00 | 2.097e+00 | 1.2x | 4.941e-01 | 1.918e-01 |
| `M+2_L+4_T-2` | 19 | 1.926e-02 | 6.099e-02 | 3.583e-01 | 5.9x | 7.265e-03 | 2.296e-03 |
| `M+3_L+4_T-3` | 12 | 2.623e-02 | 1.944e-01 | 2.197e+00 | 11.3x | 5.146e-02 | 2.227e-02 |
| `M+4_L+4_T-4` | 6 | 9.918e-02 | 1.719e-01 | 2.139e+00 | 12.4x | 3.168e-02 | 3.057e-03 |

For the leading sector directions, the calibration/train Lie RMS ratio ranges from 1.2x to 12.4x. No additional numerical-null direction was detected at the declared tolerance.

## Publication Blockers

- `independent_threebody_reduction_replication`: The qualified WP2-3BRQ-v1 implementation has trajectory conformance but no second independently coded reduction implementation.
- `qualified_spatial_chaotic_n3bp_corpus`: Current qualified trajectories are periodic and planar up to rigid rotation; random spatial collocation is not external trajectory evidence.
- `high_precision_n3bp_oracle`: REBOUND IAS15 is an independent float64 implementation, not an arbitrary-precision N3BP oracle.
- `qualified_reduced_or_lifted_vector_field`: WP2-3BRQ-v1 qualifies maps and kinematic lifts, not reduced Hamilton equations or a lifted N3BP flow.
- `sealed_wp3_publication_holdout`: The existing WP1 holdout has already been executed and cannot serve as a fresh candidate-blind WP3 holdout.
- `candidate_covariance_and_gauge_falsification`: No screening mode has yet passed candidate-specific covariance and gauge falsification.
- `candidate_independence_poisson_variational_evidence`: No screening mode has yet passed rank, Poisson, variational, or long-time tests.
- `candidate_independent_replication`: No screening result has yet been replicated independently.

## Decision

The v1 screen does not advance an additional direction to candidate qualification. Exploration may continue, but candidate interpretation is prohibited by the fail-closed gate. Any later candidate-specific campaign must freeze its model, thresholds, and a genuinely sealed holdout before evaluation.
