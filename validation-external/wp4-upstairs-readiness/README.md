# WP4 Upstairs Readiness

This control-only qualification tests whether the WP4 upstairs gauntlet can
recognize known integrals and reject false or dependent controls on the exact
qualified `WP2-UPQ-v2` model.

It consumes only the public WP2 qualification record and the public
machine-readable WP3 staged gate. It does not consume candidate data or read
the sealed publication reserve.

```bash
./validation-external/wp4-upstairs-readiness/run_qualification.sh freeze
./validation-external/wp4-upstairs-readiness/run_qualification.sh run
./validation-external/wp4-upstairs-readiness/run_qualification.sh verify
```

`HARNESS_READY` is explicitly separate from `CANDIDATE_NOT_TRIGGERED` and is
not a WP4 candidate or Morales-Ramis result.
