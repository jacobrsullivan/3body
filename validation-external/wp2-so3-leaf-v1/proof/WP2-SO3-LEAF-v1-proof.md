# WP2-SO3-LEAF-v1 proof and evidence map

## R1: Cotangent momentum coordinates

In the body chart

`rho=(r,0,0)`, `lambda=(x,y,0)`,

write `u=p_rho`, `v=p_lambda`, and
`ell=rho cross u + lambda cross v`.  Define

`pr=u1`, `px=v1`, `py=v2`.

The inverse is

`v3=ell_x/y`,

`u3=-(ell_y+x*ell_x/y)/r`,

`u2=(ell_z-x*py+y*px)/r`.

These formulas are exact when `r>0,y>0`.

## R2: Roundtrip and momentum map

Substitution of the inverse gives each original momentum component and
reconstructs all three components of `ell`.  Deterministic qualification
states compare both directions to the existing body-frame quotient.

## R3: Poisson tensor and leaves

The first six coordinates have the canonical tensor.  The body block is

`[[0,-ell_z,ell_y],[ell_z,0,-ell_x],[-ell_y,ell_x,0]]`.

Thus `ell_dot=ell cross dH/dell`.  The tensor is antisymmetric, has rank
eight for `ell!=0`, rank six at `ell=0`, and annihilates
`d(|ell|^2)`.

## R4: Hamiltonian

With reduced masses

`mu_rho=m1*m2/(m1+m2)`,

`mu_lambda=m3*(m1+m2)/(m1+m2+m3)`,

the kinetic energy is

`|u|^2/(2*mu_rho)+|v|^2/(2*mu_lambda)`.

The potential uses pair distances

`r`, `sqrt((x-alpha*r)^2+y^2)`, and
`sqrt((x+beta*r)^2+y^2)`.

It agrees with the qualified 12D Jacobi Hamiltonian after reconstruction.

## R5: Analytic gradient

Production implements all nine analytic derivatives.  The reference
implementation independently reconstructs the momenta and uses centered
finite differences with coordinate scaling.  Every deterministic case must
meet the locked tolerance.

## R6: Hamiltonian flow

Production computes `P(z)*grad(H)`.  A separate path evolves the qualified
12D Jacobi state, pushes that tangent through the moving body frame, and
differentiates the momentum map.  The two nine-dimensional derivatives
agree to the locked tolerance.

## R7: Leaf tangency

The Casimir derivative is zero.  At `ell=0`, the body block and all three
angular-momentum derivatives vanish exactly.  At nonzero momentum the flow
is tangent to the sphere `|ell|=mu`.

## R8: Zero leaf

Setting `ell=0` removes the Lie-Poisson sphere and leaves the six canonical
shape coordinates.  The reconstructed momenta satisfy zero total body
angular momentum by construction.

## R9: Domain rejection

The state contract rejects `r<=0`, `y<=0`, nonfinite coordinates, invalid
masses, and invalid gravity.  The chart therefore never silently selects a
frame at a singular orbit type.

## R10: Chart scope

This is one regular orientation-fixed chart, not a global Darboux atlas.
Collinear configurations and collisions require separate charts or
regularization.

## Model boundary

The regular zero leaf and the singular collinear zero-momentum stratum are
different orbit types.  The `WP6-L0-v1` Euler witness is not inserted into
this chart.

## Authorized claim

The project has an independently qualified explicit Hamiltonian model of
the regular non-collinear SO(3) Poisson quotient, including nonzero and zero
angular-momentum leaves, in the declared body-frame chart.

## Nonclaims

No global atlas, collinear chart, collision regularization, or
integrability conclusion is claimed.
