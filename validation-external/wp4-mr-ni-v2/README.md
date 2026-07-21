# WP4-MR-NI-v2

This separately locked campaign replicates and applies the exact mass
arithmetic and claim boundary of two published planar three-body
non-integrability analyses. It uses `fractions.Fraction` in production and a
source-disjoint SymPy reference. It does not use the repository's incomplete
legacy Kovacic placeholder and does not validate WP3 candidates.

The source PDFs are not redistributed. Execution requires local copies whose
SHA-256 hashes match `sources/manifest.json`:

```bash
./validation-external/wp4-mr-ni-v2/run_qualification.sh test
./validation-external/wp4-mr-ni-v2/run_qualification.sh freeze
./validation-external/wp4-mr-ni-v2/run_qualification.sh execute
./validation-external/wp4-mr-ni-v2/run_qualification.sh finalize
```

`TSYGVINTSEV_PDF` and `BOUCHER_WEIL_PDF` may override the default `/tmp`
paths. The campaign verifies both hashes before reading either source.
