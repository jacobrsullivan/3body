# WP3-MULTI-CAND-v1 bobs-mini Parity

Date: 2026-07-21

The clean `/Users/bob/Desktop/3body` checkout on `bobs-mac-mini` was
fast-forwarded to `d7ba233f2191442a6ce658f5c4443915d24a713f`.

The host verified all three frozen campaign-chain locks:

- `WP1-CAT-N3BP-v1-605c6dbd59d1` (52 frozen files)
- `WP2-MULTIQ-v1-72c81d86644a` (66 frozen files)
- `WP3-MULTI-CAND-v1-225359a13711` (104 frozen files)

The focused WP3 multi-chart suite passed 9/9 tests. The broader dependency
chain passed 235/235 tests in 10.41 seconds. The checkout remained clean after
verification.

## Runtime

- Python 3.11.15
- macOS 26.5.2 arm64
- NumPy 2.2.6
- SciPy 1.16.1
- pytest 8.4.1
- REBOUND 4.4.10
- JAX/JAXLIB 0.9.0.1

This runtime does not match the frozen decision runtime of Python 3.13.2,
NumPy 2.3.5, and SciPy 1.16.3. The numerical search was therefore not replayed,
the publication gate was not regenerated, and the sealed reserve was not
executed. This host does not vote on the bounded-null decision.

The broad suite emitted 30 NumPy matmul runtime warnings: 12 in pre-existing
Jacobi/variational checks and 18 in the new known-module control test. They are
the same older-stack divide-by-zero, overflow, and invalid-operation warning
pattern previously disclosed on this host. No assertion failed. The exact
decision-runtime local run passed all 235 tests without these warnings.

This is supplemental hash-integrity and implementation-portability evidence
only. The authoritative decision remains the committed exact-runtime record.
