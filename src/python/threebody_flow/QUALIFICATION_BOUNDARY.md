# Three-Body Flow Qualification Boundary

This package implements physical-time dynamics only. The canonical path is the
12-dimensional translation-reduced Newtonian Hamiltonian in Jacobi variables.
The rotation path is the nine-coordinate generic non-collinear SO(3) quotient
together with the discarded body-frame derivative required for reconstruction.
The pairwise path horizontally lifts all three physical relative derivatives
through the qualified zero-Xi KS cotangent map and preserves the redundant
position/velocity closure constraints.

No function in this package assigns three independent Kepler Hamiltonians to a
perturbed three-body state. No function introduces three pair-specific Sundman
times, claims three regular oscillators, or qualifies collision passage. A
single global regularized time transformation would be a separate model and
requires a separate specification.
