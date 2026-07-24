# WP5-PUB-v1 external review gate

## Why this gate exists

Exact symbolic replay and internal adversarial testing establish
reproducibility and claim discipline. They do not replace independent
mathematical judgment. The campaign therefore stops at
`READY_FOR_EXTERNAL_REVIEW` until the evidence below exists.

## Required people

Two distinct consenting human reviewers must be independent of the author
and implementation chain. Collectively they must cover:

- planar Hamiltonian reduction and differential-Galois integrability; and
- symplectic reduction, spatial variational subquotients, and KS
  regularization.

One reviewer may cover both areas, but a second independent human review is
still mandatory. Automated agents, anonymous reviews, self-review, and
reviews generated on behalf of an unidentified person are rejected.

## Required clean-room replay

At least one reviewer or a separate independent person must run:

```bash
./scripts/reproduce_wp5_pub_v1.sh --core
```

The machine and account must not be controlled by the project. The receipt
must conform to `clean_room_receipt_schema.json`, pin the reviewed commit and
artifact hashes, report the actual command and runtime, and have a detached
signature artifact.

Project-controlled second-host runs, including `bobs-mini`, are supplemental
portability checks only.

## Findings policy

- Any blocker makes the gate fail.
- Any unresolved major finding makes the gate fail.
- Minor and editorial findings must be dispositioned in a response ledger.
- Revisions that change a theorem premise, scientific source, locked claim,
  review rule, or negative control require a successor campaign.
- Editorial revisions that preserve the lock may be made only with a
  recorded before/after hash and reviewer confirmation.

## Author and license gates

The author must explicitly confirm:

- name and affiliation status;
- contact and ORCID status;
- contribution statement;
- conflicts and funding;
- AI-assistance disclosure;
- code, evidence/data, and manuscript licenses; and
- final release authorization.

Null or inferred values do not pass.

## Exact handoff

Submit the following under
`validation-external/wp5-pub-v1/review/external/`:

1. two JSON review records matching `external_review_schema.json`;
2. each reviewer's separate signature artifact;
3. at least one JSON clean-room receipt matching
   `clean_room_receipt_schema.json`;
4. its separate signature artifact; and
5. a finding-response ledger if either review reports findings.

Then update `publication/wp5-pub-v1/release/metadata.json` with author-confirmed
values and rerun the evaluator. Do not edit a signed review record.
