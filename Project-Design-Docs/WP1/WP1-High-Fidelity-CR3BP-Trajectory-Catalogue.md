### **WP1-Work Package 1 High-Fidelity CR3BP Trajectory Catalogue**

#### **0\. Purpose**

To generate and release an open, rigorously validated trajectory catalogue for the Circular Restricted Three-Body Problem (CR3BP), designed specifically to enable Machine Learning (ML) and symbolic regression searches for hidden integrals of motion. This dataset must meet unprecedented precision standards to distinguish novel invariants from numerical artifacts.

**Key Requirements:**

1. **Parameter Space Coverage:** Span mass ratios 10−3≤μ≤0.5 and a comprehensive range of Jacobi constants C.
2. **Stratified Precision:** Employ a dual-tiered strategy, culminating in a "gold standard" subset maintaining a relative error in the Jacobi constant ∣ΔC/C∣\<10−25 over 104–106 characteristic periods.
3. **Rich Data Format:** Include full phase-space vectors in multiple coordinate systems (co-rotating, inertial, regularized), alongside validated chaos indicators (MEGNO, FLI).
4. **ML Readiness and Reproducibility:** Deliver data in high-throughput formats (Parquet) with a fully reproducible codebase.

#### **1\. Core Concepts and Methodologies**

| Concept | Explanation and Relevance |
| :---- | :---- |
| **CR3BP (Co-rotating Frame)** | Standard formulation where primaries are fixed. While convenient, this frame introduces fictitious forces (Coriolis, centrifugal) that may obscure fundamental symmetries. Data must also be provided in the inertial frame. |
| **Symplectic Integration** | Integrators that exactly preserve the symplectic 2-form. Crucial for long-term stability as they suppress secular energy drift. We prioritize **Adaptive Symplectic Methods**, which use time transformations (e.g., Sundman) to allow variable stepping while remaining symplectic. |
| **High Precision (Double-Double)** | Standard double precision is insufficient. We mandate **Double-Double arithmetic** (≈31 digits) to achieve the 10−25 error target, balancing performance and precision better than software-emulated quadruple precision. |
| **Regularization (e.g., Levi-Civita)** | Coordinate transformations that mathematically remove the singularities at the primary masses. Essential for maintaining precision and stability during close encounters. |
| **Shadow Hamiltonian Analysis** | A backward error analysis technique. Confirms that the numerical trajectory is the *exact* solution of a nearby Hamiltonian (H). This provides a stronger guarantee of fidelity than monitoring energy drift alone. |
| **Chaos Indicators (MEGNO & FLI)** | **MEGNO** distinguishes regular from chaotic motion. The **Fast Lyapunov Indicator (FLI)** is added to rapidly identify resonance structures and separatrices. |

#### **2\. Implementation Road-Map**

##### **2.1 Week 0-1: Environment, High-Precision Setup, and Validation Harness**

* **Tool Chain:** Python 3.11+ (orchestration); C++/Fortran (integration kernels).
* **High Precision Implementation:** Implement Double-Double arithmetic using an optimized library (e.g., QD library in C++).
* **Numerics:** REBOUND (IAS15 baseline); Custom implementations of adaptive symplectic integrators.
* **Data Handling:** HDF5 (archival), Apache Parquet (ML-ready).
* **Reproducibility:** conda/poetry environment lock, Git/GitHub CI.
* **Smoke Tests:** Integrate a Kepler ellipse in double-double; verify relative energy error \<10−28 for 104 periods.

##### **2.2 Week 2-4: Integrator Shoot-out and Precision Budget**

**Integrator Selection Criteria:** Prioritize symplecticity, adaptivity, and robust handling of close encounters.

| Candidate | Type | Key Feature | Evaluation Priority |
| :---- | :---- | :---- | :---- |
| **Adaptive Symplectic** | Symplectic, Adaptive | Variable time steps via Sundman transform while preserving phase-space volume. | High (Primary Goal) |
| **IAS15 (REBOUND)** | Gauss–Radau (Non-Symplectic) | Highly optimized, adaptive, proven robustness. | High (Baseline/Fallback) |
| **High-Order Composition (Yoshida/Tao)** | Symplectic, Fixed Step | Excellent long-term stability. | Medium (If adaptivity fails) |

**Precision Strategy (Stratified Approach):**

* **Tier 1 (Exploration):** 105 orbits integrated in optimized double precision (∣ΔC/C∣\<10−14). Used for initial ML training and phase space mapping.
* **Tier 2 (Gold Standard):** A dynamically interesting subset (≈10,000 orbits) re-integrated in double-double precision. **Target: ∣ΔC/C∣\<10−25**. Used for rigorous validation of candidate invariants.

##### **2.3 Week 5-6: Parameter-Space Design and Sampling**

* **Mass Ratio μ:** 30 samples, log-uniform in \[10−3,0.5\].
* **Jacobi Constant C:** 15 values bracketing Lagrange point energies CL1…L5​.
* **Initial Conditions (IC) Sampling:**
  * **Quasi-Random Coverage:** Use **Sobol sequences** on the relevant Poincaré section to ensure uniform, low-discrepancy coverage of the accessible phase space.
  * **Dynamically Informed Refinement:** Use FLI/MEGNO maps from a pilot run (≈5000 orbits) to adaptively increase sampling density near separatrices and resonance structures.
  * **Known Structures:** Explicitly include known stable and unstable periodic orbit families (e.g., Lyapunov, Halo).

##### **2.4 Week 7-10: Production Integration and Data Generation**

* **Orchestration:** Use Dask or Snakemake for parallel execution on HPC resources.
* **Integration Core:**
  * Integrate state \+ variational equations simultaneously to compute MEGNO and FLI on-the-fly.
  * Integrate to tmax​=105T (T=2π) or until escape.
  * **Mandatory Regularization:** Implement robust regularization (either via the adaptive symplectic method or automatic switching to Levi-Civita coordinates) for all production runs.
* **Data Output:**
  * **Coordinate Diversity:** Store state vectors in **(1) Co-rotating, (2) Inertial (Barycentric), and (3) Regularized coordinates** (if applicable).
  * **Adaptive Storage:** Use **Dense Output** (interpolated integrator steps) rather than fixed strides to capture dynamics accurately during close encounters without excessive storage.
* **File Structure (HDF5):** /mu\_{i}/C\_{j}/orbit\_{k}/ with datasets for all coordinate frames, Jacobi values, MEGNO, and FLI.

##### **2.5 Week 11-12: Quality Assurance and Validation**

* **Precision Histogram:** Verify the distribution of ΔC. For Tier 2, the 95th percentile must be below 10−25.
* **Mandatory Shadow Hamiltonian Analysis:** Perform backward error analysis on a subset of chaotic orbits in Tier 2\. Quantify the distance between the numerical flow and the true Hamiltonian flow, ensuring the shadow Hamiltonian H is bounded and exhibits no secular drift.
* **Regularization Check:** Verify continuity and precision are maintained across any coordinate switches during close encounters.
* **Time Reversibility Test:** Integrate forward, negate velocities, integrate backward. RMS position error \<10−20 (Tier 2).
* **Chaos Map Verification:** Reproduce standard Poincaré sections and compare MEGNO/FLI maps against literature.

##### **2.6 Week 13-14: Post-Processing, Packaging, and Release**

* **ML-Ready Format:** Post-process HDF5 archives into flattened **Apache Parquet** files for high-throughput I/O during ML training.
* **Public Release:** DOI via Zenodo (HDF5 and Parquet). GitHub release v1.0.0 of the integration suite.
* **Documentation:** Draft a Data Descriptor paper (e.g., for *Scientific Data* or *JOSS*).

#### **3\. Risk Mitigation**

| Risk | Impact | Mitigation Strategy |
| :---- | :---- | :---- |
| **High-Precision Overhead** | Run-time blow-up prevents Tier 2 completion. | The stratified approach guarantees a usable Tier 1 dataset. Utilize optimized Double-Double libraries (e.g., QD) and prioritize efficient C++/Fortran implementation over pure Python/mpmath. |
| **Adaptive Symplectic Implementation Delay** | Complexity of adaptive methods (Sundman transform) delays WP. | Fallback to IAS15 (non-symplectic but robust and adaptive) if implementation proves intractable within the timeline, while acknowledging the theoretical compromise. |
| **Regularization Switching Errors** | Discontinuities at coordinate patches destroy precision. | Implement smooth switching functions (e.g., Mikkola's approach). Rigorous QA testing (2.5) of the switching mechanism is mandatory before production. |
| **I/O Bottlenecks in ML Pipeline** | HDF5 format too slow for WP3 training. | Mandate the delivery of the dataset in flattened, cloud-optimized formats (Parquet). |

#### **4\. Assessment Criteria**

1. **Precision Targets Met:** Median and 95th percentile Jacobi drift meet the 10−14 (Tier 1\) and 10−25 (Tier 2\) requirements.
2. **Shadow Hamiltonian Bounds:** Successful demonstration and reporting of bounded shadow Hamiltonian error for representative chaotic orbits in Tier 2\.
3. **Data Integrity:** Successful ingestion of the Parquet dataset into a prototype ML pipeline; presence of all required coordinate systems and chaos indicators.
4. **Reproducibility Badge:** An independent researcher can regenerate a 1% subset of the Tier 2 data bit-for-bit.

#### **5\. Timeline and Effort (3.5 Months, 1 FTE)**

| Month | Milestone | Deliverable |
| :---- | :---- | :---- |
| 0.5 | Environment & Double-Double validated | Repo \+ CI \+ Precision Benchmark |
| 1.0 | Integrator Shoot-out Complete; Selection Finalized | PDF Memo; Validated Integrator Code |
| 1.5 | Sampling strategy finalized (Sobol \+ adaptive) | YAML Spec for ICs; Pilot run data |
| 2.5 | Full Tier 1 (Double) integration complete | Raw Tier 1 Data (Parquet/HDF5) |
| 3.0 | Full Tier 2 (Double-Double) integration complete | Raw Tier 2 Data |
| 3.5 | QA/Shadow Analysis passed; Public Release | Zenodo DOI; Data Descriptor Draft |

#### **6\. Reading Starter-Kit**

* **Hairer, Lubich, Wanner (2006):** *Geometric Numerical Integration*. (Key reference for Shadow Hamiltonian analysis and symplectic methods).
* **Mikkola & Tanikawa (1999):** Algorithmic regularization, smooth switching, and adaptive symplectic methods.
* **Rein & Spiegel (2015):** IAS15 algorithm (MNRAS 446, 1424).
* **Cincotta & Simó (2000) / Lega et al. (2016):** Primers on MEGNO and FLI.
* **Hida, Li, Bailey (2000):** Algorithms and implementation for Double-Double Arithmetic.
