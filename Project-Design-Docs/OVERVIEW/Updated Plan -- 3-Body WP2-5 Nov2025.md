This document outlines the revised working plan for the project: "A Systematic Search for Hidden Integrability in the Newtonian Three-Body Problem via Higher-Dimensional Symplectic Embedding."

This plan integrates critical expert feedback, pivoting the core strategy towards **lift-integrability**. The goal is to find a new conserved quantity ($\\widetilde{I}$) in a minimal higher-dimensional symplectic extension ("upstairs"), whose projection reproduces the standard three-body dynamics ("downstairs"). This approach circumvents classical obstructions (e.g., Bruns, Poincaré).

Work Package 1 (WP1: High-Precision Symplectic Integration Suite and R3BP Data Generation) is complete. The following plan details the subsequent phases, designed for developers to create detailed weekly implementation plans.

---

### **WP 2: Geometric Foundations and Lift Construction**

This phase establishes the mathematical framework and implements the two primary higher-dimensional embeddings (lifts): the minimal cohomological fix (S¹ untwisting) and the maximal symmetry fix (KS-Spinor lift).

#### **WP 2.1: Geometric Reduction and Shape Space Analysis**

**Objective:** Implement the standard reduction pipeline to shape space and explicitly compute the geometric structures that obstruct integrability downstairs.

* **Task 2.1.1: Coordinate Systems and Reduction Implementation:**
  * Implement robust, high-precision transformations between Cartesian, Jacobi, and Shape Space coordinates (e.g., using relative normalized coordinates or inter-particle distances).
  * Implement the Marsden-Weinstein symplectic reduction (quotienting by translations and rotations SO(3)).
* **Task 2.1.2: Computation of the "Magnetic Twist":**
  * Symbolically and numerically compute the mechanical connection one-form ($A$).
  * Compute the curvature two-form ($\\sigma \= dA$). This is the explicit geometric obstruction to integrability downstairs.
* **Task 2.1.3: Jacobi-Maupertuis (JM) Metric Analysis:**
  * Implement the JM metric ($g\_{JM}=(E-V) g\_{\\text{mass}}$) on the shape space.
  * Numerically evaluate and visualize the scalar curvature of the JM metric, confirming regions of negative curvature (the signature of chaos) in key regimes (e.g., planar equal-mass).
* **Deliverable 2.1:** A validated library for reduced coordinates, the connection ($A$), curvature ($\\sigma$), and the JM metric.

#### **WP 2.2: Construction of the Minimal S¹ "Untwisting" Lift**

**Objective:** Construct the minimal extension required to neutralize the magnetic twist identified in WP 2.1.

* **Task 2.2.1: Fiber Bundle Construction:**
  * Define the extended configuration space by adding one cyclic angle ($\\theta \\in S^1$) and its canonical momentum ($p\_\\theta$).
* **Task 2.2.2: Extended Symplectic Form and Hamiltonian:**
  * Implement the extended symplectic form $\\widetilde{\\omega}$ using the connection $A$: $\\widetilde\\omega \= \\omega\_{\\text{can}} \+ d\\theta \\wedge (p\_\\theta \- A)$. Verify it is globally exact.
  * Define the extended Hamiltonian $\\widetilde{H}$ on the S¹ bundle.
* **Task 2.2.3: Lifted Dynamics Implementation and Verification:**
  * Adapt the high-precision symplectic integrators (from WP1) to evolve the equations of motion derived from $\\widetilde{H}$ and $\\widetilde{\\omega}$.
  * **Validation (Kill Switch):** Verify that the projection of the lifted dynamics (reduction by the S¹ action on a constant $p\_\\theta$ level set) exactly recovers the original reduced dynamics downstairs.
* **Deliverable 2.2:** Verified implementation of the S¹ lifted Hamiltonian and corresponding integrators.

#### **WP 2.3: Construction of the KS-Spinor "Pairwise" Lift**

**Objective:** Implement a structured lift inspired by the Kustaanheimo-Stiefel (KS) transformation, aiming to reveal hidden symmetries analogous to the Kepler problem's SO(4).

* **Task 2.3.1: Pairwise KS Implementation:**
  * Implement the spinor/quaternion representation (KS transformation) for each relative vector ($r\_{ij}$), transforming them into 4D oscillators ($Q\_{ij}$).
* **Task 2.3.2: Constraint Implementation (Triangle Closure):**
  * Enforce the triangle closure constraint ($r\_{12} \+ r\_{23} \+ r\_{31} \= 0$) in the spinor variables. This defines the gauge group coupling the spinors.
* **Task 2.3.3: Constrained Hamiltonian and Dynamics:**
  * Derive and implement the constrained Hamiltonian $\\widetilde{H}\_{KS}$ using techniques for constrained symplectic systems (e.g., Dirac brackets or symplectic reduction).
  * Implement specialized integrators capable of handling the constrained dynamics (e.g., RATTLE/SHAKE or stabilization techniques).
* **Task 2.3.4: Candidate Integral Initialization:**
  * Implement the symbolic form of the pairwise Runge-Lenz vectors in spinor variables. Define a candidate integral $\\widetilde{I}\_{RL}$ as a weighted sum (a concrete starting point for Phase 3).
* **Deliverable 2.3:** Verified implementation of the KS-Spinor lifted Hamiltonian and specialized integrators.

---

### **WP 3: Discovery of Candidate Invariants ($\\widetilde{I}$)**

This phase utilizes the constructed lifts (WP 2.2, 2.3) to search for new conserved quantities using a synthesis of deterministic geometric methods and data-driven machine learning techniques.

#### **WP 3.1: Deterministic Geometric Search (Killing Fields/Tensors)**

**Objective:** Directly search for symmetries of the lifted geometry by solving the Killing equations.

* **Task 3.1.1: Lifted JM Metric Implementation:**
  * Implement the JM metric on the lifted configuration spaces (Shape $\\times$ Fiber for S¹, and the constrained KS space).
* **Task 3.1.2: Killing PDE Formulation:**
  * Formulate the Killing vector field PDE ($\\nabla\_{(i} K\_{j)} \= 0$) for linear integrals.
  * Formulate the Killing tensor PDE ($\\nabla\_{(k} K\_{ij)} \= 0$) for quadratic integrals (Runge-Lenz type).
* **Task 3.1.3: Numerical Solution of Killing PDEs:**
  * Discretize the lifted configuration manifold (mesh generation).
  * Implement a numerical solver (e.g., least-squares on the mesh).
  * Incorporate smoothness regularization and physical symmetry priors (e.g., permutation of identical masses).
* **Task 3.1.4: Integral Conversion and Filtering:**
  * Convert discovered fields ($K$) or tensors ($K\_{ij}$) into candidate integrals $\\widetilde{I}\_K$.
  * Perform initial triviality checks (ensure they are not E, L, or $p\_\\theta$).
* **Deliverable 3.1:** A library of candidate Killing fields/tensors and corresponding invariants; or a rigorous negative result (e.g., bounds on non-existence up to degree 2).

#### **WP 3.2: Structure-Preserving Machine Learning Discovery**

**Objective:** Utilize Geometric Deep Learning to identify implicitly conserved quantities within the lifted dynamics.

* **Task 3.2.1: Data Generation on the Lift:**
  * Generate extensive, high-precision trajectory datasets using the lifted Hamiltonians ($\\widetilde{H}$ and $\\widetilde{H}\_{KS}$).
* **Task 3.2.2: HNN/SympNet Architecture:**
  * Implement Hamiltonian Neural Networks (HNNs) or Symplectic Neural Networks (SympNets) (using JAX/PyTorch).
  * **Crucial:** The network must operate on the lifted phase space.
* **Task 3.2.3: Constrained Training for Invariant Discovery:**
  * Design an auxiliary head to predict a scalar $\\widetilde{I}$.
  * Implement the conservation law $\\frac{d\\widetilde{I}}{dt}=\\{\\widetilde{I},\\widetilde{H}\\}=0$ as a soft penalty in the loss function.
  * Utilize "Noether-inspired regularizers" to encourage invariance under candidate group actions.
* **Task 3.2.4: Validation and Generalization Guardrails:**
  * Test the predicted $\\widetilde{I}$ out-of-distribution.
  * Implement rigorous hold-out strategies (e.g., entire mass-ratio regimes or energy shells) to ensure generalization.
* **Deliverable 3.2:** Trained HNN/SympNet models capable of predicting conserved quantities in the lift.

#### **WP 3.3: Symbolic Regression and Consolidation**

**Objective:** Convert numerically discovered candidates (from WP 3.1 and 3.2) into concise analytical expressions.

* **Task 3.3.1: Symbolic Regression Pipeline:**
  * Implement a pipeline using tools like SINDy, PySR, or AI-Feynman.
  * Apply the pipeline to the high-precision data and the numerical candidates.
* **Task 3.3.2: Basis Function Optimization:**
  * Restrict the search space to physically meaningful basis functions (e.g., sparse polynomials/rationals in distances, dot products, shape coordinates, fiber angles).
* **Task 3.3.3: Candidate Ranking and Consolidation:**
  * Consolidate candidates from all tracks. Filter based on complexity and initial numerical conservation tests.
* **Deliverable 3.3:** A consolidated list of analytical expressions for candidate integrals $\\widetilde{I}$.

---

### **WP 4: Rigorous Validation and Falsification (The "Gauntlet")**

This critical phase subjects the candidate integrals $\\widetilde{I}$ to stringent analytical and numerical tests designed to meet the criteria of Liouville integrability and compatibility with known obstructions.

#### **WP 4.1: Analytical Vetting (The Liouville Criteria)**

**Objective:** Symbolically verify the core requirements of integrability: Conservation, Independence, and Involution.

* **Task 4.1.1: Poisson Bracket Computation (Conservation):**
  * Utilize Computer Algebra Systems (CAS, e.g., SymPy, Mathematica) to compute $\\{\\widetilde{I},\\widetilde{H}\\}\_{\\widetilde{\\omega}}$.
  * **Acceptance Threshold:** Must be symbolically zero, or the normalized residual must be $\<10^{-12}$ (quad precision) on random test points if full symbolic proof is intractable.
* **Task 4.1.2: Poisson Bracket Computation (Involution \- Crucial):**
  * Verify that $\\widetilde{I}$ commutes with all classical integrals (E, L). If multiple new integrals are found, verify they commute with each other.
* **Task 4.1.3: Functional Independence (Jacobian Rank Test):**
  * Calculate the rank of the Jacobian matrix of the gradients of all integrals.
  * **Validation:** Verify that $\\widetilde{I}$ is independent of known invariants AND the fiber momentum ($p\_\\theta$). Empirical Jacobian rank must increase by 1 on \>99% of randomly sampled states.
* **Kill Switch A:** If $\\widetilde{I}$ fails the Poisson bracket tests, or if it is functionally dependent on known quantities or the trivial fiber momentum, discard the candidate.
* **Deliverable 4.1:** Symbolic proof (or refutation) of Liouville criteria for each candidate.

#### **WP 4.2: Defensive Falsification (The Morales-Ramis Test)**

**Objective:** Protect the credibility of the results by proving that the discovered integral *must* live upstairs, ensuring compatibility with no-go theorems.

* **Task 4.2.1: Variational Equations Setup:**
  * Set up the Normal Variational Equations (NVE) along specific known periodic solutions (e.g., Lagrange equilateral, Collinear configurations) in the *original* (downstairs) coordinates.
* **Task 4.2.2: Differential Galois Group Computation:**
  * Apply the Morales-Ramis (MR) criteria (e.g., using the Kovacic algorithm) to the NVE.
* **Task 4.2.3: Confirmation of Downstairs Non-Integrability:**
  * Verify that the identity component of the differential Galois group is non-abelian.
  * **Validation:** This confirms non-integrability downstairs, proving that $\\widetilde{I}$ is a genuine feature of the lift and does not contradict Bruns/Poincaré.
* **Deliverable 4.2:** Formal proof of downstairs non-integrability via MR tests.

#### **WP 4.3: Numerical Robustness and Generalization**

**Objective:** Validate the universality and stability of $\\widetilde{I}$ across the entire parameter space of the general three-body problem.

* **Task 4.3.1: Generalization and Monte Carlo Suite:**
  * Generalize the analytical expression of $\\widetilde{I}$ to the full 3BP (arbitrary masses, 3D orbits).
  * Execute a large-scale simulation ($\\geq 10^5$ initial conditions) covering the full parameter space.
* **Task 4.3.2: Stress Testing and Regularization:**
  * Test $\\widetilde{I}$ in extreme scenarios: near-triple collisions, high eccentricity orbits.
  * Ensure the integrator employs robust regularization (KS, chain regularization, Sundman time scaling) during close encounters.
* **Task 4.3.3: Long-Time Invariance Analysis:**
  * Analyze the drift of $\\widetilde{I}$ relative to the energy error (shadow Hamiltonian accuracy).
  * **Acceptance Threshold:** Require $\\sup\_{t\\le T}\\frac{|\\Delta \\widetilde{I}(t)|}{\\max(1,|\\widetilde{I}(0)|)} \\le C\\cdot \\epsilon\_H(T)$ with $C\\approx 10$. Drift in $\\widetilde{I}$ must not exceed the integrator error.
* **Task 4.3.4: Chaos Correlation Analysis:**
  * Measure Lyapunov exponents downstairs and verify that $\\widetilde{I}$ remains conserved upstairs even in strongly chaotic regions.
* **Deliverable 4.3:** Comprehensive statistical validation report confirming the universality and robustness of $\\widetilde{I}$.

---

### **WP 5: Consolidation and Publication**

#### **WP 5.1: Results Consolidation and Dissemination**

* **Task 5.1.1: Formal Proof Construction:** Consolidate the analytical proofs (WP 4.1, 4.2) and numerical evidence (WP 4.3) into a formal mathematical argument for Lift-Integrability.
* **Task 5.1.2: Analysis of Negative or Partial Results:** If a universal $\\widetilde{I}$ is not found, rigorously characterize the boundaries established (from WP 3.1) or characterize any discovered approximate/regime-specific invariants.
* **Task 5.1.3: Reproducibility Package:** Publish the code, data artifacts (e.g., curvature fields, connection 1-forms), and the learned $\\widetilde{I}$ (if found) as executable artifacts with unit tests.
* **Task 5.1.4: Publication:** Prepare manuscripts for major journals in Physics, Mathematics, and Computational Science.
