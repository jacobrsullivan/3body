# WP2-MULTIQ-v1

This campaign qualifies a fixed-energy canonical KS atlas with two spinors per
chart, a `T^2` gauge, and the chart-independent Heggie clock
`dt/ds=r12*r23*r31`. Three central-body charts cover all isolated binary
collisions. Triple collision remains outside the model.

The claim is inert until both the specification lock and final qualification
record verify. Legacy modules under `src/python/regularization` are not
consumed by this campaign.

Each split executes 64 seeded structural probes. They measure the two
independent `Xi` constraint ranks, the two gauge-generator ranks, the resulting
14-dimensional quotient count, the Hamiltonian generator relation, the
symplecticity of every physical chart-coordinate transition, and the identity
`K=g(H+p_t)` off shell.

The three declared near-collision values are physical pair distances. Their KS
spinor radii are therefore their square roots. `collision_limit_scaled` is the
quadratic-in-spinor-radius extrapolation of the three independently evaluated
fields to the exact divisor; raw probe error and monotone convergence are also
stored. Exact-passage cases additionally measure gauge covariance, signed
spinor crossing, Hamiltonian/`Xi` drift, and agreement with the separately
encoded JAX field in both fictitious-time directions.

For every noncollision case the runner deliberately lifts into the chart where
the smallest pair is unregularized, applies the production smallest-pair
switch policy on an overlap, and compares a mixed-chart integration with a
single-chart integration. The switched-trajectory error is included in the
locked chart-cocycle gate.
