# WP1 External Qualification Plan

Date: 2026-07-19

Authoritative checkout: `/Users/bob/Desktop/3body`

## Objective

Substantiate this bounded claim with an external, versioned data source and a
locked holdout decision:

> WP1 is qualified for normalized rotating-frame CR3BP propagation against
> externally sourced JPL periodic-orbit data across the declared systems,
> Lyapunov and Halo families, published stability regimes, and float64/high-
> precision validation tiers. Qualification includes independent arbitrary-
> precision checkpoint propagation, invariant and reversibility checks,
> analytic STM/Floquet validation, strict representative differential
> correction, output-schema enforcement, and a locked holdout suite.

This is a qualification of the WP1 numerical and reconstruction methods. It is
not a claim that WP1 natively generates a production periodic-orbit catalogue.
It also excludes universal correctness, production-scale Tier 2 throughput,
10^4-10^6-period accuracy, regularized close-encounter switching, and validated
MEGNO/FLI labels.

## External Evidence

- Source: NASA/JPL Three-Body Periodic Orbits API, required API version `1.0`.
- Systems: Sun-Earth, Jupiter-Europa, Saturn-Titan, Earth-Moon.
- Families: Lyapunov L1/L2 and Halo L1/L2 north/south.
- Source snapshot: 67,218 records in four content-addressed raw payloads.
- Qualification corpus: 400 records, balanced at 100 per system.
- Stability strata: marginal, weakly unstable, moderately unstable, strongly
  unstable.
- Split: 240 development, 80 calibration, 80 locked holdout records.
- Stable IDs derive from the source values and API version. Raw files, corpus,
  split assignments, and result files are SHA-256 addressed.

The pinned source snapshot under
`validation-external/wp1-validation/data/qualification` is a publication input.
It is versioned so reproduction does not depend on the future contents of the
live JPL API.

## Qualification Methods

1. Propagate every split record for one published period with the WP1 REBOUND
   IAS15 path and measure catalogue Jacobi agreement, maximum Jacobi drift,
   coordinate-frame roundtrip, and CR3BP reversing-symmetry error.
2. Compare a deterministic, stratified subset against a separately encoded
   224-bit `heyoka.real` adaptive Taylor implementation at nine checkpoints.
3. Integrate the state and analytic 6x6 STM together, compute monodromy/Floquet
   multipliers, and compare the JPL/Poincare stability index and classification.
4. Perturb external Lyapunov and Halo seeds, run strict symmetry-based
   differential correction with no fallback, and independently verify
   full-period closure.
5. Require every method-level subset to cover all four systems, both families,
   and all four stability regimes.
6. Require qualified HDF5/Parquet artifacts to retain float64 state columns,
   decimal high-precision state columns for Tier 2, and immutable qualification
   identifiers and hashes.

Published decimal seeds that pass within a physical secondary are retained in
propagation, oracle, and stability evidence. They are excluded only from the
neighbor-reconstruction subset because an unregularized differential corrector
is not a physical interior-body model.

## Locked Decision Protocol

1. Fetch and preserve the external source snapshot.
2. Build deterministic development, calibration, and holdout assignments.
3. Develop the implementation and thresholds using development data only.
4. Confirm the fixed thresholds on calibration data.
5. Commit the code, specification, source snapshot, corpus, and all pre-holdout
   result files.
6. Create a repository-relative lock that hashes the complete numerical source,
   qualification scripts, environment locks, external snapshot, corpus,
   holdout IDs, tests, and passing development/calibration evidence.
7. Verify the lock before any holdout calculation, execute the holdout exactly
   once, and evaluate it without threshold or code changes.
8. Generate a machine-readable qualification record and human-readable report.
9. Regenerate bounded Tier 1/Tier 2 artifacts and verify their qualification
   metadata and numeric schema.
10. Run bounded Linux/amd64 parity and the canonical macOS/arm64 acceptance gate.

Any change to a locked numerical input after step 6 invalidates the campaign.
A failed holdout remains a failed result; it cannot be repaired by changing a
gate and reusing the same holdout.

## Pre-Holdout Status

- Development: PASS, 39/39 gates.
- Calibration: PASS, 39/39 gates.
- Development cases: 240 float64, 36 oracle, 48 stability, 40 reconstruction.
- Calibration cases: 80 float64, 20 oracle, 24 stability, 24 reconstruction.
- Stability classification accuracy: 100% on both pre-holdout splits.
- Reconstruction success: 100% on both pre-holdout splits.
- Canonical bobs-mini acceptance gate: 843 tests collected, 104 focused WP1
  tests passed, and 2/2 QD CTests passed.
- No holdout output existed when this status was recorded.

## Final Evidence Paths

- Specification: `validation-external/wp1-validation/qualification_spec.json`
- Runner: `validation-external/wp1-validation/run_qualification.sh`
- Source/corpus: `validation-external/wp1-validation/data/qualification/`
- Split results: `validation-external/wp1-validation/results/qualification/`
- Freeze lock: `validation-external/wp1-validation/reports/wp1_qualification_lock.json`
- Decision report: `validation-external/wp1-validation/reports/wp1_qualification_report.md`
- Machine record: `validation-external/wp1-validation/reports/wp1_qualification_record.json`

## Downstream Rule

No production HDF5 or Parquet artifact may be represented as qualified unless
the qualification record is present and has status `PASS`. Writers reject a
missing, failed, or integrity-invalid record. Qualified artifacts embed the
qualification ID, lock hash, and exact qualification-record file hash.
