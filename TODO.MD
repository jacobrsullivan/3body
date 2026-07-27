# Current Roadmap

Updated: 2026-07-27

This roadmap begins after the sealed
`WP6-DZ-FEAS-v3-d1b87638e369` qualification. It replaces the accidental RTF
placeholder previously stored in this file.

## P0 — Canonicalize and Preserve

- [x] Preserve the sealed WP6 v3 evidence commit with an annotated milestone
  tag.
- [x] Fast-forward the canonical `main` branch through the documentation
  consolidation commit.
- [x] Confirm the remote `main` branch and milestone tag resolve to the intended
  commits.
- [ ] Keep Bob's older dirty worktree separate; do not reset, clean, or absorb
  its uncommitted legacy-baseline work into the canonical history.

## P1 — External Publication Gates

- [ ] Obtain two independent, consenting human reviewers collectively covering
  the planar/differential-Galois and spatial/KS arguments.
- [ ] Complete an external clean-room core replay on non-project-controlled
  hardware and account.
- [ ] Resolve every blocker and major review finding through a new locked
  revision.
- [ ] Confirm author identity, affiliation, contact, ORCID, contributions,
  conflicts, funding, and AI-assistance disclosures.
- [ ] Select code, evidence/data, and manuscript licenses.
- [ ] Obtain explicit release authorization and immutable archive identifiers.

The frozen `WP5-PUB-v1` package must remain unchanged while these gates are
open.

## P2 — WP6 Publication Decision

- [ ] Choose between:
  - a separately locked WP5 manuscript revision incorporating WP6; or
  - a companion paper focused on the hierarchy of nonintegrability boundaries.
- [ ] Create a new claim ledger and proof-dependency map for the selected scope.
- [ ] Keep the WP6 v3 bounded null distinct from a theorem about
  `(H,C)=(0,0)`.

## P3 — Repository Maintenance

- [ ] Add CI for `./scripts/verify_project.sh` on the pinned Python 3.11 stack.
- [ ] Classify and reduce the historical `XFAIL` inventory without changing
  qualification records.
- [ ] Replace tests that return booleans with explicit assertions.
- [ ] Triage numerical overflow and invalid-matmul warnings in legacy tests.
- [ ] Decide whether optional exploratory dependencies such as PySR, PySINDy,
  and JAX belong in separate environment extras.
- [ ] Review the legacy user guides against the current six-work-package
  evidence map.

## P4 — Named Research Questions

Only open a new campaign for a precise unresolved claim:

- [ ] Planar rational integrability at `(H,C)=(0,0)`.
- [ ] One additional integral defined only on a fixed reduced leaf.
- [ ] Spatial fixed-common-level nonintegrability.
- [ ] Non-rational/non-meromorphic regularity classes.
- [ ] Local figure-eight, hierarchical, or other non-Lagrange domains.

Do not enlarge the exhausted WP6 v3 finite graph library without a new
mathematical reason, frozen specification, and explicit promotion criteria.
