# WP4-LIFT-NI-v3

This successor campaign reruns the unchanged qualified v2 spatial/KS transfer
and replaces the external planar premise with `WP4-MR-REPL-v1`.

```bash
./validation-external/wp4-lift-ni-v3/run_qualification.sh test
./validation-external/wp4-lift-ni-v3/run_qualification.sh freeze
./validation-external/wp4-lift-ni-v3/run_qualification.sh execute
./validation-external/wp4-lift-ni-v3/run_qualification.sh finalize
./validation-external/wp4-lift-ni-v3/run_qualification.sh verify
```

The four PDF arguments are inherited source-comparison inputs from v2. The
decision-bearing planar NVE/Galois premise is the frozen MR reproduction
record, not those comparison papers.
