# WP2-UP-v1 Model Boundary

This package defines a canonical 14-dimensional fixed-energy KS lift of the
translation-reduced Newtonian three-body problem.  It regularizes the selected
`rho = x2 - x1` binary channel, preserves the KS `S1` momentum map, and projects
from `K_h = Xi = 0` to the physical Jacobi Hamiltonian flow with
`dt/ds = |q|^2`.

It does not regularize the other two binary channels or triple collision.  It
does not assert that the redundant three-pair KS representation is a global
symplectic manifold, that any new first integral exists, or that the lifted
system is Liouville integrable.  Those require separate qualifications.
