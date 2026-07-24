# WP5-PUB-v1 Publication Plan

Date: 2026-07-24

## Focused Goal

Turn the completed, project-owned WP4 theorem chain into an independently
auditable preprint and reproducibility package without widening any qualified
claim. The package must make the exact theorem, prior-art relationship,
proof dependencies, computational evidence, and nonclaims visible to a reader
who has not followed the work-package history.

The publication campaign must distinguish three states:

1. `READY_FOR_EXTERNAL_REVIEW`: every internal manuscript, integrity,
   reproducibility, and adversarial claim-boundary gate passes.
2. `READY_FOR_SUBMISSION`: two independent human review roles and an external
   clean-room reproduction pass, all material findings are resolved, and
   author and license metadata are confirmed.
3. `PUBLISHED`: the author has approved release, the exact qualified commit is
   archived, and the preprint and software archive identifiers are recorded.

Internal automation, language models, source-disjoint code, and `bobs-mini`
parity cannot satisfy the independent-human-review requirement.

## Locked Order

1. Commit the claim specification, source registry, review schema, and this
   plan before manuscript or evaluator implementation.
2. Lock those files and every predecessor record by content hash.
3. Draft a venue-neutral LaTeX manuscript and supplement from the immutable
   WP1/WP2/WP3/WP4 records.
4. Attribute the planar nonintegrability theorem to its published sources.
   Treat exact reproduction, auditability, and the qualified spatial/KS
   transfer as the project contribution; make no novelty claim before an
   independent literature review.
5. Build a proof-dependency map, claim ledger, artifact manifest, reviewer
   packet, release checklist, and one-command clean-room reproducer.
6. Compile and visually inspect the manuscript PDF.
7. Freeze the internal implementation, execute exact gates and adversarial
   controls, and record either `READY_FOR_EXTERNAL_REVIEW` or `FAIL`.
8. Reproduce the frozen package from a clean checkout on `bobs-mini`.
9. Commit and push the review-ready package.
10. Issue `READY_FOR_SUBMISSION` only after qualifying external evidence is
    supplied. A missing reviewer, author confirmation, license decision, or
    clean-room receipt remains an explicit blocked gate rather than an
    inferred pass.

## Terminal Standard

This implementation phase is complete when a frozen, clean-host-reproduced
package reaches `READY_FOR_EXTERNAL_REVIEW` and leaves an exact reviewer
handoff. Publication authorization itself remains fail-closed until the
external and administrative gates pass.
