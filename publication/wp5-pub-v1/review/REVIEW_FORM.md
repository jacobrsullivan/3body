# WP5-PUB-v1 human review form

This form is a checklist for creating the required machine-readable review
record. It is not itself a signed review.

## Reviewer identity and independence

- Name:
- ORCID, if any:
- Affiliation, if any:
- Expertise categories:
- I am a human:
- I consent to publication of my identity:
- I am not the author:
- I did not implement the project evidence:
- I am not a project-controlled agent:
- Conflict statement:

## Frozen target

- Git commit:
- Artifact-manifest SHA-256:
- Manuscript-PDF SHA-256:
- Clean-room receipt SHA-256, if reviewed:

## Scope completed

Select all that apply:

- planar derivation
- differential-Galois argument
- positive-mass domain
- spatial subquotient
- KS/Sundman transfer
- claim boundary
- clean-room reproduction

## Findings

For every finding provide:

- stable finding ID;
- severity: blocker, major, minor, or editorial;
- exact location; and
- actionable description.

## Recommendation

Choose exactly one:

- `APPROVE`
- `REVISE`
- `REJECT`

`APPROVE` is incompatible with any blocker or unresolved major finding.

## Signature

Record the signing time in UTC and use one permitted method:

- detached PGP signature;
- signed PDF; or
- archived institutional email.

The final JSON must validate against
`validation-external/wp5-pub-v1/review/external_review_schema.json`.
