# WP2 Interpretation Checks

## Sanity Checks
- Connection coefficients should be finite and stable under small perturbations.
- Curvature matrix should be antisymmetric (F_ij = -F_ji).
- Scalar curvature should be finite and consistent across nearby points.

## Common Caveats
- Curvature magnitude depends on coordinate scaling; compare only within consistent setups.
- JM metric is undefined when E <= V_eff (classically forbidden region).
- Near collisions (small r_ij), numerical derivatives can blow up; prefer KS-regularized analysis.

## Symmetry Cases (Quick Reference)
- Equal masses with equilateral shape often provide stable baselines for checks.
- If symmetry is broken (mass hierarchy), expect anisotropy in curvature and JM metric.
