# WP6-COMMON-v1 plan

Date: 2026-07-24

## Objective

Qualify the strongest direct fixed-common-level result currently supported by
an explicit non-Lagrange witness:

> For arbitrary finite positive masses and every planar common level
> `(H,C)=(h,c)` with `(h,c)!=(0,0)`, the problem is not rationally
> integrable in the locked restricted-integrability sense.

The proof authority is the pinned Maciejewski-Przybylska-Combot theorem. The
project-owned work audits its complete level branching, its Euler-Moulton
homographic witness, the strict spectral parameter, and representative normal
variational coefficients.

## Why This Track

`WP6-FI1-v1` excludes one additional global meromorphic integral on the
unreduced vector field, but it cannot be transferred by implication to a
function defined only on one reduced leaf.

`WP6-L0-v1` already uses an Euler-Moulton witness, but only qualifies the
zero-angular-momentum branch `(h,0)` with `h!=0`.

The selected theorem directly treats each common level and therefore avoids
the invalid FI1 transfer. It extends the Euler-Moulton evidence to nonzero
angular momentum, including the exceptional circular energy relation.

## Candidate Screen

- Euler-Moulton common-level theorem: selected. It is exact, published,
  arbitrary-mass, and directly level-specific.
- Lagrange homographic witness: not selected. Existing WP4 and WP6 campaigns
  already qualify the available Lagrange conclusions.
- Figure-eight witness: deferred. The orbit is numerically and variationally
  accessible, but no locked algebraic differential-Galois certificate is
  available.
- Hierarchical near-Keplerian domains: deferred. Available conclusions are
  perturbative or parameter-dependent and do not improve the selected
  arbitrary-mass common-level claim.

## Qualification Structure

1. Lock the theorem statement, source payloads, predecessor evidence, branch
   partition, exact benchmarks, controls, and decision policy before code.
2. Implement an exact common-level branch classifier.
3. Reproduce the equal-mass Euler-Moulton spectral parameter
   `lambda=12/5`, `delta=7/5`.
4. Reproduce the Kepler relation
   `2*h*c^2=mu^2*(e^2-1)`.
5. Audit the noncircular and circular normal-variational coefficient
   invariants on exact benchmarks.
6. Use a source-disjoint SymPy derivation for the Euler spectrum and Kepler
   relation.
7. Require explicit rejection of `(h,c)=(0,0)`, one-integral transfer,
   spatial transfer, non-rational regularity claims, and insertion of the
   collinear witness into the regular SO(3) chart.
8. Freeze, execute, finalize, verify, regress, document, commit, and push.

## Completion Standard

Completion requires an immutable PASS qualification, exact predecessor and
source verification, source-disjoint agreement, all negative controls, a
clean fast-lane regression, and a final statement of what the theorem does
and does not add to the broader project.
