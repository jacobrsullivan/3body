# WP6-DZ-FEAS-v3 qualification boundary

This package changes only exact equation construction and ideal decision for
the 11,700 systems frozen by `WP6-DZ-FEAS-v2`.

The production model, covers, supports, mass/order sentinels, graph
identities, coefficient field, saturation, and enumeration are imported
from or checked against the hash-pinned v2 definitions.

Removing a coefficient monomial is valid only after exact-support saturation
makes every support coefficient a unit. Clearing `z`, `x`, `1-x`, or cover
denominators is valid only on the declared collision-free Laurent dense
open. No other factor may be removed.

Every unit decision requires exact agreement between fixed F5B and
Buchberger computations over `QQ` in graded reverse lexicographic order.
Timeout, disagreement, exception, cap exhaustion, or an unaudited non-unit
ideal forces `INCOMPLETE`.

A complete bounded null covers only the frozen graph library. It does not
prove nonexistence of a suitable orbit or nonintegrability at `(H,C)=(0,0)`.
It cannot authorize `WP6-DZ-MR-v1`; only a signed `QUALIFIED_WITNESS` can do
that.
