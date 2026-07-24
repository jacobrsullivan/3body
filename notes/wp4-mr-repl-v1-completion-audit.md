# WP4-MR-REPL-v1 Completion Audit

Date: 2026-07-24

## Completed Goal

Replace the externally consumed planar Morales-Ramis premise with a
project-owned exact derivation and qualification, transfer that reproduced
obstruction through the already qualified spatial and KS model boundary, and
produce a publication-gated WP1 residual work map in parallel. Preserve all
completed predecessor evidence, reproduce the result on `bobs-mini`, and
state exactly what the resulting theorem does and does not establish.

## Obligation Trace

| Obligation | Evidence | Status |
| --- | --- | --- |
| Preserve completed WP1/WP2/WP3/WP4 evidence | Successor-only campaigns; predecessor production, reference, proof, and qualification hashes remain unchanged | PASS |
| Lock claims before implementation | Preimplementation specification locks for all three successor campaigns | PASS |
| Derive the parabolic Lagrange phase curve | Exact six-Hamilton-equation and zero-energy residuals in the production and SymPy derivations | PASS |
| Derive the planar variational equation | Full 6x6 Hessian-derived Hamiltonian variational system | PASS |
| Derive the published normal equation | Exact Whittaker shell reduction and Fuchsian gauge to the 4x4 NVE | PASS |
| Audit the full positive-mass domain | Exact proof of `0 < sigma <= 1/3`; empty complete-integrability exceptional set | PASS |
| Retain exceptional-set distinctions | First-NVE set `{1/3, 8/27, 2/9}` recorded as higher-variation work, not as an exception to the complete obstruction | PASS |
| Establish a non-Abelian Galois certificate | Exact residue spectra, infinity exponents, and noncommuting identity-component generators | PASS |
| Use source-disjoint implementations | Dependency-free exact production model and independently differentiated SymPy reference agree exactly | PASS |
| Establish published equivalence | 13/13 source-text contracts and 7/7 convention/equivalence checks against three hash-pinned primary publications | PASS |
| Qualify adversarial behavior | 9/9 Morales-Ramis controls and 4/4 exact mass specializations pass | PASS |
| Freeze immutable planar evidence | `WP4-MR-REPL-v1-2ea23024c64b`, 10/10 theorem obligations, status `PASS` | PASS |
| Replace the v2 external premise | `WP4-LIFT-NI-v3` requires the complete reproduced record and rejects a status-only substitute | PASS |
| Requalify the spatial and KS transfer | `WP4-LIFT-NI-v3-9ba955931b23`, 21/21 gates, T1-T10, and 8/8 controls pass | PASS |
| Map qualified WP1 follow-on work | `WP1-RESIDUAL-MAP-v1-9526e09d01ba` maps all 169 rows with exact production/reference agreement | PASS |
| Keep WP1 interpretation publication-gated | No invariant, KAM, manifold, spatial-stability, or catalogue-expansion claim is authorized | PASS |
| Reproduce the complete local baseline | 1,270 tests partitioned into green fast, green slow, and exact strict-quarantine lanes | PASS |
| Reproduce on an independent host | Exact generic algebra, 93/93 focused tests, 2/2 CTest checks, and the full 1,270-test partition pass on `bobs-mini` | PASS |

No remediation remains inside the declared goal.

## Immutable Decisions

| Campaign | Qualification | Lock payload | Result SHA-256 | Record payload |
| --- | --- | --- | --- | --- |
| Planar obstruction | `WP4-MR-REPL-v1-2ea23024c64b` | `35f7dcfe223dbe87775f11c6e31043c1b1ead02850d6f21ccb8e84a3b4406abb` | `a2934f78647ad31bd91dfc72ed3f5f7ad78a7278dd807f1d0d424148db506ff0` | `2bfad5976b806d89d075bbbefe08f50680a8e677193b3b82cc3488e82082b951` |
| WP1 work map | `WP1-RESIDUAL-MAP-v1-9526e09d01ba` | `da58537b9e904fa702580f244f6d928e72e5be07a6d10ba63965a6ff019c321e` | `3a1a939ef520aaa77fdee7398f5aa66424015ed82a3fdbf22c103d1fe0d04798` | `577e0d42270e1cd7781c5ac071e8dd50e60fa67f5aab66e0f8c0826258b548a6` |
| Spatial/KS transfer | `WP4-LIFT-NI-v3-9ba955931b23` | `9e16fbdbf65744ebb69641323e1b657f260390f4ef7938194a9259fb96a1d0a6` | `14034da1372383ba9a530a68ac027018053c50ccedee1a67060c3fa1e94f5cc9` | `0eda9e41caa997b65983542dc715598d93e586d152bfd1f0b56a8e5c45eb12f4` |

## Authorized Result

For every finite positive mass triple, the declared fixed-nonzero-angular-
momentum planar Newtonian three-body Hamiltonian is not completely integrable
by meromorphic first integrals in a complex neighborhood of the parabolic
Lagrange phase curve.

The qualified v3 transfer makes this project-owned rather than conditional:
the translation-reduced spatial Hamiltonian has the same local complete-
integrability obstruction near the embedded phase curve. Therefore no
complete shell-regular physically admissible meromorphic Liouville family can
exist on a qualified `WP2-MULTIQ-v1` atlas domain that contains that regular
neighborhood.

This is a substantive local nonintegrability theorem. It is not a proof that
the three-body problem has no additional first integral, nor a global result
over every phase-space domain. It does not cover non-meromorphic regularity,
zero angular momentum, nonzero-`Xi` magnetic dynamics, a general `SO(3)`
quotient, triple collision, or domains that avoid the obstructed neighborhood.

The parallel WP1 result is a work allocation, not a theorem of invariant
existence: 118 catalogue members are assigned to stable local-normal-form
work, 51 to asymptotic-manifold work, one exact mass case receives a
higher-variation overlay, and all 169 retain domain-restricted or
non-meromorphic options behind candidate-specific publication gates.

## Evidence Index

- Planar result: `notes/wp4-mr-repl-v1-result.md`
- Spatial/KS result: `notes/wp4-lift-ni-v3-result.md`
- WP1 residual map: `notes/wp1-residual-map-v1-result.md`
- Clean-host parity: `notes/wp4-mr-repl-v1-bobs-parity.md`
- Exact planar proof:
  `validation-external/wp4-mr-repl-v1/proof/WP4-MR-REPL-v1-proof.md`
- Spatial transfer addendum:
  `validation-external/wp4-lift-ni-v3/proof/WP4-LIFT-NI-v3-addendum.md`
