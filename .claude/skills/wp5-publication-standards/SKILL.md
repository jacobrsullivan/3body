---
name: wp5-publication-standards
description: Use when preparing manuscript, proofs, or code for publication. Points to WP5 consolidation workflow.
---

# WP5 Publication Workflow

## Source of Truth
- **User Guide**: `User-Guides/User-Guide-WP5.md`
- **Visualization**: `src/python/visualization/publication_plots.py`
- **Manuscript Template**: `manuscript/main.tex` (if exists)

## Manuscript Structure
See `User-Guides/User-Guide-WP5.md` Section 1

**LaTeX Standards**:
- Document class: `amsart` or journal-specific
- Theorem environments: `\newtheorem{theorem}{Theorem}`
- Bibliography: BibTeX (`.bib` file)

## Figure Standards
**Format**: PDF (vector), not PNG
**Font size**: 10-12pt
**Color**: Colorblind-safe (matplotlib 'tab10' or 'viridis')

**Tool**: `src/python/visualization/publication_plots.py`

## Code Release
**Checklist**:
1. Format: `black src/ tests/`
2. Lint: `flake8 src/ tests/`
3. Tests pass: `./scripts/run_tests.sh`
4. Reproducibility: Reference dataset validates

**Zenodo Workflow**: See `User-Guides/User-Guide-WP5.md` Section 3
