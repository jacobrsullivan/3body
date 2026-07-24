# WP6-COMMON-v1 qualification boundary

## Authorized result

For arbitrary finite positive masses and every finite real planar common
level `(H,C)=(h,c)` with `(h,c)!=(0,0)`, the pinned
Maciejewski-Przybylska-Combot theorem proves that the Newtonian three-body
problem is not rationally integrable in its restricted-integrability sense.

The project-owned evidence audits, but does not replace, that theorem. It
reproduces the complete branch partition, the Kepler
energy-angular-momentum relation, the equal-mass Euler-Moulton spectral
parameter, both block discriminants, and representative generic NVE
coefficients against a source-disjoint exact implementation.

## Proof branches

- `c=0,h!=0` uses the qualified `WP6-L0-v1` homothetic result.
- `c!=0,2*h*c^2!=-mu^2` uses the noncircular Euler-Moulton homographic
  solution and source Lemma 5.1.
- `c!=0,2*h*c^2=-mu^2` does not use the real circular orbit as an
  obstruction. It uses the source's complex homographic solution and
  Lemma 5.3.
- `(h,c)=(0,0)` remains unqualified.

## Model connection

The theorem is stated on the center-of-mass algebraic-distance
complexification of the planar problem. Its Euler-Moulton witness is
collinear and lies on a singular rotation orbit-type stratum.
`WP2-SO3-LEAF-v1` covers a regular noncollinear SO(3) chart; this campaign
does not insert the witness into that chart or infer the theorem by chart
continuation.

`WP6-FI1-v1` excludes one additional global meromorphic integral on the
unreduced vector field. This campaign does not transfer that conclusion to
a fixed common level. It instead applies a theorem stated directly on each
common level.

## Exclusions

This track does not prove:

- rational nonintegrability on `(H,C)=(0,0)`;
- absence of one additional integral on each fixed common level;
- a spatial three-body theorem;
- absence of meromorphic, analytic, smooth, or other non-rational
  integrability structures;
- pointwise nonintegrability on every open phase-space domain;
- collision-regularized continuation;
- a single regular SO(3) chart containing the collinear witness.

The result concerns failure of a complete family of rational commuting
integrals in the precise restricted sense of the pinned theorem. Those
quantifiers must remain attached to every downstream use.
