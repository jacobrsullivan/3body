# WP6-COMMON-v1 proof and evidence map

## R1: Pinned theorem sources

The campaign verifies the exact SHA-256 payloads for:

1. Maciejewski, Przybylska, and Combot, arXiv `2502.01426v2`;
2. Combot, arXiv `1112.1889`.

Executable text contracts require the primary source title, Theorem 1.1,
Definition 2.1, all three proof branches, Lemmas 5.1 and 5.3, and the
non-solvable differential-Galois conclusions. The predecessor source
contract requires its nonzero-angular-momentum theorem and its explicit
statement that the doubly-zero level needs another particular solution.

The primary payload is a preprint version of the work later published as
JEMS DOI `10.4171/JEMS/1717`; qualification remains tied to the exact
hashed arXiv payload rather than mutable publication metadata.

## R2: Qualified predecessors

The runner verifies the content hashes, signed qualification locks, signed
PASS records, and qualification identities for:

- `WP6-L0-v1`, which supplies the `c=0,h!=0` branch;
- `WP6-FI1-v1`, which fixes the one-integral theorem and prohibits its
  automatic transfer to a fixed common level;
- `WP2-SO3-LEAF-v1`, which fixes the regular noncollinear SO(3) chart
  boundary.

Changing any predecessor invalidates this campaign.

## R3: Direct common-level theorem

The authorized conclusion is taken directly from Theorem 1.1 on
`M_(h,c)`. It is not derived from the global unreduced
`WP6-FI1-v1` result. This distinction matters because a first integral
defined only on one common level need not extend to a neighborhood in the
unreduced phase space.

The theorem uses rational first integrals in the center-of-mass
algebraic-distance complexification. Restricted integrability requires a
complete family that is independent on the level and Poisson-commuting on
the level.

## R4: Exhaustive level partition

Every finite real pair except `(0,0)` falls into exactly one branch:

1. `c=0,h!=0`;
2. `c!=0,2*h*c^2!=-mu^2`;
3. `c!=0,2*h*c^2=-mu^2`.

The first condition is disjoint from the other two. For `c!=0`, equality
with `-mu^2` and inequality with `-mu^2` are exhaustive and disjoint.
The only pair with `c=0` omitted from branch 1 is `(0,0)`.

The exact classifier tests this partition over a deterministic rational
grid as an implementation control. Exhaustiveness itself is the symbolic
case distinction above, not an inference from finite sampling.

## R5: Kepler relation

For

`rho(nu)=c^2/[mu*(1+e*cos(nu))]`,

with `nu_dot=c/rho^2`, direct substitution into

`h=(rho_dot^2+rho^2*nu_dot^2)/2-mu/rho`

gives

`h=mu^2*(e^2-1)/(2*c^2)`.

Thus

`2*h*c^2=mu^2*(e^2-1)`.

The SymPy reference derives this expression from `rho(nu)` while the
production implementation checks the final identity using exact rational
arithmetic.

## R6: Equal-mass Euler-Moulton spectrum

For equal masses at collinear positions `(-1,0,1)`, the central multiplier
is `mu=5/4`. Equations (4.15)-(4.16) give

```text
C = [[ 9/10, -4/5, -1/10],
     [ -4/5,  8/5,   -4/5],
     [-1/10, -4/5,   9/10]].
```

Exact eigenvectors give:

- `(1,1,1)` with eigenvalue `0`;
- `(-1,0,1)` with eigenvalue `1`;
- `(1,-2,1)` with eigenvalue `12/5`.

The physical block therefore has `lambda=12/5` and
`delta=lambda-1=7/5>0`. The production model verifies the eigenvectors;
the source-disjoint reference constructs and diagonalizes the matrix.

## R7: Noncircular discriminant

For `delta>0,e>0`, equation (5.5) gives

```text
Delta^2 =
  4*e^4
  + 4*e^2*(delta+1)*(delta+4)
  + (delta+1)*(3*delta+4)^2*(9*delta+1).
```

All three summands are strictly positive, so `Delta^2>0`. At the
equal-mass benchmark `delta=7/5,e=1`,

`Delta^2=1406596/625` and `Delta=1186/25`.

The non-solvable identity component is the published conclusion of
Lemma 5.1. The project code audits its coefficient premises and does not
claim to reproduce the appendix's universal Kovacic analysis.

## R8: Circular relation

When `2*h*c^2=-mu^2`, the real circular solution gives a constant
variational equation and no obstruction. Treating that real orbit as the
proof witness is an explicit campaign failure.

The source instead chooses `f(nu)=1+exp(i*nu)` on the complexified common
level. Equation (5.16) gives

`Delta^2=9*delta^2+10*delta+1`.

For `delta=7/5`, this is `816/25>0`. Lemma 5.3 supplies the non-solvable
identity component for every `delta>0`.

## R9: Generic NVE coefficient agreement

The production and reference implementations independently evaluate the
plus scalar NVE in equation (5.12):

```text
b1(z) =
  (z-1)/[(z-e-1)*(z+e-1)] - 8*(2*delta+3)/l(z),

l(z) =
  8*(2*delta+3)*z
  + delta*(9*delta+17) + Delta + 2*e^2 + 4.
```

They also evaluate the complete `b0(z)` numerator and denominator. Exact
agreement is required at `delta=7/5,e=1,Delta=1186/25,z=3`. The sample
lies away from every coefficient pole.

## R10: Claim controls

The executable controls reject:

- `(h,c)=(0,0)` as qualified;
- qualification of the zero-momentum branch without the pinned
  `WP6-L0-v1` predecessor;
- the real circular orbit as an obstruction witness;
- `delta<=0` as satisfying the Euler-Moulton spectral premise;
- absence of one additional integral on every common level;
- a spatial conclusion;
- any meromorphic, analytic, smooth, or other non-rational conclusion;
- placement of the collinear witness in the regular noncollinear SO(3)
  chart;
- a reference implementation coupled to production imports.

## Model boundary

The model is the planar Newtonian three-body problem with finite positive
masses, after center-of-mass reduction and in the algebraic-distance
complexification used by the pinned theorem. The known rational integrals
are `H` and planar angular momentum `C`.

The theorem is applied directly on `M_(h,c)`. The Euler-Moulton witness is
collinear and belongs to a singular rotational orbit-type stratum, so no
regular-chart continuation is asserted.

## Authorized claim

For arbitrary finite positive masses and every finite real common level
`(H,C)=(h,c)` with `(h,c)!=(0,0)`, the pinned
Maciejewski-Przybylska-Combot theorem, together with this exact audit,
proves that the planar Newtonian three-body problem is not rationally
integrable in the locked restricted-integrability sense. The proof is
direct on each common level and uses Euler-Moulton homographic witnesses.

## Nonclaims

This campaign does not qualify the doubly-zero level, absence of one
additional fixed-level integral, spatial motion, non-rational regularity
classes, collision continuation, or pointwise nonintegrability of every
open phase-space domain.
