# WP4 Upstairs v2 Readiness Result

## Supersession Notice

The numerical control result remains reproducible, but this record is not the
authoritative project chain because its prerequisite `WP3-UP-CAND-v2` null
claim was invalidated. WP4 must be re-frozen against corrected WP3 evidence.

## Decision

- Qualification: `WP4-UP-READY-v2-9a29e65bd8d9`
- Historical harness result: `HARNESS_READY`
- Frozen gates: 30/30 passed
- Candidate validation: `CANDIDATE_NOT_TRIGGERED`
- Candidate-specific sealed qualification: `NOT_TRIGGERED`
- Morales-Ramis: `NOT_TRIGGERED`
- Publication reserve: `SEALED_UNEXECUTED`

The signed lock binds `WP2-UPQ-v2`, the complete immutable
`WP3-UP-CAND-v2` null chain, the candidate non-trigger decision, and the sealed
reserve commitment. The readiness record SHA-256 is
`a7fd4f83165ed87193ad13390b376fdfbd795673fb8b8887bf8ea213ed6ea4a3`.

## Controls

All five known controls (`K_h`, `Xi`, `Lx`, `Ly`, `Lz`) passed conservation,
gauge, rank, and bounded-trajectory checks. Maximum scaled Lie residual was
`4.11e-12`; maximum trajectory drift was `7.99e-15`. The nonconserved,
gauge-variant `q0` control and the conserved but functionally dependent
`2 K_h - 3 Xi` control were both correctly rejected.

## Boundary

This qualifies the control harness, not an additional integral. No candidate
was supplied, fabricated, or interpreted. No reserve row was opened and no
Morales-Ramis computation ran. The result supports neither integrability nor
non-integrability of the upstairs N3BP model.
