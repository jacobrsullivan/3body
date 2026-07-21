# WP2-MULTIQ-v1 and WP1-CAT-N3BP-v1 bobs-mini Parity

Date: 2026-07-21

The clean `/Users/bob/Desktop/3body` checkout on `bobs-mac-mini` was
fast-forwarded to `3d1296c591be4a1d63b02a9f94381351fed8fc71`.

The host verified both frozen locks:

- `WP2-MULTIQ-v1-72c81d86644a` (66 frozen files)
- `WP1-CAT-N3BP-v1-605c6dbd59d1` (52 frozen files)

The focused WP1/WP2 suite passed 46/46 tests. The broader relevant regression
surface passed 192/192 tests in 9.74 seconds. No holdout, evaluation, record, or
other decision-bearing artifact was regenerated.

## Runtime

- Python 3.11.15
- macOS 26.5.2 arm64
- NumPy 2.2.6
- SciPy 1.16.1
- pytest 8.4.1
- REBOUND 4.4.10
- JAX/JAXLIB 0.9.0.1

## Dependency Caveat

The first focused run passed 43/46 tests and failed only because JAX was absent.
JAX/JAXLIB 0.9.0.1, matching the authoritative host, was then installed into
the existing `wp1_env`; all 46 focused and all 192 broader tests passed.
The exact supplemental JAX stack is recorded in
`validation-external/wp2-multi-parity/requirements.txt`.

JAX is used by the independent autodiff reference but is not declared in the
frozen `pyproject.toml`, `poetry.lock`, or `environment.yml`, and its version is
not included in the generic v1 runtime fingerprint. Changing those frozen files
would invalidate the v1 locks, so this is disclosed rather than retroactively
altered. A superseding qualification version should add JAX/JAXLIB to both the
environment declaration and exact runtime fingerprint before its specification
lock is created.

Nine NumPy/Accelerate matmul runtime warnings occurred in the WP1 variational
tests under the older NumPy stack. They did not change any assertion or test
outcome and are retained as portability diagnostics.

This replay is supplemental portability evidence only. It does not replace or
vote on either authoritative qualification decision.
