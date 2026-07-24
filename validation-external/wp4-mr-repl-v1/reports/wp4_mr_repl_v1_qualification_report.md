# WP4-MR-REPL-v1 Qualification Report

**Status:** PASS

**Qualification ID:** `WP4-MR-REPL-v1-2ea23024c64b`

## Qualified Result

The project independently reproduces, from the declared reduced Newtonian Hamiltonian and exact parabolic Lagrange phase curve, a 4x4 Fuchsian normal variational equation whose differential-Galois identity component is non-Abelian for every finite positive mass triple. By the pinned Morales-Ramis theorem, the declared translation- and rotation-reduced planar positive-mass Newtonian three-body Hamiltonian at fixed nonzero angular momentum is not completely integrable by meromorphic first integrals in a complex neighborhood of that phase curve.

- Exact generic Hamiltonian-to-NVE replay: PASS
- Exact specialized benchmarks: 4/4
- Production/reference exact agreement: PASS
- Positive-mass exceptional set for complete integrability: empty
- Theorem obligations: 10/10
- Adversarial controls rejected: 9/9

## Claim Boundary

A PASS is a project-owned exact reproduction of the local planar Morales-Ramis obstruction. It starts from the explicitly declared reduced Newtonian Hamiltonian and independently differentiates it; it does not independently reconstruct every canonical translation/rotation coordinate map from the unreduced 18-dimensional state. It proves no absence of individual additional first integrals, no non-meromorphic obstruction, no zero-angular-momentum theorem, no spatial theorem without the separately qualified WP4-LIFT-NI-v3 transfer, no global orbit classification, no catalogue completeness, and no statement about triple collision.

## Prohibited Summaries

- The three-body problem has no integrals.
- The project independently rederived every canonical reduction from the unreduced 18-dimensional Hamiltonian.
- The local phase-curve obstruction classifies all trajectories or all regularity classes.

## Integrity

- Evidence commit: `17f34f83bc914332fb468497ee9401018c9bbda8`
- Qualification lock: `35f7dcfe223dbe87775f11c6e31043c1b1ead02850d6f21ccb8e84a3b4406abb`
- Results SHA-256: `a2934f78647ad31bd91dfc72ed3f5f7ad78a7278dd807f1d0d424148db506ff0`
- Proof SHA-256: `3cf75bd36925c296c69d302c2d7e229b1eb9da5928aa9690a7f06545c77104cc`
- Record payload SHA-256: `2bfad5976b806d89d075bbbefe08f50680a8e677193b3b82cc3488e82082b951`
