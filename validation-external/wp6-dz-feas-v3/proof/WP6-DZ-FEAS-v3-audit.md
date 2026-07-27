# WP6-DZ-FEAS-v3 Audit

## Frozen Scope

The campaign repeated the exact 11,700-system mathematical enumeration from
WP6-DZ-FEAS-v2. It changed only the pre-registered exact equation
construction, localization, term order, dual-algorithm verification, and
resource caps.

## Exact Controls

- Specification lock: `960fc53758af0c361f4cab58a49d2f3715f2c1ce81230cc34cba32ca2e45c1c0`
- Search ledger SHA-256: `145a2e91cb2f22628f698327effab63ac26527f4f32e96a33c833a594979f8a5`
- Search payload SHA-256: `9555fbcdeb532db2986c9b7f9ed2e3927fab109d9abb17d418917f548b4b3034`
- Source-disjoint reference checks: all pass
- Runtime checks: all pass
- Exact algorithms: F5B grevlex and Buchberger grevlex over `QQ`
- Algorithm disagreements: 0

## Ideal Results

- Systems executed: 11,700/11,700
- Unit ideals: 11,700
- Non-unit ideals: 0
- Timeouts: 0
- Errors: 0
- Energy-stage decisions: 11,687
- Energy-and-v-stage decisions: 13
- Full-stage decisions: 0

The 13 systems requiring the vector residual were:

- `S00836`
- `S01736`
- `S02636`
- `S03536`
- `S04436`
- `S05336`
- `S06236`
- `S07136`
- `S08036`
- `S08936`
- `S09836`
- `S10736`
- `S11636`

## V2 Gap Closure

All 140 v2 timeouts and all 11 v2 unexecuted systems were rerun in the full
v3 enumeration. Every one of those 151 systems is an exact dual-algorithm
unit ideal.

## Candidate And Branch Audit

No non-unit ideal exists in the frozen enumeration, so there is no
coefficient branch or sentinel candidate to promote. The branch audit is
vacuously complete and the candidate count is zero.

## Qualified Interpretation

The evidence supports `COMPLETE_BOUNDED_NULL_RESULT`: no graph in the frozen
four-cover, one- and two-term Laurent, thirteen-sentinel library can become
a W1-W12 arbitrary-positive-mass witness.

It does not prove that no suitable algebraic orbit exists outside that
library, does not prove nonintegrability on `(H,C)=(0,0)`, and does not
authorize `WP6-DZ-MR-v1`.
