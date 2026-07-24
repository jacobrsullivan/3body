# WP6-DZ-FEAS-v1 Qualification Boundary

This module supports a bounded witness-feasibility campaign on the full planar
Newtonian three-body common level `(H,C)=(0,0)`.

It can certify one of three outcomes:

- `QUALIFIED_WITNESS`: exactly identified algebraic phase-curve evidence passes
  every locked `W1`-`W12` requirement.
- `COMPLETE_BOUNDED_NULL_RESULT`: the locked queries, candidate classes,
  citation expansion, exact controls, and integrity checks are complete, but no
  candidate passes every requirement.
- `INCOMPLETE`: some locked obligation is missing or invalid.

A bounded null result is not a proof that no suitable orbit exists. It does not
prove nonintegrability on `(H,C)=(0,0)`, does not transfer the ambient
one-additional-integral theorem to the common level, and does not authorize a
Morales-Ramis or Ziglin conclusion.

The known parabolic central-configuration curve is exact and algebraic, but it
is homothetic. Its tangent common-level variational equations are the
obstruction-free case that motivated this campaign. Numerical trajectories,
restricted or modified models, special-mass-only formulas, and unregularized
collision curves are not substitutes.

`WP6-DZ-MR-v1` may be created only from a signed `QUALIFIED_WITNESS` record
that freezes exactly one witness payload. A `COMPLETE_BOUNDED_NULL_RESULT` or
`INCOMPLETE` record explicitly prohibits that promotion.
