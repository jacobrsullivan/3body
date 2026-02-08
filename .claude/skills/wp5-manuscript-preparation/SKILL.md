---
name: wp5-manuscript-preparation
description: Scientific manuscript preparation for publication, including LaTeX generation, figure creation, journal-specific formatting, and submission workflow. Use when generating manuscript sections, creating publication figures, formatting for specific journals (PRL, CMDA, PNAS), or preparing supplementary materials. Triggers on requests involving LaTeX writing, figure generation, journal submission, arXiv preprint, or manuscript drafting.
---

# WP5 Manuscript Preparation

Generate publication-ready manuscripts from validated results.

## Target Journals

| Result Type | Primary Target | Secondary | Format |
|-------------|----------------|-----------|--------|
| Positive (breakthrough) | Nature/Science | PRL | Letter (3500 words) |
| Positive (technical) | PRL | PNAS | Letter (3500 words) |
| Partial | CMDA | PRE | Article (8000 words) |
| Negative | CMDA | Nonlinearity | Article (8000 words) |

**PRL** = Physical Review Letters
**CMDA** = Celestial Mechanics and Dynamical Astronomy
**PNAS** = Proceedings of the National Academy of Sciences

## Quick Start

```python
from src.python.publication.manuscript_generator import ManuscriptGenerator

# Create generator with consolidated results
gen = ManuscriptGenerator(
    results=consolidated_report,
    result_type='positive',
    target_journal='prl'
)

# Generate all sections
gen.generate_all_sections()

# Export to LaTeX
gen.export_latex('manuscript/main.tex')

# Generate figures
gen.generate_all_figures(output_dir='manuscript/figures/')

# Compile PDF
gen.compile_pdf()
```

## Manuscript Structure

### PRL Format (3500 words)

```
manuscript/
├── main.tex           # Main document
├── references.bib     # Bibliography
├── figures/
│   ├── figure1.pdf    # Reduction pipeline
│   ├── figure2.pdf    # Conservation validation
│   ├── figure3.pdf    # Morales-Ramis test
│   └── figure4.pdf    # Phase space structure
└── supplement/
    ├── supplement.tex # Supplementary material
    └── proofs.tex     # Detailed proofs
```

### Section Overview

| Section | Words | Content |
|---------|-------|---------|
| Abstract | 150 | Motivation, method, result, significance |
| Introduction | 500 | Historical context, hypothesis, contribution |
| Methods | 800 | WP1-4 summary |
| Results | 1200 | Main theorem, validation |
| Discussion | 600 | Implications, limitations, future |
| Conclusion | 250 | Summary, open questions |

## Generating Manuscript Sections

### Abstract

```python
from src.python.publication.manuscript_generator import ManuscriptGenerator

gen = ManuscriptGenerator(results=report, target_journal='prl')

abstract = gen.generate_abstract()
print(abstract)
```

**Output** (positive result):
```latex
The Newtonian three-body problem has resisted analytical solution for
over 300 years, with classical proofs establishing its non-integrability
in standard coordinates. We demonstrate that the planar Circular
Restricted Three-Body Problem becomes Liouville integrable when lifted
to an S¹ principal bundle over shape space. Using a combination of
symbolic regression, Morales-Ramis differential Galois theory, and
Monte Carlo validation (10⁵ samples, 99.7\% pass rate), we discover
a new conserved quantity—the fiber momentum $p_\theta$—independent of
the classical integrals (energy, angular momentum, Jacobi constant).
This "lift-integrability" resolves apparent non-integrability as a
consequence of working in an insufficiently rich phase space.
```

### Introduction

```python
intro = gen.generate_introduction()
```

**Key elements**:
1. Historical context (Bruns 1887, Poincaré 1890)
2. Recent developments (Morales-Ramis theory)
3. Lift-integrability hypothesis
4. This work's contribution

### Methods

```python
methods = gen.generate_methods()
```

**Subsections**:
- WP1: High-precision integration (IAS15, double-double arithmetic)
- WP2: Geometric reduction + S¹ bundle construction
- WP3: Symbolic regression + ML discovery
- WP4: Morales-Ramis + Monte Carlo validation

### Results

```python
results = gen.generate_results()
```

**Content**:
1. Main theorem statement
2. Analytical validation (conservation, involution, independence)
3. Morales-Ramis compatibility
4. Numerical validation statistics

### Discussion

```python
discussion = gen.generate_discussion()
```

**Topics**:
- Implications for celestial mechanics
- Comparison with previous work
- Limitations (planar CR3BP, specific lift)
- Broader impact (methodology for other systems)

### Conclusion

```python
conclusion = gen.generate_conclusion()
```

## Figure Generation

### Figure 1: Reduction Pipeline

```python
from src.python.publication.figure_generator import FigureGenerator

fig_gen = FigureGenerator(results=report)

# Panel A: Dimension reduction (18D → 12D → 13D)
# Panel B: Connection curvature landscape
# Panel C: S¹ bundle structure
fig1 = fig_gen.generate_figure1_reduction()
fig1.savefig('figures/figure1.pdf', dpi=300)
```

### Figure 2: Conservation Validation

```python
# Panel A: p_θ time series (flat = conserved)
# Panel B: Monte Carlo histogram (error distribution)
# Panel C: Long-time drift comparison
fig2 = fig_gen.generate_figure2_conservation()
fig2.savefig('figures/figure2.pdf', dpi=300)
```

### Figure 3: Morales-Ramis Test

```python
# Panel A: Periodic orbit (Lagrange L4)
# Panel B: Monodromy eigenvalues
# Panel C: Galois group analysis (downstairs vs upstairs)
fig3 = fig_gen.generate_figure3_morales_ramis()
fig3.savefig('figures/figure3.pdf', dpi=300)
```

### Figure 4: Phase Space Structure

```python
# Panel A: Poincaré section (y=0)
# Panel B: MEGNO chaos indicator
# Panel C: Tori structure
fig4 = fig_gen.generate_figure4_phase_space()
fig4.savefig('figures/figure4.pdf', dpi=300)
```

## LaTeX Templates

### Main Document

**main.tex**:
```latex
\documentclass[aps,prl,twocolumn,superscriptaddress]{revtex4-2}

\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}

\begin{document}

\title{Discovery of Hidden Integrability in the Three-Body Problem
       via Geometric Lifting}

\author{A. Author}
\affiliation{Department of Physics, University}

\date{\today}

\begin{abstract}
\input{sections/abstract}
\end{abstract}

\maketitle

\section{Introduction}
\input{sections/introduction}

\section{Methods}
\input{sections/methods}

\section{Results}
\input{sections/results}

\section{Discussion}
\input{sections/discussion}

\section{Conclusion}
\input{sections/conclusion}

\begin{acknowledgments}
This work was supported by...
\end{acknowledgments}

\bibliography{references}

\end{document}
```

### Supplementary Material

**supplement.tex**:
```latex
\documentclass[aps,prd,twocolumn]{revtex4-2}

\begin{document}

\title{Supplementary Material: Discovery of Hidden Integrability...}

\maketitle

\section{Detailed Proofs}
\input{proofs/conservation_proof}
\input{proofs/independence_proof}
\input{proofs/morales_ramis_details}

\section{Numerical Methods}
\input{numerical/integrator_details}
\input{numerical/precision_analysis}

\section{Additional Figures}
\input{additional_figures}

\section{Reproducibility}
Code and data available at:
\begin{itemize}
\item GitHub: \url{https://github.com/author/3body-lift}
\item Zenodo: \url{https://doi.org/10.5281/zenodo.XXXXXXX}
\end{itemize}

\end{document}
```

## Publication Workflow

### Complete Workflow

```python
def prepare_manuscript(results_dir, output_dir, result_type, journal):
    """Complete manuscript preparation workflow."""
    from src.python.publication.manuscript_generator import ManuscriptGenerator
    from src.python.publication.figure_generator import FigureGenerator
    from src.python.publication.result_consolidator import ResultConsolidator

    print(f"=== Preparing Manuscript for {journal.upper()} ===\n")

    # 1. Load results
    consolidator = ResultConsolidator.from_directory(results_dir)
    report = consolidator.generate_report()

    # 2. Create manuscript generator
    gen = ManuscriptGenerator(
        results=report,
        result_type=result_type,
        target_journal=journal
    )

    # 3. Generate sections
    print("Generating sections...")
    gen.generate_abstract()
    gen.generate_introduction()
    gen.generate_methods()
    gen.generate_results()
    gen.generate_discussion()
    gen.generate_conclusion()

    # 4. Export LaTeX
    print("Exporting LaTeX...")
    gen.export_latex(f'{output_dir}/main.tex')
    gen.export_bibtex(f'{output_dir}/references.bib')

    # 5. Generate figures
    print("Generating figures...")
    fig_gen = FigureGenerator(results=report)
    fig_gen.generate_all_figures(f'{output_dir}/figures/')

    # 6. Generate supplementary material
    print("Generating supplementary material...")
    gen.generate_supplement(f'{output_dir}/supplement/')

    # 7. Compile PDF
    print("Compiling PDF...")
    gen.compile_pdf(f'{output_dir}/main.tex')

    print(f"\n=== Manuscript Ready ===")
    print(f"Output: {output_dir}/")
    print(f"Main: {output_dir}/main.pdf")

    return {
        'main_tex': f'{output_dir}/main.tex',
        'main_pdf': f'{output_dir}/main.pdf',
        'supplement': f'{output_dir}/supplement/',
        'figures': f'{output_dir}/figures/'
    }

# Usage
result = prepare_manuscript(
    results_dir='results/wp4/',
    output_dir='manuscript/',
    result_type='positive',
    journal='prl'
)
```

### arXiv Submission

```python
from src.python.publication.arxiv_packager import ArxivPackager

packager = ArxivPackager(manuscript_dir='manuscript/')

# Create arXiv package
packager.create_package(
    output='arxiv_submission.tar.gz',
    categories=['astro-ph.EP', 'math.DS', 'physics.class-ph'],
    comments='15 pages, 4 figures, submitted to PRL'
)

# Upload instructions
print("""
arXiv Submission:
1. Go to https://arxiv.org/submit
2. Upload arxiv_submission.tar.gz
3. Select categories: astro-ph.EP (primary), math.DS, physics.class-ph
4. Submit
""")
```

### Journal Submission

```python
from src.python.publication.journal_submitter import JournalSubmitter

submitter = JournalSubmitter(journal='prl')

# Prepare submission package
submitter.prepare_package(
    manuscript='manuscript/main.tex',
    figures='manuscript/figures/',
    supplement='manuscript/supplement/',
    cover_letter='cover_letter.tex'
)

# Check compliance
issues = submitter.check_compliance()
if issues:
    print("Compliance issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Ready for submission!")
```

## Journal-Specific Formatting

### Physical Review Letters (PRL)

```python
gen = ManuscriptGenerator(results=report, target_journal='prl')

# PRL-specific settings
gen.set_format(
    document_class='revtex4-2',
    options=['aps', 'prl', 'twocolumn', 'superscriptaddress'],
    word_limit=3500,
    figure_limit=4,
    reference_limit=30
)
```

### Celestial Mechanics (CMDA)

```python
gen = ManuscriptGenerator(results=report, target_journal='cmda')

gen.set_format(
    document_class='svjour3',
    options=['smallextended'],
    word_limit=8000,
    figure_limit=10,
    reference_limit=50
)
```

### PNAS

```python
gen = ManuscriptGenerator(results=report, target_journal='pnas')

gen.set_format(
    document_class='pnas-new',
    options=[],
    word_limit=6000,
    figure_limit=6,
    reference_limit=50
)
```

## Cover Letter Template

```latex
\documentclass{letter}
\begin{document}

\begin{letter}{Physical Review Letters Editorial Office}

\opening{Dear Editors,}

We submit the manuscript entitled "Discovery of Hidden Integrability
in the Three-Body Problem via Geometric Lifting" for consideration
as a Letter in Physical Review Letters.

\textbf{Summary}: We demonstrate that the three-body problem, long
considered non-integrable, becomes Liouville integrable when lifted
to an S¹ principal bundle. This resolves a 300+ year puzzle by
showing that non-integrability is a consequence of insufficient
phase space structure.

\textbf{Significance}: This work:
\begin{itemize}
\item Discovers the first new integral beyond E, L, C in the 3BP
\item Validates lift-integrability via Morales-Ramis theory
\item Provides methodology applicable to other non-integrable systems
\end{itemize}

\textbf{Reproducibility}: All code and data are available at
[GitHub URL] and archived at [Zenodo DOI].

\closing{Sincerely,}

\end{letter}
\end{document}
```

## Common Issues

**Word count exceeded?**
- Move detailed proofs to supplement
- Condense methods section
- Remove redundant explanations

**Figure quality issues?**
- Use vector formats (PDF, EPS)
- Ensure 300+ DPI for raster
- Check color accessibility

**LaTeX compilation errors?**
- Verify all packages installed
- Check for missing figures
- Run BibTeX before final compile

**Journal format mismatch?**
- Download official template
- Check author guidelines
- Verify reference format

## Tests

```bash
pytest tests/wp5/test_manuscript_generator.py -v
pytest tests/wp5/test_figure_generator.py -v
pytest tests/wp5/test_latex_compiler.py -v
```

## References

- `src/python/publication/manuscript_generator.py` - Section generation
- `src/python/publication/figure_generator.py` - Figure creation
- `src/python/publication/arxiv_packager.py` - arXiv packaging
- PRL Author Guidelines: https://journals.aps.org/prl/authors
- arXiv: https://arxiv.org/
