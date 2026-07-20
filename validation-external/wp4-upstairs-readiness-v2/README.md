# WP4 Upstairs Readiness v2

This control-only qualification tests whether the WP4 upstairs gauntlet can
recognize known integrals and reject false or dependent controls on the exact
qualified `WP2-UPQ-v2` model.

It consumes the public WP2 qualification record and the immutable WP3-v2 null
chain: search lock, final record, staged gate, zero-candidate decision, and the
sealed reserve commitment file. It does not consume a candidate expression or
open any publication-reserve source row.

```bash
./validation-external/wp4-upstairs-readiness-v2/run_qualification.sh freeze
./validation-external/wp4-upstairs-readiness-v2/run_qualification.sh run
./validation-external/wp4-upstairs-readiness-v2/run_qualification.sh verify
```

`HARNESS_READY` is explicitly separate from `CANDIDATE_NOT_TRIGGERED` and is
not a WP4 candidate or Morales-Ramis result.
