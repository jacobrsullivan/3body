# WP2-MULTIQ-v1 and WP1-CAT-N3BP-v1 Results

Date: 2026-07-21

## Decisions

| Campaign | Qualification | Decision |
|---|---|---|
| WP2-MULTIQ-v1 | `WP2-MULTIQ-v1-72c81d86644a` | PASS |
| WP1-CAT-N3BP-v1 | `WP1-CAT-N3BP-v1-605c6dbd59d1` | PASS |

Both specification locks were frozen before implementation. Both full locks
verify after finalization, and every development, calibration, and sealed
first-execution holdout gate passed. The relevant regression suite passes
192/192 tests.

## WP1 Result

WP1 natively generated and froze 169 members of one connected planar
`bABabaBAba` Newtonian three-body family before the selected external numerical
rows were present. The candidate payload hash is
`23f9fefd7251403f7c27b247583b622f96e794e51c321ef3d011b1100e82152e`.

The pinned Li-Li-Liao/SJTU comparison contains 168 exact-mass cases split
84/42/42. All three splits passed 29/29 gates. The holdout retained one-to-one
matching and 100% reduced-planar stability-label agreement. Its maximum scaled
position and velocity closure errors were `3.12e-11` and `1.43e-10`; maximum
external parameter and relative-period errors were `3.76e-11` and `2.01e-11`;
the maximum DOP853-to-REBOUND velocity difference was `4.89e-9`.

The result qualifies native correction, two-parameter continuation, full 18D
barycentric state production, and bounded reduced-planar Floquet diagnostics
from one disclosed published equal-mass root. It does not qualify independent
root discovery, other or disconnected families, spatial or relative-periodic
orbits, collision passage, bifurcation handling, completeness, or a general
production catalogue for the full three-body problem.

## WP2 Result

WP2 qualifies the declared fixed-energy extended-canonical three-chart,
two-spinor KS atlas for the translation-reduced spatial Newtonian three-body
problem. Each chart carries a `T^2` gauge action and zero-`Xi` quotient, all
charts share `dt/ds = r12*r23*r31`, overlap transitions are canonical, and the
flow continues smoothly through each isolated binary-collision divisor while
the third body remains separated.

Development, calibration, and holdout passed 27/27 gates over 21/12/12 corpus
cases, with 64 seeded structural probes per split. On holdout, the independent
vector-field error was `7.33e-16`, the chart-cocycle error including automatic
smallest-pair switching was `1.29e-11`, and the extrapolated collision-limit
error was `6.77e-5`. All three physical collision channels are represented in
every split.

The result excludes triple collision, simultaneous pair collisions, nonzero-
`Xi` magnetic reduction, SO(3) reduction, arbitrary-duration accuracy,
additional first integrals, and every WP3/WP4 conclusion.

## Project Consequence

WP1 now supplies a qualified bounded full-state periodic family, and WP2 now
supplies a qualified atlas covering every isolated binary-collision channel.
The existing `WP3-UP-CAND-v3` bounded-null result and `WP4-UP-READY-v3` harness
record remain tied to `WP2-UPQ-v2`, the older one-channel model. They cannot be
used to infer a result on `WP2-MULTIQ-v1`.

The next scientific step is a new locked WP3 search specification bound to
`WP2-MULTIQ-v1-72c81d86644a`. Its publication gate must be evaluated before any
candidate interpretation. A discovered candidate must then pass a separate
sealed candidate-specific qualification before WP4; a null result remains only
a bounded null for the frozen observable library and corpus.

Supplemental clean-checkout parity on `bobs-mac-mini` verifies both locks and
passes 192/192 relevant tests. The exact runtime and its disclosed dependency
caveat are recorded in `notes/wp2-multi-wp1-cat-n3bp-bobs-parity.md`.
