# Reproducing WP5-PUB-v1

## Core environment

The core replay requires:

- Python 3.11 or newer;
- SymPy 1.14.0;
- pytest 8.4.1;
- Tectonic 0.16.9;
- Poppler `pdfinfo` and `pdftotext`; and
- a clean checkout containing the pinned WP1--WP4 evidence.

Install the Python packages into an isolated environment:

```bash
python -m pip install -r publication/wp5-pub-v1/requirements-publication.txt
```

Tectonic and Poppler are system dependencies. On macOS with Homebrew:

```bash
brew install tectonic poppler
```

## One-command replay

From the repository root:

```bash
./scripts/reproduce_wp5_pub_v1.sh --core
```

The command:

1. compiles `main.tex` with a fixed `SOURCE_DATE_EPOCH`, preferring the local
   Tectonic bundle cache and enabling downloads only when that cache is
   incomplete;
2. copies the inspected publication PDF to
   `output/pdf/wp5-pub-v1-manuscript.pdf`;
3. rebuilds the canonical artifact manifest;
4. verifies the specification lock and every predecessor hash;
5. validates the claim ledger and proof dependency graph;
6. reruns the generic source-disjoint symbolic derivation;
7. compares every decision-bearing field with the frozen payload after
   removing only `elapsed_seconds`;
8. runs publication-specific tests and adversarial controls; and
9. writes a replay report under `build/wp5-pub-v1/`.

The generic exact derivation takes approximately 10--15 minutes on the
qualified Apple Silicon hosts. `--static` performs all package, manuscript,
PDF, hash, graph, and adversarial checks without rerunning that derivation.

## Full legacy replay

The optional full mode also runs the three disjoint legacy lanes:

```bash
./scripts/reproduce_wp5_pub_v1.sh --full
```

This requires the pinned environment in `environment-legacy.yml`, an active
matching `CONDA_PREFIX`, and the in-place `qd_python` extension. The expected
partition is:

- fast: ordinary deterministic tests;
- slow: qualified long simulations; and
- quarantine: strict expected failures or declared skips only.

The legacy partition is software-regression evidence. It is not mathematical
evidence for the theorem.

## External clean-room receipt

An external reproducer must use hardware and an account not controlled by the
project. Before running, record:

```bash
git rev-parse HEAD
shasum -a 256 publication/wp5-pub-v1/artifact_manifest.json
shasum -a 256 publication/wp5-pub-v1/manuscript/main.pdf
```

After a successful `--core` replay, complete a receipt conforming to
`validation-external/wp5-pub-v1/review/clean_room_receipt_schema.json`,
sign it by one of the permitted methods, and return both the JSON receipt and
signature artifact. A run on `bobs-mini`, Navillus, or another
project-controlled machine is useful portability evidence but cannot satisfy
the external clean-room gate.

## Reproducibility boundary

Primary papers are not redistributed. Their URLs and downloaded PDF hashes
are pinned in the scientific source manifest. Rebuilding the PDF and generic
payload does not itself constitute independent mathematical peer review.
