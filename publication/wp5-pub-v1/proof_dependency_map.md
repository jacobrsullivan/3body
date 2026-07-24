# WP5-PUB-v1 proof dependency map

This map separates theorem evidence from bounded computational context. Exact
paths and hashes are authoritative in `proof_dependency_map.json`.

## Theorem chain

```text
published reduced model and primary sources
  |
  v
C2 exact project-owned planar reconstruction
  |  WP4-MR-REPL-v1 PASS + generic source-disjoint replay
  v
C3 non-Abelian NVE Galois identity component for all positive masses
  |  Morales-Ramis necessary condition
  v
C4 local planar complete-meromorphic-integrability obstruction
  |  reflection-fixed block + fixed-Lz + energy/flow subquotient
  v
C5 local translation-reduced spatial obstruction
  |  WP2-MULTIQ-v1 quotient + Sundman + shell-rank transfer
  v
C6 no complete physically admissible KS family on a domain containing
   the regular lifted neighborhood
```

The planar result is attributed to Tsygvintsev and Boucher-Weil. The package
claims an exact reproduction, convention comparison, and qualification, not
discovery of the published theorem.

## Immutable authorities

| Node | Authority | SHA-256 role |
|---|---|---|
| `REC-WP2-MULTI` | `wp2_multi_v1_qualification_record.json` | Qualified KS model |
| `REC-WP4-MR` | `wp4_mr_repl_v1_qualification_record.json` | Planar reproduction PASS |
| `PROOF-WP4-MR` | `WP4-MR-REPL-v1-proof.md` | Exact derivation and Galois proof |
| `REC-WP4-LIFT` | `wp4_lift_ni_v3_qualification_record.json` | Transfer PASS |
| `PROOF-WP4-LIFT` | `WP4-LIFT-NI-v2-proof.md` | T1--T10 transfer proof |
| `ADDENDUM-WP4-LIFT` | `WP4-LIFT-NI-v3-addendum.md` | Project-owned planar premise |
| `SRC-MORALES-RAMIS` | Hash-pinned primary PDF | Necessary condition |
| `SRC-TSYGVINTSEV` | Hash-pinned primary PDF | Reproduction target |
| `SRC-BOUCHER-WEIL` | Hash-pinned primary PDF | Conclusion-level comparison |

## Context isolation

`WP1-CAT-N3BP-v1`, `WP1-RESIDUAL-MAP-v1`, and
`WP3-MULTI-CAND-v2-KQ-v1` do not feed the theorem chain. WP1 supports a
bounded external numerical-efficacy statement. WP3 records a null result only
within its frozen 285-function library after quotienting the known `L^2`
class. A verifier must reject any dependency edge from these records to
claims C3 through C6.

## Claim boundary

The root claim is local, complete, and meromorphic. It applies near the
embedded fixed-nonzero-angular-momentum parabolic Lagrange phase curve.
It does not exclude one additional integral, non-meromorphic integrability,
zero-angular-momentum dynamics, or domains disjoint from the obstructed
neighborhood.
