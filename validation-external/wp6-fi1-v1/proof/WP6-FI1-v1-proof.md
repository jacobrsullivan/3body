# WP6-FI1-v1 proof and evidence map

## R1: Published theorem

The pinned Morales-Ruiz--Simon manuscript states its Theorem 3.1 for every
`d>=2`, arbitrary positive masses, and a first integral independent with the
classical first integrals.  The source hash and normalized text contracts are
qualification gates.  The project does not restate this as a fixed-leaf
theorem.

## R2: Positive mass domain

Let

`Q=(m1*m2+m2*m3+m3*m1)/(m1+m2+m3)^2`.

For positive masses, `Q>0`, and

`1/3-Q=((m1-m2)^2+(m2-m3)^2+(m3-m1)^2)/(6*(m1+m2+m3)^2)`.

Hence `Q<=1/3`, with equality exactly for equal masses.

## R3: Real Lagrange Hessian

After mass weighting, the real homothetic Lagrange configuration has
classical eigenvalues `-2,0,0,1` and two roots of

`lambda^2+lambda+(27*Q-8)/4`.

Equivalently,

`lambda_pm=-1/2 +/- (3/2)*sqrt(1-3*Q)`.

The source-disjoint reference constructs the Newtonian pair Hessian and
checks the complete characteristic polynomial exactly.

## R4: Table-membership branch

For homogeneity degree `-1`, membership of a nonclassical eigenvalue in the
Morales-Yoshida table implies

`-27*Q=(p-1)*(p-2)*(p-4)*(p+1)`, `p>1`.

The right side is zero for `p=2,4`, positive for `p>4`, and negative only for
`p=3`.  Positivity of `Q` therefore leaves only `Q=8/27`.

## R5: Pair-equivalence branch

The second alternative in the one-integral necessary condition compares the
two nonclassical exponents.  On `0<Q<=1/3`, exact elimination leaves only
`Q=1/3`.  The production certificate records the candidate set and the
source-disjoint symbolic reference checks the elimination identity.

## R6: Second Lagrange witness

Write the second witness parameter as

`a_*^2=A/(2*m^2)`,

where

`A_re=2*m1^2+2*m2^2+2*m3^2-5*m1*m2-5*m2*m3+7*m1*m3`

and the coefficient of `-i*sqrt(3)` is

`B=m1*m2+m2*m3-5*m1*m3`.

For `Q=1/3`, the squared-difference identity forces equal masses, so `B` is
nonzero and `a_*^2` is nonreal.  Both necessary alternatives fail.

For `Q=8/27`, nonzero `B` again makes both alternatives nonreal.  If `B=0`,
table membership would additionally require
`m^2=(189/8)*m1*m3`; together those conditions force `Q=16/63`, contradicting
`8/27`.  The same `B=0`, `Q=8/27` branch forces `a_*^2=-1/27`.  An integer
pair relation would require

`36*a_*^2=n^2*(13-n^2)`.

Its left side is `-4/3` and its right side is an integer.  This is impossible.

## R7: Legacy exceptional set

The pinned Tsygvintsev source leaves first-NVE polynomial invariants at
`Q in {1/3,8/27,2/9}`.  A polynomial invariant of a linearized equation is
not a nonlinear first integral.  All three values pass the final two-witness
obstruction.

## R8: Independent exact replay

The reference implementation imports no production code.  It constructs
the real mass-weighted Newtonian Hessian from pair blocks at exact Lagrange
configurations and checks the characteristic polynomial for equal,
`Q=8/27`, and generic masses.

## R9: Logical scope

The theorem is about a meromorphic integral of the unreduced vector field
that is independent with all classical first integrals.  A function defined
only on a specified common level or reduced symplectic leaf need not extend
to such an integral.  No fixed-leaf transfer is used.

## R10: Claim discipline

Every record includes meromorphicity, independence from the classical
integrals, arbitrary positive masses, dimension `d>=2`, and witness
selection.  The short statement "the three-body problem has no integrals"
is prohibited.

## Model boundary

This track complements but does not mutate `WP4-MR-REPL-v1`.  WP4 is a
fixed-nonzero-angular-momentum complete-integrability obstruction.  FI1 is
an unreduced one-extra-integral theorem reproduction.

## Authorized claim

For every finite positive mass triple and every integer `d>=2`, the pinned
Morales-Ruiz--Simon theorem, with this exact branch reproduction, excludes a
meromorphic first integral of the Newtonian three-body vector field that is
functionally independent of the classical first integrals.

## Nonclaims

No conclusion is made about an integral defined only on one fixed leaf,
non-meromorphic regularity classes, collision continuation, or a uniform
single witness curve for every mass.
