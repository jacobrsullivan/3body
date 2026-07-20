# WP1-CAT-v1 result

## Qualification outcome

`WP1-CAT-v1-5dc7ad44b78f` is an immutable `PASS` under lock
`31da65d3965b98c57c2e05c8906677710e570f996c1fca44f915a0584a75b4dd`.

The native, external-seed-free run generated 159 corrected and Floquet-labelled
Earth-Moon planar Lyapunov members: 80 on the declared L1 segment and 79 on the
declared L2 segment.  No candidates were removed as duplicates.  Maximum
one-period closure error was `4.248e-12`; the p95 symmetry residual was
`3.404e-14`.  Both branches had strictly monotone Jacobi constant over the
declared continuation grids.

Development, calibration, and holdout passed every frozen gate. Every one of
the 300 sampled JPL rows had a nearest-neighbor native match within the frozen
tolerances; these matches selected 138 distinct native candidates. This is
sampled family-curve coverage, not one-to-one recovery. On the 60-row holdout,
p95 errors were:

- state: `3.041e-3`
- relative period: `2.919e-3`
- Jacobi constant: `1.064e-3`
- relative stability index: `1.198e-2`

Holdout stability-label agreement was 100%.  The measured host-specific rate
was 10.503 corrected and stability-labelled candidates per second; throughput
was deliberately reported rather than used as a portable gate.

The three partitions are deterministic and disjoint, and holdout execution was
reserved until development and calibration passed. The source rows were not
independently blinded or held by a separate custodian, so this is an
execution-reserved holdout rather than a blind publication holdout.

All 159 native candidates and all 300 sampled external rows lie in the frozen
`strongly_unstable` bin.  The quantitative stability-index errors are therefore
meaningful evidence, but the categorical agreement is single-class evidence;
v1 does not qualify behavior at stability-class boundaries.

## Defensible use

This establishes a usable native catalogue component for the two explicitly
bounded planar family segments.  It does not establish completeness, Halo or
spatial generation, traversal through folds or bifurcations, disconnected
family discovery, other mass systems, or a general production catalogue for
CR3BP or the full three-body problem.
