# WP3-UP-CAND-v3

This corrective campaign searches the qualified `WP2-UP-v2` model after
removing, in coefficient space, the complete degree-three part of the `Xi=0`
constraint ideal and all represented fixed-parameter multiples of angular
momentum. It preserves exact conserved directions when handling finite-sample
value nuisance directions and compares invariant fold subspaces rather than
individual singular vectors.

The complete hypothesis class contains every combined-degree-three-or-less
monomial with at least one of the 14 canonical state variables and optional
fixed-energy and symmetric-mass factors. Exact physical-flow and S1-generator
derivatives are evaluated on development and disjoint calibration data. This
is a locked remediation using previously examined splits, not a fresh blind
confirmation.

The decision-bearing numerical runtime is pinned in
`runtime_requirements.txt`; cross-runtime replay is supplemental evidence and
cannot alter the frozen decision. The runner refuses to execute unless Python,
NumPy, and SciPy match the frozen `decision_runtime` exactly.

The sealed 24-case publication reserve is commitment-only input.  This
campaign cannot execute it.  A surviving mode can only trigger a new
candidate-specific qualification lock.

```bash
./validation-external/wp3-upstairs-candidate-v3/run_search.sh build
./validation-external/wp3-upstairs-candidate-v3/run_search.sh freeze
./validation-external/wp3-upstairs-candidate-v3/run_search.sh search
./validation-external/wp3-upstairs-candidate-v3/run_search.sh report
./validation-external/wp3-upstairs-candidate-v3/run_search.sh finalize
```
