# WP6-L0-v1 qualification boundary

## Authorized result

For arbitrary finite positive masses and every finite nonzero energy `h`, the
planar Newtonian three-body problem restricted to the common level
`(H,C)=(h,0)` is not rationally integrable in the restricted sense defined in
the pinned 2025 theorem.

The project-owned certificate reproduces the exact spectral implication:

1. the Euler-Moulton longitudinal Hessian has an eigenvalue `lambda>2`;
2. the planar transverse block has eigenvalue `-lambda/2<-1`;
3. every degree-minus-one Morales-Ramis table value
   `(k-1)(k+2)/2`, `k in N_0`, is at least `-1`;
4. the scalar NVE therefore has Galois group `SL(2,C)`;
5. its identity component is not solvable, violating the necessary condition
   for restricted integrability.

An independent exact equal-mass Euler calculation gives
`lambda=24/5` and transverse eigenvalue `-12/5`.

## Model connection

`WP2-SO3-LEAF-v1` qualifies the regular non-collinear `ell=0` leaf.  The
Euler-Moulton witness here is collinear and belongs to a singular SO(3)
orbit-type stratum.  The theorem is bound to the translation-reduced planar
common-level model directly; it is not represented as a trajectory inside
the regular SO(3) chart.

## Exclusions

This track does not prove:

- nonintegrability on `(H,C)=(0,0)`;
- absence of one additional integral;
- a spatial zero-angular-momentum theorem;
- absence of non-rational integrals;
- continuation through collision;
- a global chart containing the Euler-Moulton orbit.

At the doubly-zero level the homothetic variational equations used here are
integrable, including at higher orders in the pinned analysis.  A different
explicit witness or a different obstruction is required.
