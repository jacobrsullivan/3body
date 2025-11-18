# WP 5.3: Publication Preparation
## Complete Implementation Plan

**Duration**: 14-21 days
**Prerequisites**: WP 5.1 Complete (Formal proofs available), WP 5.2 In Progress (Code ready)
**Objective**: Draft publication-ready manuscripts for peer-reviewed journals and preprint servers

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Task 5.3.1: Main Manuscript Drafting](#task-531-main-manuscript-drafting)
4. [Task 5.3.2: Supplementary Materials](#task-532-supplementary-materials)
5. [Task 5.3.3: Preprint Preparation](#task-533-preprint-preparation)
6. [Task 5.3.4: Journal Submission](#task-534-journal-submission)
7. [Figure and Table Generation](#figure-and-table-generation)
8. [Writing Guidelines](#writing-guidelines)
9. [Deliverables](#deliverables)

---

## Overview

### Purpose

WP 5.3 transforms formal proofs (WP 5.1) and reproducibility package (WP 5.2) into **publication-ready manuscripts** that communicate results clearly to the scientific community.

### The Publication Ladder

Depending on WP4 outcomes, we target different tiers of journals:

**Positive Result** (Validated Integral):
- **Tier 1**: Nature, Science, Nature Physics, Physical Review Letters
- **Tier 2**: Physical Review E, SIAM Journal on Applied Dynamical Systems
- **Tier 3**: Nonlinearity, Chaos

**Partial Result** (Regime-Specific):
- **Tier 1**: Physical Review E, SIAM Journal on Applied Dynamical Systems
- **Tier 2**: Celestial Mechanics and Dynamical Astronomy, Nonlinearity
- **Tier 3**: Physica D, Chaos

**Negative Result** (No Integrals):
- **Tier 1**: Communications in Mathematical Physics, Nonlinearity
- **Tier 2**: Physical Review E, Journal of Computational Physics
- **Tier 3**: Chaos

**WP 5.3 Goal**: Submit to Tier 1 journal within 21 days, with Tier 2/3 ready if needed.

---

## Architecture

### Four-Task Pipeline

```
WP 5.3: Publication Preparation (4 sequential tasks)
│
├── Task 5.3.1: Main Manuscript Drafting (7-10 days)
│   ├── Abstract
│   ├── Introduction
│   ├── Methods
│   ├── Results
│   ├── Discussion
│   └── Conclusion
│
├── Task 5.3.2: Supplementary Materials (3-5 days)
│   ├── Mathematical proofs
│   ├── Numerical methods
│   ├── Additional results
│   └── Figures and tables
│
├── Task 5.3.3: Preprint Preparation (2-3 days)
│   ├── arXiv formatting
│   ├── Social media strategy
│   └── Community engagement
│
└── Task 5.3.4: Journal Submission (2-3 days)
    ├── Cover letter
    ├── Suggested reviewers
    ├── Submission portal
    └── Response to editors
```

**Dependencies**: Tasks 5.3.1 and 5.3.2 partially overlap; 5.3.3 and 5.3.4 depend on 5.3.1 completion.

---

## Task 5.3.1: Main Manuscript Drafting

**Duration**: 7-10 days
**Objective**: Write the main paper (8,000-12,000 words) for submission to peer-reviewed journal

### Implementation Details

#### Part A: Abstract (0.5 days)

**Structure** (150-200 words):

**Template for Positive Result**:

```
The three-body problem, despite over 300 years of study, remains one of
the most challenging problems in classical mechanics. Bruns' and Poincaré's
no-go theorems establish that no additional algebraic integrals exist beyond
energy and angular momentum in the original phase space. We report the
discovery of a new conserved quantity in a minimal higher-dimensional
symplectic extension—an S¹ fiber bundle over the reduced shape space. This
"lift-integral" circumvents classical obstructions by living in the extended
space while generating nontrivial constraints on the original dynamics.

[1 sentence: Discovery method - geometric/ML/symbolic]

We validate conservation symbolically via Poisson brackets and numerically
across 10^5 trajectories spanning the full parameter space. The Morales-Ramis
criterion confirms downstairs non-integrability, proving our integral is a
genuine feature of the lift. This result opens a new avenue for studying
integrability through higher-dimensional embeddings.

[Impact statement: implications for celestial mechanics, dynamical systems theory]
```

**Key Components**:
1. **Hook** (1-2 sentences): Problem importance and history
2. **Gap** (1-2 sentences): What was missing / classical obstructions
3. **Contribution** (2-3 sentences): What we discovered and how
4. **Validation** (1-2 sentences): Evidence of correctness
5. **Impact** (1 sentence): Broader implications

**Negative Result Template**:

```
[Similar structure, but emphasizing:]
- Comprehensive search performed (geometric, ML, symbolic)
- No integrals found within computational bounds
- Morales-Ramis confirms non-integrability
- Establishes rigorous limits on lift-integrability hypothesis
- Advances understanding of chaos in 3BP
```

---

#### Part B: Introduction (1-2 days, ~1500 words)

**Structure**:

**Section I.1: Historical Context** (300 words)
```latex
\section{Introduction}

The three-body problem—to predict the motion of three point masses under
mutual gravitational attraction—has captivated scientists for over three
centuries \cite{Newton1687, Euler1772, Lagrange1772}. While exact solutions
exist for the two-body problem (Kepler), the three-body problem exhibits
rich chaotic behavior and admits only special-case solutions (Lagrange
equilibria \cite{Lagrange1772}, Euler collinear \cite{Euler1772}, Figure-8
choreography \cite{Moore1993, Chenciner2000}).

\subsection{Classical No-Go Theorems}

In the late 19th century, Bruns \cite{Bruns1887} and Poincaré
\cite{Poincare1892} proved that no additional \emph{algebraic} integrals of
motion exist beyond energy ($E$) and angular momentum ($\mathbf{L}$) in the
original $3N$-dimensional configuration space. These results, formalized by
the modern theory of Hamiltonian systems \cite{Arnold1989}, establish the
three-body problem as fundamentally non-integrable in the Liouville-Arnold
sense.

[Continue with KAM theory, chaos, Sundman series...]
```

**Section I.2: Lift-Integrability Hypothesis** (400 words)
```latex
\subsection{The Lift-Integrability Hypothesis}

A natural question arises: Do Bruns-Poincaré obstructions persist in
\emph{higher-dimensional} symplectic extensions? Recent work on the Kepler
problem demonstrates that the Kustaanheimo-Stiefel (KS) transformation
\cite{Kustaanheimo1965} reveals hidden SO(4) symmetry by lifting to
$\mathbb{R}^4$. This suggests a strategy: embed the three-body problem in a
minimal symplectic extension where classical obstructions may be circumvented.

We pursue two complementary lifts:
\begin{enumerate}
\item \textbf{S¹ Untwisting Bundle}: Neutralize the ``magnetic twist''
  (curvature of the mechanical connection) by adding a single cyclic
  coordinate \cite{Montgomery1991, Marsden1999}.

\item \textbf{KS-Spinor Lift}: Apply pairwise KS transformations to
  each relative vector, revealing potential hidden symmetries
  \cite{Levi-Civita1920, Moser1970}.
\end{enumerate}

If a conserved quantity $\widetilde{I}$ exists in the lift that is
\emph{functionally independent} of known integrals and \emph{does not
descend} to the base space, we have circumvented Bruns-Poincaré and discovered
"lift-integrability."
```

**Section I.3: Our Contribution** (400 words)
```latex
\subsection{Main Results}

In this work, we present a comprehensive computational and analytical study
of the lift-integrability hypothesis. Using a synthesis of geometric analysis,
machine learning, and symbolic methods, we [discovered/failed to discover]
conserved quantities in the S¹ bundle lift of the planar three-body problem.

\textbf{[FOR POSITIVE RESULT]}
Our main result is the discovery of a new conserved quantity $\widetilde{I}$
in the minimal S¹ bundle extension (Theorem 1). This integral:
\begin{itemize}
\item Is functionally independent of $E$, $\mathbf{L}$, and $p_\theta$
\item Poisson-commutes with the lifted Hamiltonian: $\{\widetilde{I},
  \widetilde{H}\} = 0$ (verified symbolically)
\item Is conserved across parameter space (validated on $10^5$ trajectories)
\item Does not descend to the base (confirmed via Morales-Ramis criterion)
\end{itemize}

\textbf{[FOR NEGATIVE RESULT]}
Our main result is a rigorous computational search establishing bounds on
non-existence of additional integrals within the search domain $\mathcal{D}$
(Theorem 1). We demonstrate:
\begin{itemize}
\item Comprehensive search via geometric (Killing fields), data-driven
  (Hamiltonian neural networks), and symbolic methods (symbolic regression)
\item No integrals found of polynomial degree $\leq 4$ or rational complexity
  $\leq 8$
\item Morales-Ramis criterion confirms downstairs non-integrability
\item Computational bounds establish limits on lift-integrability hypothesis
\end{itemize}

[Impact paragraph: implications for celestial mechanics, dynamical systems,
numerical methods]
```

**Section I.4: Paper Organization** (200 words)
```latex
\subsection{Organization}

This paper is organized as follows. Section \ref{sec:background} reviews
symplectic geometry and integrability theory. Section \ref{sec:lifts}
describes the construction of the S¹ and KS-Spinor lifts. Section
\ref{sec:discovery} details our discovery methods (geometric, ML, symbolic).
Section \ref{sec:validation} presents the validation framework (Liouville
criteria, Morales-Ramis, Monte Carlo). Section \ref{sec:results} reports the
main results. Section \ref{sec:discussion} discusses implications and
limitations. Complete proofs and numerical details are provided in the
Supplementary Material.

Code and data are publicly available at [GitHub URL] and archived at
[Zenodo DOI].
```

---

#### Part C: Methods Section (2-3 days, ~3000 words)

**Structure**:

**Section II: Mathematical Framework** (800 words)
- Hamiltonian systems and symplectic geometry
- Liouville-Arnold integrability
- Symplectic reduction (Marsden-Weinstein)
- Connection forms and curvature

**Section III: Symplectic Lifts** (1000 words)
- S¹ bundle construction
  - Fiber bundle definition
  - Lifted symplectic form
  - Lifted Hamiltonian
  - Validation of projection
- KS-Spinor lift (if used)
  - Pairwise KS transformation
  - Constraint handling
  - Constrained Hamiltonian

**Section IV: Discovery Methods** (1200 words)

**Subsection IV.A: Geometric Search (Killing Fields)**
```latex
\subsection{Geometric Discovery via Killing Fields}

Conserved quantities in geodesic flows correspond to Killing vector fields
of the Jacobi-Maupertuis metric \cite{Paternain1999}. We numerically solve
the Killing equation:
\begin{equation}
\nabla_{(i} K_{j)} = 0
\end{equation}
on a discretized mesh of the lifted configuration space.

\textbf{Implementation:}
\begin{itemize}
\item Mesh: $10^6$ points covering shape space $\times$ S¹
\item Discretization: Finite differences, $\Delta x \sim 10^{-3}$
\item Solver: Least-squares with Tikhonov regularization
\item Symmetry priors: Permutation invariance for identical masses
\end{itemize}

[Details of numerical method, convergence criteria...]
```

**Subsection IV.B: Machine Learning Discovery**
```latex
\subsection{Data-Driven Discovery via Hamiltonian Neural Networks}

We employ Hamiltonian Neural Networks (HNNs) \cite{Greydanus2019} with an
auxiliary invariant-discovery head. The network learns the lifted Hamiltonian
$\widetilde{H}$ and simultaneously predicts a conserved quantity
$\widetilde{I}$.

\textbf{Architecture:}
\begin{itemize}
\item Encoder: $(\mathbf{q}, \mathbf{p}, \theta, p_\theta) \mapsto \mathbf{h}$
  (5 layers, 256 units)
\item Hamiltonian head: $\mathbf{h} \mapsto \widetilde{H}$ (outputs scalar)
\item Invariant head: $\mathbf{h} \mapsto \widetilde{I}$ (outputs scalar)
\end{itemize}

\textbf{Loss Function:}
\begin{equation}
\mathcal{L} = \mathcal{L}_{\text{dyn}} + \lambda_1 \mathcal{L}_{\text{cons}}
  + \lambda_2 \mathcal{L}_{\text{Noether}}
\end{equation}
where:
\begin{itemize}
\item $\mathcal{L}_{\text{dyn}}$: Trajectory prediction error
\item $\mathcal{L}_{\text{cons}}$: Conservation penalty
  $\|\frac{d\widetilde{I}}{dt}\|^2$
\item $\mathcal{L}_{\text{Noether}}$: Regularizer encouraging symmetry
\end{itemize}

[Training details, hyperparameters, validation...]
```

**Subsection IV.C: Symbolic Regression**
```latex
\subsection{Symbolic Discovery via Evolutionary Regression}

We use PySR \cite{Cranmer2020} to search for explicit symbolic expressions
conserved along trajectories.

\textbf{Basis Functions:}
$\{1, q_i, p_i, \theta, p_\theta, q_i q_j, q_i p_j, \sin\theta,
\cos\theta, \ldots\}$

\textbf{Complexity Penalty:} Pareto front balancing accuracy vs. simplicity

[Details of symbolic regression pipeline...]
```

---

#### Part D: Results Section (2-3 days, ~3000 words)

**FOR POSITIVE RESULT**:

**Section V: Main Result** (500 words)
```latex
\section{Results}

\subsection{Discovery of a Lift-Integral}

We report the discovery of a conserved quantity $\widetilde{I}$ in the S¹
bundle lift of the planar three-body problem. The explicit form is:

\begin{equation}
\widetilde{I}(q, p, \theta, p_\theta) = [EXPLICIT EXPRESSION]
\end{equation}

where $q \in \mathcal{M}$ are shape-space coordinates, $p \in T^*_q\mathcal{M}$
are conjugate momenta, and $(\theta, p_\theta) \in T^*S^1$ are fiber
coordinates.

[Physical/geometric interpretation if available]

This integral was discovered via [geometric Killing field analysis / HNN
training / symbolic regression] (see Methods).
```

**Section V.1: Analytical Validation** (800 words)
```latex
\subsection{Analytical Validation}

We verify that $\widetilde{I}$ satisfies the Liouville integrability criteria.

\subsubsection{Conservation}

The Poisson bracket with the Hamiltonian vanishes:
\begin{equation}
\{\widetilde{I}, \widetilde{H}\}_{\widetilde{\omega}} = 0
\end{equation}

\textbf{Symbolic Verification:}
Using SymPy, we compute the bracket symbolically and verify it simplifies to
zero (see Supplementary Section S1 for full computation).

\textbf{Numerical Verification:}
On $N = 10^4$ random phase space points, we evaluate
$|\{\widetilde{I}, \widetilde{H}\}|$ and find:
\begin{equation}
\max_{i=1,\ldots,N} |\{\widetilde{I}, \widetilde{H}\}(x_i)| = 3.2 \times 10^{-13}
\end{equation}
This is below quad-precision tolerance, confirming conservation.

\subsubsection{Functional Independence}

We verify $\widetilde{I}$ is independent of known integrals via Jacobian rank:
\begin{equation}
J = \begin{pmatrix} \nabla E \\ \nabla L_z \\ \nabla p_\theta \\
\nabla \widetilde{I} \end{pmatrix}
\end{equation}

On the same $10^4$ sample, we find $\text{rank}(J) = 4$ on 99.97\% of points,
confirming independence (Figure \ref{fig:jacobian}).

\subsubsection{Non-Descent (Morales-Ramis Test)}

To verify $\widetilde{I}$ does not descend to the base, we apply the
Morales-Ramis criterion to the downstairs system. Computing the differential
Galois group along three periodic orbits (Lagrange, Euler, Figure-8), we find
$G^0 = \text{SL}(2, \mathbb{C})$ (non-abelian), confirming downstairs
non-integrability (Supplementary Section S2).

This proves $\widetilde{I}$ genuinely lives in the lift.
```

**Section V.2: Numerical Validation** (1200 words)
```latex
\subsection{Numerical Validation Across Parameter Space}

We validate conservation of $\widetilde{I}$ across the full parameter space
of the general three-body problem via Monte Carlo simulation.

\subsubsection{Monte Carlo Parameter Sweep}

\textbf{Sampling:} $N = 10^5$ initial conditions spanning:
\begin{itemize}
\item Mass ratios: $\mu \in [10^{-3}, 0.5]$ (30 values)
\item Energies: $E \in [E_{\min}, E_{\max}]$ (15 values)
\item Angular momenta: $L \in [0, L_{\max}]$ (10 values)
\end{itemize}

\textbf{Integration:} Yoshida 8th-order symplectic integrator, $\Delta t =
10^{-4}$, duration $T = 10^4$ periods.

\textbf{Conservation Metric:}
\begin{equation}
\epsilon_I(T) = \sup_{t \in [0,T]} \frac{|\widetilde{I}(t) - \widetilde{I}(0)|}
{\max(1, |\widetilde{I}(0)|)}
\end{equation}

\textbf{Results:}
Figure \ref{fig:monte_carlo} shows the distribution of $\epsilon_I$ across
all trajectories. We find:
\begin{itemize}
\item Success rate ($\epsilon_I < 10^{-6}$): 97.3\%
\item Mean drift: $\langle\epsilon_I\rangle = 2.1 \times 10^{-8}$
\item 95th percentile: $\epsilon_{I,95} = 8.4 \times 10^{-7}$
\end{itemize}

[Include Table 1: Success rates at different tolerances]
[Include Figure 2: Heatmap of success rate vs. (mass, energy)]

\subsubsection{Stress Testing}

\textbf{Near-Collisions:}
We test 1000 trajectories initialized near binary collision ($r_{12} < 10^{-3}$).
Using KS regularization, we integrate through the collision and verify
$\epsilon_I < 10^{-6}$ in 94\% of cases (Figure \ref{fig:collision}).

\textbf{Chaotic Regions:}
We select 5000 trajectories with positive Lyapunov exponent
$\lambda_{\max} > 10^{-2}$. Conservation is independent of chaos:
correlation $\rho(\epsilon_I, \lambda_{\max}) = 0.03$ (Figure
\ref{fig:chaos}).

[Continue with high-eccentricity tests, long-time integration...]
```

**Section V.3: Physical Interpretation** (500 words)
```latex
\subsection{Interpretation and Implications}

[Discuss geometric/physical meaning of $\widetilde{I}$]
[Connection to adiabatic invariants, if any]
[Implications for orbit prediction, stability analysis]
```

---

**FOR NEGATIVE RESULT**:

**Section V: Main Result** (similar structure)
- No integrals found within search bounds
- Document search comprehensiveness
- Morales-Ramis confirms non-integrability
- Establish computational bounds
- Discuss implications

---

#### Part E: Discussion Section (1-2 days, ~1500 words)

**Section VI: Discussion** (1500 words)

**Subsection VI.A: Comparison to Previous Work** (400 words)
- Relation to Bruns-Poincaré theorems
- Comparison to KAM theory
- Connection to Sundman series
- Differences from Kepler-problem lifts (KS transformation)

**Subsection VI.B: Limitations** (300 words)
- Restricted to planar case (3D future work)
- Computational bounds on search (degree ≤ 4 polynomials)
- Numerical validation (not formal proof)
- Specific lift construction (other lifts unexplored)

**Subsection VI.C: Future Directions** (400 words)
- Extension to spatial (3D) three-body problem
- Higher-rank lifts (KS-Spinor, higher bundles)
- N-body problem generalization
- Applications to restricted three-body problem (spacecraft trajectory design)
- Theoretical developments (characterize all possible lifts)

**Subsection VI.D: Broader Impact** (400 words)
- Implications for celestial mechanics
- New approach to studying integrability
- Computational methods transferable to other systems
- Connections to gauge theory, fiber bundles in physics

---

#### Part F: Conclusion (0.5 days, ~300 words)

```latex
\section{Conclusion}

[Summary paragraph: Restate main result]

[Positive result: We have demonstrated that lift-integrability circumvents
classical obstructions...]

[Negative result: We have established rigorous computational bounds on
lift-integrability...]

[Significance: This work opens new directions in the study of integrability
and provides tools for future research...]

[Call to action: Community engagement, extensions, applications...]
```

---

## Task 5.3.2: Supplementary Materials

**Duration**: 3-5 days
**Objective**: Provide complete mathematical and computational details

### Implementation Details

#### Part A: Supplementary Proofs (2 days, ~30 pages)

**Structure**:

**Section S1: Complete Poisson Bracket Computation** (5-10 pages)
```latex
\section{Supplementary Mathematical Proofs}

\subsection{S1: Poisson Bracket Computation}

We provide the complete symbolic computation of $\{\widetilde{I},
\widetilde{H}\}$.

[Full SymPy code + intermediate steps]
[Simplification steps]
[Final result: 0 or numerical bound]
```

**Section S2: Morales-Ramis Detailed Computation** (10-15 pages)
- Variational equations setup
- Normal variational equations
- Kovacic algorithm application
- Galois group determination
- Interpretation

**Section S3: Additional Lemmas** (5-10 pages)
- Technical lemmas used in main proof
- Estimates and bounds
- Convergence analysis

---

#### Part B: Numerical Methods Details (1 day, ~10 pages)

**Section S4: Integration Methods**
- Yoshida 8th-order coefficients
- Timestep selection criteria
- Regularization techniques (KS, Sundman)
- Error analysis

**Section S5: Mesh Generation**
- Configuration space discretization
- Adaptive refinement
- Boundary handling

**Section S6: Machine Learning Hyperparameters**
- Full HNN architecture
- Training procedure
- Hyperparameter tuning results

---

#### Part C: Additional Results (1 day, ~15 pages)

**Section S7: Extended Parameter Sweeps**
- Additional mass ratios
- Additional energy regimes
- 3D case (if attempted)

**Section S8: Alternative Discovery Methods**
- Killing tensors (rank 2)
- Alternative ML architectures
- Different symbolic regression bases

**Section S9: Validation Tests**
- Additional Poisson brackets (involution)
- Alternative Morales-Ramis orbits
- Longer integration times

---

#### Part D: Figures and Tables (1 day)

**High-Resolution Figures**:
- All main-text figures in vector format (PDF/SVG)
- Additional figures not in main text
- Figure data files (CSV)

**Data Tables**:
- Monte Carlo statistics (full tables)
- Hyperparameter sweeps
- Convergence data

---

## Task 5.3.3: Preprint Preparation

**Duration**: 2-3 days
**Objective**: Prepare arXiv preprint and engage community

### Implementation Details

#### Part A: arXiv Formatting (1 day)

**arXiv Submission Requirements**:
1. LaTeX source files (+ PDF)
2. Figures in acceptable formats
3. Bibliography file (.bib)
4. Total size < 50 MB

**Prepare Submission**:
```bash
# Compile locally
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Create arXiv bundle
tar -czf arxiv_submission.tar.gz \
  main.tex \
  supplement.tex \
  main.bbl \
  figures/*.pdf \
  revtex4-2.cls  # If needed
```

**arXiv Metadata**:
- **Title**: [Full title]
- **Authors**: [Names, affiliations, ORCIDs]
- **Abstract**: [Same as manuscript]
- **Categories**:
  - Primary: `math.DS` (Dynamical Systems)
  - Secondary: `astro-ph.EP` (Earth and Planetary Astrophysics)
  - Optional: `nlin.CD` (Chaotic Dynamics)
- **Comments**: "X pages, Y figures; code and data available at [URL]"
- **DOI**: [Will be assigned after publication]

---

#### Part B: Social Media and Community Engagement (1 day)

**Twitter Thread** (8-10 tweets):
```
🧵 THREAD: We just posted a new preprint on the three-body problem!

For 300+ years, we've known that the 3-body problem has no additional
integrals beyond energy & angular momentum (Bruns & Poincaré). But what
if we look in *higher dimensions*? 1/10

[Continue with accessible explanation, figures, link to arXiv]

Code & data: [GitHub URL]
Preprint: [arXiv URL]
Feedback welcome!
```

**Blog Post** (500-1000 words):
- Accessible explanation for broader audience
- Visualizations and animations
- Link to arXiv and GitHub

**Mailing List Announcement**:
- Email to relevant mailing lists:
  - Celestial Mechanics discussion groups
  - Dynamical Systems (SIAM)
  - Symplectic geometry
- Brief summary + link to arXiv

**Forum Posts**:
- MathOverflow (if appropriate)
- Physics Forums
- Relevant Slack/Discord channels

---

#### Part C: Direct Outreach (0.5 days)

**Email Key Researchers**:
- Identify 10-20 leaders in field
- Personalized email:
  ```
  Dear Prof. [Name],

  I hope this email finds you well. I'm writing to share a preprint
  that may be of interest given your work on [specific topic].

  We've been investigating the lift-integrability hypothesis for the
  three-body problem, and [main result]. The preprint is available at
  [arXiv link], and all code/data are open source at [GitHub link].

  We would greatly appreciate any feedback you might have, and would
  be happy to discuss the results further if you're interested.

  Best regards,
  [Your name]
  ```

---

## Task 5.3.4: Journal Submission

**Duration**: 2-3 days
**Objective**: Submit to target journal(s)

### Implementation Details

#### Part A: Cover Letter (1 day)

**Template**:

```
Dear Editor,

We are pleased to submit our manuscript entitled "[Full Title]" for
consideration in [Journal Name].

This work addresses a fundamental question in classical mechanics: can the
three-body problem be integrable in a higher-dimensional symplectic extension?
We report [main result], which [significance statement].

Our key contributions are:
1. [Contribution 1]
2. [Contribution 2]
3. [Contribution 3]

This work is timely and significant because [relevance to journal's scope].
We believe it will be of broad interest to the [Journal]'s readership,
spanning celestial mechanics, dynamical systems, and mathematical physics.

All data and code are publicly available at [URLs], ensuring full
reproducibility. The manuscript adheres to [Journal]'s formatting guidelines
and has not been submitted elsewhere.

We suggest the following potential reviewers:
[List 5-10 suggested reviewers with justification]

Thank you for considering our manuscript. We look forward to your response.

Sincerely,
[Authors]
```

---

#### Part B: Suggested Reviewers (0.5 days)

**Criteria for Reviewers**:
1. **Expertise**: Relevant background in dynamical systems, celestial mechanics, or symplectic geometry
2. **No Conflicts**: Not recent collaborators or advisors
3. **Geographic Diversity**: Mix of regions
4. **Career Stage**: Mix of senior and mid-career researchers

**Format**:
```
Suggested Reviewers:

1. Prof. Jane Doe (University of X)
   Email: jane.doe@university-x.edu
   Expertise: Hamiltonian systems, integrability theory
   Justification: Leading expert on Morales-Ramis criterion applications

2. Prof. John Smith (Institute Y)
   Email: john.smith@institute-y.edu
   Expertise: Three-body problem, celestial mechanics
   Justification: Author of recent review on 3BP solutions

[Continue for 5-10 reviewers]

Excluded Reviewers:
[If any conflicts of interest, list here]
```

---

#### Part C: Submission Portal (0.5 days)

**Submission Steps**:

1. **Create Account** on journal's submission portal
2. **Enter Metadata**:
   - Title, abstract, keywords
   - Authors (names, affiliations, ORCIDs, corresponding author)
   - Suggested reviewers
3. **Upload Files**:
   - Main manuscript (PDF)
   - Supplementary materials (PDF)
   - Cover letter (PDF)
   - Source files (LaTeX, figures) if required
4. **Review and Submit**

**Post-Submission**:
- **Confirmation Email**: Save for records
- **Manuscript Number**: Track submission status
- **Editor Assignment**: Typically 1-2 weeks

---

#### Part D: Response Timeline (Ongoing)

**Expected Timeline**:

- **Week 1-2**: Editorial office checks formatting, plagiarism
- **Week 2-4**: Editor decides: Desk reject OR send to reviewers
- **Week 4-8**: Peer review (2-3 reviewers)
- **Week 8-10**: Editor decision:
  - Accept (rare on first submission)
  - Minor revisions
  - Major revisions
  - Reject

**Response Strategy**:

**If Minor Revisions**:
- Respond within 2 weeks
- Address all comments point-by-point
- Resubmit promptly

**If Major Revisions**:
- Carefully assess feasibility (may require new WP4 validation)
- Respond within 4-6 weeks
- Consider escalating to collaborators if needed

**If Reject**:
- Incorporate feedback
- Submit to Tier 2 journal within 1 week
- Update arXiv with revised version

---

## Figure and Table Generation

### Key Figures

**Figure 1: Schematic of Lift Construction**
- Panel A: Original phase space (downstairs)
- Panel B: S¹ bundle (upstairs)
- Panel C: Projection map
- **Format**: Vector graphic (Inkscape/Illustrator)

**Figure 2: Conservation Validation**
- Panel A: $\widetilde{I}(t)$ for representative trajectory
- Panel B: Histogram of $\epsilon_I$ across Monte Carlo ensemble
- Panel C: Success rate vs. tolerance
- **Format**: Matplotlib (high-res PNG or PDF)

**Figure 3: Parameter Space Coverage**
- Heatmap: Success rate vs. (mass ratio, energy)
- **Format**: Matplotlib with colorbar

**Figure 4: Stress Tests**
- Panel A: Conservation during near-collision
- Panel B: $\epsilon_I$ vs. Lyapunov exponent (chaos independence)
- Panel C: Long-time behavior (10^6 periods)
- **Format**: Matplotlib

**Figure 5: Morales-Ramis Computation**
- Variational equation solutions
- Galois group determination
- **Format**: Matplotlib + schematic

### Key Tables

**Table 1: Monte Carlo Statistics**
| Tolerance | Success Rate | Mean $\epsilon_I$ | 95th Percentile |
|-----------|--------------|-------------------|-----------------|
| $10^{-6}$ | 97.3% | $2.1 \times 10^{-8}$ | $8.4 \times 10^{-7}$ |
| $10^{-8}$ | 89.1% | - | $4.2 \times 10^{-8}$ |
| $10^{-10}$ | 67.4% | - | $9.8 \times 10^{-10}$ |

**Table 2: Comparison to Known Integrals**
| Integral | Conservation | Independence | Involution |
|----------|--------------|--------------|------------|
| $E$ | ✓ (exact) | ✓ | ✓ |
| $L_z$ | ✓ (exact) | ✓ | ✓ |
| $p_\theta$ | ✓ (exact) | ✓ | ✓ |
| $\widetilde{I}$ | ✓ ($< 10^{-12}$) | ✓ (99.97%) | ✓ ($< 10^{-10}$) |

**Table 3: Discovery Method Comparison**
| Method | Success | Complexity | Runtime |
|--------|---------|------------|---------|
| Killing fields | Yes/No | Degree 2 | 3 days |
| HNN | Yes/No | 5M params | 1 week |
| Symbolic regression | Yes/No | Degree 4 | 2 days |

---

## Writing Guidelines

### Style and Clarity

**1. Active Voice**:
- ❌ "The integral was discovered by the HNN"
- ✅ "The HNN discovered the integral"

**2. Precise Language**:
- ❌ "very small", "quite large"
- ✅ "$< 10^{-12}$", "$> 10^5$ samples"

**3. Short Sentences**:
- Target: 15-25 words per sentence
- Break complex sentences into multiple sentences

**4. Avoid Jargon** (or define it):
- First use: "Morales-Ramis (MR) criterion"
- Later: "MR criterion"

**5. Transitions**:
- Between paragraphs: "Having established X, we now turn to Y"
- Between sections: "In the previous section, we X. Here, we Y"

### Mathematical Notation

**Consistency**:
- Scalars: italic ($E$, $H$, $I$)
- Vectors: bold ($\mathbf{q}$, $\mathbf{p}$, $\mathbf{L}$)
- Operators: upright ($\nabla$, $\text{d}$)
- Sets: calligraphic ($\mathcal{M}$, $\mathcal{D}$)

**Define Before Use**:
- Never use a symbol without defining it first
- Reminder definitions in long papers (e.g., "Recall that $\mathcal{M}$ denotes the shape space")

### Citation Practices

**Types of Citations**:
- **Authority**: "The Bruns theorem [15] establishes..."
- **Support**: "This approach has been successful [20-25]"
- **Comparison**: "Unlike previous work [10], our method..."

**Balance**:
- ~50-100 references typical for 8000-word paper
- Mix classic papers (Bruns, Poincaré) and recent work (<5 years)

---

## Deliverables

### Primary Outputs

1. **Main Manuscript** (8,000-12,000 words):
   - `manuscript/main.tex` + `main.pdf`
   - Abstract, Introduction, Methods, Results, Discussion, Conclusion
   - All figures and tables

2. **Supplementary Materials** (30-50 pages):
   - `manuscript/supplement.tex` + `supplement.pdf`
   - Complete proofs, numerical details, additional results

3. **arXiv Preprint**:
   - Submitted and assigned arXiv ID (e.g., `arXiv:2511.XXXXX`)
   - Link to GitHub and Zenodo in arXiv comments

4. **Journal Submission**:
   - Submitted to Tier 1 journal
   - Manuscript number and confirmation email
   - Cover letter and suggested reviewers

### Supporting Materials

5. **Figures Package**:
   - All figures in high resolution (vector preferred)
   - Figure source files (Matplotlib scripts, Inkscape SVGs)
   - Located in `manuscript/figures/`

6. **Social Media Content**:
   - Twitter thread (draft)
   - Blog post (500-1000 words)
   - Outreach emails (template)

7. **Revision Tracker**:
   - Document tracking journal feedback (when received)
   - Revision plan

---

## Timeline

### Day-by-Day Breakdown

**Days 1-3**: Abstract and Introduction
**Days 4-7**: Methods Section
**Days 8-11**: Results Section
**Days 12-14**: Discussion and Conclusion
**Days 15-17**: Supplementary Materials
**Days 18-19**: arXiv Preparation and Submission
**Days 20-21**: Journal Submission

**Total**: 21 days

---

## Success Criteria

### Minimum Success
- [ ] Complete manuscript (main + supplement)
- [ ] arXiv preprint submitted
- [ ] Journal submission initiated
- [ ] Code and data links functional

### Target Success
- [ ] Tier 1 journal submission
- [ ] High-quality figures (publication-ready)
- [ ] Community engagement (social media, emails)
- [ ] Positive initial feedback from colleagues

### Stretch Success
- [ ] Invited commentary or perspective piece
- [ ] Press release coordinated with journal
- [ ] Multiple journals approached (if fast-track possible)
- [ ] Conference presentation scheduled

---

## References

### Scientific Writing
1. Schimel, J. "Writing Science" (2012)
2. Alley, M. "The Craft of Scientific Writing" (2018)
3. Day, R. A. & Gastel, B. "How to Write and Publish a Scientific Paper" (2016)

### Journal-Specific Guides
4. Nature Physics Author Guidelines
5. Physical Review Letters Guide for Authors
6. SIAM Journal Author Information

---

**Document Version**: 1.0
**Created**: 2025-11-17
**Status**: Complete Implementation Plan
**Dependencies**: WP 5.1 Complete, WP 5.2 In Progress
**Next**: Journal Review Process and Revision
