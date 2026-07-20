# WP4 Upstairs Readiness Result

## Decision

- Qualification ID: `WP4-UP-READY-v1-c902df008d70`
- Harness status: `HARNESS_READY`
- Gates: 30/30 passed
- Candidate validation: `CANDIDATE_NOT_TRIGGERED`
- Candidate-specific sealed qualification: `NOT_TRIGGERED`
- Morales-Ramis: `NOT_TRIGGERED`
- Publication reserve: `SEALED_UNEXECUTED`

## Control evidence

All five known controls (`K_h`, `Xi`, `Lx`, `Ly`, and `Lz`) passed the
conservation, gauge, and bounded-trajectory criteria. The largest scaled Lie
derivative was `4.108521101135921e-12`, and the largest trajectory drift was
`7.993605777301127e-15`.

The `q0` coordinate was correctly rejected: its minimum scaled Lie derivative
was `0.0026523977122992538`, its minimum gauge change was
`0.1460798640462211`, and its minimum trajectory drift was
`0.00039602281581074816`.

The dependent control `2 K_h - 3 Xi` first passed conservation, gauge, and
trajectory prechecks, then was correctly rejected because it increased the
known functional rank by zero. The known control rank was five on every one
of the six deterministic states.

## Canonical checks

- Hamiltonian-vector-field residual: `1.0996836533007357e-11`
- Xi-to-S1-generator residual: `3.1894632071494924e-11`
- Momentum-map commutation residual: `1.3220624595078334e-10`
- Angular-momentum SO(3) algebra residual: `1.2507328506217164e-11`
- Poisson antisymmetry residual: `1.4210854715202004e-14`

## Boundary

This result qualifies the control harness only. No candidate was supplied,
fabricated, or evaluated. No reserve data was read. No Morales-Ramis
calculation was run, and no integrability or non-integrability conclusion is
authorized.
