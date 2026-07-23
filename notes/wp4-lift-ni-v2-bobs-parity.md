# WP4-LIFT-NI-v2 bobs-mini Parity

Date: 2026-07-23

## Status

The committed `wp4/lift-ni-v2` branch was replayed from a separate clean
detached worktree on `bobs-mac-mini`:

```text
/Users/bob/Desktop/3body-wp4-lift-ni-v2
commit 984c02a
```

The canonical host checkout was not changed. The validation worktree remained
clean after every build and test lane.

## Pinned Runtime

The replay used the established environment:

```text
/Users/bob/micromamba/envs/3body-legacy-v1
```

`qd_python` 1.0.0 was rebuilt against QD 2.3.22 before testing. The repository
C++ QD targets were also rebuilt, and both CTest checks passed.

## Results

The frozen `WP4-LIFT-NI-v2` lock verified all 38 files. The focused WP2/WP4
dependency suite passed 59/59 tests in 8.56 seconds.

| Lane | Result | Runtime |
| --- | --- | --- |
| collection | 1,231 tests collected | 1.81 s |
| fast | 1,095 passed, 2 skipped, 134 deselected | 82.32 s |
| slow | 45 passed, 2 skipped, 1,184 deselected | 274.58 s |
| quarantine | 79 strict xfailed, 8 skipped, 1,144 deselected | 741.96 s |

There were no ordinary failures and no unexpected passes. The three execution
lanes account for all 1,231 collected tests without overlap:

```text
1,097 fast + 47 slow + 87 quarantine = 1,231
```

The fast lane reported 61 known warnings. The slow lane reported 1,533 known
warnings, principally repeated legacy energy-constraint initialization
diagnostics. The quarantine lane reported 14 warnings. They remain visible and
did not alter any assertion or disposition.

## Claim Boundary

This replay is supplemental portability and repository-regression evidence. It
shows that the frozen qualification, its dependencies, the native QD binding,
and the complete legacy test partition reproduce on the pinned project host.
It does not change the frozen result, strengthen the conditional theorem, or
rehabilitate quarantined historical prototypes.
