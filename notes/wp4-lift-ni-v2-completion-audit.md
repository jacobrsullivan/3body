# WP4-LIFT-NI-v2 Completion Audit

Date: 2026-07-23

## Completed Goal

Lock, implement, and independently qualify the precise transfer from a
physically admissible Liouville family on the qualified `WP2-MULTIQ-v1` KS
atlas to the physical translation-reduced spatial three-body model, then
connect that transfer only where justified to the pinned planar
Morales-Ramis obstruction. Preserve immutable evidence and explicit
claim/nonclaim boundaries.

The initial `WP4-LIFT-NI-v1` formulation was not advanced to implementation
freeze or execution because its ambient-rank premise was false. The exact
counterexample was recorded and v1 was invalidated claim-free.
`WP4-LIFT-NI-v2` replaced that premise with shell-relative rank and is the
completed qualification.

## Obligation Trace

| Obligation | Evidence | Status |
| --- | --- | --- |
| Precise locked specification | `qualification_spec.json`; specification lock `d1beb0f04c1bfd3b3b7d792592d9259474b213ed7790f766d7b033afe6eadb69` | PASS |
| Invalid v1 premise rejected | `validation-external/wp4-lift-ni-v1/reports/wp4_lift_ni_v1_specification_assessment.json`; exact negative control | PASS |
| Canonical single-KS zero-level quotient | Proof T1; exact production/reference identities | PASS |
| Product gauge reduction and `18 -> 16 -> 14` dimensions | Proof T2; rank and dimension checks | PASS |
| WP2 atlas chart gluing and Poisson compatibility | Proof T3; pinned WP2 contracts | PASS |
| Fixed-energy Sundman transfer | Proof T4; exact on-shell identities | PASS |
| First-integral descent and involution | Proof T5; projectability and bracket checks | PASS |
| Shell-relative rank descent | Proof T6; positive and adversarial rank controls | PASS |
| Collision-domain restriction | Proof T7; regular-domain checks | PASS |
| Spatial-to-planar variational subquotient | Proof T8; `12 -> 8 -> 7 -> 6 -> 5 -> 4` checks | PASS |
| Differential-Galois obstruction transfer | Proof T9; pinned published obstruction contracts | PASS |
| Local obstruction versus global atlas family | Proof T10; domain-restriction logic | PASS |
| Independent implementation agreement | Dependency-free production model versus source-disjoint SymPy reference | PASS |
| External evidence provenance | Ten source-text contracts and hash-pinned source manifest | PASS |
| Adversarial behavior | Six required negative controls | PASS |
| Immutable qualification | 38-file snapshot; qualification lock and finalized record | PASS |
| Host reproducibility | Clean pinned `bobs-mini` replay and complete 1,231-test partition | PASS |

## Immutable Decision

- Qualification: `WP4-LIFT-NI-v2-8d553cb1fa7f`
- Result: `PASS`
- Frozen snapshot:
  `8d553cb1fa7f1d2cd28c7ef01691127903a3824ded2262bf7f6ee88de1aef774`
- Qualification lock:
  `ead00fca45a4328bbe4534c3fb85e457b990a94a020ef47e7f0651b9bafaead1`
- Result hash:
  `4875c0ec8f7bcc894d2c84e7c8623ae4050e6ec74259c92282230441150bfb72`
- Record payload:
  `a253f302149fdb6d4fae66bc19bd3cd2efa94eff995be0ad6112d1b6725ff3a4`

All 19 locked gates, T1 through T10, all ten external-source contracts, and all
six negative controls pass. The qualification is complete with no open
remediation inside its declared scope.

## Authorized Result

Conditional on the pinned published planar normal-variational
nonintegrability result, the translation-reduced spatial positive-mass
Newtonian three-body Hamiltonian is not completely integrable by meromorphic
first integrals near the embedded nonzero-angular-momentum parabolic Lagrange
phase curve. Consequently, the qualified `WP2-MULTIQ-v1` atlas admits no
complete shell-regular physically admissible meromorphic Liouville family on
any domain containing that regular neighborhood.

This does not prove that the three-body problem has no additional integrals.
It does not cover non-meromorphic or non-Liouville notions, nonzero-`Xi`
magnetic dynamics, a general `SO(3)` quotient, triple collision, or domains
that avoid the obstructed neighborhood. The published 4x4 planar NVE and its
Galois calculation are consumed as pinned external evidence rather than
independently rederived.
