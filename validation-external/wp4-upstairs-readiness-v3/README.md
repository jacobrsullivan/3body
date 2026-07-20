# WP4 Upstairs Readiness v3

This control-only qualification tests whether the WP4 upstairs gauntlet
recognizes the declared known integrals and rejects false or functionally
dependent controls on the exact qualified `WP2-UPQ-v2` model.

It verifies the authoritative `WP3-UP-CAND-v3` bounded-null chain and the v3
candidate `NOT_TRIGGERED` decision. It does not consume a candidate expression
or open any publication-reserve row. `HARNESS_READY` is not a candidate,
integrability, non-integrability, or Morales-Ramis result.

```bash
./validation-external/wp4-upstairs-readiness-v3/run_qualification.sh freeze
./validation-external/wp4-upstairs-readiness-v3/run_qualification.sh run
./validation-external/wp4-upstairs-readiness-v3/run_qualification.sh verify
```
