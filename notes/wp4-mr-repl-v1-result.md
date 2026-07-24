# WP4-MR-REPL-v1 Result

Date: 2026-07-24

## Decision

- Qualification: `WP4-MR-REPL-v1-2ea23024c64b`
- Status: `PASS`
- Frozen lock payload:
  `35f7dcfe223dbe87775f11c6e31043c1b1ead02850d6f21ccb8e84a3b4406abb`
- Result:
  `a2934f78647ad31bd91dfc72ed3f5f7ad78a7278dd807f1d0d424148db506ff0`
- Final record payload:
  `2bfad5976b806d89d075bbbefe08f50680a8e677193b3b82cc3488e82082b951`

The frozen campaign passes 10/10 theorem obligations, 13/13 source-text
contracts, 7/7 published-equivalence checks, 4/4 exact specializations, and
9/9 adversarial controls. The dependency-free exact production certificate
and source-disjoint SymPy derivation agree exactly.

## Reproduced Certificate

Starting from the declared translation- and rotation-reduced planar Newtonian
Hamiltonian, the project:

1. verifies the exact parabolic Lagrange phase curve and all six Hamilton
   equations;
2. differentiates the Hamiltonian to obtain the full planar 6x6 variational
   equation;
3. performs the Whittaker energy-shell reduction to the published 4x4 normal
   variational equation and its Fuchsian gauge;
4. reproduces the two finite residue spectra and the infinity exponent
   polynomial;
5. proves
   `sigma=(m1*m2+m1+m2)/(m1+m2+1)^2` satisfies `0<sigma<=1/3` for every
   finite positive mass triple; and
6. proves the differential-Galois identity component is non-Abelian
   throughout that domain.

The positive-mass exceptional set for complete meromorphic Liouville
integrability is empty. The separate first-NVE polynomial set
`{1/3, 8/27, 2/9}` is retained as an exact higher-variational work overlay; it
is not an exception to the completed obstruction.

## Authorized Claim

The declared reduced planar positive-mass Newtonian three-body Hamiltonian at
fixed nonzero angular momentum is not completely integrable by meromorphic
first integrals in a complex neighborhood of the parabolic Lagrange phase
curve.

This is a local complete-integrability obstruction. It does not prove the
absence of an individual additional integral, cover non-meromorphic
regularity, cover zero angular momentum or triple collision, classify all
trajectories, or independently reconstruct every canonical reduction from the
unreduced 18-dimensional state.

## Evidence

The immutable machine-readable record is
`validation-external/wp4-mr-repl-v1/reports/wp4_mr_repl_v1_qualification_record.json`.
The complete derivation and claim boundary are in
`validation-external/wp4-mr-repl-v1/proof/WP4-MR-REPL-v1-proof.md`.
