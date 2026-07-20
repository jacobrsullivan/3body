# Three-Body Reduction Boundary

This package implements a canonical Jacobi translation reduction and a generic
body-frame chart on the SO(3) orbit quotient of the qualified 18D Newtonian
three-body state.

The translation quotient is a 12D canonical phase space. The combined
translation-and-rotation representation is a 9D Poisson quotient. At nonzero
angular-momentum magnitude its generic symplectic leaves are 8D; the zero
momentum leaf is 6D. The body-frame momenta are quotient coordinates, not a
claim that the nine-coordinate chart is Darboux.

The SO(3) chart excludes binary collision and collinear configurations. Those
are singular orbit-type strata and require separate charts. Reconstruction
metadata is not part of the quotient state.

This package does not implement reduced Hamilton equations, a mechanical
connection, collision regularization, orbit discovery, continuation, or a
periodic-orbit catalogue.
