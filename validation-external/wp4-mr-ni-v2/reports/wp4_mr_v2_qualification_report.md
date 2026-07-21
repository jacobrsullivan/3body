# WP4-MR-NI-v2 Qualification Report

**Status:** PASS

**Qualification ID:** `WP4-MR-NI-v2-4eb909c77a41`

## Qualified Result

Conditional on the two pinned published analyses, the declared positive-mass planar Newtonian three-body Hamiltonian is not completely integrable with meromorphic first integrals near the parabolic Lagrange solution. The exact project mass corpus satisfies the theorem's positive-mass hypothesis.

- Qualified WP1 catalogue cases: 169
- Distinct exact mass triples: 169
- Linear-NVE exceptional mass triples: 1
- Nonexceptional mass triples: 168
- Production/reference arithmetic: exact agreement
- Legacy Kovacic placeholder: excluded

The linear-NVE exceptional classification is not interpreted as nonlinear integrability. The universal complete-integrability obstruction applies to every positive-mass case, including exceptional first-variational-equation cases.

## Qualification Gates

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `specification_lock_verified` | 1 | == 1 | PASS |
| `invalidated_v1_is_not_executable` | 1 | == 1 | PASS |
| `source_manifest_verified` | 1 | == 1 | PASS |
| `source_download_hashes_reverified` | 1 | == 1 | PASS |
| `source_text_contracts_verified` | 1 | == 1 | PASS |
| `source_power_notation_transcribed_exactly` | 1 | == 1 | PASS |
| `all_benchmarks_exact` | 1 | == 1 | PASS |
| `all_permutations_and_common_scales_exact` | 1 | == 1 | PASS |
| `project_candidate_count` | 169 | == 169 | PASS |
| `production_reference_exact_agreement` | 1 | == 1 | PASS |
| `all_project_masses_positive` | 1 | == 1 | PASS |
| `all_project_cases_universally_obstructed` | 1 | == 1 | PASS |
| `exceptional_cases_not_overinterpreted` | 1 | == 1 | PASS |
| `legacy_placeholder_solver_excluded` | 1 | == 1 | PASS |
| `claim_boundary_present` | 1 | == 1 | PASS |

## Claim Boundary

A passing result verifies the source identities, exactly reproduces the published symmetric mass invariant and exceptional-set arithmetic, cross-checks an independent implementation, and applies two published non-complete-integrability theorems to the declared positive-mass planar model and project mass corpus. It is a theorem replication/application, not a new derivation of the 4x4 normal variational system, its factorization, local logarithms, monodromy generators, or differential Galois group. It establishes no obstruction for the spatial system as such, the zero-angular-momentum level in isolation, non-meromorphic or non-Liouville integrability, the regularized upstairs atlas, or any WP3 candidate. Exceptional first-variational-equation polynomial invariants are not nonlinear first integrals.

## Integrity

- Evidence commit: `076ababc3aefdf9afcdd264049b58330bcd41e14`
- Qualification lock: `5a8fad5ae70435cfcc7912a6c481569a4df7adad9f4a272dceeb0cc9cb538ed6`
- Results SHA-256: `c8fe232f515d61df3e42a7136d3a11e22720bb5dbb04e21f623d99e33b54a5a9`
- Record payload SHA-256: `8c94b28d89b6390e672bec9dfaa3f1c6998c279293c41f734a3630eb2db163c9`
- WP4-MR-NI-v1: invalidated before implementation or execution
