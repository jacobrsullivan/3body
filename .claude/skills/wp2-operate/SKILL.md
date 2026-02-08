---
name: wp2-operate
description: >
  Run WP2 computations and workflows: coordinate transforms, reduction, connection/curvature,
  JM metric, lift constructions, and regularization. Use when executing WP2 code, preparing
  inputs/outputs, running WP2 tests, or producing WP2 artifacts for WP3/WP4. Trigger on
  requests to "run WP2", "compute connection/curvature", "build lift", or "validate WP2".
---

# WP2 Operate

## Overview
Execute WP2 workflows and produce reproducible outputs (geometry, lifts, and validations).

## Preflight
- Ensure repo root is the working directory and `PYTHONPATH` includes the repo root.
- Ensure Python environment has `numpy`, `pytest`, and project deps.
- Prefer running from repo root so imports like `src.python.*` resolve cleanly.

## Execution Workflow
1. Build the state and parameters.
   - Masses: `src/python/coordinates/base.py` (`Masses`)
   - State: `src/python/coordinates/cartesian.py` (`CartesianState`) or
     `src/python/coordinates/shape_space.py` (`ShapeSpaceState`)
2. (Optional) Reduce coordinates.
   - Translation: `src/python/reduction/translation_reduction.py`
   - Rotation: `src/python/reduction/rotation_reduction.py`
3. Compute geometry.
   - Connection: `src/python/geometry/connection_form.py`
   - Curvature: `src/python/geometry/curvature_form.py`
   - JM metric and scalar curvature: `src/python/geometry/jm_metric.py`, `src/python/geometry/riemann_curvature.py`
4. Construct lifts (if needed).
   - S1 bundle: `src/python/lifts/s1_bundle.py`, `src/python/lifts/extended_symplectic.py`
   - KS/regularization: `src/python/regularization/ks_transform.py`, `src/python/regularization/sundman.py`
5. Validate with targeted tests.
   - Use `scripts/wp2_run_tests.sh` from this skill for fast or full WP2 test runs.

## Canonical Smoke Run
- Use `scripts/wp2_smoke.py` from this skill to produce a minimal, validated WP2 compute.
- Capture masses, shape state, energy, L, and computed A/F/R values in outputs.

## Tests
- Fast subset: `scripts/wp2_run_tests.sh --fast`
- Full subset: `scripts/wp2_run_tests.sh`

## Output Checklist
- Inputs: masses, coordinate system, energy, L, configuration/state
- Geometry: connection coefficients, curvature magnitude, scalar curvature
- Lift artifacts (if any): lifted Hamiltonian or integrability checks
- Versioning: git SHA or note local modifications when reporting results

## Resources
### scripts/
- `wp2_smoke.py` (minimal operational pipeline)
- `wp2_run_tests.sh` (WP2-focused test runner)

### references/
- `commands.md` (common command recipes and test targets)
