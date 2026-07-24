# WP6-DZ-FEAS-v1 plan

Date: 2026-07-24

## Objective

Run a bounded, fail-closed search for an explicit non-equilibrium algebraic
phase curve on the planar Newtonian three-body common level

`(H,C)=(0,0)`

that is suitable for a Morales-Ramis or Ziglin obstruction.

The campaign closes only the feasibility question. It does not claim
nonintegrability. `WP6-DZ-MR-v1` may begin only if the frozen feasibility
record contains a fully qualified witness.

## Why a separate feasibility gate is required

`WP6-COMMON-v1` qualifies every finite real common level except `(0,0)`.
Its pinned sources state that the known zero-energy, zero-angular-momentum
homothetic variational equations are integrable, including at higher order,
and that a different explicit orbit is required.

An unbounded orbit search would make a negative conclusion meaningless.
The candidate classes, literature protocol, witness requirements, source
budget, and stop rule are therefore locked before any new search.

## Success standard

A witness must:

- solve the full planar Newtonian three-body equations exactly;
- lie exactly on `H=C=0`;
- be nonstationary and not merely the known homothetic
  central-configuration curve;
- work for arbitrary finite positive masses or provide a finite exhaustive
  mass-branch cover;
- define an algebraic phase curve over a declared differential field;
- lie on a generically smooth common level;
- admit an exact tangent common-level VE and a nontrivial NVE;
- avoid collision singularities or carry a proved meromorphic
  regularization and exact pullback;
- be reproduced by a source-disjoint exact implementation.

Numerical trajectories, asymptotic expansions, restricted problems,
special-mass-only examples, and unregularized collision curves cannot pass.

## Outcomes

- `QUALIFIED_WITNESS`: every locked witness requirement passes.
- `COMPLETE_BOUNDED_NULL_RESULT`: the entire locked search is complete and
  no candidate passes every requirement.
- `INCOMPLETE`: any search class, query, exact audit, or source record is
  missing.

Only `QUALIFIED_WITNESS` authorizes creation of `WP6-DZ-MR-v1`.

## Completion sequence

1. Commit the specification and discovery protocol.
2. Generate and commit the pre-discovery lock.
3. Execute the bounded primary-source search.
4. Build the candidate ledger and exact negative controls.
5. Qualify one witness or seal the bounded null result.
6. Open `WP6-DZ-MR-v1` only on qualified success.
7. Regress, document, commit, and push.
