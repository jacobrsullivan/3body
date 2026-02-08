---
name: wp5-reproducibility-package
description: Create reproducibility packages for scientific publication, including code repositories, data archives, containerized environments, and workflow automation. Use when packaging code for GitHub release, archiving data to Zenodo, creating Docker/conda environments, or setting up CI/CD pipelines. Triggers on requests involving reproducibility, FAIR data principles, artifact packaging, or open science practices.
---

# WP5 Reproducibility Package

Package code, data, and environments for independent replication.

## Package Components

| Component | Platform | Purpose |
|-----------|----------|---------|
| Code Repository | GitHub | Source code + documentation |
| Data Archive | Zenodo | Input data + results (with DOI) |
| Environment | Docker/conda | Containerized dependencies |
| Workflow | Snakemake | Automated reproduction |

**Target**: ACM/IEEE Reproducibility Badges (Results Replicated/Reproduced)

## Quick Start

```bash
# Create complete reproducibility package
python scripts/create_reproducibility_package.py \
  --results results/wp4/ \
  --code src/ \
  --tests tests/ \
  --output reproducibility/

# Test locally
cd reproducibility
docker build -t 3body-reproducibility .
docker run 3body-reproducibility

# Upload to Zenodo
zenodo upload reproducibility/ --title "3-Body Lift-Integrability"
```

## Package Structure

```
reproducibility/
├── README.md              # How to reproduce
├── INSTALL.md             # Installation instructions
├── LICENSE                # MIT or BSD-3-Clause
├── environment.yml        # Conda environment
├── requirements.txt       # Pip fallback
├── Dockerfile             # Containerized environment
├── Snakefile              # Workflow automation
├── Makefile               # Build shortcuts
├── data/
│   ├── trajectories.h5    # Input data
│   ├── validation_results.parquet
│   └── checksums.sha256   # Integrity verification
├── scripts/
│   ├── run_all_validations.py
│   └── generate_figures.py
├── tests/
│   └── test_reproducibility.py
└── expected_results/
    ├── figure1.pdf
    ├── figure2.pdf
    └── table1.csv
```

## Code Repository (GitHub)

### Repository Structure

```python
from src.python.publication.repo_packager import RepoPackager

packager = RepoPackager(
    repo_name='3body-lift-integrability',
    license='MIT',
    author='Your Name',
    email='your.email@institution.edu'
)

# Add components
packager.add_source_code('src/')
packager.add_tests('tests/')
packager.add_documentation('User-Guides/', 'Project-Design-Docs/')
packager.add_examples('examples/')

# Generate repo structure
packager.create_package('output/github/')
```

### Essential Files

**README.md**:
```markdown
# 3-Body Lift-Integrability

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview
Investigation of lift-integrability in the Newtonian three-body problem.

## Quick Start
```bash
conda env create -f environment.yml
conda activate 3body
python scripts/run_validation.py
```

## Citation
If you use this code, please cite:
```bibtex
@article{author2025lift,
  title={Discovery of Hidden Integrability...},
  author={Author, A.},
  journal={Physical Review Letters},
  year={2025}
}
```
```

**LICENSE** (MIT):
```text
MIT License

Copyright (c) 2025 [Author Name]

Permission is hereby granted, free of charge, to any person obtaining a copy...
```

### GitHub Actions CI

**.github/workflows/test.yml**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: conda-incubator/setup-miniconda@v3
      with:
        environment-file: environment.yml
    - name: Run tests
      run: pytest tests/ -v
    - name: Run reproducibility check
      run: python scripts/verify_reproducibility.py
```

## Data Archive (Zenodo)

### Preparing Data Package

```python
from src.python.publication.data_packager import DataPackager

packager = DataPackager()

# Add data files with metadata
packager.add_file(
    path='data/trajectories.h5',
    description='High-precision CR3BP trajectories (Tier 2)',
    format='HDF5',
    size_mb=450
)

packager.add_file(
    path='results/validation_results.parquet',
    description='WP4 validation results',
    format='Parquet',
    size_mb=25
)

# Generate checksums
packager.generate_checksums()

# Create Zenodo metadata
metadata = packager.create_zenodo_metadata(
    title='3-Body Lift-Integrability: Data and Results',
    description='Reproducibility data for lift-integrability paper',
    creators=[{'name': 'Author, A.', 'affiliation': 'University'}],
    keywords=['three-body problem', 'integrability', 'celestial mechanics'],
    license='CC-BY-4.0'
)

# Export package
packager.export('zenodo_package/')
```

### Zenodo Upload

```bash
# Install zenodo-client
pip install zenodo-client

# Upload to Zenodo (sandbox for testing)
zenodo-client upload zenodo_package/ \
  --sandbox \
  --metadata zenodo_metadata.json

# Upload to production
zenodo-client upload zenodo_package/ \
  --metadata zenodo_metadata.json

# Returns DOI: 10.5281/zenodo.XXXXXXX
```

### FAIR Data Compliance

| Principle | Implementation |
|-----------|----------------|
| **F**indable | DOI, rich metadata, keywords |
| **A**ccessible | Open access, standard protocols |
| **I**nteroperable | Standard formats (HDF5, Parquet) |
| **R**eusable | Clear license, documentation |

## Computational Environment

### Conda Environment

**environment.yml**:
```yaml
name: 3body
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - numpy>=1.24
  - scipy>=1.11
  - sympy>=1.12
  - h5py>=3.9
  - pyarrow>=13.0
  - matplotlib>=3.8
  - rebound>=3.28
  - pytest>=7.4
  - pip:
    - pysr>=0.16
    - torch>=2.0
```

### Docker Container

**Dockerfile**:
```dockerfile
FROM continuumio/miniconda3:latest

WORKDIR /app

# Copy environment
COPY environment.yml .
RUN conda env create -f environment.yml

# Copy code and data
COPY src/ src/
COPY scripts/ scripts/
COPY data/ data/
COPY tests/ tests/

# Set environment
SHELL ["conda", "run", "-n", "3body", "/bin/bash", "-c"]

# Run validation
CMD ["python", "scripts/run_all_validations.py"]
```

### Building and Testing

```bash
# Build Docker image
docker build -t 3body-reproducibility .

# Run validation
docker run 3body-reproducibility

# Interactive shell
docker run -it 3body-reproducibility /bin/bash

# Mount local directory for development
docker run -v $(pwd)/results:/app/results 3body-reproducibility
```

## Workflow Automation

### Snakemake Pipeline

**Snakefile**:
```python
# Configuration
configfile: "config.yaml"

# Final targets
rule all:
    input:
        "results/validation_summary.json",
        "figures/figure1.pdf",
        "figures/figure2.pdf",
        "figures/figure3.pdf"

# Generate trajectories
rule generate_trajectories:
    output:
        "data/trajectories.h5"
    shell:
        "python scripts/generate_trajectories.py --output {output}"

# Run WP4.1 analytical validation
rule analytical_validation:
    input:
        "data/trajectories.h5"
    output:
        "results/analytical_validation.json"
    shell:
        "python scripts/run_analytical_validation.py --input {input} --output {output}"

# Run WP4.2 Morales-Ramis test
rule morales_ramis:
    input:
        "data/trajectories.h5"
    output:
        "results/morales_ramis.json"
    shell:
        "python scripts/run_morales_ramis.py --input {input} --output {output}"

# Run WP4.3 Monte Carlo validation
rule monte_carlo:
    input:
        "data/trajectories.h5"
    output:
        "results/monte_carlo.json"
    shell:
        "python scripts/run_monte_carlo.py --input {input} --output {output}"

# Consolidate results
rule consolidate:
    input:
        analytical="results/analytical_validation.json",
        morales_ramis="results/morales_ramis.json",
        monte_carlo="results/monte_carlo.json"
    output:
        "results/validation_summary.json"
    shell:
        "python scripts/consolidate_results.py --output {output}"

# Generate figures
rule figures:
    input:
        "results/validation_summary.json"
    output:
        "figures/figure1.pdf",
        "figures/figure2.pdf",
        "figures/figure3.pdf"
    shell:
        "python scripts/generate_figures.py --input {input} --output-dir figures/"
```

### Running the Pipeline

```bash
# Dry run (show what would be executed)
snakemake -n

# Run with 4 cores
snakemake --cores 4

# Generate DAG visualization
snakemake --dag | dot -Tpdf > dag.pdf

# Force re-run of specific rule
snakemake --forcerun monte_carlo
```

## Verification Scripts

### Reproducibility Test

**scripts/verify_reproducibility.py**:
```python
#!/usr/bin/env python3
"""Verify that results are reproducible."""

import hashlib
import json
from pathlib import Path

def compute_checksum(filepath):
    """Compute SHA256 checksum of file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_checksums(checksum_file='data/checksums.sha256'):
    """Verify all checksums match."""
    with open(checksum_file) as f:
        expected = dict(line.strip().split('  ') for line in f)

    errors = []
    for filepath, expected_hash in expected.items():
        if not Path(filepath).exists():
            errors.append(f"Missing: {filepath}")
            continue
        actual_hash = compute_checksum(filepath)
        if actual_hash != expected_hash:
            errors.append(f"Mismatch: {filepath}")

    if errors:
        print("REPRODUCIBILITY CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("REPRODUCIBILITY CHECK PASSED")
    return True

def verify_results(expected_dir='expected_results/', actual_dir='results/'):
    """Compare actual results to expected."""
    # Compare key metrics
    with open(f'{expected_dir}/validation_summary.json') as f:
        expected = json.load(f)
    with open(f'{actual_dir}/validation_summary.json') as f:
        actual = json.load(f)

    # Allow small numerical differences
    tolerance = 1e-10
    for key in ['monte_carlo_pass_rate', 'mean_conservation_error']:
        diff = abs(expected[key] - actual[key])
        if diff > tolerance:
            print(f"Result mismatch: {key}")
            return False

    print("RESULTS VERIFICATION PASSED")
    return True

if __name__ == '__main__':
    success = verify_checksums() and verify_results()
    exit(0 if success else 1)
```

## Complete Packaging Workflow

```python
def create_full_package(results_dir, output_dir):
    """Create complete reproducibility package."""
    from src.python.publication.repo_packager import RepoPackager
    from src.python.publication.data_packager import DataPackager
    from src.python.publication.env_packager import EnvironmentPackager

    print("=== Creating Reproducibility Package ===\n")

    # 1. Code repository
    print("1. Packaging code repository...")
    repo = RepoPackager(repo_name='3body-lift-integrability')
    repo.add_source_code('src/')
    repo.add_tests('tests/')
    repo.add_documentation('User-Guides/')
    repo.create_package(f'{output_dir}/github/')

    # 2. Data archive
    print("2. Packaging data archive...")
    data = DataPackager()
    data.add_directory('data/')
    data.add_directory(results_dir)
    data.generate_checksums()
    data.export(f'{output_dir}/zenodo/')

    # 3. Environment
    print("3. Creating environment files...")
    env = EnvironmentPackager()
    env.create_conda_env('environment.yml')
    env.create_dockerfile('Dockerfile')
    env.create_requirements('requirements.txt')
    env.export(f'{output_dir}/')

    # 4. Workflow
    print("4. Creating workflow automation...")
    create_snakefile(f'{output_dir}/Snakefile')
    create_makefile(f'{output_dir}/Makefile')

    # 5. Documentation
    print("5. Generating documentation...")
    create_readme(f'{output_dir}/README.md')
    create_install_guide(f'{output_dir}/INSTALL.md')
    create_reproducibility_guide(f'{output_dir}/REPRODUCIBILITY.md')

    # 6. Verification
    print("6. Creating verification scripts...")
    copy_verification_scripts(f'{output_dir}/scripts/')

    print("\n=== Package Complete ===")
    print(f"Output: {output_dir}/")
    print("\nNext steps:")
    print("  1. Test locally: docker build && docker run")
    print("  2. Push to GitHub: git push origin main")
    print("  3. Upload to Zenodo: zenodo upload zenodo/")

# Usage
create_full_package('results/wp4/', 'reproducibility/')
```

## Common Issues

**Docker build fails?**
- Check Dockerfile syntax
- Verify base image availability
- Check network access for package downloads

**Checksum mismatch?**
- Regenerate checksums after any data update
- Check for file encoding issues
- Verify no unintended modifications

**Snakemake rule fails?**
- Check input file dependencies
- Verify script paths are correct
- Run with `-p` for detailed output

**Zenodo upload fails?**
- Check API token is valid
- Verify metadata format
- Check file size limits (50GB max)

## Tests

```bash
pytest tests/wp5/test_repo_packager.py -v
pytest tests/wp5/test_data_packager.py -v
pytest tests/wp5/test_env_packager.py -v
```

## References

- `src/python/publication/repo_packager.py` - Code packaging
- `src/python/publication/data_packager.py` - Data packaging
- `src/python/publication/env_packager.py` - Environment packaging
- ACM Reproducibility Badges: https://www.acm.org/publications/policies/artifact-review-and-badging-current
- FAIR Principles: https://www.go-fair.org/fair-principles/
- Zenodo: https://zenodo.org/
