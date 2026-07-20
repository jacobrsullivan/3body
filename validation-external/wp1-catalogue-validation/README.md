# WP1-CAT-v1

This is a locked, bounded qualification of native Earth-Moon planar Lyapunov
family generation.  It intentionally does not claim a complete CR3BP or
three-body periodic-orbit catalogue.

Run the phases separately so the lock and pre-holdout gate are inspectable:

```bash
./validation-external/wp1-catalogue-validation/run_qualification.sh prepare
./validation-external/wp1-catalogue-validation/run_qualification.sh holdout
```

`prepare` creates the disjoint corpus, generates the native candidates without
an external data input, freezes all evidence-bearing inputs, and evaluates only
development and calibration.  `holdout` verifies the lock, refuses execution
unless both prior splits passed, evaluates the sealed split, and writes the
immutable qualification record and report.
