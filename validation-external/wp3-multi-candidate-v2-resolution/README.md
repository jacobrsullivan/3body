# WP3-MULTI-CAND-v2 Candidate Resolution

This campaign resolves the single rank-one v2 spectral subspace under the
separately locked `WP3-MULTI-CAND-v2-RES-v1` protocol. Candidate coefficients
were not accessed before the specification lock. The campaign never reads or
executes the 24-case publication reserve.

```bash
./validation-external/wp3-multi-candidate-v2-resolution/run_resolution.sh build
./validation-external/wp3-multi-candidate-v2-resolution/run_resolution.sh test
./validation-external/wp3-multi-candidate-v2-resolution/run_resolution.sh freeze
./validation-external/wp3-multi-candidate-v2-resolution/run_resolution.sh execute
./validation-external/wp3-multi-candidate-v2-resolution/run_resolution.sh finalize
```

The possible outcomes are rejection, identification as an exact known
direction, a reproducible survivor, or a numerically reproducible direction
whose formula remains unresolved. None authorizes reserve access directly.
