# WP2 Command Recipes

## Core WP2 Tests (from User Guide)
- All WP2 tests:
  - `pytest tests/unit/reduction/ tests/geometry/ tests/lifts/ -v`
- Coordinate transformations:
  - `pytest tests/unit/reduction/test_translation_reduction.py -v`
- Connection & curvature:
  - `pytest tests/geometry/test_connection.py -v`
- JM metric:
  - `pytest tests/geometry/test_jm_metric.py -v`
- S1 bundle:
  - `pytest tests/lifts/test_s1_bundle.py -v`
- Integration reduction:
  - `pytest tests/integration/reduction/test_full_reduction.py -v`

## Regularization and Symbolic Lifts
- KS symbolic validation:
  - `pytest tests/symbolic_lifts/test_ks_symbolic.py -v`
- Time regularization:
  - `pytest tests/regularization/test_time_regularization.py -v`

## Visualizations (if needed)
- Connection plots: `src/python/visualization/connection_plots.py`
- Curvature plots: `src/python/visualization/curvature_plots.py`
- JM metric plots: `src/python/visualization/metric_plots.py`
