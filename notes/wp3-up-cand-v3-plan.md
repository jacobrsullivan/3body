# WP3-UP-CAND-v3 Corrective Plan

## Defect Being Corrected

V2 included exact controls `h Li`, `s2 Li`, and `s3 Li` in its parameter-aware
grammar but removed only bare one-hot controls. Its approximate finite-sample
value quotient then distorted those exact directions, so zero reported
candidates did not establish a library null result.

## Locked Method

1. Retain all 1,120 combined-degree-three-or-less monomials containing a state
   factor.
2. Remove in coefficient space the rank-30 known module: the complete
   degree-three `Xi` constraint ideal and all represented parameter multiples
   of the three angular momenta.
3. Solve the generalized Lie/value problem while optimizing finite-sample
   value-nuisance directions instead of discarding them as identities.
4. Treat repeated or numerically unresolved singular directions as complete
   subspaces. A bounded null requires the backend-guarded lower bound on the
   smallest generalized singular value to exceed the frozen training gate;
   individual SVD basis vectors can never establish that null.
5. Extend every fold-mode boundary through the complete singular cluster that
   intersects it, so fold projections do not depend on an arbitrary basis
   rotation.
6. Evaluate exact S1-generator derivatives and finite gauge-orbit spreads.
7. Compare lowest-mode fold subspaces, not basis-dependent singular vectors.
8. Require disjoint calibration, trajectory drift, and all known-module gates
   before any candidate can trigger a separately sealed qualification.

This remediation reuses previously examined development and calibration data.
It can yield bounded corrective evidence, not fresh confirmatory evidence.
