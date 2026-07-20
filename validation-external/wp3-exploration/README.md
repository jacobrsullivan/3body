# WP3-EXP-v1

This campaign performs deterministic numerical screening in the qualified
12-dimensional canonical Jacobi representation of the exact Newtonian
three-body vector field. It verifies total energy and angular-momentum-squared
as controls, projects those directions out, and ranks additional low-residual
linear combinations of an SO(3)-invariant feature library.

All output is `EXPLORATORY_ONLY`. Run the campaign with:

```bash
./validation-external/wp3-exploration/run_exploration.sh
```

The publication gate is evaluated first. A blocked gate does not prevent
screening, but it prohibits interpreting a screening direction as a conserved
quantity or as evidence of integrability. The upstream WP1 holdout is excluded:
it has already served its original qualification purpose and is not a fresh WP3
holdout.

Future `artifact` evidence must be a JSON evidence record with matching
`evidence_id`, `status: PASS`, and a valid canonical `record_payload_sha256`.
The evidence manifest must also pin the complete artifact file SHA-256. A text
assertion or an unverified file cannot open the gate.

The checked parity report compares the local record with a clean bobs-mini run
under `parity_spec.json`. Exact matrix hashes are required; only LAPACK-level
SVD deltas receive a numerical tolerance.
