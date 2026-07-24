# WP5-PUB-v1 reviewer packet

## Review target

Title: *Exact reproduction and KS-atlas transfer of a Morales-Ramis
obstruction near the parabolic Lagrange solution*

The package asks reviewers to assess a narrowly bounded result:

1. exact reproduction of a published planar normal-variational calculation;
2. the positive-mass non-Abelian monodromy/Galois argument;
3. the spatial differential-subquotient transfer; and
4. the KS quotient, Sundman, involution, and shell-rank transfer.

The planar theorem is prior art. The project does not claim its discovery or
first proof.

## Frozen artifacts

Review only a committed checkout and record all three identifiers:

```bash
git rev-parse HEAD
shasum -a 256 publication/wp5-pub-v1/artifact_manifest.json
shasum -a 256 publication/wp5-pub-v1/manuscript/main.pdf
```

Begin with:

- `publication/wp5-pub-v1/manuscript/main.pdf`
- `publication/wp5-pub-v1/claims/claim_ledger.json`
- `publication/wp5-pub-v1/proof_dependency_map.md`
- `validation-external/wp4-mr-repl-v1/proof/WP4-MR-REPL-v1-proof.md`
- `validation-external/wp4-lift-ni-v2/proof/WP4-LIFT-NI-v2-proof.md`
- `validation-external/wp4-lift-ni-v3/proof/WP4-LIFT-NI-v3-addendum.md`

The exact source URLs and hashes are in
`validation-external/wp4-mr-repl-v1/sources/manifest.json`.

## Planar and differential-Galois questions

- Does the declared reduced Hamiltonian match the cited convention?
- Does the phase-curve tangency check establish an integral phase curve?
- Is the Whittaker `6 -> 4` reduction mathematically valid on the stated
  regular neighborhood?
- Do the gauge, pole, residue, and infinity calculations establish the
  displayed Fuchsian system?
- Is every finite local monodromy unipotent for the reason stated?
- Is the passage of those unipotents into the algebraic identity component
  valid?
- Does the commuting-unipotent contradiction at infinity hold for the full
  positive-mass interval `0 < sigma <= 1/3`?
- Is the Morales-Ramis conclusion stated with the correct locality,
  completeness, and regularity?

## Spatial and KS questions

- Is the planar normal variational module genuinely a differential
  subquotient of the spatial variational module?
- Are reflection, fixed-`Lz`, rotation quotient, energy tangent, and flow
  quotient used in the correct order and dimensions?
- Is the algebraic-image argument for differential Galois identity
  components valid?
- Do the KS cotangent lift and `Xi=0` quotient have the stated Poisson and
  rank properties?
- Does the fixed-energy Sundman identity transfer conservation only on the
  stated shell?
- Does shell-relative rank nine imply physical rank six?
- Are gauge projectability, chart compatibility, and clock independence
  sufficient and explicitly retained?

## Claim-boundary questions

- Does any passage imply absence of a single additional integral?
- Does any passage imply a global result beyond restriction from a larger
  domain containing the local neighborhood?
- Is WP3 kept out of the proof?
- Are WP1 claims restricted to numerical external-efficacy context?
- Is prior art credited without an unsupported novelty claim?

## Required output

Return one JSON review record conforming to
`validation-external/wp5-pub-v1/review/external_review_schema.json` and a
separate signature artifact. Use `REVIEW_FORM.md` as the human checklist.
Every blocker or major issue must have a concrete manuscript/proof location.
An `APPROVE` recommendation with unresolved blocker or major findings is
invalid.
