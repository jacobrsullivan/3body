# WP6 FI1, WP2 SO(3), and WP6 L0 result

Date: 2026-07-24

## Decision

All three locked campaigns passed and their frozen scopes verify:

| Track | Qualification | Result |
| --- | --- | --- |
| One additional integral | `WP6-FI1-v1-c9099f7494b1` | PASS |
| Regular SO(3) quotient leaf | `WP2-SO3-LEAF-v1-837d711e7074` | PASS |
| Planar zero angular momentum | `WP6-L0-v1-27f160d029ca` | PASS |

Each result passed source hashes, source-text contracts, prerequisites,
theorem obligations, production/reference agreement, adversarial controls,
proof coverage, and implementation-independence gates.

## 1. One additional integral

The qualified claim is:

> For every finite positive mass triple and every integer dimension `d >= 2`,
> the Newtonian three-body vector field has no meromorphic first integral
> functionally independent of all classical first integrals.

This is the pinned Morales-Ruiz--Simon theorem, supported by a project-owned
exact audit of the mass branches and a source-disjoint SymPy Hessian
specialization. The audit closes the apparent first-NVE mass candidates
`Q = 1/3` and `Q = 8/27` by selecting the required complex Lagrange witness.

This result addresses the distinction between failure of complete Liouville
integrability and existence of one additional integral. It excludes one such
additional meromorphic integral on the unreduced Newtonian vector field.

It does not exclude smooth, continuous, real-analytic outside the declared
meromorphic setting, or other non-meromorphic integrals. It also does not
automatically imply the corresponding statement for a function defined only
on one fixed-energy or fixed-angular-momentum reduced leaf.

Evidence:
`validation-external/wp6-fi1-v1/results/qualification_results.json`

## 2. Broader SO(3) reduction

The qualified implementation is an explicit Hamiltonian model of the regular
non-collinear SO(3) Poisson quotient in the locked body-frame chart. It
includes:

- the inverse cotangent reconstruction and body angular momentum;
- the canonical plus minus-body Lie-Poisson tensor;
- the Newtonian reduced Hamiltonian and exact analytic gradient;
- rank-eight nonzero-angular-momentum leaves;
- the rank-six regular zero-angular-momentum leaf;
- independent finite-difference and quotient-flow comparisons.

Maximum observed errors were:

| Check | Error |
| --- | ---: |
| Reconstruction round trip | `5.551115123125783e-16` |
| Hamiltonian | `0.0` |
| Analytic gradient | `3.749242694084387e-09` |
| Hamiltonian flow | `3.552713678800501e-15` |
| Casimir derivative | `3.219646771412954e-15` |

This is a regular-chart qualification, not a global atlas. It excludes
`rho = 0`, collinearity (`y = 0`), collisions, singular orbit types, and any
claim that all nine quotient variables are one Darboux chart.

Evidence:
`validation-external/wp2-so3-leaf-v1/results/qualification_results.json`

## 3. Zero angular momentum

The qualified claim is:

> For arbitrary finite positive masses and every finite nonzero energy `h`,
> the planar Newtonian three-body problem on `(H,C) = (h,0)` is not rationally
> integrable in the locked restricted-integrability sense.

The certificate combines the pinned restricted-integrability theorem with the
Pacella/Combot spectrum. A longitudinal eigenvalue `lambda > 2` gives a
transverse mode `-lambda/2 < -1`, outside the allowed degree-minus-one
spectrum `(k-1)(k+2)/2`. The resulting scalar NVE has Galois group
`SL(2,C)`, whose identity component is not solvable. An independent exact
equal-mass Euler benchmark reproduces longitudinal spectrum `{0,2,24/5}` and
transverse spectrum `{0,-1,-12/5}`.

This does not cover `(H,C) = (0,0)`, the spatial problem, non-rational
regularity classes, collision continuation, or absence of one additional
integral on the fixed zero-momentum level.

Evidence:
`validation-external/wp6-l0-v1/results/qualification_results.json`

## Combined assessment

The three priorities are now separated cleanly:

1. The one-integral question has a qualified global unreduced meromorphic
   obstruction for all positive masses and dimensions `d >= 2`.
2. The spatial rotation reduction has a qualified local model on every
   regular non-collinear angular-momentum leaf, including the regular
   zero-momentum leaf.
3. The planar zero-angular-momentum problem has a qualified rational complete
   nonintegrability result for every nonzero energy.

Together these materially broaden the project's nonintegrability evidence,
but they do not constitute a proof of "global three-body nonintegrability" in
an unrestricted sense. The remaining mathematically distinct gaps are:

- transfer of the one-integral obstruction to individual reduced leaves;
- the planar double-zero level `(H,C) = (0,0)`;
- a spatial zero-angular-momentum nonintegrability theorem;
- quotient charts through collinearity and collision regularization;
- regularity classes outside the locked meromorphic or rational categories.

Any publication must use the authorized claims above and retain these
boundaries. Closing one of the remaining gaps requires a separately locked
qualification campaign rather than reinterpretation of these PASS results.

## Verification

- Focused successor tests: `53 passed`.
- Pinned Python 3.11 legacy fast lane: `1202 passed`, `2 skipped`,
  `134 deselected`, `19 warnings`.
- The 134 slow simulations remain isolated in the established slow lane; none
  of the successor tests is marked slow.
- All three qualification locks verify their complete frozen file scopes.
