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

## WP3-UP-CAND-v1

The locked degree-three upstairs search returned zero candidates. The
candidate-specific gate records `NOT_TRIGGERED_NO_CANDIDATE`; the publication
reserve remains sealed. See `notes/wp3-up-cand-v1-assessment.md`.

This result is historical. `WP3-UP-CAND-v2` supersedes it with a
parameter-aware grammar and stronger evidence binding.

## Project Effect

The catalogue track can continue independently from the invariant track. The
central lift-integrability hypothesis has not received positive support from
WP3-UP-CAND-v1. Any next discovery campaign must preregister a materially new
hypothesis class, such as rational/interaction-aware functions, higher-degree
sparse forms, or a different qualified upstairs geometry.
