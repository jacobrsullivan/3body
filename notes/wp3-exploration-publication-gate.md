# WP3 Exploration and Publication Gate

## Decision

WP3 restarts as a disjoint exploratory track on top of the qualified WP1/WP2
artifacts. Legacy WP3 completion/readiness statements are not accepted as
claim-bearing evidence because that stack contains placeholder dynamics,
synthetic demonstrations, and unqualified lifted/reduced constructions.

## V1 Exploration

1. Use the exact WP1Q-N3BP-v1 Newtonian vector field.
2. Map it through the qualified WP2-3BRQ-v1 canonical Jacobi transformation.
3. Evaluate a deterministic SO(3)-invariant library and exact Lie derivatives.
4. Recover energy and angular-momentum-squared as positive controls.
5. Partition features into homogeneous mass-length-time dimension sectors.
6. Project controls out of their sectors and rank remaining directions by SVD.
7. Fit only on upstream development data plus disclosed spatial collocation.
8. Evaluate only on upstream calibration data plus a disjoint collocation seed.
9. Never execute an upstream holdout from WP3 code.
10. Label every result `EXPLORATORY_ONLY`.

Random spatial collocation broadens the algebraic probe but is not external
trajectory evidence. The qualified trajectory corpus is periodic and planar up
to rigid rotation, so it cannot support a broad spatial/chaotic claim.

## Publication Gate

Candidate interpretation remains prohibited until all gate requirements pass:

- the three existing WP1/WP2 qualification records and locks;
- an independently coded three-body reduction replication;
- a qualified genuinely spatial and chaotic external N3BP corpus;
- an independent high-precision N3BP oracle;
- a qualified reduced or KS-lifted three-body vector field;
- a newly sealed, candidate-blind WP3 publication holdout;
- candidate-specific covariance, gauge, reconstruction, rank, Poisson,
  variational, long-time, and out-of-distribution checks;
- independent replication of each surviving candidate.

Even a complete gate authorizes only a bounded numerical candidate claim. It
does not establish a theorem of global conservation or integrability.

## First Run

The first `WP3-EXP-v1` run used 365 training points and 219 disjoint
calibration points. Energy and angular-momentum-squared cancel at float64
roundoff in both splits. After those controls were projected out, numerical
nullity across all nine physical-dimension sectors was zero at the declared
relative tolerance of `1e-10`. The leading direction in every sector had a
larger calibration Lie RMS, with calibration/train ratios from 1.2 to 12.4.
No direction advances to candidate qualification from this run.

The publication gate is `BLOCKED`: 3 of 11 evidence requirements pass. The
three passing items are the existing WP1Q-N3BP-v1, WP2KSQ-v1, and WP2-3BRQ-v1
records with verified locks. The remaining requirements are listed in the
campaign report and must not be inferred from this exploratory result.

A clean bobs-mini rerun on Python 3.11/SciPy 1.16.1 matches the local Python
3.13/SciPy 1.16.3 feature and Lie-derivative matrices bit for bit. The largest
sector singular-value delta is `2.22e-15`, the largest coefficient delta is
`2.78e-16`, and the frozen parity record passes all 10 checks. This is
implementation parity, not the independent scientific replication required by
the publication gate.
