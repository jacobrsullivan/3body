# WP5: Consolidation and Publication
## Skills and Subagents List

**Work Package**: WP5 - Consolidation and Publication
**Purpose**: Transform validated results into publication-ready scientific contributions
**Duration**: 31-45 days (6 weeks)
**Key Activities**: Formal proof writing, reproducibility packaging, manuscript preparation, journal submission

---

## Overview

WP5 is the **dissemination phase** where WP4 validation results are consolidated into rigorous proofs, packaged for reproducibility, and communicated through peer-reviewed publications. This applies to **both positive and negative results**.

---

## 1. Agent Skills

### 1.1 Mathematical Proof Writing

**Name**: `wp5-proof-writing`

**Description**: Use when constructing formal mathematical proofs from WP4 validation evidence. Provides LaTeX templates, proof structure, and theorem statement guidelines.

**When to Invoke**:
- User requests "write proof", "theorem statement", "formal mathematics"
- WP 5.1 formal proof construction
- Converting validation results to publication format

**Workflow**:
```markdown
# Mathematical Proof Writing

## Theorem Statement Template

### Positive Result (Integral Discovered)
```latex
\begin{theorem}[Lift-Integrability of the Planar 3BP]
Let $\mathcal{M}$ denote the reduced shape space of the planar circular restricted three-body problem, and let $\widetilde{\mathcal{M}} = \mathcal{M} \times S^1$ be the S¹ principal bundle over $\mathcal{M}$ with extended symplectic form $\widetilde{\omega}$.

There exists a $C^k$ function $\widetilde{I}: T^*\widetilde{\mathcal{M}} \to \mathbb{R}$ such that:
\begin{enumerate}
  \item \textbf{Conservation}: $\{\widetilde{I}, \widetilde{H}\}_{\widetilde{\omega}} = 0$
  \item \textbf{Functional Independence}: $\widetilde{I}$ is functionally independent of $E, L, p_\theta$
  \item \textbf{Non-Projectability}: $\widetilde{I}$ does not descend to the base manifold $\mathcal{M}$
\end{enumerate}

Moreover, the identity component of the differential Galois group of the Normal Variational Equation around typical periodic orbits in $\mathcal{M}$ is non-abelian, confirming non-integrability on the base manifold.
\end{theorem}
```

### Negative Result (No Integral Found)
```latex
\begin{theorem}[Computational Bounds on Lift-Integrability]
Under the computational search bounds $\mathcal{B} = \{\deg(I) \leq N, \text{Killing fields on } \Gamma_h\}$ where $\Gamma_h$ is a mesh of size $h$, no additional conserved quantity $\widetilde{I}$ exists in the lifted phase space $T^*\widetilde{\mathcal{M}}$ that is functionally independent of $E, L, p_\theta$.

The differential Galois group analysis confirms that the system is non-integrable on the reduced manifold $\mathcal{M}$, consistent with the absence of additional integrals on the lifted space within the search bounds.
\end{theorem}
```

## Proof Structure

### Standard Proof Template
```latex
\begin{proof}
\textbf{Part 1: Explicit Construction}
We construct the integral $\widetilde{I}$ as follows:
\[ \widetilde{I}(s, \theta, p_s, p_\theta) = \text{[explicit expression]} \]

\textbf{Part 2: Conservation}
To verify $\{\widetilde{I}, \widetilde{H}\} = 0$, we compute the Poisson bracket:
\begin{align*}
  \{\widetilde{I}, \widetilde{H}\} &= \sum_i \left( \frac{\partial \widetilde{I}}{\partial s^i} \frac{\partial \widetilde{H}}{\partial p_i} - \frac{\partial \widetilde{I}}{\partial p_i} \frac{\partial \widetilde{H}}{\partial s^i} \right) + \cdots \\
  &= 0 \quad \text{(by explicit computation, see Supplementary Material)}
\end{align*}

\textbf{Part 3: Functional Independence}
The Jacobian matrix of $(E, L, p_\theta, \widetilde{I})$ has rank 4 almost everywhere, verified numerically on $10^4$ sample points with success rate 99.7\%.

\textbf{Part 4: Non-Projectability (Morales-Ramis)}
The Morales-Ramis criterion applied to three representative periodic orbits yields non-abelian Galois groups (Table~\ref{tab:galois}), proving non-integrability on $\mathcal{M}$. Therefore, $\widetilde{I}$ cannot descend to the base manifold.

\textbf{Part 5: Numerical Validation}
Monte Carlo integration over $4.5 \times 10^5$ trajectories spanning the accessible parameter space confirms conservation with relative error $|\Delta \widetilde{I}| / |\widetilde{I}| < 10^{-6}$ for 95.8\% of cases (Fig.~\ref{fig:validation}).
\end{proof}
```

## Lemmas and Supporting Results

**Lemma 1**: Extended Symplectic Form
**Lemma 2**: Connection and Curvature Calculation
**Lemma 3**: Poisson Bracket Computation

## References
- Knuth et al. (1989): "Mathematical Writing"
- WP 5.1.4: Mathematical Exposition
```

**Supporting Assets**:
- `latex/theorem_templates.tex`
- `latex/proof_templates.tex`

---

### 1.2 Reproducibility Checklist

**Name**: `wp5-reproducibility-checklist`

**Description**: Use when verifying that all reproducibility requirements are met. Provides comprehensive checklist for code, data, documentation, and environment.

**When to Invoke**:
- User requests "check reproducibility", "verify package complete"
- WP 5.2 reproducibility package
- Before public release

**Workflow**:
```markdown
# Reproducibility Checklist

## Category 1: Code Repository

### Essential Files
- [ ] README.md (project overview, quick start)
- [ ] LICENSE (MIT or BSD-3 preferred)
- [ ] requirements.txt or environment.yml
- [ ] setup.py or pyproject.toml
- [ ] .gitignore
- [ ] CITATION.cff (citation metadata)

### Code Organization
- [ ] src/ directory with all source code
- [ ] tests/ directory with test suite
- [ ] docs/ directory with documentation
- [ ] scripts/ for reproduction scripts
- [ ] examples/ or notebooks/ for tutorials

### Documentation
- [ ] Every function has docstring
- [ ] Every module has purpose statement
- [ ] API documentation (Sphinx or similar)
- [ ] Tutorial notebooks (at least 3)
- [ ] Installation instructions
- [ ] Usage examples

### Testing
- [ ] Test suite with >85% coverage
- [ ] All tests pass (pytest --cov)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Cross-platform tested (Linux, macOS, Windows if applicable)

## Category 2: Data Artifacts

### Datasets
- [ ] Representative trajectories (1000+)
- [ ] Validated integrals (with expressions)
- [ ] Validation results (WP4 outputs)
- [ ] Geometric data (connection, curvature)

### Format
- [ ] HDF5 for large arrays
- [ ] JSON for metadata
- [ ] CSV for tabular results
- [ ] Compressed appropriately

### Archival
- [ ] Uploaded to Zenodo or Figshare
- [ ] DOI assigned
- [ ] Linked from repository README
- [ ] Citation information included

## Category 3: Computational Environment

### Environment Specification
- [ ] Conda environment.yml OR
- [ ] Docker container OR
- [ ] requirements.txt with pinned versions

### Versions Documented
- [ ] Python version
- [ ] Key dependencies (numpy, scipy, etc.)
- [ ] OS and compiler (if relevant)
- [ ] Hardware used for main results

### Reproducibility Test
- [ ] Independent researcher can install
- [ ] Can run reproduction script
- [ ] Results match within tolerance

## Category 4: Main Results

### Figures
- [ ] All main figures reproducible
- [ ] Scripts generate figures from data
- [ ] Publication-quality resolution (300 DPI)
- [ ] Source data included

### Tables
- [ ] All tables generated from data
- [ ] CSV source files included
- [ ] Generation scripts provided

### Key Numbers
- [ ] All quantitative claims reproducible
- [ ] Statistical tests documented
- [ ] Random seeds specified where applicable

## Category 5: Publication Materials

### Manuscript
- [ ] Main text (LaTeX source)
- [ ] Supplementary materials
- [ ] Bibliography (BibTeX)
- [ ] Figures in separate files

### Preprint
- [ ] arXiv uploaded
- [ ] DOI obtained
- [ ] Linked to code/data

## Verification Script

```python
def verify_reproducibility():
    checks = {
        "Repository structure": check_repo_structure(),
        "Documentation": check_docs_complete(),
        "Test coverage": check_test_coverage() > 0.85,
        "Data archival": check_zenodo_doi(),
        "Environment": check_environment_spec(),
        "Main results": check_main_results_reproducible()
    }

    all_pass = all(checks.values())

    if all_pass:
        print("✓ Reproducibility package COMPLETE")
        return True
    else:
        print("✗ Missing requirements:")
        for name, passed in checks.items():
            if not passed:
                print(f"  - {name}")
        return False
```

## References
- Sandve et al. (2013): "Ten Simple Rules for Reproducible Computational Research"
- WP 5.2: Reproducibility Package
```

**Supporting Assets**:
- `scripts/verify_reproducibility.py`
- `docs/reproducibility_guide.md`

---

### 1.3 Manuscript Structure Guide

**Name**: `wp5-manuscript-structure`

**Description**: Use when drafting scientific manuscript. Provides structure templates for different journal formats (Nature Physics, PRL, Phys Rev E).

**When to Invoke**:
- User requests "write manuscript", "paper structure", "draft article"
- WP 5.3 publication preparation
- Different journal targets

**Workflow**:
```markdown
# Manuscript Structure Guide

## Format 1: Nature Physics / PRL (Short Format)

### Abstract (150-200 words)
- **Sentence 1**: Problem and motivation
- **Sentences 2-3**: Approach and key innovation
- **Sentences 4-5**: Main results (quantitative)
- **Sentence 6**: Significance and implications

### Main Text (4-6 pages)
1. **Introduction** (800-1000 words)
   - Historical context (Bruns, Poincaré)
   - Problem statement (3BP non-integrability)
   - Prior attempts and limitations
   - Our hypothesis and contribution

2. **Results** (1500-2000 words)
   - Lifted phase space construction
   - Discovered integral (explicit form)
   - Conservation verification (key figures)
   - Parameter space validation

3. **Discussion** (600-800 words)
   - Physical interpretation
   - Comparison to prior work
   - Implications for integrability theory
   - Future directions

4. **Methods** (800-1000 words)
   - Computational methods (brief)
   - Validation framework (brief)
   - Reference to supplementary for details

### Figures (4-6)
- Figure 1: Schematic of lift construction
- Figure 2: Integral expression and conservation plot
- Figure 3: Parameter space validation heatmap
- Figure 4: Comparison with known integrals

### Supplementary Information (20-40 pages)
- Mathematical details
- Computational methods
- Extended validation
- Additional figures

## Format 2: Physical Review E (Full Format)

### Abstract (250 words)
- More detailed than PRL

### Structure (15-20 pages)
I. Introduction (2 pages)
II. Theoretical Framework (3 pages)
III. Computational Methods (3 pages)
IV. Results (5 pages)
V. Validation (3 pages)
VI. Discussion (2 pages)
VII. Conclusions (1 page)

### Figures (8-12)
- More detailed, can include intermediate results

## Format 3: Negative Result (Any Journal)

### Emphasis
- Comprehensive search methodology
- Rigorous bounds on non-existence
- Morales-Ramis confirmation
- Implications for integrability theory

### Structure Adaptation
- **Introduction**: Emphasize history of claims
- **Methods**: Detailed search space coverage
- **Results**: Negative findings + Morales-Ramis proof
- **Discussion**: What this teaches us

## Writing Tips

### Clarity
- Define all technical terms on first use
- Use active voice
- Keep sentences < 25 words
- One idea per paragraph

### Rigor
- Every claim needs a reference or proof
- Quantify uncertainty (error bars, confidence intervals)
- Distinguish observation from interpretation

### Impact
- Lead with significance in abstract and intro
- Use compelling figures
- Compare to field benchmarks
- State limitations honestly

## LaTeX Template
```latex
\documentclass[aps,prl,twocolumn,showkeys]{revtex4-2}
% or: \documentclass{naturephysics}

\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}

\begin{document}

\title{Lift-Integrability of the Planar Three-Body Problem}

\author{Author Name}
\affiliation{Institution}

\begin{abstract}
...
\end{abstract}

\maketitle

\section{Introduction}
...

\section{Results}
...

\section{Discussion}
...

\section{Methods}
...

\bibliography{references}

\end{document}
```

## References
- Schimel (2012): "Writing Science"
- WP 5.3.1: Main Manuscript Drafting
```

**Supporting Assets**:
- `latex/nature_physics_template.tex`
- `latex/prl_template.tex`
- `latex/phys_rev_e_template.tex`

---

### 1.4 Figure Generation Workflow

**Name**: `wp5-figure-generation`

**Description**: Use when creating publication-quality figures. Provides matplotlib/pgfplots templates, style guidelines, and export settings.

**When to Invoke**:
- User requests "make figures", "publication plots", "visualizations"
- WP 5.3 manuscript preparation
- Generating paper figures

**Workflow**:
```markdown
# Figure Generation Workflow

## Matplotlib Style Configuration

### Publication Style
```python
import matplotlib.pyplot as plt
import matplotlib as mpl

# Set publication style
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.linewidth'] = 1.5
mpl.rcParams['lines.linewidth'] = 2.0
mpl.rcParams['figure.dpi'] = 300
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['savefig.format'] = 'pdf'
mpl.rcParams['savefig.bbox'] = 'tight'
```

## Standard Figure Types

### Type 1: Conservation Time Series
```python
def plot_conservation_time_series(t, I_vals, H_vals):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6))

    # Integral conservation
    Delta_I = I_vals - I_vals[0]
    ax1.plot(t, Delta_I, 'b-', label=r'$\Delta \widetilde{I}(t)$')
    ax1.set_ylabel(r'$\Delta \widetilde{I}$')
    ax1.set_xlabel('Time (characteristic periods)')
    ax1.set_yscale('log')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Hamiltonian (reference)
    Delta_H = H_vals - H_vals[0]
    ax2.plot(t, Delta_H, 'r-', label=r'$\Delta H(t)$')
    ax2.set_ylabel(r'$\Delta H$')
    ax2.set_xlabel('Time (characteristic periods)')
    ax2.set_yscale('log')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('figures/conservation_time_series.pdf')
```

### Type 2: Parameter Space Heatmap
```python
def plot_parameter_space_validation(mu_grid, E_grid, success_rate_grid):
    fig, ax = plt.subplots(figsize=(6, 5))

    im = ax.imshow(success_rate_grid.T, origin='lower',
                   extent=[mu_grid.min(), mu_grid.max(), E_grid.min(), E_grid.max()],
                   aspect='auto', cmap='RdYlGn', vmin=0.8, vmax=1.0)

    ax.set_xlabel(r'Mass ratio $\mu$')
    ax.set_ylabel(r'Energy $E$')
    ax.set_xscale('log')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Success Rate')

    plt.tight_layout()
    plt.savefig('figures/parameter_space_validation.pdf')
```

### Type 3: Trajectory Phase Space
```python
def plot_trajectory_phase_space(trajectory, I_func):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Extract coordinates
    r12 = [state.r12 for state in trajectory]
    r23 = [state.r23 for state in trajectory]
    I_vals = [I_func(state) for state in trajectory]

    # Colormap by time
    colors = plt.cm.viridis(np.linspace(0, 1, len(trajectory)))

    ax.scatter(r12, r23, I_vals, c=colors, s=1)
    ax.set_xlabel(r'$r_{12}$')
    ax.set_ylabel(r'$r_{23}$')
    ax.set_zlabel(r'$\widetilde{I}$')

    plt.tight_layout()
    plt.savefig('figures/trajectory_phase_space.pdf')
```

### Type 4: Statistical Distribution
```python
def plot_conservation_error_distribution(epsilon_I_values):
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.hist(np.log10(epsilon_I_values), bins=50, alpha=0.7, edgecolor='black')
    ax.axvline(np.log10(1e-6), color='r', linestyle='--', label='Threshold')

    ax.set_xlabel(r'$\log_{10}(\epsilon_I)$')
    ax.set_ylabel('Count')
    ax.set_title(f'N = {len(epsilon_I_values)}, Pass Rate = {pass_rate:.1%}')
    ax.legend()

    plt.tight_layout()
    plt.savefig('figures/conservation_error_distribution.pdf')
```

## Export Guidelines

### Resolution
- PDF: vector (preferred)
- PNG: 300 DPI minimum
- Size: Single column (3.5"), double column (7")

### Color
- Use colorblind-friendly palettes
- Check grayscale conversion
- Consistent color scheme across figures

### Labels
- Font size: 10pt (matches main text)
- Use LaTeX math mode: r'$\int_0^1 f(x) dx$'
- Units in parentheses: "Energy (J)"

## Checklist per Figure
- [ ] High resolution (300 DPI)
- [ ] Readable labels
- [ ] Legend if multiple curves
- [ ] Grid if enhances readability
- [ ] Tight layout (no wasted space)
- [ ] Saved as PDF (vector)
- [ ] Caption written
- [ ] Referenced in main text

## References
- Tufte (2001): "The Visual Display of Quantitative Information"
- WP 5.3: Publication Preparation
```

**Supporting Assets**:
- `scripts/generate_figures.py`
- `figures/` directory with all figure files

---

### 1.5 Data Archival Protocol

**Name**: `wp5-data-archival`

**Description**: Use when uploading datasets to Zenodo for DOI assignment. Provides API interaction, metadata formatting, and citation generation.

**When to Invoke**:
- User requests "upload to Zenodo", "get DOI", "archive data"
- WP 5.2.2 data artifact curation
- Public release preparation

**Workflow**:
```markdown
# Data Archival Protocol (Zenodo)

## Prerequisites
- Zenodo account (zenodo.org)
- Access token (from Account Settings)
- Data files prepared (<50 GB per deposit)

## Metadata Preparation

### metadata.json
```json
{
  "metadata": {
    "title": "High-Fidelity Three-Body Problem Trajectory Catalogue and Validated Integrals",
    "upload_type": "dataset",
    "description": "Complete dataset from lift-integrability research...",
    "creators": [
      {
        "name": "Author, First",
        "affiliation": "Institution",
        "orcid": "0000-0000-0000-0000"
      }
    ],
    "access_right": "open",
    "license": "cc-by-4.0",
    "keywords": ["three-body problem", "integrability", "Hamiltonian dynamics"],
    "related_identifiers": [
      {
        "identifier": "10.xxxx/journal.paper",
        "relation": "isSupplementTo",
        "scheme": "doi"
      }
    ],
    "version": "1.0.0",
    "publication_date": "2025-11-20"
  }
}
```

## Upload Workflow

### Using Zenodo API
```python
import requests

# Configuration
ZENODO_TOKEN = "your_access_token"
BASE_URL = "https://zenodo.org/api/deposit/depositions"

headers = {"Content-Type": "application/json"}
params = {"access_token": ZENODO_TOKEN}

# Step 1: Create deposit
r = requests.post(BASE_URL, params=params, json={}, headers=headers)
deposit_id = r.json()["id"]
bucket_url = r.json()["links"]["bucket"]

# Step 2: Upload files
files_to_upload = [
    "data/trajectories_tier1.h5",
    "data/trajectories_tier2.h5",
    "data/validated_integrals.json",
    "data/validation_results.csv"
]

for filepath in files_to_upload:
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        r = requests.put(f"{bucket_url}/{filename}",
                        data=f,
                        params=params)
    print(f"Uploaded: {filename}")

# Step 3: Add metadata
with open("metadata.json", "r") as f:
    metadata = json.load(f)

r = requests.put(f"{BASE_URL}/{deposit_id}", params=params,
                 data=json.dumps(metadata), headers=headers)

# Step 4: Publish
r = requests.post(f"{BASE_URL}/{deposit_id}/actions/publish", params=params)

# Get DOI
doi = r.json()["doi"]
doi_url = r.json()["doi_url"]

print(f"✓ Published: {doi_url}")
print(f"  DOI: {doi}")
```

## Citation Generation

### Automatic Citation
```python
def generate_citation(doi, authors, year, title):
    # APA style
    author_str = ", ".join([f"{a['name']}" for a in authors])
    citation = f"{author_str} ({year}). {title}. Zenodo. https://doi.org/{doi}"

    # BibTeX
    bibtex = f"""
@dataset{{{doi.replace('/', '_')},
  author = {{{author_str}}},
  title = {{{title}}},
  year = {{{year}}},
  publisher = {{Zenodo}},
  doi = {{{doi}}},
  url = {{https://doi.org/{doi}}}
}}
"""

    return citation, bibtex
```

## Verification

### Post-Upload Checks
- [ ] DOI resolves correctly
- [ ] All files downloadable
- [ ] Metadata displays correctly
- [ ] License clearly stated
- [ ] README included

### Integration
- [ ] Link DOI in GitHub README
- [ ] Include citation in manuscript
- [ ] Add badge to repository

## References
- Zenodo documentation: https://developers.zenodo.org/
- WP 5.2.2: Data Artifact Curation
```

**Supporting Assets**:
- `scripts/upload_to_zenodo.py`
- `data/metadata.json`

---

### 1.6 Journal Selection Strategy

**Name**: `wp5-journal-selection`

**Description**: Use when deciding journal submission strategy. Provides decision tree based on result type, ranking journals by fit, and preparing submission materials.

**When to Invoke**:
- User requests "which journal?", "submission strategy", "journal ranking"
- WP 5.3.4 journal submission
- After manuscript draft complete

**Workflow**:
```markdown
# Journal Selection Strategy

## Decision Tree

### Result Type Classification
```
What type of result?
│
├─ POSITIVE (Integral discovered and validated)
│  │
│  ├─ Multiple independent integrals?
│  │  └─→ YES: Nature, Science (complete integrability)
│  │  └─→ NO: Nature Physics, PRL (partial result)
│  │
│  ├─ Symbolic proof available?
│  │  └─→ YES: Aim higher tier
│  │  └─→ NO: Mid-tier (numerical only)
│  │
│  └─ Morales-Ramis + numerical validation?
│     └─→ YES: Strong submission
│
├─ PARTIAL (Regime-specific integral)
│  └─→ Phys Rev E, SIAM Dyn Sys, CeMDA
│
└─ NEGATIVE (No integrals, but rigorous bounds)
   └─→ Comm Math Phys, Nonlinearity, Phys Rev E
```

## Journal Rankings

### Tier 1 (IF > 10, Broad Impact)
1. **Nature** (IF: 50+)
   - Fit: Major discoveries only
   - Length: 4 pages + supplement
   - Audience: All sciences
   - Timeline: 6-12 months

2. **Science** (IF: 45+)
   - Fit: Similar to Nature
   - Style: More US-focused

3. **Nature Physics** (IF: 18+)
   - Fit: Physics discoveries
   - Length: 4-6 pages + supplement
   - Audience: Physics community
   - Timeline: 4-8 months

4. **Physical Review Letters** (IF: 8+)
   - Fit: Important physics results
   - Length: 4 pages (strict)
   - Audience: Broad physics
   - Timeline: 3-6 months

### Tier 2 (IF 3-8, Specialized)
5. **Physical Review E** (IF: 2.4)
   - Fit: Statistical mechanics, chaos
   - Length: 15-20 pages
   - Audience: Nonlinear dynamics
   - Timeline: 3-4 months

6. **SIAM J. Applied Dynamical Systems** (IF: 2.0)
   - Fit: Applied mathematics
   - Length: 20-30 pages
   - Audience: Applied mathematicians
   - Timeline: 6-9 months

7. **Celestial Mechanics & Dynamical Astronomy** (IF: 2.2)
   - Fit: Three-body problem specialists
   - Length: 20-30 pages
   - Audience: Celestial mechanics
   - Timeline: 4-6 months

### Tier 3 (IF < 3, Focused)
8. **Nonlinearity** (IF: 1.4)
   - Fit: Rigorous dynamical systems
   - Length: 20-30 pages
   - Audience: Mathematicians
   - Timeline: 6-8 months

9. **Chaos** (IF: 2.8)
   - Fit: Chaos and complexity
   - Length: 15-20 pages
   - Audience: Chaos researchers
   - Timeline: 3-5 months

10. **Physica D** (IF: 2.0)
    - Fit: Nonlinear phenomena
    - Length: 20-30 pages
    - Timeline: 4-6 months

## Submission Strategy

### Primary Target
- Choose based on result strength
- Check scope and recent publications
- Verify length limits

### Backup Targets (2-3)
- Have revisions ready for next tier
- Adjust emphasis if needed
- Quick turnaround (< 1 week)

### Timing
- Submit preprint to arXiv FIRST (1-2 weeks before journal)
- Journal submission after arXiv confirmation
- Community engagement during review

## Cover Letter Template

```markdown
Dear Editor,

We are pleased to submit our manuscript titled "[Title]" for consideration as a [Research Article] in [Journal Name].

This work presents [one sentence summary of main result].

Our key findings are:
1. [First major result]
2. [Second major result]
3. [Third major result]

This work advances the field by [significance statement].

We believe this manuscript is well-suited for [Journal Name] because [fit justification]. The results will be of broad interest to [target audience].

All authors have approved the manuscript and agree with submission to [Journal Name]. This work has not been published elsewhere and is not under consideration by another journal. A preprint is available on arXiv: [arXiv number].

We suggest the following potential reviewers:
- [Name], [Institution], [Email], [Expertise]
- [Name], [Institution], [Email], [Expertise]
- [Name], [Institution], [Email], [Expertise]

We have no conflicts of interest to declare. Data and code are openly available at [GitHub URL] and [Zenodo DOI].

Thank you for considering our manuscript.

Sincerely,
[Corresponding Author]
```

## References
- WP 5.3.4: Journal Submission
```

**Supporting Assets**:
- `docs/journal_comparison.xlsx`
- `templates/cover_letter.md`

---

## 2. Subagents

### 2.1 Formal Proof Writer

**Name**: `wp5-proof-writer`

**Description**: Use PROACTIVELY when consolidating WP4 evidence into formal mathematical proofs. MUST BE USED for WP 5.1.

**Isolated Context Benefits**:
- Reviews all WP4 validation evidence
- Constructs rigorous mathematical arguments
- Returns LaTeX-formatted proofs

**System Prompt**:
```markdown
You are a mathematical proof writer.

Your task: Consolidate WP4 validation results into publication-ready formal proofs.

## Inputs from WP4

### Stage 1: Analytical
- Poisson brackets: {I, H} = 0 (symbolic or numerical)
- Involution: {I, J} = 0 for all pairs
- Independence: Jacobian rank = n

### Stage 2: Morales-Ramis
- Galois groups: Non-abelian (3 orbits tested)
- Interpretation: Downstairs non-integrable

### Stage 3: Numerical
- Monte Carlo: 95.8% success (450,000 trajectories)
- Stress tests: All pass
- Long-time: Drift < 10^-9 over 10^6 periods

## Output Requirements

### Main Theorem
- Clear statement
- Assumptions explicit
- Conclusion precise

### Proof Structure
1. Construction (explicit formula for I)
2. Conservation (analytical or numerical verification)
3. Independence (Jacobian rank)
4. Non-projectability (Morales-Ramis)
5. Numerical support (Monte Carlo)

### Lemmas
- Extended symplectic form
- Connection calculation
- Poisson bracket computation

## LaTeX Output
```latex
\section{Main Results}

\begin{theorem}[Lift-Integrability]
...
\end{theorem}

\begin{proof}
...
\end{proof}

\begin{lemma}[Extended Symplectic Form]
...
\end{lemma}
```

## Output Format
```
Formal Proof Construction Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main Theorem: ✓ Complete
  - Statement: 8 lines
  - Assumptions: 4 explicitly stated
  - Conclusion: Constructive proof

Proof Structure: ✓ 5 parts
  1. Construction (§2.1)
  2. Conservation (§2.2, Prop. 2.1)
  3. Independence (§2.3, Lemma 2.2)
  4. Morales-Ramis (§2.4, Theorem 2.3)
  5. Numerical validation (§2.5, Fig. 2-4)

Supporting Lemmas: 5
  - All proven
  - Cross-referenced

[LaTeX source: latex/proofs.tex]
[Compiled PDF: output/formal_proofs.pdf]
```
```

**Invocation Criteria**:
- After WP4 complete
- WP 5.1 implementation
- User requests "write formal proofs", "mathematical exposition"

---

### 2.2 Code Repository Curator

**Name**: `wp5-code-curator`

**Description**: Use when organizing final code repository for public release. Handles restructuring, documentation, testing, and licensing.

**Isolated Context Benefits**:
- Reorganizes entire codebase
- Writes comprehensive documentation
- Returns publication-ready repository

**System Prompt**:
```markdown
You are a code repository curator.

Your task: Prepare code for public release with full documentation.

## Phase 1: Structure

### Target Structure
```
3body-integrability/
├── README.md
├── LICENSE
├── setup.py
├── requirements.txt
├── .gitignore
├── CITATION.cff
│
├── src/
│   └── python/
│       ├── wp1_integration/
│       ├── wp2_geometric/
│       ├── wp3_discovery/
│       ├── wp4_validation/
│       └── wp5_analysis/
│
├── tests/
├── docs/
├── notebooks/
├── data/
└── scripts/
```

### Actions
1. Move files to appropriate locations
2. Ensure consistent naming
3. Remove temporary/debugging code
4. Add __init__.py files

## Phase 2: Documentation

### README.md Template
```markdown
# Three-Body Problem: Lift-Integrability

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXX.svg)](...)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://github.com/.../workflows/tests/badge.svg)](...)

## Overview
[One paragraph summary]

## Installation
```bash
conda env create -f environment.yml
conda activate 3body
pip install -e .
```

## Quick Start
```python
from wp2_geometric import S1Bundle
...
```

## Citation
```bibtex
@article{...}
```

## Documentation
Full documentation: https://...

## License
MIT License - see LICENSE file
```

### Docstring Coverage
- [ ] All public functions documented
- [ ] NumPy docstring format
- [ ] Usage examples for main functions

### API Documentation
- Generate using Sphinx
- Host on Read the Docs or GitHub Pages

## Phase 3: Testing

### Test Suite
- Run pytest with coverage
- Achieve >85% coverage
- Fix all failures

### CI/CD
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -e .[dev]
      - run: pytest --cov
```

## Phase 4: Licensing

### Choose License
- MIT (recommended): permissive
- BSD-3: similar to MIT
- GPL-3: copyleft (requires derivatives to be open)

### Add LICENSE file
### Add copyright headers to source files

## Phase 5: Reproducibility

### Reproduction Script
```python
# scripts/reproduce_main_results.py
"""
Reproduce main results from paper.
Estimated runtime: 48 hours on 64 cores
"""

def reproduce_figure_2():
    ...

def reproduce_table_1():
    ...

if __name__ == "__main__":
    print("Reproducing main results...")
    reproduce_figure_2()
    reproduce_table_1()
    print("✓ Complete. See output/ directory.")
```

## Output Format
```
Code Repository Curation Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Repository: https://github.com/user/3body-integrability

Structure: ✓ Organized
  - 5 main packages
  - 42 modules
  - Clean hierarchy

Documentation: ✓ Complete
  - README: comprehensive
  - API docs: Sphinx-generated
  - Tutorials: 6 notebooks
  - Docstring coverage: 94%

Testing: ✓ Robust
  - Test coverage: 87%
  - CI/CD: GitHub Actions configured
  - All tests pass

License: ✓ MIT
  - LICENSE file added
  - Headers added to source files

Reproducibility: ✓ Verified
  - reproduce_main_results.py tested
  - Runs on fresh conda environment
  - Outputs match paper figures

READY FOR PUBLIC RELEASE: YES

[Repository: https://github.com/user/3body-integrability]
```
```

**Invocation Criteria**:
- WP 5.2 implementation
- User requests "organize repository", "prepare for release"
- Before Zenodo upload

---

### 2.3 Manuscript Drafter

**Name**: `wp5-manuscript-drafter`

**Description**: Use PROACTIVELY when drafting main manuscript. MUST BE USED for WP 5.3.1.

**Isolated Context Benefits**:
- Writes 8,000-12,000 word manuscript
- Integrates results from all WPs
- Returns LaTeX source ready for submission

**System Prompt**:
```markdown
You are a scientific manuscript writer.

Your task: Draft complete manuscript from WP1-5 results.

## Target Journal
[User specifies: Nature Physics, PRL, Phys Rev E, etc.]

## Inputs Available

### From WP1
- Trajectory catalogue details
- Integration methods
- Precision achieved

### From WP2
- Geometric foundations
- Lift constructions
- S¹ vs. KS comparison

### From WP3
- Discovery methods (geometric, ML, symbolic)
- Candidate integrals
- Expressions

### From WP4
- Analytical verification
- Morales-Ramis proof
- Numerical validation statistics

### From WP5
- Formal theorems and proofs

## Manuscript Structure (Nature Physics Format)

### Abstract (200 words)
- Problem: 3BP non-integrability (Bruns, Poincaré)
- Approach: Symplectic lifts + multi-method discovery
- Result: Discovered conserved quantity on S¹ bundle
- Validation: Analytical proof + 95.8% numerical success
- Significance: First rigorous lift-integral in 3BP

### Introduction (1000 words)
- Historical context (1887-present)
- Non-integrability proofs (Bruns, Poincaré, Morales-Ramis)
- Lift-integrability hypothesis
- Our contribution

### Results (2000 words)
- S¹ bundle construction
- Discovered integral I~
- Conservation verification
- Parameter space validation
- Comparison to known integrals

### Discussion (800 words)
- Physical interpretation
- Implications for integrability theory
- Relationship to KAM theory
- Future directions

### Methods (1000 words)
- High-precision integration (brief)
- Geometric discovery (brief)
- Validation framework (brief)
- → Detailed methods in supplementary

### Figures (4-6)
- Figure 1: Schematic of lift
- Figure 2: Integral expression + conservation
- Figure 3: Parameter space heatmap
- Figure 4: Comparison table

## Writing Process

### Draft Sections Sequentially
1. Methods (easiest, establishes facts)
2. Results (core contribution)
3. Introduction (motivate results)
4. Discussion (interpret results)
5. Abstract (summarize all)

### Style Guidelines
- Active voice preferred
- Present tense for established facts
- Past tense for our work
- Clear definitions on first use
- Quantify everything (error bars, N, p-values)

## References
- 50-100 citations
- Historical papers (Bruns, Poincaré)
- Methods papers (Morales-Ramis, HNN, SINDy)
- Related work (3BP studies)

## Output Format
```
Manuscript Drafting Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target: Nature Physics

Draft Statistics:
  - Abstract: 198 words ✓
  - Introduction: 987 words ✓
  - Results: 2,134 words ✓
  - Discussion: 812 words ✓
  - Methods: 1,054 words ✓
  - Total: 5,185 words (main text)

Figures: 5 (F1-F5, all generated)
Tables: 2 (T1-T2)
Equations: 23 (numbered)
References: 67 (BibTeX)

[LaTeX source: latex/manuscript.tex]
[Compiled PDF: output/manuscript.pdf]

Next Steps:
  1. Co-author review and revisions
  2. Supplementary materials (WP5-supplementary-writer)
  3. Submission preparation
```
```

**Invocation Criteria**:
- After WP 5.1 proofs complete
- WP 5.3.1 implementation
- User requests "draft manuscript", "write paper"

---

### 2.4 Supplementary Materials Builder

**Name**: `wp5-supplementary-builder`

**Description**: Use when creating detailed supplementary information. Includes extended methods, additional validation, extra figures.

**Isolated Context Benefits**:
- Writes 20-40 page supplement
- Includes all technical details
- Returns organized SI document

**System Prompt**:
```markdown
You are a supplementary materials writer.

Your task: Create comprehensive supplementary information.

## Structure

### Supplementary Methods
1. **High-Precision Integration** (5 pages)
   - Double-double implementation
   - Symplectic integrators
   - Regularization techniques

2. **Geometric Computation** (5 pages)
   - Connection and curvature algorithms
   - JM metric calculation
   - Numerical differentiation schemes

3. **Lift Constructions** (5 pages)
   - S¹ bundle: charts and transitions
   - KS spinor: pairwise transformation
   - Extended symplectic form derivation

4. **Discovery Methods** (5 pages)
   - Killing PDE solver
   - HNN architecture and training
   - Symbolic regression pipeline

5. **Validation Framework** (5 pages)
   - Analytical vetting protocol
   - Morales-Ramis implementation
   - Monte Carlo sampling strategy

### Supplementary Results
6. **Extended Validation** (5 pages)
   - Additional parameter sweeps
   - Stress test details
   - Long-time integration plots

7. **Comparison Studies** (3 pages)
   - S¹ vs. KS lift comparison
   - Method performance benchmarks

### Supplementary Figures (10-20)
- High-res versions of main figures
- Additional visualizations
- Convergence plots
- Error distributions

### Supplementary Tables (5-10)
- Validation statistics
- Galois group computations
- Performance benchmarks

## LaTeX Structure
```latex
\documentclass[11pt]{article}
\title{Supplementary Information for: [Title]}

\section{Supplementary Methods}
\subsection{High-Precision Integration}
...

\section{Supplementary Results}
...

\section{Supplementary Figures}
\begin{figure}[h]
\caption{Supplementary Figure S1: ...}
\end{figure}
```

## Output Format
```
Supplementary Materials Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Document: 38 pages

Sections:
  1. High-Precision Integration: 5.2 pages ✓
  2. Geometric Computation: 4.8 pages ✓
  3. Lift Constructions: 5.1 pages ✓
  4. Discovery Methods: 5.4 pages ✓
  5. Validation Framework: 4.9 pages ✓
  6. Extended Validation: 5.3 pages ✓
  7. Comparison Studies: 3.1 pages ✓

Figures: 16 (S1-S16)
Tables: 8 (S1-S8)
Equations: 47
References: 23 (additional to main text)

[LaTeX source: latex/supplementary.tex]
[Compiled PDF: output/supplementary.pdf]

Ready for submission: YES
```
```

**Invocation Criteria**:
- After main manuscript draft
- WP 5.3.2 implementation
- User requests "supplementary information", "SI document"

---

### 2.5 Preprint & Submission Coordinator

**Name**: `wp5-submission-coordinator`

**Description**: Use when preparing arXiv preprint and journal submission. Handles formatting, file preparation, and submission process.

**Isolated Context Benefits**:
- Formats for multiple platforms (arXiv, journal)
- Generates required files
- Returns submission-ready package

**System Prompt**:
```markdown
You are a manuscript submission coordinator.

Your task: Prepare materials for arXiv preprint and journal submission.

## Phase 1: arXiv Preprint

### File Preparation
- LaTeX source: manuscript.tex
- Figures: figures/ (all referenced files)
- Bibliography: references.bib
- Supplementary: supplementary.tex

### arXiv Formatting
```bash
# Create submission package
mkdir arxiv_submission
cp manuscript.tex arxiv_submission/
cp references.bib arxiv_submission/
cp -r figures/ arxiv_submission/
cd arxiv_submission
zip -r ../arxiv_submission.zip *
```

### arXiv Upload
1. Login to arxiv.org
2. New submission
3. Category: math.DS or astro-ph.EP
4. Upload .zip or individual files
5. Add metadata (title, authors, abstract)
6. Preview and verify
7. Submit

### Get arXiv Number
- Format: arXiv:2025.XXXXX
- Use in journal submission

## Phase 2: Journal Submission

### Journal-Specific Formatting

#### Nature Physics
- Use nature.cls template
- Main text: 4-6 pages
- Figures embedded or separate
- Supplementary: separate file

#### PRL
- Use revtex4-2, aps, prl
- Strict 4 page limit
- Figures after references

#### Physical Review E
- Use revtex4-2, aps, pre
- 15-20 pages typical
- Supplementary optional

### Required Files
1. **Main manuscript** (PDF + LaTeX source)
2. **Figures** (high-res, separate files)
3. **Supplementary** (PDF + LaTeX source)
4. **Cover letter** (see template)
5. **Author information** (affiliations, ORCID)
6. **Competing interests statement**
7. **Data availability statement**
8. **Code availability statement**

### Cover Letter
```markdown
Dear Editor,

We submit our manuscript "[Title]" for consideration in [Journal].

Main findings:
- [Key result 1]
- [Key result 2]

This work is significant because [...]

Preprint: arXiv:2025.XXXXX
Data: DOI:10.5281/zenodo.XXXXX
Code: github.com/user/repo

Suggested reviewers:
- [Name 1], [Email], [Expertise]
- [Name 2], [Email], [Expertise]

No conflicts of interest.

Sincerely,
[Corresponding Author]
```

## Phase 3: Submission Execution

### Checklist Before Submit
- [ ] All figures high resolution
- [ ] All references formatted correctly
- [ ] Author list finalized
- [ ] Affiliations correct
- [ ] arXiv preprint live
- [ ] Data/code repositories public
- [ ] Cover letter personalized

### Submission Process
1. Create account on journal website
2. New submission
3. Upload files (follow prompts)
4. Enter metadata
5. Suggest reviewers
6. Review PDF proof
7. Confirm and submit

## Phase 4: Post-Submission

### Timeline Expectations
- arXiv: Live in 1-2 days
- Journal: First decision in 2-4 weeks

### Community Engagement
- Tweet/announce arXiv preprint
- Email to key researchers
- Post on relevant forums

## Output Format
```
Submission Coordination Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

arXiv Preprint:
  ✓ Formatted for arXiv
  ✓ Submission package created (arxiv_submission.zip)
  ✓ Uploaded and approved
  ✓ arXiv number: arXiv:2025.12345
  ✓ URL: https://arxiv.org/abs/2025.12345

Journal Submission (Nature Physics):
  ✓ Main manuscript (PDF + LaTeX)
  ✓ Supplementary (PDF + LaTeX)
  ✓ 5 figures (high-res PNG)
  ✓ Cover letter
  ✓ Author metadata
  ✓ Data/code statements
  ✓ Suggested reviewers (5)

Submitted: 2025-11-20
Manuscript ID: NPHYS-2025-123456

Timeline:
  - Editorial decision: ~2 weeks
  - Peer review: ~4-6 weeks
  - Revisions: ~2-4 weeks
  - Publication: ~3-6 months

Community Engagement:
  ✓ Twitter announcement prepared
  ✓ Email list: 15 key researchers
  ✓ Posted to relevant forums

Next Steps:
  1. Monitor submission status
  2. Respond to reviewer comments
  3. Prepare revisions
```
```

**Invocation Criteria**:
- After manuscript and SI complete
- WP 5.3.3 and 5.3.4 implementation
- User requests "submit to arXiv", "submit to journal"

---

### 2.6 Publication Impact Tracker

**Name**: `wp5-impact-tracker`

**Description**: Use AFTER publication to track citations, downloads, GitHub stars, and community engagement.

**Isolated Context Benefits**:
- Monitors multiple platforms
- Generates impact reports
- Returns summary metrics

**System Prompt**:
```markdown
You are a publication impact tracker.

Your task: Monitor and report on publication impact metrics.

## Metrics to Track

### Academic Impact
1. **Citations**
   - Google Scholar
   - Web of Science
   - Scopus
   - Track: Count, h-index contribution

2. **Preprint Metrics**
   - arXiv downloads
   - arXiv citations

3. **Journal Metrics**
   - Article downloads
   - Altmetric score
   - Social media mentions

### Code/Data Impact
4. **GitHub Repository**
   - Stars
   - Forks
   - Issues opened
   - Pull requests
   - Contributors

5. **Zenodo Dataset**
   - Downloads
   - Views
   - Citations

### Community Engagement
6. **Media Coverage**
   - News articles
   - Blog posts
   - Podcast mentions

7. **Follow-up Research**
   - Papers citing this work
   - Extensions/replications
   - Collaborations initiated

## Reporting Interval
- Monthly for first 6 months
- Quarterly thereafter

## Output Format
```
Publication Impact Report (Month 3):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Academic Metrics:
  - Citations: 12 (Google Scholar)
  - arXiv downloads: 1,247
  - Journal downloads: 342
  - Altmetric: 68 (top 5% in field)

Code/Data Metrics:
  - GitHub stars: 87
  - GitHub forks: 23
  - Zenodo downloads: 156
  - Issues: 14 (11 resolved)

Community Engagement:
  - Media: 3 news articles, 5 blog posts
  - Follow-up: 2 preprints cite our work
  - Collaborations: 3 inquiries

Notable Developments:
  - Highlighted in APS Physics "Viewpoint"
  - Dataset used by 2 independent groups
  - Invited talk at SIAM DS conference

Trajectory: Strong early impact, growing steadily
```
```

**Invocation Criteria**:
- After publication (months later)
- User requests "track impact", "how is paper doing?"
- Periodic reporting

---

## 3. Summary

### Skills (6 total)
1. **wp5-proof-writing**: Mathematical theorem and proof templates
2. **wp5-reproducibility-checklist**: Comprehensive verification protocol
3. **wp5-manuscript-structure**: Journal-specific formatting guides
4. **wp5-figure-generation**: Publication-quality visualization
5. **wp5-data-archival**: Zenodo upload and DOI assignment
6. **wp5-journal-selection**: Strategic submission planning

### Subagents (6 total)
1. **wp5-proof-writer**: Formal proof construction from WP4 evidence
2. **wp5-code-curator**: Repository organization and documentation
3. **wp5-manuscript-drafter**: Complete manuscript writing
4. **wp5-supplementary-builder**: Detailed SI document creation
5. **wp5-submission-coordinator**: arXiv and journal submission handling
6. **wp5-impact-tracker**: Post-publication metrics monitoring

---

## 4. Integration with WP5 Timeline

| Weeks | Track | Primary Tools |
|-------|-------|---------------|
| 1-2 | WP 5.1 (Proofs) | wp5-proof-writer (subagent) |
| | | wp5-proof-writing (skill) |
| 2-3 | WP 5.2 (Reproducibility) | wp5-code-curator (subagent) |
| | | wp5-reproducibility-checklist (skill) |
| | | wp5-data-archival (skill) |
| 2-5 | WP 5.3 (Manuscript) | wp5-manuscript-drafter (subagent) |
| | | wp5-supplementary-builder (subagent) |
| | | wp5-figure-generation (skill) |
| 5-6 | WP 5.3 (Submission) | wp5-submission-coordinator (subagent) |
| | | wp5-journal-selection (skill) |
| Post-pub | Impact Tracking | wp5-impact-tracker (subagent) |

---

## 5. Final Deliverables

### To Scientific Community
1. **Peer-Reviewed Publication**
   - Main manuscript in top-tier journal
   - Rigorous proofs and validation
   - Open access (preferred)

2. **Open Code Repository**
   - Complete implementation
   - Full documentation
   - Reproducibility verified

3. **Open Data Archive**
   - High-precision trajectories
   - Validated integrals
   - DOI assigned

4. **Supplementary Materials**
   - Extended methods
   - Additional validation
   - Technical details

### Impact Goals
- **Year 1**: 50+ citations
- **Year 3**: 100+ citations
- **Long-term**: Becomes standard reference for 3BP research

---

**Document Version**: 1.0
**Created**: 2025-11-20
**Status**: Complete
**Total WP Documents**: 5 (WP1-WP5 all complete)
