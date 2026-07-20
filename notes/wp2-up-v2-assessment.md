# WP2-UP-v2 Assessment

## Decision

`WP2-UPQ-v2-3baea4a70768` is `PASS`. It supersedes
`WP2-UPQ-v1-64cdda5ede83` as the downstream qualification record.

The v1 Hamiltonian was mathematically correct, but an independent audit found
that its lock omitted consumed upstream modules/results, its reference copied
the production derivative formulas, and its collision gate checked only
pointwise finiteness. V1 remains immutable and is retained as internal
compositional evidence.

## V2 Evidence

- 84 external spatial Brutus cases: 48 development, 24 calibration, and 12
  execution-reserved conformance cases.
- All three splits pass 25/25 frozen gates.
- A separately implemented JAX x64 scalar Hamiltonian supplies the gradient
  and canonical vector field by automatic differentiation.
- The maximum production/autodiff vector-field discrepancy is below
  `1.3e-14` across development and calibration.
- The full consumed spatial campaign, N3BP implementation, reduction, KS, and
  three-body-flow inputs are frozen or checked through prerequisite hashes.
- The selected collision test enforces `K_h=Xi=0`, verifies a monotone
  on-shell limit to `q=0`, and integrates in both fictitious-time directions
  through collision while preserving `K_h` and `Xi`.
- A symbolic polynomial identity verifies the KS kinetic relation used to
  obtain `K_h=|q|^2(H-h)` on `Xi=0`.

## Boundary

The result qualifies one canonical KS channel, `rho=x2-x1`. It does not
qualify either other binary channel, simultaneous three-pair regularization,
triple collision, nonzero-`Xi` physical reduction, an additional integral, or
integrability. The split named holdout reserves WP2-UP transformation
execution only; the upstream states were already present and it is not an
unseen scientific holdout.
