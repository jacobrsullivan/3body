# WP5-PUB-v1 bobs-mini parity

Date: 2026-07-24

## Scope

The publication package was reproduced from an isolated clean clone at
`/Users/bob/Desktop/3body-wp5-pub-v1` on `bobs-mini`. The checkout was pinned
to pushed commit `900119268a81345eae3e7573f3693fe6c1099460`.

The canonical `/Users/bob/Desktop/3body` checkout was not modified.

## Runtime

| Component | Value |
| --- | --- |
| Platform | macOS 26.5.2, arm64 |
| Python | 3.11.15 |
| SymPy | 1.14.0 |
| pytest | 8.4.1 |
| Tectonic | 0.16.9 |
| Poppler | 26.07.0 |

Tectonic and Poppler were installed with Homebrew. The first cache-only TeX
attempt failed as expected on the fresh host; the wrapper enabled downloads,
populated the bundle, and completed the build.

## Result

The unmodified command

```bash
WP5_PYTHON=/Users/bob/micromamba/envs/3body-legacy-v1/bin/python \
  ./scripts/reproduce_wp5_pub_v1.sh --core
```

returned `READY_FOR_EXTERNAL_REVIEW` with every internal gate passing.

| Evidence | Local | bobs-mini |
| --- | --- | --- |
| Artifact-manifest SHA-256 | `cf42a6eb...0053` | `cf42a6eb...0053` |
| PDF SHA-256 | `7470d736...585d` | `7470d736...585d` |
| PDF pages/bytes | 9 / 86,928 | 9 / 86,928 |
| Generic fields | 32 | 32 |
| Normalized generic SHA-256 | `4f8f9774...5678` | `4f8f9774...5678` |
| Exact frozen-payload equality | PASS | PASS |
| Generic runtime | 685.10 s | 580.64 s |

The complete bobs-mini wrapper took 582.65 seconds. The checkout remained
clean after rebuilding the PDF and artifact manifest.

The machine-readable supplemental record is
`validation-external/wp5-pub-v1/reports/wp5_pub_v1_bobs_mini_replay.json`.

## Boundary

This is second-host portability evidence, not external clean-room evidence.
`bobs-mini` is project-controlled hardware. No independent human mathematical
review occurred, so this run cannot satisfy any locked external gate.
