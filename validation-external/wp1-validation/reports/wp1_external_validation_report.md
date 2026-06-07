# WP1 External Validation Report

Generated: 2026-02-15T04:35:54.052971+00:00

## Tier 1 Validation
```
WP1 Tier 1 Validation Report
============================================================

Total orbits: 30
Target accuracy: 1e-14

Jacobi Constant Precision:
  Mean drift: 3.13e-15
  Median drift: 1.23e-15
  95th percentile: 1.46e-14
  Max drift: 1.89e-14

Pass rate (< 1e-14): 90.0%

Chaos Classification:
  Regular: 22 (73.3%)
  Chaotic: 7 (23.3%)

```

## Tier 2 Validation
```
(missing)
```

## JPL Cross-Check Summary
*300 orbits sampled from 21938 total JPL orbits (max_jpl=300), matched against 40 WP1 candidates.*

### Integrator Accuracy

Measures IAS15 performance on **JPL initial conditions** (converged periodic orbits). Isolates integrator quality.

| Metric | Count | Median | P95 | Max |
|--------|------:|-------:|----:|----:|
| Closure error (||x(T) - x(0)||) | 300 | 2.30e-11 | 1.24e-08 | 3.17e-07 |
| Jacobi drift (|C(T) - C(0)|) | 300 | 4.44e-16 | 4.87e-14 | 2.59e-13 |

### Richardson Approximation Quality

Measures geometric distance between WP1 Richardson 3rd-order ICs and JPL converged ICs. No integration — purely geometric comparison.

| Metric | Count | Median | P95 | Max |
|--------|------:|-------:|----:|----:|
| State distance (||x_WP1 - x_JPL||) | 300 | 7.95e-01 | 2.52e+00 | 2.72e+00 |
| Jacobi constant delta (|C_WP1 - C_JPL|) | 300 | 1.37e-01 | 4.53e-01 | 6.58e-01 |
| Period error (|T_WP1 - T_JPL| / T_JPL) | 300 | 9.09e-01 | 9.63e-01 | 9.66e-01 |

## Extended Precision Summary
See `../results/extended_precision_summary.csv` for full details.

## Chaos Maps
