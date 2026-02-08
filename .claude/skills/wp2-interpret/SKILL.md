---
name: wp2-interpret
description: >
  Interpret WP2 outputs and results: connection/curvature values, JM metric and scalar curvature,
  lift integrability checks, and comparisons between S1 and KS constructions. Use when asked to
  explain what WP2 numbers mean, assess integrability/chaos indicators, or summarize WP2 outcomes.
---

# WP2 Interpret

## Overview
Translate WP2 outputs into clear, defensible conclusions and next steps.

## Interpretation Workflow
1. Confirm inputs: masses, coordinate system, energy, angular momentum, and shape state.
2. Check validity: triangle inequality, classically allowed region (E > V_eff), and finite values.
3. Interpret each output in context (connection/curvature, JM metric, lifts).
4. Cross-check against known tests or symmetry cases.
5. Summarize implications for WP3 (upstairs integrability search).

## Connection and Curvature
- Non-zero curvature (|F| > tolerance) indicates a geometric obstruction to integrability downstairs.
- Curvature magnitude is scale-dependent; compare across consistent normalization or within the same dataset.
- Flatness (`CurvatureForm.is_flat`) is a strong signal, but confirm numerical stability and epsilon settings.

## JM Metric and Scalar Curvature
- R < 0 suggests local exponential divergence (chaos signature).
- R > 0 suggests locally stable/elliptic behavior.
- Near E ≈ V_eff, the metric degenerates; treat results with caution.

## Lift Constructions
- S1 lift: look for conservation of fiber momentum and involution with Hamiltonian.
- KS lift: check constraint preservation and regularized behavior near collisions.
- Compare S1 vs KS outcomes to decide if additional regularization is required.

## Reporting Template (Concise)
```
Inputs: masses=[...], energy=..., L=..., coordinates=...
Geometry: |F|=..., flat? ..., scalar curvature R=...
Interpretation: obstruction present? chaos signal? caveats?
Lift status: S1 integrability check=..., KS constraint/regularization=...
Next: recommend WP3 invariant search / revisit parameters / run tests
```

## References
- `User-Guides/User-Guide-WP2.md` (tests + workflows)
- `tests/geometry/test_connection.py`, `tests/geometry/test_jm_metric.py`
- `tests/lifts/test_integrability.py`, `tests/lifts/test_s1_bundle.py`
- `tests/regularization/test_time_regularization.py`

## Resources
### references/
- `interpretation-checks.md` (sanity checks and common caveats)
