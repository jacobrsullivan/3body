# WP1-CAT-v1 pre-qualification audit

## Existing assets

- `src/python/orbits/differential_correction.py` supplies strict planar and Halo
  symmetry correctors with full-period closure verification.
- `src/python/orbits/periodic_families.py` supplies exact L1/L2 locations and a
  small-amplitude planar center-mode generator.  Its larger-amplitude fallback
  is explicitly an approximation and is not used by WP1-CAT-v1.
- `src/python/validation/cr3bp_variational.py` supplies analytic rotating-frame
  variational equations, monodromy propagation, reciprocal-pair diagnostics,
  and the JPL/Poincare stability index.
- `validation-external/wp1-validation/data/jpl/normalized.parquet` is the pinned
  21,938-row Earth-Moon JPL corpus used by the existing external validation.
- The existing JPL-seeded catalogue accepts 284 of 300 sampled external seeds.
  This validates propagation from external seeds, not native discovery.

## Gap found

The historical native comparison constructs only 40 approximation candidates.
Its recorded median state distance is about 0.837 and median relative period
error about 0.890.  It cannot substantiate native production catalogue claims.

## v1 remediation boundary

WP1-CAT-v1 replaces that comparison with analytic external-free seeds,
sequential fixed-section continuation, strict correction, invariant
deduplication, and blinded external recovery.  The windows are intentionally
bounded to branch segments traversed robustly by this parameterization; v1 does
not hide the absence of pseudo-arclength continuation or global family logic.
