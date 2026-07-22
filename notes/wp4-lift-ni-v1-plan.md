# WP4-LIFT-NI-v1 Qualification Plan

Date: 2026-07-22

## Goal

Complete a locked theorem-level qualification that tests the remaining
physically meaningful lift-integrability loophole. The campaign will prove
whether a complete meromorphic, gauge-invariant, chart-compatible, and
clock-independent Liouville family on `WP2-MULTIQ-v1` must descend to the
physical spatial three-body system. It will also establish the spatial
variational obstruction required by that implication rather than importing a
planar theorem without proof.

## Order

1. Commit the specification and source manifest without implementation.
2. Generate and commit a claim-specification lock binding every prerequisite.
3. Implement an exact production checker, a source-disjoint SymPy reference,
   negative controls, and a proof covering obligations T1 through T10.
4. Freeze the complete implementation in a clean committed worktree.
5. Execute once against hash-verified primary sources.
6. Commit the result, finalize an immutable record in another clean commit,
   and run focused and repository-wide regression gates.

## Terminal Outcomes

`PASS` authorizes only the conditional claim written in the locked
specification. `FAIL` remains a result and requires a successor campaign; no
threshold or admissibility definition may be changed after locking.

The campaign cannot authorize the unqualified statement that the three-body
problem has no integrals. It also cannot rule out gauge-dependent,
chart-dependent, explicitly clock-dependent, non-meromorphic, or
non-Liouville constructions.
