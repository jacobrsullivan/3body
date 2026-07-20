# WP4 Upstairs v3 Readiness Result

## Decision

- Qualification: `WP4-UP-READY-v3-696827675bff`
- Lock payload SHA-256:
  `1ca028a3feae2f9eca448fb20909197502c5a474e42095d09e49caa6a27dee0c`
- Immutable record SHA-256:
  `955e35a0c660b14e9655976aa04cedab22f4dcbd458eb5cd8b2e2aaa8a42f1de`
- Harness result: `HARNESS_READY`
- Frozen gates: 30/30 passed
- Candidate validation: `CANDIDATE_NOT_TRIGGERED`
- Candidate-specific sealed qualification: `NOT_TRIGGERED`
- Morales-Ramis: `NOT_TRIGGERED`
- Publication reserve: `SEALED_UNEXECUTED`

The signed lock binds `WP2-UPQ-v2`, the authoritative
`WP3-UP-CAND-v3-2979adbb0597` spectral-null chain, the v3 candidate
non-trigger decision, the sealed reserve commitment, the complete control
harness dependency set, and the execution runtime.

## Controls

All five known controls (`K_h`, `Xi`, `Lx`, `Ly`, `Lz`) passed conservation,
gauge, rank, and bounded-trajectory checks. Maximum scaled Lie residual was
`4.1086e-12`; maximum trajectory drift was `7.9937e-15`. The nonconserved,
gauge-variant `q0` control and the conserved but functionally dependent
`2 K_h - 3 Xi` control were both correctly rejected. Known functional rank was
five on every case and the dependent control increased rank by zero.

## Boundary

This qualifies the WP4 control harness, not an additional integral. No
candidate was supplied, fabricated, or interpreted. No reserve row was opened
and no Morales-Ramis computation ran. The result supports neither integrability
nor non-integrability of the upstairs N3BP model.
