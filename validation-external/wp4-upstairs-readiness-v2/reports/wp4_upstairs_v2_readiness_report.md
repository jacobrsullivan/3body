# WP4 Upstairs Readiness Qualification v2

## Decision

- Harness status: **HARNESS_READY**
- Candidate validation: **CANDIDATE_NOT_TRIGGERED**
- Candidate-specific sealed qualification: **NOT_TRIGGERED**
- Morales-Ramis: **NOT_TRIGGERED**
- Publication reserve: **SEALED_UNEXECUTED**
- Gates: **30/30 passed**

## Control Result

The gauntlet accepted the known upstairs controls `K_h`, `Xi`, `Lx`, `Ly`, and `Lz`.
It rejected `q0` as nonconserved and gauge variant, and rejected `2 K_h - 3 Xi`
because adding it did not increase functional rank.

## Key Metrics

- Deterministic states: `6`
- Maximum positive-control scaled Lie derivative: `4.1085211011359211e-12`
- Minimum false-coordinate scaled Lie derivative: `2.6523977122992538e-03`
- Maximum Hamiltonian-vector-field residual: `1.0996836533007357e-11`
- Maximum angular-momentum Poisson-algebra residual: `1.2507328506217164e-11`
- Minimum known functional rank: `5`
- Dependent-control rank increment: `0`
- Maximum positive-control trajectory drift: `7.9936057773011271e-15`
- Minimum false-coordinate trajectory drift: `3.9602281581074816e-04`

## Claim Boundary

This qualification covers deterministic numerical differentiation, canonical Poisson behavior, local functional-rank discrimination, S1 gauge behavior, and bounded fictitious-time integration for known controls on six declared collision-free zero-Xi states. It is a harness readiness result, not validation of an additional first integral. It excludes candidate qualification, sealed-reserve execution, Liouville integrability, non-integrability, Morales-Ramis analysis, collision passage, other KS channels, and global three-body regularization.

No candidate expression was supplied or evaluated. No reserve data was read, and no
Morales-Ramis computation was run.
