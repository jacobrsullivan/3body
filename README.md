# Three-Body Lift-Integrability Research

[![Review Status](https://img.shields.io/badge/WP5--PUB--v1-READY__FOR__EXTERNAL__REVIEW-blue)](#publication-state--external-review)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This repository tests whether geometric lifting and regularization reveal
additional conserved quantities in the Newtonian three-body problem, and maps
the precise settings in which integrability is obstructed.

> **Open-Source Release Status (`READY_FOR_EXTERNAL_REVIEW`)**: This repository
> is publicly released along its sequential Work Package (`WP1`–`WP6`)
> boundaries with all cryptographic qualification locks intact. The frozen
> `WP5-PUB-v1` manuscript package ([`publication/wp5-pub-v1`](publication/wp5-pub-v1))
> has passed all internal deterministic verification gates and is published in
> `READY_FOR_EXTERNAL_REVIEW` state to enable independent human mathematical
> review and external clean-room `--core` replay on non-project-controlled
> hardware.

The original hidden-integrability hypothesis remains a research question, but
the qualified evidence has shifted the project's center of gravity:

> Build a reproducible, mathematically exact map of which hidden-integrability
> claims survive geometric lifting and which are obstructed, without extending
> any conclusion beyond its locked model, domain, or regularity class.

The authoritative project history currently ends at
`WP6-DZ-FEAS-v3-d1b87638e369`. Its result is a complete bounded null over a
frozen finite graph library, not a proof of unrestricted three-body
nonintegrability.

## Current Evidence Map

| Work package | Release tag | Role | Current qualified conclusion |
| --- | --- | --- | --- |
| **WP1** | `v0.1.0-wp1` | Numerical infrastructure and orbit catalogues | High-precision CR3BP infrastructure and one native 169-member planar N3BP family are qualified in their frozen scopes. This is not a general orbit catalogue. |
| **WP2** | `v0.2.0-wp2` | Reduction and geometric lifts | Canonical reductions and a fixed-energy three-chart KS atlas are qualified through isolated binary collisions. Triple collision, singular rotation charts, and a global atlas remain open. |
| **WP3** | `v0.3.0-wp3` | Invariant discovery | After exact removal of represented known quantities, no eligible direction remains in the frozen 285-function physical library. This is a bounded finite-library null, not a no-integral theorem. |
| **WP4** | `v0.4.0-wp4` | Exact obstruction and lift transfer | The project independently reproduces the scoped planar Morales-Ramis obstruction and transfers it to shell-regular physically admissible meromorphic Liouville families on the qualified KS atlas. |
| **WP5** | `v1.0.0-wp5` | Publication and reproducibility | A deterministic nine-page manuscript package is internally qualified as `READY_FOR_EXTERNAL_REVIEW`. Human review, external clean-room replay, metadata, licensing, release approval, and archival identifiers remain required before `READY_FOR_SUBMISSION`. |
| **WP6** | `v1.1.0-wp6` | Broader nonintegrability boundaries | Qualified results exclude an additional global meromorphic integral independent of the classical ones and prove rational nonintegrability on every finite planar common level except `(H,C)=(0,0)`. The final double-zero finite-library search found no witness. |

The evidence chain does **not** combine into a claim that:

- no additional integral exists in every regularity class or on every reduced
  leaf;
- the Newtonian three-body problem is globally nonintegrable in an unrestricted
  sense;
- the KS lift is integrable or globally regularizes triple collision; or
- the qualified orbit family is complete.

## Work-Package Release Tags

Because each Work Package's fail-closed qualification lock
(`validation-external/*/reports/*_lock.json`) cryptographically pins both its
own source files and predecessor qualification records across the repository,
the open-source release is organized as a single monorepo with sequential
milestone tags at each Work Package boundary:

| Release tag | Milestone commit | Qualified campaign records | Summary |
| --- | --- | --- | --- |
| `v0.1.0-wp1` | `da91937` | `WP1Q-v1-937694ba58a8` | Extended-precision (`dd_real`/`qd_real`) C++/Python integrators and JPL CR3BP qualification |
| `v0.2.0-wp2` | `dc09eee` | `WP1Q-N3BP-v1-892335b25187`, `WP1-CAT-N3BP-v1-605c6dbd59d1`, `WP2KSQ-v1-dc4b342e3bd2`, `WP2-3BRQ-v1-d4c0d5d7e2e3`, `WP2-MULTIQ-v1-72c81d86644a` | Native planar N3BP family, Jacobi/canonical reductions, pairwise KS, and 3-chart KS collision atlas |
| `v0.3.0-wp3` | `33d3e26` | `WP3-MULTI-CAND-v1-225359a13711`, `WP3-MULTI-CAND-v2-KQ-v1-514be9de7232` | Multi-chart invariant discovery and exact known-quotient bounded-null resolution |
| `v0.4.0-wp4` | `fad73c5` | `WP1-RESIDUAL-MAP-v1-9526e09d01ba`, `WP4-MR-REPL-v1-2ea23024c64b`, `WP4-LIFT-NI-v3-9ba955931b23` | Independent exact Morales-Ramis planar reproduction and spatial/KS-atlas differential Galois transfer |
| `v1.0.0-wp5` | `e043906` | `WP5-PUB-v1-5c0fb6c94077` | Deterministic 9-page manuscript package and verifier (`READY_FOR_EXTERNAL_REVIEW`) |
| `v1.1.0-wp6` | `HEAD` | `WP6-FI1-v1-c9099f7494b1`, `WP2-SO3-LEAF-v1-837d711e7074`, `WP6-L0-v1-27f160d029ca`, `WP6-COMMON-v1-502728e5b811`, `WP6-DZ-FEAS-v3-d1b87638e369` | Global meromorphic one-integral obstruction, regular `SO(3)` leaf, zero-momentum, planar common-level, and double-zero finite-library bounded null |

## Canonical Result Chain

The main qualified progression is:

```text
WP1 numerical/full-state foundations
    -> WP2 reduction and multi-chart KS atlas
    -> WP3 bounded invariant-search null
    -> WP4 reproduced obstruction and KS transfer
    -> WP5 internally qualified manuscript (READY_FOR_EXTERNAL_REVIEW)
    -> WP6 broader fixed-level and one-integral boundaries
```

Key result summaries:

- [`notes/wp2-multi-wp1-cat-n3bp-result.md`](notes/wp2-multi-wp1-cat-n3bp-result.md)
- [`notes/wp3-multi-cand-v1-result.md`](notes/wp3-multi-cand-v1-result.md)
- [`notes/wp4-mr-repl-v1-result.md`](notes/wp4-mr-repl-v1-result.md)
- [`notes/wp4-lift-ni-v3-result.md`](notes/wp4-lift-ni-v3-result.md)
- [`notes/wp5-pub-v1-result.md`](notes/wp5-pub-v1-result.md)
- [`notes/wp6-fi1-so3-l0-result.md`](notes/wp6-fi1-so3-l0-result.md)
- [`notes/wp6-common-level-v1-result.md`](notes/wp6-common-level-v1-result.md)
- [`validation-external/wp6-dz-feas-v3/reports/wp6_dz_feas_v3_qualification_report.md`](validation-external/wp6-dz-feas-v3/reports/wp6_dz_feas_v3_qualification_report.md)

Machine-readable qualification records and their frozen inputs live under
`validation-external/`. A `PASS` record authorizes only the claim written in
that record.

## Authoritative Verification

The supported environment is Python 3.11 with the versions pinned by
`environment-locks/bobs-osx-arm64.lock`. Create or activate the environment
described by `environment.yml`, then install the Poetry dependencies.

From the repository root, run:

```bash
./scripts/verify_project.sh
```

This single entry point:

1. verifies the active environment;
2. builds and verifies the pinned QD Python extension;
3. builds the C++ QD executables and runs their CTest checks; and
4. runs the complete non-slow Python regression suite (including all
   qualification lock and campaign contract checks).

Use `./scripts/verify_project.sh --all` to include tests marked `slow`.
Historical expected failures remain visible as `XFAIL`; they are not qualified
evidence. Optional exploratory WP3 packages such as PySR and PySINDy are not
required by the core qualification chain.

Qualification campaigns are intentionally not regenerated by the general
verification command. Each campaign has its own locked runner and immutable
record under `validation-external/`.

## Publication State & External Review

The frozen WP5 package is under [`publication/wp5-pub-v1`](publication/wp5-pub-v1).
It predates WP6 and is preserved byte-for-byte against
[`publication/wp5-pub-v1/artifact_manifest.json`](publication/wp5-pub-v1/artifact_manifest.json).

To run the deterministic WP5 publication verifier and clean-room replay:

```bash
# Fast static gate check (~10s)
./scripts/reproduce_wp5_pub_v1.sh --static

# Full core clean-room replay (~1 min; requires tectonic and pdftotext/pdfinfo)
./scripts/reproduce_wp5_pub_v1.sh --core
```

Both commands verify the locked specification, prerequisite WP1–WP4 records,
claim ledger, proof dependency map, deterministic PDF build, and adversarial
tamper controls, reporting `"status": "READY_FOR_EXTERNAL_REVIEW"`.

External reviewers and clean-room verifiers should consult:

- [`publication/wp5-pub-v1/REPRODUCING.md`](publication/wp5-pub-v1/REPRODUCING.md)
- [`publication/wp5-pub-v1/review/REVIEWER_PACKET.md`](publication/wp5-pub-v1/review/REVIEWER_PACKET.md)
- [`publication/wp5-pub-v1/review/EXTERNAL_REVIEW_GATE.md`](publication/wp5-pub-v1/review/EXTERNAL_REVIEW_GATE.md)
- [`publication/wp5-pub-v1/release/SUBMISSION_CHECKLIST.md`](publication/wp5-pub-v1/release/SUBMISSION_CHECKLIST.md)

The remaining fail-closed gates required before promoting `WP5-PUB-v1` from
`READY_FOR_EXTERNAL_REVIEW` to `READY_FOR_SUBMISSION` are:

1. two independent, consenting human reviewers with complementary mathematical
   coverage;
2. an external clean-room replay receipt on non-project-controlled hardware and
   account;
3. resolution of all blocker and major findings;
4. confirmed author identity, affiliations, contributions, conflicts, funding,
   ORCID status, and AI-assistance disclosure in
   `publication/wp5-pub-v1/release/metadata.json`;
5. confirmed code, evidence/data, and manuscript licenses in
   `publication/wp5-pub-v1/release/metadata.json`; and
6. explicit release authorization and immutable archive identifiers.

WP6 should be handled as a separately locked manuscript revision or companion
publication.

## Research Frontier

Open research must target a named claim rather than an unrestricted search.
The current priorities are:

1. planar rational integrability on the double-zero common level
   `(H,C)=(0,0)`;
2. existence of one additional integral defined only on a fixed reduced leaf;
3. a spatial fixed-common-level nonintegrability theorem;
4. regularity classes outside the qualified rational/meromorphic settings; and
5. local results near figure-eight, hierarchical, or other non-Lagrange
   dynamics.

The WP6 v3 finite graph library is exhausted. Enlarging it is not a default
next step; a new campaign should begin only from new mathematical structure and
a separately frozen protocol.

See [`TODO.MD`](TODO.MD) for the operational roadmap.

## Repository Layout

```text
src/python/             Production and research Python modules
src/cpp/                QD bindings, checks, and benchmarks
tests/                  Regression and campaign-contract tests
validation-external/    Frozen specifications, sources, evidence, and records
publication/            Internally qualified manuscript artifacts (WP5-PUB-v1)
notes/                  Plans, results, parity reports, and claim boundaries
Project-Design-Docs/    Historical and work-package design documents
User-Guides/            Legacy tutorial documentation
```

Historical design documents explain how the project arrived here; they are not
automatically current authority. For current claims, prefer the qualification
record, its result note, and this evidence map.

## Development Rules

- Run commands from the repository root.
- Preserve qualification records and frozen artifacts byte-for-byte.
- Put new claims behind a separately locked, fail-closed campaign.
- Keep exploratory results distinct from qualified evidence.
- Do not interpret a bounded null as a general nonexistence theorem.
- Do not modify the frozen WP5 manuscript to incorporate successor evidence.

## License

Repository source code is released under the [MIT License](LICENSE). Frozen
publication artifacts under [`publication/wp5-pub-v1/`](publication/wp5-pub-v1/)
are distributed in `READY_FOR_EXTERNAL_REVIEW` state with their cryptographic
hashes locked in `publication/wp5-pub-v1/artifact_manifest.json` for external
verification; final manuscript and evidence/data license metadata will be
recorded in `publication/wp5-pub-v1/release/metadata.json` upon completion of
the external review gate.

The project is research software. Verify claim boundaries before citing or
reusing any result.
