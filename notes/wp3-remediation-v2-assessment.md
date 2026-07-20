# WP3 Remediation v2 Assessment

## Decision

The remediation plan is complete. WP3 search infrastructure is now ready, but
no invariant candidate was found and no publication interpretation is
authorized.

## Qualification Record

- `WP1Q-N3BP-SPATIAL-v1-8216e5f53247`: **FAIL**. The immutable first campaign
  failed two float64 gates on one holdout close-encounter case because its
  variable first checkpoint extended to 2.125 time units.
- `WP1Q-N3BP-SPATIAL-v2-294429ca5655`: **PASS**. A fresh 84-case corpus excludes
  all v1 cases and all 24 sealed WP3-reserve rows. Development, calibration,
  and holdout pass 15/15 gates. Arbitrary precision covers each full 5-20-unit
  Brutus trajectory; float64 is qualified on a fixed 0.5-unit horizon.
- `WP2-3BFLOWQ-v1-90fab6dac1ca`: **PASS**. Development, calibration, and holdout
  pass 16/16 gates for the clean-room Jacobi replication, canonical flow,
  generic SO(3) quotient/reconstruction flow, and constrained zero-Xi pairwise
  KS physical-time lift.

## WP3 v2 Result

- Search input: 522 training and 261 calibration points.
- External component: 48 development and 24 calibration Brutus trajectories,
  each sampled at nine arbitrary-precision checkpoints.
- Coverage component: 90 development and 45 calibration deterministic spatial
  collocation states with varying mass ratios.
- Library: 630 dimensionless SO(3) scalar features from ten dot products, four
  scalar triple products, five energy primitives, products through degree two,
  and three symmetric mass-parameter blocks.
- Removed before search: 325 frozen-corpus value-identity directions and rank
  11 of the represented constant, H, H^2, and squared-angular-momentum algebra.
- Smallest remaining weighted Lie RMS: `4.708878795940952e-3` against a frozen
  candidate ceiling of `1e-10`.
- Candidate count: zero. The 24-case publication reserve remains
  `SEALED_UNEXECUTED` on the custodian host.

## Prove-able Boundary

The records support qualified bounded spatial N3BP propagation, the declared
canonical/reduced/lifted physical-time flow maps, and a reproducible bounded
null search in the declared feature library. They do not support a new first
integral, hidden integrability, global three-body regularization, arbitrary
long-horizon float64 prediction, periodic-orbit catalogue completeness, or a
publication-ready WP3 invariant.
