# WP1-CAT-v1 qualification plan

## Frozen objective

Qualify a bounded, native, external-seed-free periodic-orbit catalogue path for
the Earth-Moon planar Lyapunov L1 and L2 family segments declared in the locked
specification.  The campaign tests generation, sequential correction,
canonical-section deduplication, JPL recovery, Floquet labels, provenance, and
measured throughput.

## Leakage controls

1. The native generator has no external-corpus input.
2. Candidate generation and the qualification lock occur before any external
   split is evaluated.
3. Corpus partitions are deterministic, disjoint, and balanced by L-point.
4. Holdout execution requires a valid lock plus PASS records for development
   and calibration.
5. The holdout result and final qualification record refuse overwrite.

## Execution order

1. Build the pinned, amplitude-window-filtered JPL corpus and partition it.
2. Generate the native catalogue without loading that corpus.
3. Freeze the specification, implementation, dependencies, corpus, source,
   candidate catalogue, runner, and provenance into one qualification lock.
4. Execute development and calibration; do not change thresholds.
5. Execute holdout only if both prior splits pass.
6. Write an immutable PASS or FAIL record and a claim-bounded report.

## Explicit exclusions

No completeness, Halo, spatial, bifurcation, fold traversal, disconnected
family discovery, all-system production, long-horizon stability, or general
three-body catalogue claim is made by v1.
