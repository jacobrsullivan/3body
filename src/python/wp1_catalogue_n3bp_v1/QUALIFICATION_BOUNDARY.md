# WP1-CAT-N3BP-v1 Qualification Boundary

This package implements the native candidate generator for the locked
`WP1-CAT-N3BP-v1` campaign.

## In Scope

- The unsoftened Newtonian three-body equations with `G=1` and `m3=1`.
- The connected planar `bABabaBAba` family on the locked 13 by 13 ordered
  `(m1,m2)` grid from 0.970 through 1.030.
- Correction of one disclosed rounded equal-mass root, followed by signed
  secant continuation first along `m1` at `m2=1`, then independently along
  `m2` for each corrected `m1` row.
- Full labelled 18D barycentric inertial states and positive physical periods.
- Planar linear stability after translation reduction, subject to the locked
  ambiguity guard.

Row-level workers only schedule already-defined `m2` continuation lines. They
do not change predictors, parentage, correction order within a line, or output
ordering.

## External-Data Boundary

The generator accepts no source table, external row, corpus, or seed-file
argument. Its only non-native initial datum is the rounded equal-mass root
embedded in `model.py` and disclosed by the qualification specification.
External SJTU rows enter only after the native catalogue payload receives its
separate candidate lock.

## Out of Scope

The package does not independently discover the root, enumerate other
topologies or disconnected branches, qualify spatial or nonlinear stability,
cross collisions, handle folds with pseudo-arclength continuation, or claim a
complete/general three-body catalogue.
