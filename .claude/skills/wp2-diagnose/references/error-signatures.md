# WP2 Error Signatures

## "Classically forbidden" ValueError
Likely cause: energy E <= V_eff in `compute_jm_metric`.
Check: increase E or choose a shape point with lower V_eff.

## "Planar motion requires z-positions = 0"
Likely cause: mismatch between `dimension=2` and state input.
Fix: zero z-components or set `dimension=3`.

## NaNs in curvature or JM metric
Likely cause: near-collision or invalid finite-difference step.
Fix: move away from r_ij ~ 0, reduce epsilon, or switch to KS-regularized pipeline.

## Connection/curvature instability across nearby points
Likely cause: inconsistent gauge or shape constraint violation.
Fix: enforce triangle inequalities and use canonical orientation.
