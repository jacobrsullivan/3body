# WP3-MULTI-CAND-v2 Corrected Candidate Resolution

This campaign supersedes the nonconformant `WP3-MULTI-CAND-v2-RES-v1`
decision without modifying any predecessor artifact. It tests whether the
rank-one candidate is an alternate feature representation of the known
total-angular-momentum-squared observable.

The correction is necessary because the active feature library has a large
value-nuisance kernel. Coefficient vectors are therefore non-unique, and raw
coefficient projection cannot decide whether two directions represent the
same observable function.

The campaign fits a single candidate-to-`L^2` scale on frozen training rows,
holds it fixed on calibration and challenge rows, repeats the comparison for
three SVD backends in observable response space, and checks exact-rational
challenge states with a source-disjoint 80-digit physical `L^2` evaluator.
The 24-case publication reserve remains sealed.

Commands:

```bash
./validation-external/wp3-multi-candidate-v2-resolution-v2/run_resolution.sh test
./validation-external/wp3-multi-candidate-v2-resolution-v2/run_resolution.sh freeze
./validation-external/wp3-multi-candidate-v2-resolution-v2/run_resolution.sh execute
./validation-external/wp3-multi-candidate-v2-resolution-v2/run_resolution.sh finalize
```
