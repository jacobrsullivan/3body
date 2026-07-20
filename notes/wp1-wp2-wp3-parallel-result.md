# Parallel Qualification Result

## WP1-CAT-v1

`WP1-CAT-v1-5dc7ad44b78f` is `PASS` for two bounded Earth-Moon planar Lyapunov
segments. It generated 159 corrected and stability-labelled candidates from
analytic center-mode seeds without external orbit seeds, rejected zero
duplicates, and gave all 300 partitioned JPL comparison rows a native
nearest-neighbor match within the frozen tolerances. This is sampled
family-curve coverage, not one-to-one recovery of 300 externally specified
orbits: 138 of the 159 native candidates were selected by at least one row.

This is a real native catalogue component, not a general production catalogue.
It excludes Halo/spatial families, folds and bifurcations, disconnected-family
discovery, completeness, other mass systems, and full Newtonian N3BP periodic
orbits. All comparison rows are strongly unstable, so quantitative Floquet
agreement is informative while categorical stability accuracy is single-class.
The holdout partition was execution-reserved and disjoint, but not independently
blinded. These limits make v1 bounded engineering evidence rather than a final
standalone publication package.

## WP2-UP-v2

`WP2-UPQ-v2-3baea4a70768` is the authoritative one-channel upstairs model
qualification. See `notes/wp2-up-v2-assessment.md`.

## WP3-UP-CAND-v3

`WP3-UP-CAND-v3-2979adbb0597` is the authoritative corrective search. It
removed the exact rank-30 represented known module and evaluated all 1,090
observable quotient directions. The guarded minimum generalized singular value
was `1.63949e-4`, versus the `1e-10` candidate threshold, so it produced a
basis-invariant bounded finite-library null. The candidate gate was not
triggered and the publication reserve remains sealed. See
`notes/wp3-up-cand-v3-result.md`.

## WP4-UP-READY-v3

`WP4-UP-READY-v3-696827675bff` passes all 30 control-harness gates against the
authoritative WP2/WP3 chain. This qualifies known/false/dependent control
discrimination only. Candidate validation and Morales-Ramis analysis were not
triggered.

## Project Effect

The catalogue track can continue independently from the invariant track. The
current polynomial hypothesis class has now been assessed with a bounded null,
but the broader lift-integrability hypothesis remains unresolved. No discovered
invariant exists to interpret or advance into candidate-specific WP4 stages.
