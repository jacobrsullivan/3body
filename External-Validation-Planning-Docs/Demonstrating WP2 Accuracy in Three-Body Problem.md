

# **Feasibility and Validation Framework for Higher-Dimensional Symplectic Embeddings in the Newtonian Three-Body Problem**

## **1\. Executive Summary and Project Feasibility Overview**

The project "A Systematic Search for Hidden Integrability in the Newtonian Three-Body Problem via Higher-Dimensional Symplectic Embedding" represents a bold theoretical and computational venture into one of the oldest and most intractable problems in dynamical astronomy. The core hypothesis—that the chaotic mixing inherent in the three-body problem might be disentangled through an embedding into a higher-dimensional symplectic manifold—requires a rigorous, transparent, and reproducible validation framework to be accepted by the scientific community. This report evaluates the feasibility of demonstrating the efficacy of the Work Package 2 (WP2) components, which comprise the numerical engine, the embedding algorithms, and the diagnostic suite.

The analysis confirms that a public demonstration of WP2 is not only feasible but can be robustly supported by a mature ecosystem of existing open-source data and research. The feasibility rests on three pillars: the availability of high-precision "ground truth" datasets for periodic orbits, the existence of standard metrics for quantifying chaos and symplectic fidelity, and the accessibility of web-based visualization technologies. Specifically, the "Three-Body Gallery" established by Šuvakov and Dmitrašinović, along with the subsequent high-precision libraries by Li and Liao, provides an extensive testbed of periodic orbits that serve as strict boundary conditions for validating the embedding’s dynamical accuracy.1 These orbits act as discrete points of integrability within the chaotic sea, offering binary pass/fail criteria for the embedding's topological preservation.

Furthermore, the methodology for validating "hidden integrability" is well-defined through Frequency Map Analysis (FMA). By leveraging the Python library nafflib—a wrapper for Jacques Laskar’s numerical analysis of fundamental frequencies—the project can quantitatively demonstrate the suppression of Arnold diffusion in the embedded space.4 If the embedding effectively regularizes the dynamics, the tune diffusion rates derived from the high-dimensional variables should be orders of magnitude lower than those derived from standard Cartesian coordinates. This provides a clear, falsifiable metric for "efficacy."

The resource requirements for this validation are moderate. While the generation of high-resolution stability maps (Arnold webs) is computationally intensive, requiring cluster-level resources for comprehensive parameter sweeps, the validation of individual orbits and the generation of demonstration-quality visualizations can be performed on high-end consumer workstations. The development timeline is estimated at 10-12 weeks for a full public release, including the ingestion of public datasets, the implementation of comparative benchmarks against standard symplectic integrators like the Yoshida and Forest-Ruth algorithms, and the deployment of a WebGL-based interactive visualization using Three.js.7

Ultimately, the project is highly viable. The theoretical risk lies not in the software implementation (WP2), but in the mathematical properties of the embedding itself. However, the validation framework proposed herein is designed precisely to isolate and measure these properties, ensuring that any claim of "hidden integrability" is backed by rigorous numerical evidence involving symplectic form preservation and long-term energy stability.

## **2\. Theoretical Foundations: Chaos, Integrability, and the Embedding Hypothesis**

To understand the validation requirements for WP2, one must first appreciate the geometric and dynamical magnitude of the problem. The Newtonian three-body problem has served as the testing ground for dynamical systems theory since the time of Newton, Euler, and Lagrange.

### **2.1 The Geometry of the Three-Body Phase Space**

The motion of three point masses $m\_1, m\_2, m\_3$ is governed by a Hamiltonian system with 9 degrees of freedom (18 dimensions in phase space). Through the conservation of linear momentum, the center of mass motion can be eliminated, reducing the system to 6 degrees of freedom (12 dimensions). Further reduction using the conservation of angular momentum allows the system to be viewed in a 9-dimensional or, in the planar case, an 8-dimensional phase space. Despite these reductions, the system remains fundamentally non-integrable.

Henri Poincaré’s analysis in the late 19th century demonstrated that the series expansions used to approximate solutions were divergent. More importantly, he showed that the stable and unstable manifolds of fixed points could intersect transversely, creating a "homoclinic tangle".2 This geometric structures forces trajectories to fold and stretch in a complex manner, leading to sensitive dependence on initial conditions (SDIC), commonly known as chaos. In a chaotic region, the separation between two initially close trajectories $\\delta \\mathbf{z}(t)$ grows as $|\\delta \\mathbf{z}(0)| e^{\\lambda t}$, where $\\lambda$ is the maximum Lyapunov exponent.

The implication for WP2 is significant: any numerical method, no matter how precise, will eventually lose track of the true trajectory due to the amplification of machine epsilon errors. Therefore, validation cannot be based on tracking a chaotic trajectory for infinite time. Instead, validation must focus on **topological features**—specifically, periodic orbits and invariant tori—which persist even in chaotic systems.

### **2.2 The Concept of Hidden Integrability**

Hidden integrability suggests that a system appearing chaotic in its natural physical coordinates may possess conserved quantities or symmetries that are not manifest in that representation. Historical examples include the Calogero-Moser system or the Toda lattice, which were found to be integrable despite complex non-linear interactions. In the context of this project, the hypothesis is that the chaotic three-body flow on the physical manifold $\\mathcal{M}$ is the projection of a simpler, potentially integrable flow on a higher-dimensional symplectic manifold $\\mathcal{N}$.8

If such an embedding $\\Phi: \\mathcal{M} \\hookrightarrow \\mathcal{N}$ exists, it effectively "unfolds" the homoclinic tangle. Geometrically, this means that the knotted trajectories in $\\mathcal{M}$ might correspond to geodesic motion on a torus in $\\mathcal{N}$. This provides a clear validation target for WP2: the system must demonstrate that the "hidden" dimensions are not merely adding computational noise but are resolving the dynamic complexity into regular geometric structures.

### **2.3 Symplectic Embeddings and Form Preservation**

A critical requirement for the project is that the embedding must be symplectic. A map $\\Phi$ is symplectic if it preserves the symplectic 2-form structure of the phase space. If $\\omega$ is the standard symplectic form on the physical space $\\mathbb{R}^{2n}$ (where $\\omega \= \\sum dq\_i \\wedge dp\_i$) and $\\Omega$ is the form on the higher space $\\mathbb{R}^{2N}$, the embedding must satisfy the pullback condition:

$$\\Phi^\* \\Omega \= \\omega$$

In terms of the Jacobian matrix of the embedding, $D\\Phi$, this condition is algebraically expressed as:

$$(D\\Phi)^T J\_{2N} (D\\Phi) \= J\_{2n}$$

where $J$ is the canonical symplectic matrix $\\begin{pmatrix} 0 & I \\\\ \-I & 0 \\end{pmatrix}$.
This equation is the "hard constraint" for WP2. If the numerical implementation of the embedding violates this condition, the system is no longer Hamiltonian, and any observed stability or "integrability" is likely a numerical artifact (artificial dissipation) rather than a physical discovery.11 Validating this condition numerically is therefore a primary task for the demonstration phase.

## **3\. Data Ecosystem: Leveraging Public Research for Validation**

The feasibility of validating a novel integrator for the three-body problem depends entirely on the availability of reliable test data. Fortunately, the field has recently experienced a renaissance in the numerical search for periodic orbits, providing a rich "ground truth" ecosystem.

### **3.1 The Three-Body Gallery**

The primary resource for validation is the "Three-Body Gallery," initiated by the breakthrough work of Šuvakov and Dmitrašinović in 2013\.14 Using a numerical search algorithm based on minimizing the action functional, they identified 13 distinct new families of periodic orbits in the equal-mass planar three-body problem. These orbits are topologically distinct, characterized by their "free group element," which describes the braiding pattern of the three bodies in spacetime.3

These 13 families serve as excellent "unit tests" for WP2. Unlike generic chaotic trajectories, these orbits return to their initial state exactly after a period $T$.

* **The "Figure-Eight" Orbit:** Discovered by Moore in 1993 and popularized by Chenciner and Montgomery, this is a stable orbit where three bodies chase each other along a figure-eight curve. It is robust and should be easily maintained by the WP2 integrator.3
* **The "Moth" and "Goggles" Orbits:** These are more complex and often unstable. They provide a stress test for the integrator's precision. If the WP2 embedding introduces even slight symplectic errors, these orbits will decay into chaotic motion rapidly.

### **3.2 High-Precision Datasets (Li & Liao)**

Following Šuvakov’s work, Li and Liao employed the "Clean Numerical Simulation" (CNS) strategy—utilizing arbitrary-precision arithmetic (often 1200 decimal digits) and a high-order Taylor series method—to discover over 600 new families of periodic orbits.1 This dataset represents the "gold standard" for three-body dynamics.

The availability of this data (often as supplementary material to papers or in GitHub repositories mirrored by researchers like Ricky Reusser 18\) allows for a rigorous quantitative benchmark.
Validation Insight: The WP2 system can be initialized with the exact parameters from Li & Liao (e.g., to 100 decimal places). While the WP2 runtime might be limited to double or quadruple precision, comparing the divergence of the WP2 trajectory from the CNS trajectory over short timescales (1-10 periods) provides a direct measure of the local truncation error and the fidelity of the embedding.19

### **3.3 Restricted Three-Body Problem (R3BP) Data**

For a different class of validation, the project can utilize data from the Restricted Three-Body Problem, particularly regarding the stability of Lagrange points and resonances. NASA's JPL SSD (Solar System Dynamics) group provides accurate ephemerides and orbital elements for asteroids in the solar system, including the Trojan populations (stable at L4/L5) and the Hilda group (stable in 3:2 resonance with Jupiter).20

This data is valuable because it represents "real-world" integrability. The stability of Trojans is effectively guaranteed by the topology of the R3BP phase space (invariant tori around the equilibrium points).
Validation Strategy: The WP2 system should be able to reproduce the "islands of stability" seen in the phase space of the R3BP. By initializing particles in the Trojan region, the embedded integrator should show zero (or near-zero) diffusion, matching the known physical reality.22

### **3.4 Data Format and Accessibility**

Most of these datasets are available in accessible formats such as JSON, CSV, or plain text tables containing initial positions $(x, y)$, velocities $(\\dot{x}, \\dot{y})$, period $T$, and initial energy $E$.

* Source 18 (ObservableHQ): Provides a curated JSON collection of the Šuvakov and Li-Liao orbits, ready for immediate ingestion into Python or JavaScript environments.
* Source 20 (JPL): Provides osculating elements and state vectors for solar system bodies, useful for R3BP validation.

## **4\. Methodological Validation of WP2 Components**

To rigorously demonstrate the "accuracy and efficacy" of WP2, we must decompose the system into its constituent parts—the Integrator, the Embedding, and the Chaos Detector—and validate each against specific metrics derived from the research literature.

### **4.1 Component 1: The Symplectic Integrator Engine**

The numerical engine propagating the system in the high-dimensional space is the workhorse of WP2. It must be symplectic to preserve the geometric structure of the embedding.

#### **4.1.1 Energy Error Analysis**

The hallmark of a symplectic integrator is the absence of long-term energy drift. While the energy error $\\Delta E \= |H(t) \- H(0)|$ oscillates, it should remain bounded for exponentially long times, unlike non-symplectic methods (like Runge-Kutta 4\) where error grows as $O(t)$ or $O(t^2)$.
Metric: The validation report must present a log-log plot of Energy Error vs. Time for a long integration ($10^6$ \- $10^8$ steps).
Requirement: The error band should be bounded. The magnitude of the bound depends on the order of the integrator and the step size $\\tau$. For a 4th-order method, the error Hamiltonian $\\tilde{H} \- H$ should be of order $\\tau^4$.24

#### **4.1.2 Benchmarking Against Standard Algorithms**

To prove efficacy, the WP2 integrator must be compared against industry standards. The report should include a "Work-Precision Diagram" comparing WP2 against:

1. **Leapfrog / Verlet:** The standard 2nd-order symplectic integrator. It uses 1 force evaluation per step and is the baseline for speed.26
2. **Forest-Ruth / Yoshida (4th Order):** These are explicit symplectic integrators constructed by composing Leapfrog steps. The Forest-Ruth algorithm (and Yoshida's 4th order variant) typically requires 3 or 4 force evaluations per step.28
   * *Comparison Point:* A key metric is "Force Evaluations per Step" (FEPS). If the WP2 embedding requires dense matrix multiplications that mimic $N$ force evaluations, this cost must be justified by a proportional increase in accuracy or stability.
   * *Efficiency:* The metric "Error per Unit of Wall-Clock Time" determines if the high-dimensional overhead is worth it. Even if WP2 is slower per step, if it allows for a timestep $\\tau$ that is $10\\times$ larger (perhaps due to regularizing collisions), it effectively wins.28

#### **4.1.3 Reversibility Tests**

Hamiltonian dynamics are time-reversible. A symplectic integrator should respect this symmetry.
Test: Integrate the system forward for time $T$ to state $S\_T$. Reverse the momenta $\\mathbf{p} \\to \-\\mathbf{p}$. Integrate forward again for time $T$. The final state should be $S\_0$ (the initial condition).
Metric: The Euclidean distance $||\\mathbf{q}\_{final} \- \\mathbf{q}\_{initial}||$ serves as a sensitive test for non-symplectic round-off errors and implementation bugs.32

### **4.2 Component 2: The Higher-Dimensional Embedding**

This is the unique intellectual property of the project. Validating the mathematical correctness of the embedding $\\Phi: \\mathbb{R}^{2n} \\to \\mathbb{R}^{2N}$ is paramount.

#### **4.2.1 Numerical Verification of the Symplectic Condition**

The theoretical condition $(D\\Phi)^T J\_{2N} (D\\Phi) \= J\_{2n}$ must be verified numerically.
Algorithm:

1. Sample the phase space $\\mathcal{M}$ at random points $\\mathbf{z}\_i$.
2. Compute the Jacobian matrix $D\\Phi(\\mathbf{z}\_i)$ numerically. This can be done using finite differences or, more robustly, using Automatic Differentiation (AD) frameworks like JAX or PyTorch, which are exact up to machine precision.34
3. Compute the symplectic residual matrix $R \= (D\\Phi)^T J\_{2N} (D\\Phi) \- J\_{2n}$.
4. Metric: The Frobenius Norm of the residual, $||R||\_F \= \\sqrt{\\sum |r\_{ij}|^2}$, quantifies the deviation from symplecticity.35
   Success Criterion: For a valid symplectic embedding, $||R||\_F$ should be on the order of machine epsilon ($10^{-15}$ for float64). A value like $10^{-5}$ implies the embedding is "leaky"—it introduces non-Hamiltonian forces (drag or heating) that will invalidate any findings of hidden integrability.38

#### **4.2.2 Inverse Projection Stability**

The system must possess a robust inverse mapping $\\Psi: \\mathcal{N} \\to \\mathcal{M}$ such that $\\Psi(\\Phi(\\mathbf{z})) \= \\mathbf{z}$.
Test: Check the condition number of the projection. If the high-dimensional space contains "null directions" or instabilities that grow orthogonal to the physical manifold, the inverse mapping might become ill-conditioned over time. Monitoring the "drift" of the trajectory away from the embedded sub-manifold $\\Phi(\\mathcal{M})$ is crucial.

### **4.3 Component 3: Chaos Detection via Frequency Map Analysis (FMA)**

To demonstrate "hidden integrability," one must show that the system behaves more regularly in the embedded space than in the standard space. The tool for this is Frequency Map Analysis (FMA).

#### **4.3.1 The Laskar Method (NAFF)**

Developed by Jacques Laskar, the Numerical Analysis of Fundamental Frequencies (NAFF) algorithm decomposes a quasi-periodic signal $f(t)$ into a sum of exponentials $f(t) \\approx \\sum A\_k e^{i \\omega\_k t}$ with precision far exceeding the standard Fast Fourier Transform (FFT)—typically scaling as $1/T^4$ rather than $1/T$.4
Application: In an integrable system, the fundamental frequencies $\\omega\_k$ are constants of motion. In a chaotic system, they drift over time.

#### **4.3.2 The Tune Diffusion Metric**

The "Tune Diffusion" coefficient $D$ acts as a chaos indicator. It is defined as the change in the fundamental frequency calculated over two consecutive time windows 39:

$$D \= \\log\_{10} |\\nu^{(1)} \- \\nu^{(2)}|$$

where $\\nu^{(1)}$ is the frequency calculated for $t \\in$ and $\\nu^{(2)}$ is for $t \\in$.
Validation Hypothesis: If the WP2 embedding reveals hidden integrability, the diffusion coefficient $D\_{embedded}$ calculated from the latent variables should be significantly lower (more negative) than $D\_{Cartesian}$ calculated from physical variables. Alternatively, the embedding might reveal a new frequency $\\omega\_{hidden}$ that has a diffusion rate of essentially zero, indicating a hidden conserved quantity.

#### **4.3.3 Software Implementation (nafflib)**

The project can leverage the existing nafflib Python package, which wraps Laskar's original Fortran code or equivalent C implementations.4 This library allows for the precise extraction of tunes and the application of windowing functions (like the Hann window) to suppress spectral leakage.4 Using a standard library ensures that the chaos detection methodology is peer-reviewed and reliable.

## **5\. Implementation Strategy and Visualization Framework**

To publicly demonstrate the system, the project should adopt a two-tier strategy: a scientific validation suite for peers and a visual demonstration for the broader public.

### **5.1 Tier 1: The Scientific Validation Suite (Python/Jupyter)**

This tier provides the rigorous numerical proof required by the "Evaluating Persona."

* **Architecture:** A series of Jupyter Notebooks utilizing numpy for computation, nafflib for chaos analysis, and matplotlib for static plotting.
* **Workflow:**
  1. **Ingest:** Parse JSON data from the Three-Body Gallery.18
  2. **Integrate:** Run the "Figure-Eight" orbit using WP2 and a baseline scipy.integrate.odeint.
  3. **Analyze:** Compute the Energy Error $\\Delta E(t)$ and the Symplectic Residual $||R||\_F$.
  4. **Map:** Generate a Frequency Map (Tune Diagram) by integrating a grid of $100 \\times 100$ initial conditions around a stable point (like L4).
* **Output:** The "Money Plot" is the Frequency Map. It visualizes the "Arnold Web"—the network of resonances in phase space.44 A successful WP2 validation would show this web with high clarity, potentially revealing new stable regions invisible in standard coordinates.

### **5.2 Tier 2: The Interactive Web Demonstration (WebGL/Three.js)**

Visualization is a powerful heuristic for high-dimensional geometry.

* **Technology:** Three.js is the standard for web-based 3D graphics.7 It allows for GPU-accelerated N-body simulations in the browser.
* **Concept: The "Dimensional Toggle"**
  * **Standard View:** Render the 3-body trajectory in 3D Euclidean space. For chaotic orbits, this looks like a tangled "spaghetti" mess.
  * **Embedded View:** Render the trajectory as projected from the higher-dimensional space. For example, if the embedding maps the dynamics onto a hypersphere, project this onto a 3D sphere.
  * **The "Aha\!" Moment:** If the hypothesis is correct, the "spaghetti" in the Standard View might resolve into a neat, winding coil (a torus knot) in the Embedded View. This provides an intuitive, visual proof of the "unfolding" of chaos.46
* **Implementation:** Forking existing open-source N-body simulators (e.g., particle.js or basic Three.js examples) can save significant setup time.48 The core integrator logic from WP2 would need to be ported to JavaScript or compiled to WebAssembly (Wasm) for performance.

## **6\. Resource and Time Estimation**

### **6.1 Computational Cost Analysis**

The feasibility of the project is constrained by the computational cost of the high-dimensional operations.

* **Complexity:** Standard N-body force evaluation is $O(N^2)$. For $N=3$, this is trivial. However, the embedding operations likely involve matrix multiplications of size $K \\times K$ (where $K$ is the embedding dimension). This scales as $O(K^2)$ or $O(K^3)$.
* **Estimate:** If $K \\approx 20$, the WP2 integrator could be $10x$ to $50x$ slower per step than a raw C++ Leapfrog integrator.
* **Mitigation:** This cost is acceptable for research if the embedding allows for significantly larger timesteps (due to regularization of collisions) or provides unique stability properties. The report must explicitly quantify this "FLOPS vs Accuracy" trade-off.26

### **6.2 Hardware Requirements**

* **Single Orbit Validation:** Feasible on any modern laptop. Integrating a single orbit for $10^5$ periods takes seconds to minutes.
* **Stability Maps (Arnold Webs):** High cost. Generating a high-resolution map ($1000 \\times 1000$ pixels) requires $10^6$ separate integrations.
  * *Time:* At 1 minute per integration, this is \~2 years of serial compute time.
  * *Requirement:* Parallelization is essential. Using a 64-core workstation or a small cloud cluster (AWS Spot Instances), this can be reduced to a few days. For a public demo, pre-computing a lower resolution map ($100 \\times 100$) is sufficient and feasible overnight on a consumer PC.

### **6.3 Development Timeline**

1. **Data Ingestion (Weeks 1-2):** Parsing text/JSON formats from Three-Body Gallery and Li/Liao datasets; normalizing units ($G=1$, $m=1$).
2. **Integrator & Benchmark Implementation (Weeks 3-5):** Coding the Yoshida/Forest-Ruth baselines; implementing the Frobenius norm symplectic check; debugging the WP2 engine.
3. **Analysis Pipeline (Weeks 6-8):** Integrating nafflib; calibrating window functions; generating Tune Diffusion plots.
4. **Visualization (Weeks 8-10):** Porting logic to Three.js; building the web interface.
5. **Total:** Approximately 3 months for a single researcher to produce a comprehensive, demonstration-ready package.

## **7\. Critical Risk Analysis**

### **7.1 False Positives in Integrability**

A major scientific risk is misinterpreting slow Arnold diffusion as stability. In systems with $\>2$ degrees of freedom, trajectories can drift extremely slowly ($10^9$ years) through the Arnold web.45

* **Mitigation:** The validation must use long integration times ($T \> 10^7$ periods) and high-sensitivity metrics like FMA. Simple visual inspection of orbits is insufficient.

### **7.2 Numerical Precision Limits**

If validating against the Li & Liao dataset (1200 digits), standard double-precision (float64) will fail almost immediately due to the Lyapunov time being short for chaotic 3-body systems.

* **Mitigation:** The demonstration should focus on *topological* stability (Does the orbit stay a figure-eight?) rather than *phase* stability (Is the body at exactly $x=0.5$ at $t=1000$?). For strict validation, the Python mpmath library or C++ GMP must be used, accepting a massive performance penalty ($100x \- 1000x$ slowdown).19

## **8\. Conclusion**

The proposal to publicly demonstrate the WP2 components of the "Systematic Search for Hidden Integrability" project is highly feasible. The research ecosystem provides all necessary ingredients: the "Three-Body Gallery" offers the ground truth test cases; Frequency Map Analysis (via nafflib) provides the rigorous metric for success; and Three.js offers the medium for public dissemination.

The recommended path forward is to construct a rigorous "Jupyter Validation Suite" that subjects the embedded integrator to the symplectic condition test ($||J^T \\Omega J \- \\omega||\_F \\approx 0$) and the energy stability test. Following this, the construction of "Tune Diffusion Maps" comparing Cartesian vs. Embedded coordinates will provide the definitive proof of efficacy. By adhering to these standard metrics—benchmarked against known algorithms like Yoshida and Forest-Ruth—the project can present a compelling, mathematically sound case for the existence of hidden integrability in the three-body problem.

# **Tables**

### **Table 1: Comparative Analysis of Integrator Baselines for Benchmarking**

| Integrator Algorithm | Order | Symplectic? | Force Evals/Step | Description / Relevance to WP2 |
| :---- | :---- | :---- | :---- | :---- |
| **Leapfrog / Verlet** | 2nd | Yes | 1 | The industry standard for speed. Baseline for efficiency comparisons. 27 |
| **Forest-Ruth** | 4th | Yes | 3 | Explicit symplectic integrator. Standard baseline for accuracy tests. Coefficients are analytically defined. 29 |
| **Yoshida (Method A)** | 4th | Yes | 3 | Construction based on composition of 2nd order steps. High efficiency 4th order method. 30 |
| **Yoshida (Method B)** | 6th | Yes | 7 | High-order symplectic. Used for "hero" runs requiring high precision. Computationally expensive. 31 |
| **Runge-Kutta (RK4)** | 4th | No | 4 | Non-symplectic baseline. Useful to demonstrate energy drift and why symplectic methods are needed. |
| **WP2 Embedding** | ? | Yes (Target) | ? | The novel method. Must outperform baselines in stability or reveal hidden structure to be "efficacious". |

### **Table 2: Dataset Availability and Utility**

| Dataset Source | Content Type | Precision | Utility for WP2 | Access |
| :---- | :---- | :---- | :---- | :---- |
| **Šuvakov & Dmitrašinović (2013)** | 13 Families of Periodic Orbits | Double | High: Tests topological robustness of embedding. | Public (Gallery/GitHub) 14 |
| **Li & Liao (2017)** | 600+ Families (CNS) | Arbitrary | High: Stress tests numerical precision and handling of close encounters. | Public (Supp. Material) 1 |
| **Broucke-Hénon (BHH)** | Classical Periodic Orbits | Double | Medium: Standard unit tests for basic correctness. | Public (GitHub) 3 |
| **NASA JPL (Trojans/Hildas)** | R3BP State Vectors | Double | High: Real-world validation of quasi-integrable regions. | Public (SSD Website) 20 |

---

Citations:

1

#### **Works cited**

1. Newton's method for computing high-precision periodic orbits of the planar three-body problem, accessed November 28, 2025, [https://www.jinr.ru/posts/125721/](https://www.jinr.ru/posts/125721/)
2. On the periodic solutions of the three-body problem \- PMC \- NIH, accessed November 28, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC8291409/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8291409/)
3. On the periodic solutions of the three-body problem | National Science Review, accessed November 28, 2025, [https://academic.oup.com/nsr/article/6/6/1070/5537324](https://academic.oup.com/nsr/article/6/6/1070/5537324)
4. nafflib \- PyPI, accessed November 28, 2025, [https://pypi.org/project/nafflib/](https://pypi.org/project/nafflib/)
5. Data-driven Chaos Indicator for Nonlinear Dynamics and Applications on Storage Ring Lattice Design \- arXiv, accessed November 28, 2025, [https://arxiv.org/pdf/2104.08374](https://arxiv.org/pdf/2104.08374)
6. Chaos indicators for non-linear dynamics in circular particle acceleratorsWork funded by the HL-LHC project. \- arXiv, accessed November 28, 2025, [https://arxiv.org/html/2504.12741v1](https://arxiv.org/html/2504.12741v1)
7. mrdoob/three.js: JavaScript 3D Library. \- GitHub, accessed November 28, 2025, [https://github.com/mrdoob/three.js/](https://github.com/mrdoob/three.js/)
8. University of Groningen On the Relationship Between Differential Algebra and Tropical Differential Algebraic Geometry, accessed November 28, 2025, [https://research.rug.nl/files/228546335/978\_3\_030\_85165\_1.pdf](https://research.rug.nl/files/228546335/978_3_030_85165_1.pdf)
9. Integrable Many-Body Systems and Gauge Theories \- arXiv, accessed November 28, 2025, [https://www.arxiv.org/pdf/hep-th/0011197v2](https://www.arxiv.org/pdf/hep-th/0011197v2)
10. Four Lectures: Discretization and Integrability. Discrete Spectral Symmetries, accessed November 28, 2025, [https://homepage.mi-ras.ru/\~snovikov/174.pdf](https://homepage.mi-ras.ru/~snovikov/174.pdf)
11. Optimization on Symplectic Embeddings, accessed November 28, 2025, [https://kylersiegel.xyz/Optimization\_on\_Symplectic\_Embeddings.pdf](https://kylersiegel.xyz/Optimization_on_Symplectic_Embeddings.pdf)
12. INTRODUCTION TO SYMPLECTIC MECHANICS: LECTURE IV \- IME-USP, accessed November 28, 2025, [https://www.ime.usp.br/\~piccione/Downloads/LecturesIME2.pdf](https://www.ime.usp.br/~piccione/Downloads/LecturesIME2.pdf)
13. Reduced-order modeling of Hamiltonian dynamics based on symplectic neural networks, accessed November 28, 2025, [https://arxiv.org/html/2508.11911v1](https://arxiv.org/html/2508.11911v1)
14. Three-body problem \- Wikipedia, accessed November 28, 2025, [https://en.wikipedia.org/wiki/Three-body\_problem](https://en.wikipedia.org/wiki/Three-body_problem)
15. Periodic Planar Three-Body Orbits / Ricky Reusser \- Observable, accessed November 28, 2025, [https://observablehq.com/@rreusser/periodic-planar-three-body-orbits](https://observablehq.com/@rreusser/periodic-planar-three-body-orbits)
16. Computer Algebra in Scientific Computing \- CECM, SFU, accessed November 28, 2025, [http://ftp.cecm.sfu.ca/CAG/proceedings/CASC2020.pdf](http://ftp.cecm.sfu.ca/CAG/proceedings/CASC2020.pdf)
17. Over a thousand new periodic orbits of a planar three-body system with unequal masses | Publications of the Astronomical Society of Japan | Oxford Academic, accessed November 28, 2025, [https://academic.oup.com/pasj/article/70/4/64/4999993](https://academic.oup.com/pasj/article/70/4/64/4999993)
18. Periodic Three-Body Initial Conditions / Ricky Reusser | Observable, accessed November 28, 2025, [https://observablehq.com/@rreusser/periodic-three-body-initial-conditions](https://observablehq.com/@rreusser/periodic-three-body-initial-conditions)
19. N-body simulation still losing precision despite using arbitrary-precision arithmetic and symplectic integrator \- Astronomy Stack Exchange, accessed November 28, 2025, [https://astronomy.stackexchange.com/questions/48469/n-body-simulation-still-losing-precision-despite-using-arbitrary-precision-arith](https://astronomy.stackexchange.com/questions/48469/n-body-simulation-still-losing-precision-despite-using-arbitrary-precision-arith)
20. Three-Body Periodic Orbits \- JPL Solar System Dynamics, accessed November 28, 2025, [https://ssd.jpl.nasa.gov/tools/periodic\_orbits.html](https://ssd.jpl.nasa.gov/tools/periodic_orbits.html)
21. A dynamical study of Hilda asteroids in the Circular and Elliptic RTBP \- arXiv, accessed November 28, 2025, [https://arxiv.org/html/2412.07700v1](https://arxiv.org/html/2412.07700v1)
22. Stability of Jupiter Trojans investigated using frequency map analysis: the MATROS project \- Oxford Academic, accessed November 28, 2025, [https://academic.oup.com/mnras/article/345/4/1091/1069837](https://academic.oup.com/mnras/article/345/4/1091/1069837)
23. Prospects for detecting decreasing exoplanet frequency with main-sequence age using PLATO | Monthly Notices of the Royal Astronomical Society | Oxford Academic, accessed November 28, 2025, [https://academic.oup.com/mnras/article/453/1/67/1749977](https://academic.oup.com/mnras/article/453/1/67/1749977)
24. Fractals in the 3-Body Problem Via Symplectic Integration \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/266405027\_Fractals\_in\_the\_3-Body\_Problem\_Via\_Symplectic\_Integration](https://www.researchgate.net/publication/266405027_Fractals_in_the_3-Body_Problem_Via_Symplectic_Integration)
25. On the accuracy of symplectic integrators for secularly evolving planetary systems \- Oxford Academic, accessed November 28, 2025, [https://academic.oup.com/mnras/article/490/4/5122/5601761](https://academic.oup.com/mnras/article/490/4/5122/5601761)
26. n-body problem \- Wikipedia, accessed November 28, 2025, [https://en.wikipedia.org/wiki/N-body\_problem](https://en.wikipedia.org/wiki/N-body_problem)
27. N-Body Simulation, accessed November 28, 2025, [https://home.ifa.hawaii.edu/users/barnes/ast626\_09/NBody.pdf](https://home.ifa.hawaii.edu/users/barnes/ast626_09/NBody.pdf)
28. 1\. INTRODUCTION 2\. SYMPLECTIC INTEGRATORS, accessed November 28, 2025, [https://aa.usno.navy.mil/downloads/reports/ChambersMurison2000.pdf](https://aa.usno.navy.mil/downloads/reports/ChambersMurison2000.pdf)
29. Symplectic Correctors \- MIT, accessed November 28, 2025, [http://web.mit.edu/wisdom/www/Symplectic\_Correctors.pdf](http://web.mit.edu/wisdom/www/Symplectic_Correctors.pdf)
30. arXiv:cond-mat/0110585v1 \[cond-mat.stat-mech\] 29 Oct 2001, accessed November 28, 2025, [https://arxiv.org/pdf/cond-mat/0110585](https://arxiv.org/pdf/cond-mat/0110585)
31. Symplectic Integrators: T \+ V Revisited and Round-Off Reduced \- arXiv, accessed November 28, 2025, [https://arxiv.org/pdf/1812.07007](https://arxiv.org/pdf/1812.07007)
32. Fast Indicators for Orbital Stability: A Survey on Lyapunov and Reversibility Errors \- Semantic Scholar, accessed November 28, 2025, [https://pdfs.semanticscholar.org/75aa/9cdb8d0f5120e698b3d02eb4735d96f69767.pdf](https://pdfs.semanticscholar.org/75aa/9cdb8d0f5120e698b3d02eb4735d96f69767.pdf)
33. N-body Problem in \- DSpace@MIT, accessed November 28, 2025, [https://dspace.mit.edu/bitstream/handle/1721.1/119107/1059520269-MIT.pdf](https://dspace.mit.edu/bitstream/handle/1721.1/119107/1059520269-MIT.pdf)
34. Computing the Jacobian matrix in symplectic Euler integration \- Math Stack Exchange, accessed November 28, 2025, [https://math.stackexchange.com/questions/4054176/computing-the-jacobian-matrix-in-symplectic-euler-integration](https://math.stackexchange.com/questions/4054176/computing-the-jacobian-matrix-in-symplectic-euler-integration)
35. Time-adaptive Lagrangian variational integrators for accelerated optimization \- AIMS Press, accessed November 28, 2025, [https://www.aimspress.com/article/doi/10.3934/jgm.2023010?viewType=HTML](https://www.aimspress.com/article/doi/10.3934/jgm.2023010?viewType=HTML)
36. Symplectic Model Order Reduction with Non-Orthonormal Bases \- MDPI, accessed November 28, 2025, [https://www.mdpi.com/2297-8747/24/2/43](https://www.mdpi.com/2297-8747/24/2/43)
37. Topics on geometric integration, accessed November 28, 2025, [https://www.research.unipd.it/retrieve/e14fb26f-e9d2-3de1-e053-1705fe0ac030/Ortolan\_PhD11.pdf](https://www.research.unipd.it/retrieve/e14fb26f-e9d2-3de1-e053-1705fe0ac030/Ortolan_PhD11.pdf)
38. metrics, geodesics and applications, accessed November 28, 2025, [https://portal.findresearcher.sdu.dk/files/191222862/2108.12447v1.pdf](https://portal.findresearcher.sdu.dk/files/191222862/2108.12447v1.pdf)
39. Chaos in Compact Binaries with Frequency Map Analysis ∗ \- Research in Astronomy and Astrophysics (RAA), accessed November 28, 2025, [https://www.raa-journal.org/issues/all/2006/v6n6/202203/P020220325523205749695.pdf](https://www.raa-journal.org/issues/all/2006/v6n6/202203/P020220325523205749695.pdf)
40. Frequency map analysis and particle accelerators \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/4069729\_Frequency\_map\_analysis\_and\_particle\_accelerators](https://www.researchgate.net/publication/4069729_Frequency_map_analysis_and_particle_accelerators)
41. Inner Triplet Quadrupole Fringe Fields in the High Luminosity Large Hadron Collider \- The University of Liverpool Repository, accessed November 28, 2025, [https://livrepository.liverpool.ac.uk/3074111/1/200628741\_June2019.pdf](https://livrepository.liverpool.ac.uk/3074111/1/200628741_June2019.pdf)
42. xsuite/nafflib \- GitHub, accessed November 28, 2025, [https://github.com/xsuite/nafflib](https://github.com/xsuite/nafflib)
43. PyCOMPLETE/NAFFlib \- GitHub, accessed November 28, 2025, [https://github.com/PyCOMPLETE/NAFFlib](https://github.com/PyCOMPLETE/NAFFlib)
44. THE PARAMETRIC OSCILLATOR MODEL FOR THE CASE OF RESONANT ARGUMENT CIRCULATIONS \- arXiv, accessed November 28, 2025, [https://arxiv.org/html/2511.06759v1](https://arxiv.org/html/2511.06759v1)
45. Quasi-Periodic Frequency Analysis Using Averaging-Extrapolation Methods \- Departament de Matemàtiques, accessed November 28, 2025, [https://web.mat.upc.edu/jordi.villanueva/publications/freqanal.pdf](https://web.mat.upc.edu/jordi.villanueva/publications/freqanal.pdf)
46. I built a cosmic journey portfolio with Three.js \- zoom from the Milky Way to my desk \- Reddit, accessed November 28, 2025, [https://www.reddit.com/r/threejs/comments/1kh0jot/i\_built\_a\_cosmic\_journey\_portfolio\_with\_threejs/](https://www.reddit.com/r/threejs/comments/1kh0jot/i_built_a_cosmic_journey_portfolio_with_threejs/)
47. A rudimentary simulation of the three-body problem \- Hacker News, accessed November 28, 2025, [https://news.ycombinator.com/item?id=39909123](https://news.ycombinator.com/item?id=39909123)
48. three.js n-body simulation \- javascript \- Stack Overflow, accessed November 28, 2025, [https://stackoverflow.com/questions/32080466/three-js-n-body-simulation](https://stackoverflow.com/questions/32080466/three-js-n-body-simulation)
49. ericye16/nbodies: N-Body Simulation in Javascript and three.js \- GitHub, accessed November 28, 2025, [https://github.com/ericye16/nbodies](https://github.com/ericye16/nbodies)
50. Comparison of Very Smooth Cell-Model Trajectories Using Five Symplectic and Two Runge-Kutta Integrators \- CMST | Computational Methods in Science and Technology, accessed November 28, 2025, [https://cmst.eu/wp-content/uploads/files/10.12921\_cmst.2015.21.03.001\_Hoovers.pdf](https://cmst.eu/wp-content/uploads/files/10.12921_cmst.2015.21.03.001_Hoovers.pdf)
51. Symplectic integrators: T \+ V revisited and round-off reduced \- Oxford Academic, accessed November 28, 2025, [https://academic.oup.com/mnras/article/483/4/5574/5253615](https://academic.oup.com/mnras/article/483/4/5574/5253615)
52. arXiv:1504.00620v2 \[nlin.CD\] 21 Apr 2015 \- William Hoover, accessed November 28, 2025, [https://www.williamhoover.info/Scans2010s/1504.00620.pdf](https://www.williamhoover.info/Scans2010s/1504.00620.pdf)
53. CCAR-ORCCA/PO\_database: Database of families of ... \- GitHub, accessed November 28, 2025, [https://github.com/CCAR-ORCCA/PO\_database](https://github.com/CCAR-ORCCA/PO_database)
54. WHFast512: A symplectic N-body integrator for planetary systems optimized with AVX512 instructions \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/372313603\_WHFast512\_A\_symplectic\_N-body\_integrator\_for\_planetary\_systems\_optimized\_with\_AVX512\_instructions](https://www.researchgate.net/publication/372313603_WHFast512_A_symplectic_N-body_integrator_for_planetary_systems_optimized_with_AVX512_instructions)
