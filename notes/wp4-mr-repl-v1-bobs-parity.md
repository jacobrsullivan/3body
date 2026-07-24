# WP4-MR-REPL-v1 bobs-mini Parity

Date: 2026-07-24

## Scope

The completed project-owned Morales-Ramis chain was reproduced on
`bobs-mac-mini` from the isolated clean checkout
`/Users/bob/Desktop/3body-wp4-mr-repl-v1` at commit
`4fcbec81d007f31d9f8208806f43fbcd60dd33db`. The canonical historical checkout
at `/Users/bob/Desktop/3body` was not modified.

The replay used:

| Component | Value |
| --- | --- |
| Platform | macOS 26.5.2, arm64 |
| Environment | `/Users/bob/micromamba/envs/3body-legacy-v1` |
| Python | 3.11.15 |
| NumPy | 2.2.6 |
| SciPy | 1.16.1 |
| SymPy | 1.14.0 |
| pytest | 8.4.1 |
| QD | 2.3.22 |
| `qd_python` | 1.0.0 |

`qd_python` was rebuilt in place against QD 2.3.22. Both native QD CTest
checks passed.

## Qualification Replay

The host verified all files in the three new frozen snapshots:

- `WP4-MR-REPL-v1`: 26/26 files;
- `WP1-RESIDUAL-MAP-v1`: 22/22 files; and
- `WP4-LIFT-NI-v3`: 35/35 files.

The focused dependency chain passed 93/93 tests in 18.58 seconds. It covered
`WP1-CAT-N3BP-v1`, `WP1-RESIDUAL-MAP-v1`, `WP2-MULTIQ-v1`,
`WP4-MR-REPL-v1`, `WP4-LIFT-NI-v2`, and `WP4-LIFT-NI-v3`. Nine disclosed
older-NumPy matrix-multiplication warnings did not change an assertion.

The source-disjoint SymPy implementation then reran its generic exact
derivation rather than reading the frozen result. After removing only
`elapsed_seconds`, its complete 32-field payload was exactly equal to the
frozen generic payload. In particular, all exact derivation checks passed and
the turning-point, both collision, and infinity characteristic polynomials,
as well as the symbolic mass invariant
`sigma=(m1*m2+m1+m2)/(m1+m2+1)^2`, agreed exactly. The clean-host derivation
took 615.97 seconds; the frozen qualification run took 695.74 seconds.

This replay is supplemental portability evidence. It does not regenerate or
replace any immutable qualification record.

## Complete Repository Baseline

The pinned legacy runner collected 1,270 tests in 2.43 seconds and assigned
every test to exactly one lane:

| Lane | bobs-mini result | Runtime |
| --- | --- | --- |
| Fast | 1,134 passed, 2 skipped, 134 deselected | 88.81 s |
| Slow | 45 passed, 2 skipped, 1,223 deselected | 293.26 s |
| Quarantine | 79 strict xfailed, 8 skipped, 1,183 deselected | 781.09 s |

There were no ordinary failures and no `XPASS` results. The lane dispositions
account exactly for collection: `1,136 + 47 + 87 = 1,270`.

The same commit and pinned environment were exercised locally before the host
replay:

| Lane | Local result | Runtime |
| --- | --- | --- |
| Fast | 1,134 passed, 2 skipped, 134 deselected | 114.91 s |
| Slow | 45 passed, 2 skipped, 1,223 deselected | 357.95 s |
| Quarantine | 79 strict xfailed, 8 skipped, 1,183 deselected | 903.95 s |

The slow lane emitted 1,533 known trajectory-level diagnostics on both hosts.
The quarantine emitted 14 known warnings on both hosts. The fast lane emitted
19 locally and 61 on `bobs-mini`; all were visible legacy return-value,
optional-dependency, or numerical diagnostics and no test disposition
changed.

## Conclusion

The new theorem chain, its parallel WP1 work map, the native QD dependency,
and the complete disjoint legacy baseline reproduce on a second clean host.
At the end of the replay the checkout remained clean and its branch matched
`origin/wp4/mr-repl-v1`.
