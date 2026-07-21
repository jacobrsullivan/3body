# WP3-v2 and WP4-MR Parallel Plan

Date: 2026-07-21

## Immutable Baseline

The completed `WP1-CAT-N3BP-v1`, `WP2-MULTIQ-v1`, and
`WP3-MULTI-CAND-v1` artifacts remain unchanged. Both successor tracks consume
their hashes as prerequisites and write only new versioned paths.

## WP3-MULTI-CAND-v2

The successor search moves from chart-local spinor polynomials to a physical
quotient library. It Reynolds-averages ten Gram primitives over all six body
permutations, so rotation, body-label, gauge, and chart invariance are
structural rather than inferred. Combined-degree-two numerators are evaluated
over three fixed denominators: one, the global collision product, and
barycentric moment of inertia. The resulting 285 functions reach physical
polynomial degree four and include declared collision-adapted rational forms.

The Reynolds projection has 36 exact zero identities, leaving 249 active
columns while preserving the locked 285-column declaration. The exact
represented known module is angular-momentum squared. Energy is an external
known control but is not represented by the frozen numerator and denominator
grammar. The existing development/calibration corpus and sealed 24-case
reserve remain unchanged. Candidate expressions cannot be interpreted before
the staged gate, and the reserve can be opened only after a separately locked
candidate-resolution stage.

## WP4-MR-NI-v2

`WP4-MR-NI-v1` was invalidated before implementation after its locked source
transcription flattened `5/(2^4)` to `5/24`. The corrected v2 track preserves
that invalidation record and independently locks `5/16`. It excludes the
repository's incomplete legacy Kovacic implementation, pins two primary
published analyses of the parabolic Lagrange normal variational system,
reproduces their exact symmetric mass invariant and exceptional-set arithmetic
with two source-disjoint exact implementations, and applies the published
theorem to every mass triple in the qualified WP1 catalogue.

Its authorized conclusion is conditional on the published NVE and monodromy
analysis. It is not presented as an independent re-derivation, does not extend
the planar theorem to the spatial or upstairs systems, and does not interpret
first-variational-equation exceptional cases as nonlinear integrability.

## Execution Order

1. Commit both specifications and the source manifest.
2. Generate and commit independent claim-specification locks.
3. Implement both tracks without editing frozen predecessor files.
4. Pass controls, freeze each implementation, and execute each once.
5. Evaluate the WP3 publication gate before inspecting candidates.
6. Finalize machine-readable records, run cross-track regressions, and perform
   non-voting bobs-mini portability checks where runtimes differ.

## Final Results

### WP3-MULTI-CAND-v2

The base search completed as `WP3-MULTI-CAND-v2-ab9626e19010`. All readiness
gates passed, but one rank-one spectral direction had a generalized singular
value below backend uncertainty, so the base publication gate correctly
blocked interpretation.

The first candidate-resolution implementation,
`WP3-MULTI-CAND-v2-RES-v1-31a9c87feb72`, is preserved but explicitly
superseded with no claim authority. Its raw coefficient projection was not
invariant under the 173-dimensional value-nuisance representation kernel, and
its known-direction test did not implement the locked function-identity test.

The corrected qualification,
`WP3-MULTI-CAND-v2-RES-v2-1277d77b2a25`, passed every gate and established
that the committed direction and all three independently reconstructed
directions evaluate as the known total-angular-momentum-squared function. The
minimum centered response projection was `0.9999999999999998`; the worst
challenge relative value residual was `6.830542672500359e-13`; the 80-digit
source-disjoint candidate-to-`L^2` residual was
`2.180976795577622e-13`. Raw coefficient cosines were deliberately not gates.

The separately locked successor search,
`WP3-MULTI-CAND-v2-KQ-v1-514be9de7232`, removed the complete observable
`L^2` equivalence class after the value map. It searched the complete remaining
spectrum with NumPy SVD and LAPACK `gesdd` and `gesvd` on development,
calibration, and 192 independent challenge states. It found zero candidate
subspaces. Backend-guarded lower bounds were:

- development: `0.05063722428688042`
- calibration: `0.008172395875105378`
- challenge: `0.18624504770032396`

Each lower bound exceeds the frozen `1e-10` candidate threshold. Backend
smallest-value relative spreads were at most `2.04e-13`. The publication gate
is `PASS_BOUNDED_NULL_ONLY`; the 24-case reserve remains
`SEALED_UNEXECUTED`.

The authorized WP3 claim is therefore a bounded finite-library null: after
quotienting known `L^2`, no additional eligible direction exists in the
declared 285-function Reynolds library over the three frozen evidence domains.
This is not a general absence-of-integrals or non-integrability theorem.

### WP4-MR-NI-v2

The corrected Morales-Ramis campaign completed as
`WP4-MR-NI-v2-4eb909c77a41`. Exact production arithmetic and a source-disjoint
SymPy implementation agreed on all gates. The published exceptional-set
arithmetic was applied to all 169 distinct positive-mass triples in the WP1
catalogue: one is the declared linear-NVE exception and 168 are
nonexceptional. The authorized conclusion remains conditional on the pinned
published NVE and monodromy analyses: the positive-mass planar Newtonian
three-body problem is not completely integrable by meromorphic first
integrals near the parabolic Lagrange solution. This does not extend to the
spatial or upstairs models and is independent of the WP3 finite-library null.

### Verification

All eight predecessor and successor implementation locks verify against their
frozen file maps. The focused cross-track regression suite passed `105/105`
tests. A repository-wide legacy run cannot serve as a clean gate in this
environment: collection first fails because the optional `qd_python` extension
is absent; with that test excluded, the run exposed numerous pre-existing
failures in legacy reduction, environment, regularization, symbolic-lift, and
chaos-indicator tests and was stopped during the long-running historical suite.
None of those tests is in a frozen qualification scope for the claims above.
