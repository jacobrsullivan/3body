---
name: wp2-diagnose
description: >
  Diagnose WP2 failures and anomalies: import issues, NaNs, invalid shapes, failed tests,
  regularization breakdowns, and traceability of WP2 runs. Use when debugging WP2 pipelines,
  interpreting stack traces, or performing triage on WP2 test failures.
---

# WP2 Diagnose

## Overview
Provide a structured triage flow for WP2 failures and numerical pathologies.

## Triage Flow
1. Capture a minimal reproduction: masses, state, coordinate system, energy, L, and the exact call.
2. Run `scripts/wp2_triage.py` to validate imports and a minimal geometry compute.
3. Run targeted tests (see `references/triage-tests.md`).
4. Inspect the failing module(s) and error location.
5. Summarize the root cause and proposed fix or workaround.

## Common Failure Modes
- **Invalid shape**: triangle inequality violated in `ShapeSpaceState`.
- **Classically forbidden region**: E <= V_eff in JM metric.
- **Near-collision instability**: r_ij -> 0 causing division or derivative blow-ups.
- **Dimension mismatch**: planar vs spatial confusion (dimension=2 but z != 0).
- **Constraint drift**: KS/Sundman regularization without constraint enforcement.

## Debugging Techniques
- Use `numpy.seterr(all="raise")` for fast detection of NaN/inf.
- Add local prints around `compute_connection_coefficients` and `compute_curvature`.
- Reduce epsilon in curvature to test sensitivity.
- Validate `Masses` and `ShapeSpaceState.validate()` before geometry calls.

## Escalation Guide
- If geometry tests fail: focus on `src/python/geometry/*` and `tests/geometry/*`.
- If lift tests fail: focus on `src/python/lifts/*` and `tests/lifts/*`.
- If KS regularization fails: focus on `src/python/regularization/*` and `tests/regularization/*`.

## Resources
### scripts/
- `wp2_triage.py` (import + minimal compute validation)

### references/
- `triage-tests.md` (targeted test commands)
- `error-signatures.md` (symptoms and likely causes)
