# WP3-UP-CAND-v2 Assessment

## Decision

`WP3-UP-CAND-v2-9f06dc7b2254` completed as a bounded null result.

- `SEARCH_READY=PASS`
- `CANDIDATE_READY=NOT_TRIGGERED`
- candidate count: 0
- candidate-specific qualification: `NOT_TRIGGERED_NO_CANDIDATE`
- publication reserve: `SEALED_UNEXECUTED`

The immutable search record has SHA-256
`f5d7c56033ab5387b518767bf8ade8fbf8d595288fbdb0144be181c50b7ea152`.

## Frozen Search

- 1,120 complete combined-degree-three-or-less monomials containing at least
  one of 14 canonical upstairs state variables, with optional fixed-energy and
  symmetric-mass factors.
- Six known-algebra controls: `H`, `H^2`, `Lx`, `Ly`, `Lz`, and `|L|^2`.
- 1,566 development and 783 disjoint calibration state-gauge points.
- Three sampled KS gauges per physical state.
- Active value rank 1,081, 45 removed identity directions, and known-algebra
  active rank six.

Three singular directions fall below the raw `1e-10` numerical threshold on
development data. None is a candidate. The leading direction has development
Lie RMS `1.35e-11` but calibration Lie RMS `6.94e-7`, a ratio above 51,000;
its minimum family-fold coefficient cosine is about `0.104`, and its trajectory
drift also fails. The remaining near directions fail calibration similarly.

## Claim Boundary

The result excludes only the frozen parameter-aware polynomial library on the
declared corpus, sampled gauges, and thresholds. It is not a proof that no
additional first integral exists and not a non-integrability theorem. No
candidate expression was qualified or interpreted, no reserve row was opened,
and WP4 can proceed only as a control-harness readiness stage.
