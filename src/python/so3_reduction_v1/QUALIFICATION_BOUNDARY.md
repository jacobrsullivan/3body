# WP2-SO3-LEAF-v1 qualification boundary

## Qualified model

The implementation is an explicit Hamiltonian model of the regular
translation- and SO(3)-reduced Newtonian three-body problem in the chart

`rho=(r,0,0), lambda=(x,y,0), r>0, y>0`.

Its coordinates are

`(r,x,y,pr,px,py,ell_x,ell_y,ell_z)`.

The shape variables are canonical.  Body angular momentum has the minus
Lie-Poisson bracket, with equation

`ell_dot = ell cross dH/dell`.

For `ell!=0`, fixing `|ell|=mu` gives an eight-dimensional symplectic leaf
`T*B x S^2_mu`.  For `ell=0`, the leaf is the six-dimensional canonical
space `T*B`.

## Authorized claim

A passing locked campaign authorizes the claim that this chart, its momentum
map and inverse, Poisson tensor, Newtonian Hamiltonian, analytic gradient, and
Hamiltonian flow have been independently qualified against the existing
qualified Jacobi quotient and flow.

## Exclusions

This is not:

- a global quotient atlas;
- a chart at `rho=0` or at collinearity `y=0`;
- a collision regularization;
- a treatment of singular SO(3) orbit types;
- a claim that all nine coordinates are canonical Darboux coordinates;
- a proof of integrability or nonintegrability.

The regular `ell=0` leaf does not contain the collinear Euler-Moulton witness
used by `WP6-L0-v1`.  That theorem is connected at the model-boundary level,
not by pretending the witness lies in this chart.
