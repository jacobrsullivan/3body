# WP6-DZ-FEAS-v2 plan

## Purpose

`WP6-DZ-FEAS-v1` ended with the qualified bounded result
`WP6-DZ-FEAS-v1-8609fd37a8d6`: the inspected literature contains
nonhomothetic solutions on `(H,C)=(0,0)`, but no explicit algebraic phase
curve suitable for a candidate-specific Morales-Ramis or Ziglin analysis.

Version 2 is constructive. It does not repeat or expand the v1 literature
search. It searches a frozen finite family of exact rational/Puiseux graphs
inside the arbitrary-mass rectilinear zero-energy flow.

## Locked model

Fix one ordered chamber `q1 < q2 < q3` and define

```text
a = q2-q1
b = q3-q2
r = a+b
x = a/r
v = sqrt(r) dr/dt
u = r^(3/2) dx/dt
d/dtau = r^(3/2) d/dt.
```

The physical chamber has `r>0` and `0<x<1`. Relabeling the masses covers the
six order chambers. Collinearity gives `C=0` identically.

The exact reduced vector field, energy numerator, covers, support library,
mass/order sentinels, coefficient-ideal algorithm, and stop rules are fixed
in `validation-external/wp6-dz-feas-v2/constructive_protocol.json`.

## Search boundary

The campaign searches graphs

```text
x = phi(z)
v = sum(alpha_j z^j)
u = sum(beta_j z^j)
```

on four fixed rational shape covers. Each support is a nonempty subset of
`{-2,-1,0,1,2}` with at most two exponents. Exact support is enforced by
saturation, so a coefficient cannot silently vanish into a previously
searched template.

There are exactly:

- 4 shape covers;
- 15 admissible supports for `v`;
- 15 admissible supports for `u`;
- 13 exact mass/order sentinels; and
- 11,700 coefficient ideals.

No degree increase, new cover, new denominator, new sentinel, numerical fit,
or post-result ansatz change is permitted in v2.

## Outcomes

`QUALIFIED_WITNESS` requires a candidate to pass W1-W12, including an exact
arbitrary-positive-mass extension or a finite exhaustive mass-branch proof.
A special-mass graph is a partial candidate only.

`COMPLETE_BOUNDED_NULL_RESULT` requires all 11,700 ideals to be decided,
every non-unit ideal to be audited, all exact controls and the independent
derivation to pass, and no W1-W12 witness.

Any timeout, undecided ideal, missing source, changed frozen input, or
unresolved branch gives `INCOMPLETE`.

## Conditional promotion

`WP6-DZ-MR-v1` may be created only from a signed `QUALIFIED_WITNESS` record
that names exactly one frozen full-system witness. Every other result
prohibits promotion.

