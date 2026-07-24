# WP6-L0-v1 proof and evidence map

## R1: Common-level theorem

The pinned 2025 source defines restricted rational integrability on
`M_(h,c)` and states nonintegrability for positive masses when
`(h,c)!=(0,0)`.  This track selects only its `c=0,h!=0` branch.

## R2: Pacella spectrum

For an Euler-Moulton collinear central configuration, the longitudinal
mass-weighted Hessian spectrum contains

`{0,2,lambda_i}`, with every `lambda_i>2`.

The pinned Combot source reproduces this Pacella theorem and the transverse
block.

## R3: Transverse mode

The planar transverse Hessian block is `-A/2`.  Therefore each
`lambda_i>2` gives a transverse eigenvalue

`nu_i=-lambda_i/2<-1`.

This implication is exact and has no numerical boundary tolerance.

## R4: Allowed degree-minus-one spectrum

The first-variational Morales-Ramis table for a degree-minus-one potential is

`nu=(k-1)*(k+2)/2`, `k in N_0`.

Its sequence begins `-1,0,2,5,9,14,...` and has minimum `-1`.
Consequently `nu_i<-1` is not allowed.

## R5: Galois obstruction

For the excluded scalar NVE value, the pinned classification gives
`SL(2,C)`.  Its identity component is not solvable.

## R6: Restricted-integrability condition

Restricted integrability uses a weaker necessary condition than standard
Liouville integrability: the variational Galois identity component must be
solvable.  The proof applies that condition directly; it does not replace it
with an unproved Abelian requirement.

## R7: Independent equal-mass benchmark

For equal masses at positions `(-a,0,a)` with `a^3=5/4`, the exact
longitudinal pair weights are `8/5,8/5,1/5`.  The independently constructed
matrix has spectrum

`{0,2,24/5}`.

The transverse spectrum is `{0,-1,-12/5}`, reproducing the strict
obstruction.

## R8: SO(3) stratum boundary

The Euler-Moulton orbit is collinear and lies in a singular rotation
orbit-type stratum.  `WP2-SO3-LEAF-v1` covers the regular non-collinear zero
leaf.  This theorem is applied on the translation-reduced planar common
level, not by placing the witness in the regular chart.

## R9: Doubly-zero level

At `(H,C)=(0,0)`, the homothetic variational equations used here are
integrable and provide no obstruction.  The campaign must return
`UNQUALIFIED_DOUBLE_ZERO`.

## R10: Claim discipline

The result concerns restricted rational complete integrability.  It does not
exclude one extra integral, spatial zero momentum, non-rational integrals,
or collision-regularized continuation.

## Model boundary

The model is the planar algebraic-distance extension after center-of-mass
reduction, restricted to `M_(h,0)` with `h!=0` and positive masses.

## Authorized claim

For arbitrary finite positive masses and every finite nonzero energy `h`,
the planar Newtonian three-body problem restricted to `(H,C)=(h,0)` is not
rationally integrable in the locked restricted sense.

## Nonclaims

The track does not qualify `(0,0)`, one-additional-integral absence, a
spatial theorem, non-rational regularity classes, or collision continuation.
