# WP3-UP-CAND-v3 Result

## Decision

- Qualification ID: `WP3-UP-CAND-v3-2979adbb0597`
- Lock payload SHA-256:
  `ec91c679d4b352f2c076e6b0e1c493c587ffc6f97a95984beb00a7dd67e55996`
- Immutable record SHA-256:
  `e867493b2ee64f3a565745c17e2e2a04763dd1ac905e04ea6496f3419563fd83`
- Status: `COMPLETE_BOUNDED_NULL_RESULT`
- Search readiness: `PASS` (15/15 gates)
- Null-result readiness: `PASS`
- Candidate-subspace count: `0`
- Publication reserve: `SEALED_UNEXECUTED`

## Numerical Scope

- Complete declared polynomial library: 1,120 state/energy/symmetric-mass
  monomials of combined degree at most three.
- Exact coefficient-space known module removed: rank 30, with projection
  residual `1.164062420605084e-16`.
- Observable quotient rank: 1,090; all 1,090 generalized directions were
  evaluated.
- Training rows: 1,566; calibration rows: 783.
- Smallest generalized Lie/value singular value:
  `1.6456129372731588e-4`.
- Frozen backend uncertainty bound: `6.119791306408978e-7`.
- Guarded lower bound: `1.6394931459667498e-4`.
- Candidate training threshold: `1.0e-10`.

The guarded lower bound is about 1.6 million times the candidate threshold.
Consequently, no direction in the frozen observable quotient can satisfy even
the training Lie-derivative gate. This null does not rely on the arbitrary
basis returned inside a repeated singular subspace.

## Claim Boundary

This is a bounded finite-library null on previously examined development and
calibration data. It excludes a training-eligible polynomial direction only
inside the declared degree-three quotient. It is not a proof that the upstairs
three-body system has no additional first integral, a non-integrability
theorem, or fresh blind confirmation. The candidate-specific sealed gate was
therefore not triggered, and no reserve row was opened.
