# WP5-PUB-v1 result

Date: 2026-07-24

## Decision

`WP5-PUB-v1-5c0fb6c94077` is internally qualified with status
`READY_FOR_EXTERNAL_REVIEW`.

The nine-page venue-neutral manuscript, claim ledger, proof dependency map,
deterministic PDF build, canonical artifact manifest, one-command reproducer,
adversarial controls, reviewer packet, and fail-closed release metadata are
complete.

## Internally substantiated claim

The project-owned exact reproduction of the published planar
Morales-Ramis obstruction transfers to the translation-reduced spatial
positive-mass Newtonian three-body Hamiltonian near the embedded parabolic
Lagrange phase curve at fixed nonzero angular momentum. Consequently, the
qualified `WP2-MULTIQ-v1` KS atlas admits no complete shell-regular physically
admissible meromorphic Liouville family on any domain containing the regular
lift of that neighborhood.

The result is local, complete, and meromorphic. It does not exclude one
additional integral and is not a global absence-of-integrals statement.

## Qualification evidence

- Clean evidence commit: `cd4c3460838ffbb5328d02eaf3a70121775b2c8a`
- Frozen record commit: `900119268a81345eae3e7573f3693fe6c1099460`
- Artifact-manifest SHA-256: `cf42a6eb25259a031440a50d26493da6150b5ea2688c9893d66142c214cb0053`
- Manuscript-PDF SHA-256: `7470d73612278377f3fd25f4a1bafc8caa6215160aff04f0fc9a35bef050585d`
- Normalized generic payload SHA-256: `4f8f9774e9ff486a056ce96f48ed2791e74b57dfa87e2d0ea8ca6682c2085678`
- Generic payload fields: 32/32 exact match
- Publication adversarial tests: 15/15 pass
- Internal PDF visual inspection: PASS, all 9 pages
- Local generic runtime: 685.10 seconds
- Clean bobs-mini generic runtime: 580.64 seconds

The clean bobs-mini checkout reproduced the same manifest, PDF, and normalized
generic hashes and remained clean.

## Evidence separation

- WP4-MR-REPL-v1 and WP4-LIFT-NI-v3 support the theorem.
- WP2-MULTIQ-v1 supplies the qualified KS model.
- WP1 supplies bounded external numerical-efficacy context only.
- WP3 remains `COMPLETE_BOUNDED_NULL_RESULT` with
  `PASS_BOUNDED_NULL_ONLY` authority and is not used in the proof.
- The legacy suite supplies software-regression evidence only.

## Remaining publication gates

The package is not yet submission-ready or published. It still requires:

1. two distinct, consenting, independent human reviewers collectively
   covering the planar/differential-Galois and spatial/KS arguments;
2. at least one external clean-room core replay on non-project-controlled
   hardware and account;
3. resolution of every blocker and major review finding;
4. author-confirmed identity, affiliation status, contact, ORCID status,
   contributions, conflicts, funding, and AI-assistance disclosure;
5. selected code, evidence/data, and manuscript licenses; and
6. explicit author release authorization and immutable archive identifiers.

No internal process or project-controlled host can satisfy those gates.
