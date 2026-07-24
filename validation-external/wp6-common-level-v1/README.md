# WP6-COMMON-v1

This campaign qualifies the pinned common-level rational
nonintegrability theorem for the planar positive-mass three-body problem
on every `(H,C)=(h,c)!=(0,0)`.

The campaign is intentionally theorem-audit evidence. It reproduces exact
branch, conic, Euler-Moulton, discriminant, and NVE-coefficient invariants
but relies on the pinned published proof for the universal
differential-Galois lemmas.

## Commands

```bash
./validation-external/wp6-common-level-v1/run_qualification.sh test
./validation-external/wp6-common-level-v1/run_qualification.sh freeze
./validation-external/wp6-common-level-v1/run_qualification.sh execute
./validation-external/wp6-common-level-v1/run_qualification.sh finalize
./validation-external/wp6-common-level-v1/run_qualification.sh verify
```

`execute` expects the two exact source PDFs at the defaults in
`run_qualification.sh`. The paths can be overridden with
`MPC_2025_PDF` and `COMBOT_2011_PDF`.
