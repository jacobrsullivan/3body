# WP4-LIFT-NI-v2

This corrective campaign qualifies the theorem that shell-regular physically
admissible meromorphic Liouville integrability of the frozen multi-chart KS
lift would descend to the spatial physical three-body system, where a
conditional Morales-Ramis/monodromy obstruction applies.

V1 is explicitly invalidated because its ambient rank premise did not imply
rank on the physical shell. The corrected claim specification was committed
and locked before the v2 implementation.
The production checker uses exact rational arithmetic without SymPy. A
source-disjoint SymPy implementation differentiates the defining expressions
independently. Four primary-source PDFs are required only at execution and
must match the SHA-256 values in `sources/manifest.json`.

```bash
./validation-external/wp4-lift-ni-v2/run_qualification.sh test
./validation-external/wp4-lift-ni-v2/run_qualification.sh freeze
./validation-external/wp4-lift-ni-v2/run_qualification.sh execute
./validation-external/wp4-lift-ni-v2/run_qualification.sh finalize
./validation-external/wp4-lift-ni-v2/run_qualification.sh verify
```

The default source locations under `/tmp` may be overridden with
`MARSDEN_WEINSTEIN_PDF`, `TSYGVINTSEV_PDF`, `BOUCHER_WEIL_PDF`, and
`DULLIN_MONTGOMERY_PDF`.
