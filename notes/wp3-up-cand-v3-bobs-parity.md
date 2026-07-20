# WP3-UP-CAND-v3 bobs-mini Parity

The clean `/Users/bob/Desktop/3body` checkout on the configured
`bobs-mac-mini` host was updated to commit
`e34c532ba738a756c01bc5e998868d942315168c`.

The host independently verified the `WP1-CAT-v1`, `WP3-UP-CAND-v3`, and
`WP4-UP-READY-v3` locks/records. Its applicable focused suite passed 42/42
tests. The exact WP3 decision-runtime test was intentionally deselected because
the supplemental host used Python 3.11.15, NumPy 2.2.6, and SciPy 1.16.1,
whereas the frozen decision requires Python 3.13.2, NumPy 2.3.5, SciPy 1.16.3,
and its exact macOS/Accelerate fingerprint.

The repository's WP1 acceptance gate also passed: setup verification succeeded,
104/104 focused Python tests passed, and both QD CTest checks passed.
Full pytest collection succeeds with 1,122 tests and two warnings for optional
symbolic-regression dependencies (`pysindy` and `PySR`).

A full search replay, explicitly bypassing only the runtime vote and writing to
`/tmp`, produced the same bounded-null status, `SEARCH_READY=PASS`, and zero
candidates. All six input matrix hashes were byte-identical. The guarded lower
bound was `1.6394931463167159e-4`, differing from the authoritative value by
`3.50e-14` (relative `2.13e-10`).

The older NumPy stack emitted 12 matmul runtime warnings during tests and three
during fold projection in the full replay. They caused no test failure or
decision change and are disclosed rather than suppressed. This replay is
supplemental portability evidence only; it cannot alter the frozen
decision-bearing result.
