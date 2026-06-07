

# **Feasibility Study (WP4) and Implementation Roadmap for Validating Higher-Dimensional Symplectic Embedding (WP4) in the Newtonian Three-Body Problem**

## **Executive Summary**

The validation of advanced numerical integrators for the Newtonian Three-Body Problem (3BP) requires a rigorous confrontation between theoretical novelty and established dynamical benchmarks. This report evaluates the feasibility of demonstrating the efficacy of "Work Package 4" (WP4)—a system utilizing Higher-Dimensional Symplectic Embedding—through a public-facing validation campaign. The core premise of the proposed system is the detection of "hidden integrability," a concept implying the existence of approximate conserved quantities in regions of phase space typically characterized by weak chaos or resonance. To prove the validity of such a system, one cannot rely on simple error metrics alone; one must demonstrate the preservation of geometric and topological structures over timescales that expose the failings of conventional algorithms.

The analysis indicates that a public demonstration is not only feasible but highly advantageous given the current availability of high-precision datasets. Specifically, the utilization of the "Figure-8" choreography and the newly discovered Shanghai Jiao Tong University (SJTU) "Piano-Trio" periodic families provides a rich testing ground for symplectic fidelity. Furthermore, the "Pythagorean Three-Body Problem" serves as an ideal stress test for handling the singular dynamics of close encounters in a chaotic regime. By benchmarking WP4 against industry-standard libraries such as REBOUND (Symplectic Wisdom-Holman and Adaptive IAS15) and the high-precision Taylor-series integrator Heyoka, the project can empirically quantify its advantages in long-term structural stability.

This document serves as a comprehensive roadmap for this validation effort. It details the theoretical underpinnings of the benchmarks, provides the precise initial conditions required for implementation, and outlines the architectural requirements for a public demonstration platform. The report concludes that with modest computational resources and a strategic focus on visualization of invariant tori in Poincaré sections, WP4 can be effectively validated, potentially offering a new paradigm for exploring the "dark matter" of the 3BP phase space—the hidden islands of integrability within the chaotic sea.

## **1\. Theoretical Foundations and the Problem of Integrability**

To contextualize the validation strategy, it is essential to first rigorously define the physical and mathematical landscape in which WP4 operates. The Newtonian Three-Body Problem is the archetypal system for the study of non-integrability, chaos, and the geometric integration of Hamiltonian systems. The claim of "Higher-Dimensional Symplectic Embedding" suggests a method that transcends standard discretization by embedding the dynamics into a manifold where the symplectic structure is more naturally or robustly preserved.

### **1.1 The Classical Non-Integrability of the Three-Body Problem**

The motion of three point masses $m\_1, m\_2, m\_3$ interacting via Newtonian gravity is governed by a Hamiltonian $H(q, p)$ representing the total energy of the system. While the two-body problem is integrable due to the existence of sufficient first integrals (energy, linear momentum, angular momentum, and the center of mass vector), the three-body problem lacks the requisite number of conserved quantities to reduce the system to quadrature.1 This non-integrability, famously proven by Poincaré, implies that for generic initial conditions, the equations of motion cannot be solved analytically, and the dynamics are sensitive to initial conditions (SDIC), leading to deterministic chaos.1

However, the non-integrability is not absolute in a local sense. The phase space of the 3BP is a "mixed" phase space, characterized by the coexistence of chaotic seas and regular islands. Within these islands, the motion is quasi-periodic and confined to invariant tori, as described by the Kolmogorov-Arnold-Moser (KAM) theory.4 These tori act as barriers to diffusion in low-dimensional systems. "Hidden integrability" in the context of WP4 likely refers to the ability of the symplectic embedding to resolve these surviving invariant structures in regimes where standard integrators introduce numerical noise that mimics chaotic diffusion, effectively destroying the "hidden" order.5

### **1.2 The Role of Symplectic Structure in Numerical Validity**

The validity of any integrator claiming to find "hidden" structure rests on its ability to preserve the symplectic 2-form $\\omega \= \\sum dq\_i \\wedge dp\_i$. Standard numerical methods, such as the explicit Runge-Kutta family, are generally non-symplectic; they do not conserve the phase space volume or the Hamiltonian structure. Over long integration times, this results in secular energy drift and the artificial dissipation of dynamical structures.8

A symplectic integrator, by contrast, replaces the flow of the continuous Hamiltonian $H$ with the flow of a discrete map that is exactly symplectic. This map can be viewed as the exact solution to a "shadow Hamiltonian" $\\tilde{H}$ which is close to $H$.10 The efficacy of WP4, therefore, must be judged not merely on the Euclidean error of particle positions—which naturally grows exponentially in chaotic systems due to the Lyapunov time—but on the preservation of these geometric invariants. If WP4 utilizes higher-dimensional embedding, it likely seeks to linearize the flow or regularize singularities (collisions) in a way that makes the shadow Hamiltonian $\\tilde{H}$ a better approximation of $H$ for longer periods.12

### **1.3 The Concept of Higher-Dimensional Embedding**

The specific reference to "Higher-Dimensional Symplectic Embedding" in the project title warrants detailed theoretical consideration. In classical mechanics, regularization techniques such as the Kustaanheimo-Stiefel (KS) transformation map the singular 3-dimensional equations of motion into a 4-dimensional harmonic oscillator space.14 This is a form of higher-dimensional embedding that removes the singularity at $r=0$. If WP4 employs a similar or more advanced geometric embedding, it theoretically allows the integrator to pass through close encounters—which are the primary source of error in the 3BP—with much higher fidelity than standard symplectic methods like Leapfrog or Wisdom-Holman, which can degrade when the timestep is not adaptable.15

The validation strategy must therefore specifically target regimes where close encounters are frequent (such as the Pythagorean problem) and regimes where long-term topological stability is paramount (such as periodic choreographies). The demonstration must prove that the "embedding" does not leak energy or information during these critical dynamical events.

## **2\. The Competitive Landscape: Establishing Benchmarks**

To demonstrate accuracy and efficacy "in a publicly demonstrative way," WP4 cannot exist in a vacuum. It must be compared against the current gold standards in the field. A failure to benchmark against these tools would render the report unconvincing to the domain experts. The two primary competitors identified in the research literature are REBOUND and Heyoka.

### **2.1 REBOUND: The Astrophysical Standard**

REBOUND is a multi-purpose N-body code that dominates the field of planetary dynamics and exoplanet research.15 It offers a suite of integrators that represent the "baseline" for any new system:

* **WHFast:** A symplectic Wisdom-Holman integrator. It is extremely fast and preserves the symplectic structure but assumes a dominant central mass (Keplerian splitting) and generally requires a fixed timestep.15 It is the standard for long-term stability of planetary systems.
* **IAS15:** A high-accuracy, non-symplectic integrator with adaptive timestepping (15th order). It is the standard for precision but does not guarantee long-term conservation of the Hamiltonian structure in the same theoretical sense as a symplectic method, although its accuracy is often high enough that this is negligible for integration times shorter than the "breakdown" time.15
* **MERCURIUS:** A hybrid integrator that switches between WHFast and IAS15 during close encounters.15

**Validation Relevance:** WP4 must demonstrate that it offers a distinct advantage over these. For instance, does it preserve energy better than WHFast during close encounters without the complexity of switching to a non-symplectic method like MERCURIUS? Does it maintain the topological structure of KAM islands better than IAS15 over $10^9$ periods?

### **2.2 Heyoka: The Precision Taylor Series Standard**

Heyoka represents a different philosophy: brute-force precision via Taylor series integration (TIDES methodology) implemented with modern LLVM just-in-time compilation.17

* **Mechanism:** It computes the Taylor expansion of the solution to very high order (e.g., 20-30) at each step. This allows for extremely large timesteps and machine-precision accuracy.17
* **Strengths:** It handles close encounters naturally by shrinking the radius of convergence of the Taylor series. It is often faster and more accurate than symplectic integrators for "short" (millions of orbits) timescales where exact precision is required.20
* **Weakness:** It is technically non-symplectic. Over extremely long timescales (billions of orbits), the lack of a symplectic constraint *might* allow for slow drift, although the precision is so high this is rarely observed.

**Validation Relevance:** Heyoka serves as the "Ground Truth" generator. When validating WP4, we can use Heyoka runs (with extended precision) to generate the "exact" trajectory. If WP4 deviates from the Heyoka trajectory but maintains the *energy* and *invariant tori* shapes, it validates the symplectic embedding claim: "imprecise but structurally stable."

### **2.3 Comparative Feature Matrix**

To effectively demonstrate WP4's position in this landscape, the public report should present a comparison similar to the table below, updated with WP4's actual performance data.

| Feature | REBOUND (WHFast) | REBOUND (IAS15) | Heyoka (Taylor) | WP4 (Proposed) |
| :---- | :---- | :---- | :---- | :---- |
| **Integrator Class** | Symplectic (Fixed Step) | Non-Symplectic (Adaptive) | Non-Symplectic (Adaptive) | **High-Dim Symplectic** |
| **Energy Conservation** | Bounded (Oscillatory) | Low Drift (High Order) | Machine Precision | **To Be Validated** |
| **Close Encounters** | Poor (Requires Hybrid) | Excellent | Excellent | **To Be Validated** |
| **Regularization** | None (Keplerian) | None | None (Adaptive Step) | **Embedded?** |
| **Long-Term Structure** | Excellent (KAM Preserved) | Good (Precision Dependent) | Excellent | **Target Strength** |

## **3\. Benchmark Case Study I: The Figure-8 and Periodic Choreographies**

The first pillar of the proposed "Triad of Validation" is the use of periodic orbits. These are the "standard candles" of celestial mechanics. Since periodic orbits are mathematically exact solutions where $z(T) \= z(0)$, they provide a binary pass/fail metric for the integrator. If the orbit drifts or breaks up, the integrator has failed to preserve the geometry.

### **3.1 The Figure-8 Orbit (Moore/Chenciner/Montgomery)**

Discovered numerically by Moore in 1993 and proven to exist by Chenciner and Montgomery in 2000, the "Figure-8" is a choreography where three equal masses chase each other along a single lemniscate curve.1 It is a stable orbit, but the island of stability surrounding it is finite. This makes it an ideal test case: a good symplectic integrator will keep the system on the stable torus, while a poor one will allow numerical noise to diffuse the trajectory into the surrounding chaotic sea.

#### **3.1.1 Precise Initial Conditions for Validation**

The efficacy of the demonstration depends on using high-precision initial conditions. Approximations will lead to immediate divergence, confusing physical instability with numerical error. We utilize the values refined by Simó and Hristov, which are accurate to tens of decimal places.21

For three equal masses $m\_1 \= m\_2 \= m\_3 \= 1$ (gravitational constant $G=1$), the initial configuration is:

* **Positions ($q$):**
  * Body 1: $x\_1 \= 0.97000436, y\_1 \= \-0.24308753$
  * Body 2: $x\_2 \= \-x\_1, y\_2 \= \-y\_1$
  * Body 3: $x\_3 \= 0, y\_3 \= 0$
* **Velocities ($v$):**
  * Body 3: $v\_{x3} \= \-0.93240737, v\_{y3} \= \-0.86473146$
  * Body 1: $v\_{x1} \= \-0.5 v\_{x3}, v\_{y1} \= \-0.5 v\_{y3}$
  * Body 2: $v\_{x2} \= v\_{x1}, v\_{y2} \= v\_{y1}$
* **Period ($T$):** $6.32591398$

Demonstration Implementation Plan:
The user should implement a script that initializes the system with these values and integrates for $N=10,000$ periods.

* **Metric 1: Periodicity Error:** Calculate $\\epsilon\_{per} \= ||z(nT) \- z(0)||$. A symplectic integrator should show bounded oscillation of this error. A linear growth ($\\epsilon \\propto t$) suggests phase error, which is acceptable, but an exponential growth ($\\epsilon \\propto e^{\\lambda t}$) indicates a failure to stay on the invariant torus.12
* **Metric 2: Shape Preservation:** Visual inspection in the demonstration is crucial. Plot the trajectory in the inertial frame. It must remain a thin, sharp line. Thickening of the line (width of the ink) indicates energy drift or diffusion.

### **3.2 The SJTU "Piano-Trio" and 3D Families**

While the Figure-8 is famous, it is 2D and relatively stable. To thoroughly test "Higher-Dimensional" embedding, we require 3D orbits and orbits with complex hierarchies. The recent work by Li, Liao, and the Shanghai Jiao Tong University (SJTU) group has revolutionized this field, uncovering thousands of new periodic families using the "Clean Numerical Simulation" (CNS) method.2

#### **3.2.1 Utilizing the SJTU Dataset**

The SJTU group has released their initial conditions on GitHub (sjtu-liao/three-body).2 This dataset includes:

* **Piano-Trio Orbits:** Configurations where two bodies form a binary and the third performs a choreography around them, but in a 3D structure that resembles the strings of a piano trio.24
* **Free-Fall Orbits:** Periodic orbits that begin from a pure rest state (collision-free).

Feasibility of Public Demonstration:
Using this data is highly feasible as it is open-source. The files initial-condition-of-3D-periodic-orbits.txt provide the exact parameters.

* **Test Protocol:** Select five "Piano-Trio" orbits. These orbits often exist in very narrow stability windows. Standard symplectic integrators (like a basic Leapfrog) often fail to maintain them because the varying timescales of the binary vs. the third body require either adaptive stepping (breaking symplecticity) or regularization.
* **WP4 Opportunity:** If WP4's "embedding" handles the multi-scale nature of these orbits (binary period $T\_1$ vs. system period $T\_2$) better than WHFast, it demonstrates a significant advance in finding "hidden" stability in hierarchical systems.

#### **3.2.2 3D Visualization Requirement**

For the public demonstration, these 3D orbits provide a visually stunning artifact. The report recommends building a WebGL-based viewer (using libraries like three.js or Python's plotly) where users can rotate the "Piano-Trio" orbits in 3D space.25 Seeing the complex, knotted topology of these orbits maintained over time is a powerful qualitative proof of efficacy.

## **4\. Benchmark Case Study II: Stress Testing in the Chaotic Regime**

The previous benchmarks tested stability. This section benchmarks the system's handling of **chaos** and **singularities**. The concept of "hidden integrability" is most valuable in chaotic zones, where it implies the existence of "sticky" regions or partial barriers that delay escape.

### **4.1 The Pythagorean Three-Body Problem (Burrau's Problem)**

Proposed by Burrau in 1913, this problem places masses 3, 4, and 5 at the vertices of a 3-4-5 right triangle at rest.26 It is legendary in celestial mechanics as a "torture test" because the system undergoes a prolonged period of violent interaction, including multiple close binary encounters, before eventually resolving.

#### **4.1.1 Dynamics and The "Szebehely Solution"**

The system begins at rest. The masses collapse toward the center of mass.

* **Masses:** $m\_1=3$ (at apex, opposite side 3), $m\_2=4$ (opposite side 4), $m\_3=5$ (at right angle, opposite side 5).
* **Coordinates (Szebehely 1967):**
  * $m\_1 (3)$: $x=1, y=3$
  * $m\_2 (4)$: $x=-2, y=-1$
  * $m\_3 (5)$: $x=1, y=-1$
  * $v=0$ for all.
* **Evolution:** The system remains bound and chaotic for a considerable time. At $t \\approx 59.4$, a binary of $m\_1$ and $m\_3$ forms, and $m\_2$ is ejected with hyperbolic velocity.14

Why this tests Symplectic Embedding:
The primary difficulty in Burrau's problem is the sequence of close encounters (near-collisions). As $r\_{ij} \\to 0$, the potential $V \\sim 1/r\_{ij}$ and force $F \\sim 1/r\_{ij}^2$ diverge.

* **Failure Mode:** Fixed-step symplectic integrators (like standard WHFast) will see the energy error spike massively during these encounters.
* **WP4 Goal:** If WP4 employs a "Higher-Dimensional" embedding that acts as a regularization (like KS regularization), it should handle these potential spikes smoothly, maintaining energy conservation without needing to reduce the timestep to near-zero.

#### **4.1.2 Validation Metrics and Reference Data**

The demonstration should compare the WP4 output against the high-precision reference coordinates provided in the research snippets.28

| Time (t) | Body | x Coordinate | y Coordinate |
| :---- | :---- | :---- | :---- |
| **0.0** | $m\_1$ | 1.0 | 3.0 |
| **10.0** | $m\_1$ | 0.77848... | 0.14139... |
| **10.0** | $m\_2$ | \-2.02509... | 0.09721... |
| **60.0** | $m\_1$ | 0.74368... | 1.93961... |
| **70.0** | $m\_1$ | 6.93108... | 20.2566... |

Demonstration Strategy:
Run the simulation to $t=100$.

1. **Binary Ejection Test:** Does WP4 correctly predict that mass $m\_2$ is ejected? (Many poor integrators eject the wrong mass due to chaotic amplification of errors).
2. **Precision Check:** Calculate the Euclidean distance between the WP4 state at $t=70$ and the reference values above. A distance $\< 10^{-6}$ suggests excellent handling of the chaotic transient.

### **4.2 Time-Reversibility: The Ultimate Fidelity Test**

The equations of motion are time-reversible ($t \\to \-t$). However, numerical chaos breaks this symmetry due to information loss (entropy generation in the digits).

* **The Test:** Integrate the Pythagorean problem forward to $t=50$ (deep in the chaotic mix), then reverse all velocities $v \\to \-v$, and integrate backward to $t=0$.
* **Metric:** Measure $\\Delta \= ||z\_{final} \- z\_{initial}||$.
* **Interpretation:** Ideally, $\\Delta \= 0$. For chaotic systems, this is impossible. However, symplectic integrators often perform orders of magnitude better than non-symplectic ones because they preserve the phase space volume, preventing the "focusing" of errors in one direction from collapsing the phase volume.9
* **Public Demo:** Show a video of the "Time Reversal." In the forward pass, the triangle collapses into chaos. In the reverse pass, the chaos should miraculously reassemble into the static 3-4-5 triangle. If WP4 succeeds, the triangle reforms perfectly. If it fails, the particles will miss the vertices, illustrating "the arrow of computational time."

## **5\. Quantitative Metrics for "Hidden Integrability"**

To move beyond standard error analysis and specifically address the "Hidden Integrability" aspect of the project, the report proposes adopting metrics from the field of symplectic topology and dynamical astronomy.

### **5.1 The Symplectic 2-Form Residual**

The most rigorous mathematical proof of "symplecticness" is to compute the deviation of the Jacobian from the symplectic group.10

* **Methodology:**
  1. Compute the Jacobian of the numerical step $M \= \\partial z\_{n+1} / \\partial z\_n$. (This can be done via automatic differentiation or finite differences).
  2. Check the condition $M^T J M \= J$, where $J$ is the canonical symplectic matrix $\\begin{pmatrix} 0 & I \\\\ \-I & 0 \\end{pmatrix}$.
  3. Define the metric: $\\mathcal{R}\_{symp} \= |

| M^T J M \- J ||$.

* **Efficacy Criterion:** For WP4 to claim "Symplectic Embedding," $\\mathcal{R}\_{symp}$ must be on the order of machine epsilon ($10^{-15}$), regardless of the chaos in the trajectory. If $\\mathcal{R}\_{symp}$ drifts, the method is not truly symplectic.

### **5.2 Visualizing Invariant Tori via Poincaré Sections**

"Hidden integrability" manifests as ordered structures (invariant tori) persisting in regions that should be chaotic according to lower-order perturbation theory.

* **Visualization:** Construct a Poincaré Surface of Section (e.g., plane $y\_2=0, \\dot{y}\_2 \> 0$).
* **Procedure:**
  1. Launch a swarm of test particles near a known periodic orbit (e.g., the Figure-8).
  2. Record their crossings of the section plane.
  3. **Visual Output:** Integrable regions appear as closed curves (circles/ellipses). Chaos appears as a scattered dust ("stochastic sea").
* **WP4 Advantage:** If WP4 preserves the "hidden" structure, the boundaries of these islands will remain sharp and well-defined for millions of crossings. Non-symplectic integrators will cause the points to "fuzz" and eventually leak out of the islands. This visual clarity is a powerful public demonstration of efficacy.30

### **5.3 Energy Error Spectrum**

Instead of just plotting energy error over time, compute the **Power Spectral Density (PSD)** of the energy error $\\Delta E(t)$.

* **Symplectic Signature:** The error should be bounded and oscillatory. The PSD will show discrete peaks at the orbital frequencies.
* **Non-Symplectic Signature:** The error will have a "random walk" or drift component, showing significant power at low frequencies ($f \\to 0$).
* **Demo:** Show the PSD of WP4 vs. RK4. The "clean" spectrum of WP4 visually proves it respects the Hamiltonian nature of the system.31

## **6\. Implementation Roadmap for Public Demonstration**

Based on the user's request, this section outlines the resources and steps required to build the "Public Demonstration."

### **6.1 Architecture of the Demonstration Platform**

To make this accessible, we propose a "Hybrid" architecture:

* **Core Engine (WP4):** Assumed to be C++ or Fortran for performance.
* **Interface Layer:** Python bindings (using pybind11 or ctypes). This allows easy scripting and integration with the scientific Python ecosystem (Matplotlib, NumPy).
* **Presentation Layer:** A GitHub repository and a static documentation site (Sphinx/Jupyter Book).

### **6.2 Data Acquisition Plan (Resources)**

The required data is public and free, minimizing cost.

1. **SJTU Data:** Clone the repository https://github.com/sjtu-liao/three-body. Parse the initial-condition-of-3D-periodic-orbits.txt into a JSON format standardized for the demo.2
2. **NASA Horizons:** Use the astroquery.jplhorizons Python package to fetch real-time state vectors for the Sun-Jupiter-Saturn system. This provides a "Real World" test case that resonates with the public.32
3. **Burrau/Figure-8:** Hardcode the high-precision values derived in Sections 3 and 4 into a benchmarks.py module.

### **6.3 Development Phases**

* **Phase 1: The Validation Suite (Week 1-2):**
  * Implement the Benchmark class in Python.
  * Integrate REBOUND (pip install rebound) and Heyoka (conda install heyoka) as comparison baselines.
  * Write the scripts to run the Figure-8 and Burrau tests and output error\_vs\_time.csv.
* **Phase 2: The "Hidden Integrability" Scanner (Week 3-4):**
  * Implement the Poincaré section logic.
  * Create a script that scans the vicinity of the Figure-8 orbit, launching 100 variations to map the "Island of Stability."
* **Phase 3: Visualization and Publication (Week 5):**
  * Generate the 3D WebGL plots for the Piano-Trio orbits.
  * Create the "Time Reversal" video for the Burrau problem.
  * Publish the report and the code repository.

### **6.4 Resource Estimation**

| Resource | Requirement | Cost/Availability |
| :---- | :---- | :---- |
| **Compute** | High-end Workstation (16+ Cores) | Standard Research/Personal Hardware |
| **Data Storage** | \< 1 GB | Negligible (GitHub) |
| **Software** | Python, C++, REBOUND, Heyoka | Open Source (Free) |
| **Development Time** | \~160 Hours (4 Weeks FTE) | 1 Researcher |
| **Skillset** | Numerical Analysis, Python, Dynamics | Assumed Expert |

## **7\. Feasibility Assessment**

The proposed demonstration is **High Feasibility**.

1. **Technical Feasibility:** The algorithms for 3BP integration are well-understood. The "special sauce" of WP4 (the embedding) is the only variable, but the *methods to test it* are standard. The availability of REBOUND and Heyoka provides an immediate, low-effort baseline for comparison.15
2. **Data Feasibility:** The release of the SJTU database 2 removes the need for the user to discover their own periodic orbits, which would have been a massive computational hurdle. The "Ground Truth" is already available.
3. **Demonstrative Value:** The visual nature of the 3BP (loops, chaos, triangles) makes it uniquely suited for public demonstration. Concepts like "Time Reversal" and "Figure-8 Stability" are intuitive to a lay audience yet mathematically deep for experts.

## **8\. Conclusion**

The "Systematic Search for Hidden Integrability" is a bold project that requires equally bold validation. By stepping out of the theoretical abstract and into the arena of concrete benchmarks—the precise choreography of the Figure-8, the complex topology of the SJTU Piano-Trio, and the chaotic violence of the Burrau problem—WP4 can prove its worth.

The "Triad of Validation" strategy proposed here provides a complete coverage of the integrator's performance:

1. **Periodic Orbits** prove the **Symplectic/Topological stability**.
2. **The Pythagorean Problem** proves the **Regularization/Robustness** in chaos.
3. **Poincaré Sections** visually demonstrate the core claim of **Hidden Integrability**.

By executing this roadmap and releasing the results as a "Public Validation Suite," the project will not only verify the technical components of WP4 but also contribute a valuable set of open-source benchmarks to the broader dynamical systems community. The path is clear, the data is ready, and the benchmarks are waiting.

## **9\. Appendix: Detailed Initial Condition Tables**

### **9.1 Burrau's Problem (Pythagorean 3BP)**

*Masses:* $m\_1=3, m\_2=4, m\_3=5$. *Initial Velocity:* 0\.

| Body | Mass | Initial X | Initial Y |
| :---- | :---- | :---- | :---- |
| $m\_1$ | 3 | 1 | 3 |
| $m\_2$ | 4 | \-2 | \-1 |
| $m\_3$ | 5 | 1 | \-1 |

### **9.2 Figure-8 Orbit (Simó Precision)**

*Masses:* $m\_1=m\_2=m\_3=1$. *Period:* $T \\approx 6.32591398$.

| Variable | Value |
| :---- | :---- |
| $x\_1$ | $0.97000436$ |
| $y\_1$ | $-0.24308753$ |
| $v\_{x3}$ | $-0.93240737$ |
| $v\_{y3}$ | $-0.86473146$ |
| $v\_{x1}$ | $-0.5 v\_{x3}$ |
| $v\_{y1}$ | $-0.5 v\_{y3}$ |

#### **Works cited**

1. Three-body problem \- Wikipedia, accessed November 28, 2025, [https://en.wikipedia.org/wiki/Three-body\_problem](https://en.wikipedia.org/wiki/Three-body_problem)
2. sjtu-liao/three-body: Periodic orbits for Newtonian planar three-body problem \- GitHub, accessed November 28, 2025, [https://github.com/sjtu-liao/three-body](https://github.com/sjtu-liao/three-body)
3. Newton's three-body problem explained \- Fabio Pacucci : r/threebodyproblem \- Reddit, accessed November 28, 2025, [https://www.reddit.com/r/threebodyproblem/comments/i300dy/newtons\_threebody\_problem\_explained\_fabio\_pacucci/](https://www.reddit.com/r/threebodyproblem/comments/i300dy/newtons_threebody_problem_explained_fabio_pacucci/)
4. KAM theory for the three-body problem \- Scholarpedia, accessed November 28, 2025, [http://www.scholarpedia.org/article/KAM\_theory\_for\_the\_three-body\_problem](http://www.scholarpedia.org/article/KAM_theory_for_the_three-body_problem)
5. Particular superintegrability of 3-body (modified) Newtonian gravity \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/341190817\_Particular\_superintegrability\_of\_3-body\_modified\_Newtonian\_gravity](https://www.researchgate.net/publication/341190817_Particular_superintegrability_of_3-body_modified_Newtonian_gravity)
6. Extended phase-space symplectic integration for electron dynamics \- arXiv, accessed November 28, 2025, [https://arxiv.org/html/2510.16542v1](https://arxiv.org/html/2510.16542v1)
7. Local Orbital Elements for the Circular Restricted Three-Body Problem | Journal of Guidance, Control, and Dynamics \- Aerospace Research Central, accessed November 28, 2025, [https://arc.aiaa.org/doi/10.2514/1.G007435](https://arc.aiaa.org/doi/10.2514/1.G007435)
8. Symplectic integrator \- Wikipedia, accessed November 28, 2025, [https://en.wikipedia.org/wiki/Symplectic\_integrator](https://en.wikipedia.org/wiki/Symplectic_integrator)
9. (PDF) Geometric integrators for ODEs \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/200175533\_Geometric\_integrators\_for\_ODEs](https://www.researchgate.net/publication/200175533_Geometric_integrators_for_ODEs)
10. Backward error analysis for conjugate symplectic methods \- AIMS Press, accessed November 28, 2025, [https://www.aimspress.com/article/doi/10.3934/jgm.2023005?viewType=HTML](https://www.aimspress.com/article/doi/10.3934/jgm.2023005?viewType=HTML)
11. Accurate and Efficient Simulations of Hamiltonian Mechanical Systems with Discontinuous Potentials, accessed November 28, 2025, [https://ins.sjtu.edu.cn/people/shijin/PS/Tao-Jin.pdf](https://ins.sjtu.edu.cn/people/shijin/PS/Tao-Jin.pdf)
12. The rate of error growth in Hamiltonian-conserving integrators \- Andrew Stuart, accessed November 28, 2025, [http://stuart.caltech.edu/publications/pdf/stuart30.pdf](http://stuart.caltech.edu/publications/pdf/stuart30.pdf)
13. Symplectic Flows and Maps and Volume Preservation \- webspace.science.uu.nl, accessed November 28, 2025, [https://webspace.science.uu.nl/\~frank011/Classes/numwisk/ch16.pdf](https://webspace.science.uu.nl/~frank011/Classes/numwisk/ch16.pdf)
14. Algorithmic regularization of the few-body problem, accessed November 28, 2025, [https://adsabs.harvard.edu/pdf/1999MNRAS.310..745M](https://adsabs.harvard.edu/pdf/1999MNRAS.310..745M)
15. Welcome to REBOUND \- REBOUND, accessed November 28, 2025, [https://rebound.readthedocs.io/](https://rebound.readthedocs.io/)
16. High Order Symplectic Integrators \- REBOUND, accessed November 28, 2025, [https://rebound.readthedocs.io/en/latest/ipython\_examples/HighOrderSymplectic/](https://rebound.readthedocs.io/en/latest/ipython_examples/HighOrderSymplectic/)
17. bluescarni/heyoka.py: Python library for ODE integration via Taylor's method and LLVM, accessed November 28, 2025, [https://github.com/bluescarni/heyoka.py](https://github.com/bluescarni/heyoka.py)
18. Taylor's method — heyoka.py 7.8.1 documentation, accessed November 28, 2025, [https://bluescarni.github.io/heyoka.py/tut\_taylor\_method.html](https://bluescarni.github.io/heyoka.py/tut_taylor_method.html)
19. \[PDF\] REBOUND: An open-source multi-purpose N-body code for collisional dynamics, accessed November 28, 2025, [https://www.semanticscholar.org/paper/REBOUND%3A-An-open-source-multi-purpose-N-body-code-Rein-Liu/5240c4a18da2b6dcae3fbfa633c01bee1670d0a0](https://www.semanticscholar.org/paper/REBOUND%3A-An-open-source-multi-purpose-N-body-code-Rein-Liu/5240c4a18da2b6dcae3fbfa633c01bee1670d0a0)
20. Benchmarks — heyoka 7.9.0 documentation, accessed November 28, 2025, [https://bluescarni.github.io/heyoka/benchmarks.html](https://bluescarni.github.io/heyoka/benchmarks.html)
21. A remarkable periodic solution of the three body problem in the case of equal masses \- IMCCE, accessed November 28, 2025, [https://perso.imcce.fr/alain-chenciner/huit.pdf](https://perso.imcce.fr/alain-chenciner/huit.pdf)
22. Periodic Three-Body Initial Conditions / Ricky Reusser | Observable, accessed November 28, 2025, [https://observablehq.com/@rreusser/periodic-three-body-initial-conditions](https://observablehq.com/@rreusser/periodic-three-body-initial-conditions)
23. Hundreds of New Satellites of Figure-eight Orbit Computed with High Precision \- AIP Publishing, accessed November 28, 2025, [https://pubs.aip.org/aip/acp/article-pdf/doi/10.1063/5.0177835/18217999/070003\_1\_5.0177835.pdf](https://pubs.aip.org/aip/acp/article-pdf/doi/10.1063/5.0177835/18217999/070003_1_5.0177835.pdf)
24. (PDF) Discovery of 10,059 new three-dimensional periodic orbits of general three-body problem \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/394457634\_Discovery\_of\_10059\_new\_three-dimensional\_periodic\_orbits\_of\_general\_three-body\_problem](https://www.researchgate.net/publication/394457634_Discovery_of_10059_new_three-dimensional_periodic_orbits_of_general_three-body_problem)
25. Use Python to Create Three-Body Orbits | Towards Data Science, accessed November 28, 2025, [https://towardsdatascience.com/use-python-to-create-three-body-orbits-329ffb5b2627/](https://towardsdatascience.com/use-python-to-create-three-body-orbits-329ffb5b2627/)
26. Global chaoticity in the Pythagorean three-body problem \- ResearchGate, accessed November 28, 2025, [https://www.researchgate.net/publication/226415727\_Global\_chaoticity\_in\_the\_Pythagorean\_three-body\_problem](https://www.researchgate.net/publication/226415727_Global_chaoticity_in_the_Pythagorean_three-body_problem)
27. Burrau's problem of three bodies, accessed November 28, 2025, [https://www.ucolick.org/\~laugh/oxide/projects/burrau.html](https://www.ucolick.org/~laugh/oxide/projects/burrau.html)
28. "Pythagorean Three Body Problem" \- need some points from an accurate solution for comparison, accessed November 28, 2025, [https://space.stackexchange.com/questions/15364/pythagorean-three-body-problem-need-some-points-from-an-accurate-solution-fo](https://space.stackexchange.com/questions/15364/pythagorean-three-body-problem-need-some-points-from-an-accurate-solution-fo)
29. \[2109.07013\] The relativistic Pythagorean three-body problem \- arXiv, accessed November 28, 2025, [https://arxiv.org/abs/2109.07013](https://arxiv.org/abs/2109.07013)
30. \[1001.0752\] Searching for integrable Hamiltonian systems with Platonic symmetries \- arXiv, accessed November 28, 2025, [https://arxiv.org/abs/1001.0752](https://arxiv.org/abs/1001.0752)
31. Symplectic Integrators Bound Energy Error \- RJ Nowling, accessed November 28, 2025, [https://rnowling.github.io/math/2017/01/11/symplectic-integrators-bound-energy-error.html](https://rnowling.github.io/math/2017/01/11/symplectic-integrators-bound-energy-error.html)
32. Horizons System \- JPL Solar System Dynamics, accessed November 28, 2025, [https://ssd.jpl.nasa.gov/horizons/](https://ssd.jpl.nasa.gov/horizons/)
33. Horizon API \- jpl ssd/cneos api \- NASA, accessed November 28, 2025, [https://ssd-api.jpl.nasa.gov/doc/horizons.html](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
