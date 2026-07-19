# WP1 External Validation Report

Generated: 2026-07-19T18:35:27.604252+00:00

## Tier 1 Validation
```
WP1 Tier 1 Validation Report
============================================================

Total orbits: 30
Target accuracy: 1e-14

Jacobi Constant Precision:
  Mean drift: 2.88e-15
  Median drift: 4.59e-16
  95th percentile: 1.20e-14
  Max drift: 2.94e-14

Pass rate (< 1e-14): 93.3%

Chaos Classification:
  Regular: 22 (73.3%)
  Chaotic: 7 (23.3%)

```

## Tier 2 Validation
```
WP1 Tier 2 Validation Report
============================================================

Total orbits: 3
Target accuracy: 1e-25
Integrator(s): HeyokaTaylor
Precision: heyoka-real
Precision backend(s): heyoka.real
Precision bits: 160

Jacobi Constant Precision:
  Mean drift: 5.27e-28
  Median drift: 4.83e-28
  95th percentile: 6.36e-28
  Max drift: 6.53e-28

Pass rate (< 1e-25): 100.0%

Chaos Classification:
  Regular: 3 (100.0%)
  Chaotic: 0 (0.0%)

```

## Publication-Readiness Interpretation

Current evidence supports WP1 environment setup, acceptance tests, and bounded integrator-validation claims, including the Tier 2 heyoka.real smoke run. It does not yet support publication claims for a production WP1 periodic-orbit catalogue.

The strongest positive evidence below is the JPL initial-condition cross-check, which isolates integrator behavior from candidate generation. The JPL-seeded validation catalogue is publishable only as an external-seeded catalogue. The native-candidate quality, reversibility, and convergence sections are candidate-library diagnostics; their current failures are publication blockers for native WP1 catalogue claims unless that paper scope is narrowed to infrastructure/methods and external/JPL-seeded validation.

## JPL Cross-Check Summary
*300 orbits sampled from 21938 total JPL orbits (max_jpl=300), matched against 40 WP1 candidates.*

### Integrator Accuracy

Measures IAS15 performance on **JPL initial conditions** (converged periodic orbits). This is the cleanest integrator evidence because it does not depend on WP1 candidate generation.

| Metric | Count | Median | P95 | Max |
|--------|------:|-------:|----:|----:|
| Closure error (||x(T) - x(0)||) | 300 | 2.30e-11 | 1.17e-08 | 3.18e-07 |
| Jacobi drift (|C(T) - C(0)|) | 300 | 4.44e-16 | 3.60e-14 | 1.60e-13 |

### Native Candidate Quality

Measures geometric distance between WP1 native candidate ICs (corrected small-amplitude Lyapunov seeds plus simplified Halo seeds) and JPL converged ICs. This is a candidate-library quality gate, not an integrator test. Large distances or period errors mean the native WP1 catalogue is not publication-ready.

| Metric | Count | Median | P95 | Max |
|--------|------:|-------:|----:|----:|
| State distance (||x_WP1 - x_JPL||) | 300 | 8.37e-01 | 2.91e+00 | 4.04e+00 |
| Jacobi constant delta (|C_WP1 - C_JPL|) | 300 | 7.75e-02 | 4.53e-01 | 6.58e-01 |
| Period error (|T_WP1 - T_JPL| / T_JPL) | 300 | 8.90e-01 | 9.10e-01 | 9.17e-01 |

## JPL-Seeded Validation Catalogue

This artifact validates normalized JPL periodic-orbit initial conditions with the WP1 IAS15 stack and writes an accepted-only Parquet catalogue. It is suitable for external-seeded validation claims, not for claims that WP1 generated those periodic seeds.

*Accepted 284 of 300 sampled JPL seeds (94.7%) from 21938 total records.*

Thresholds: closure <= 1e-08, absolute Jacobi drift <= 1e-12; integrator: IAS15 at tolerance 1e-14.

Accepted catalogue: `../results/jpl_seeded_catalog.parquet`

### Accepted Catalogue Metrics

| Metric | Count | Median | P95 | Max |
|--------|------:|-------:|----:|----:|
| Closure error (||x(T) - x(0)||) | 284 | 2.01e-11 | 9.73e-10 | 6.23e-09 |
| Jacobi drift (|C(T) - C(0)|) | 284 | 4.44e-16 | 9.50e-15 | 3.64e-14 |

### Accepted Catalogue Groups

| Family | L-point | Branch | Count |
|--------|---------|--------|------:|
| halo | L1 | N | 78 |
| halo | L1 | S | 78 |
| halo | L2 | N | 21 |
| halo | L2 | S | 21 |
| lyapunov | L1 | - | 43 |
| lyapunov | L2 | - | 43 |

## Extended Precision Summary
See `../results/extended_precision_summary.csv` for full details.

## Reversibility Test

This diagnostic integrates WP1 candidates forward, applies the CR3BP rotating-frame reversing symmetry, and checks whether the trajectory recovers its initial position. Short-time results test the symmetry and integrator plumbing; long-time results are a stress diagnostic in unstable orbit neighborhoods.

| Fwd Time | N | Med Pos RMS | P95 Pos RMS | Max Pos RMS | Tier1 Pass |
|----------|--:|------------:|------------:|------------:|-----------:|
| T_1 | 20 | 2.64e-16 | 3.81e-15 | 6.46e-15 | 100% |
| T_10 | 20 | 1.22e-14 | 3.53e-07 | 6.40e-06 | 45% |
| T_50 | 20 | 2.06e-13 | 5.30e-02 | 8.93e-01 | 5% |

## Convergence Order Test

Sweeps IAS15 tolerance from 1e-8 to 1e-14 on corrected small-amplitude L1/L2 Lyapunov seeds and measures one-period closure/Jacobi behavior. When the closure values sit near the corrected-seed or machine-precision floor, the fitted slope is a floor diagnostic, not an empirical order proof.

*Scope: corrected_small_amplitude_lyapunov (10 orbits, amplitudes [0.02, 0.14]).*

| Tolerance | N | Med Closure | P95 Closure | Med Jacobi | P95 Jacobi |
|-----------|--:|------------:|------------:|-----------:|-----------:|
| tol_1e-08 | 10 | 1.02e-12 | 1.12e-11 | 1.47e-16 | 3.08e-16 |
| tol_1e-09 | 10 | 1.02e-12 | 1.12e-11 | 1.47e-16 | 3.08e-16 |
| tol_1e-10 | 10 | 1.02e-12 | 1.12e-11 | 1.47e-16 | 3.08e-16 |
| tol_1e-11 | 10 | 1.02e-12 | 1.12e-11 | 1.53e-16 | 3.08e-16 |
| tol_1e-12 | 10 | 1.02e-12 | 1.12e-11 | 1.53e-16 | 3.08e-16 |
| tol_1e-13 | 10 | 1.02e-12 | 1.12e-11 | 1.53e-16 | 3.08e-16 |
| tol_1e-14 | 10 | 1.02e-12 | 1.12e-11 | 1.47e-16 | 3.06e-16 |

**Estimated convergence order (slope):** 0.00

**Interpretation:** closure_floor_limited; slope is not an empirical integrator order

## Artifact Manifest
Checksum and provenance manifest: `wp1_artifact_manifest.json`. It is generated as the final `run_validation.sh` phase so it can hash the completed report.

## Chaos Maps