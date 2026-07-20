# WP2-UP-v1 qualification

This campaign qualifies a canonical one-channel KS Hamiltonian for the
translation-reduced Newtonian three-body problem.  It consumes the locked
spatial N3BP, isolated Kepler/KS, and three-body-flow records.  Development and
calibration are executed before the code/data lock; the reserved transformation
holdout can run only after that lock verifies.

```bash
./validation-external/wp2-up-validation/run_qualification.sh build
./validation-external/wp2-up-validation/run_qualification.sh prepare
./validation-external/wp2-up-validation/run_qualification.sh freeze
./validation-external/wp2-up-validation/run_qualification.sh holdout
./validation-external/wp2-up-validation/run_qualification.sh finalize
```

The claim is intentionally limited to the selected Jacobi binary channel and
does not imply simultaneous regularization, a new invariant, or integrability.
