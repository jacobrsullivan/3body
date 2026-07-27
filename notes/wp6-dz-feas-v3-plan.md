# WP6-DZ-FEAS-v3 plan

## Purpose

`WP6-DZ-FEAS-v2-f6e66c0368d3` is a signed, fail-closed `INCOMPLETE`
qualification. It executed 11,689 of 11,700 locked systems, proved 11,549
unit ideals, timed out on 140 systems, and reached no non-unit ideal before
the aggregate cap. All timeouts occurred in `PHI-BOTH-SQ`.

Version 3 remediates that exact-computation failure. It does not enlarge the
mathematical discovery scope and it does not reinterpret any v1 or v2
result.

## Frozen mathematical scope

Version 3 repeats exactly the v2:

- arbitrary-positive-mass rectilinear zero-energy model;
- four rational shape covers;
- one- and two-term Laurent supports from exponents `-2` through `2`;
- thirteen exact mass/order sentinels;
- exact-support saturation; and
- 11,700 coefficient ideals in the same order.

No cover, support, mass case, coefficient field, vector-field identity, or
witness requirement may change.

## Exact solver remediation

The solver is changed without changing the localized ideals:

1. Construct the polynomial normalized-energy numerator first.
2. Build later vector-field residuals only if the preceding ideal is
   non-unit.
3. Canonically clear declared shape and Laurent denominators.
4. Divide each coefficient equation by its greatest monomial in support
   coefficients. This is exact because support saturation makes every such
   coefficient a unit on the searched torus.
5. Decide unitness over `QQ` in graded reverse lexicographic order with both
   SymPy F5B and Buchberger algorithms.
6. Treat disagreement, timeout, malformed input, or resource exhaustion as
   unresolved.
7. Compute a lexicographic basis and audit branches only for a full
   non-unit ideal.

The two algorithms must agree for every unit decision. The complete campaign
is single-process and deterministically ordered. It is capped at 30 seconds
per system, 3,600 seconds total, and 4,096 MiB peak memory.

## Qualification outcomes

`QUALIFIED_WITNESS` still requires W1-W12, including arbitrary-positive-mass
continuation. A sentinel-only graph cannot promote.

`COMPLETE_BOUNDED_NULL_RESULT` requires exact decisions for all 11,700
systems, complete audit of every non-unit ideal, dual-algorithm agreement,
and no qualifying witness.

Every unresolved system forces `INCOMPLETE`.

## Claim boundary

A complete null result covers only this finite graph library. It does not
prove that no explicit double-zero algebraic orbit exists, does not prove
nonintegrability on `(H,C)=(0,0)`, and does not authorize
`WP6-DZ-MR-v1`.

Only a signed `QUALIFIED_WITNESS` record naming one frozen full-system
witness may open the Morales-Ramis track.

## Observed search result

The locked implementation at commit `5eef69a` ran on Bobs-mini with CPython
3.11.15 and SymPy 1.14.0. The immutable ledger records:

- 11,700/11,700 systems executed;
- 11,700 exact dual-algorithm unit ideals;
- 0 non-unit ideals;
- 0 timeouts, errors, or algorithm disagreements;
- 11,687 decisions at `ENERGY`;
- 13 decisions at `ENERGY_AND_V`; and
- all 151 unresolved v2 systems closed as unit ideals.

The signed search payload is
`9555fbcdeb532db2986c9b7f9ed2e3927fab109d9abb17d418917f548b4b3034`.
Final interpretation remains subject to the separately frozen post-search
qualification.
