# WP2-MULTIQ-v1 Model Boundary

This package implements the model frozen in
`validation-external/wp2-multi-validation/qualification_spec.json`.

Each chart contains two canonical KS cotangent lifts, two independent `Xi=0`
momentum-map levels, and their `T^2` quotient. The fixed-energy extended
Hamiltonian uses `dt/ds=r12*r23*r31` in all charts. Three charts cover all
isolated binary collisions.

The package does not regularize triple collision, assert a global SO(3)
quotient, define nonzero-`Xi` physical dynamics, or imply an additional first
integral. Modules under `src/python/regularization` are legacy prototypes and
are not inputs to this model.
