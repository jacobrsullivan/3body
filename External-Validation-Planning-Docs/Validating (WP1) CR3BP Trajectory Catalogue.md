

# **Feasibility and Strategic Validation Framework for High-Fidelity CR3BP Trajectory Catalogues**

## **1\. Strategic Context and Dynamical Framework**

The modern era of astrodynamics is characterized by an unprecedented demand for precision in trajectory design, driven largely by the strategic pivot toward cislunar space and the utilization of libration point orbits (LPOs) for infrastructure such as the Lunar Gateway and future deep-space observatories. In this context, the implementation of a High-Fidelity Circular Restricted Three-Body Problem (CR3BP) Trajectory Catalogue (WP1) represents a foundational asset. However, the value of such a catalogue is inextricably linked to the rigorous demonstration of its accuracy, stability, and adherence to the governing dynamical equations. The proposal to validate WP1 publicly using existing open-source data and peer-reviewed research is not merely feasible; it is a critical quality assurance step that establishes the catalogue as a verified scientific instrument rather than a simple lookup table.

The feasibility analysis suggests that a robust validation campaign can be executed by triangulating WP1 against three pillars of public knowledge: the established ephemerides and periodic orbit databases provided by NASA’s Jet Propulsion Laboratory (JPL), the advanced numerical integration benchmarks found in open-source astrodynamics software like REBOUND and Heyoka, and the rich theoretical landscape of chaos indicators (MEGNO/FLI) documented in contemporary literature. By systematically cross-referencing WP1 against these standards, one can quantify "fidelity" not as a vague marketing term, but as a measurable metric defined by periodicity closure error, Jacobi constant conservation, and correct topological placement within the phase space of the three-body problem.

Furthermore, the timing of this initiative aligns with a paradigmatic shift in mission analysis: the application of Generative Artificial Intelligence (GenAI) to orbit design. Projects such as "OrbitGPT" and research into Variational Autoencoders (VAEs) for trajectory generation have created a nascent but urgent market for high-volume, high-precision training data.1 Validating WP1 is therefore not only a check of dynamical correctness but a demonstration of its utility as a "ground truth" dataset for the next generation of autonomous navigation and design algorithms. This report delineates a comprehensive framework for this validation, assessing the required computational resources, identifying key reference datasets, and synthesizing the methodological steps required to prove efficacy publicly.

### **1.1 The Circular Restricted Three-Body Problem (CR3BP) as the Validation Standard**

To assess the feasibility of validating WP1, one must first ground the evaluation in the mathematical invariants of the CR3BP. This dynamical model describes the motion of a massless particle under the gravitational influence of two primary bodies moving in circular orbits about their common center of mass.3 The governing equations of motion are derived from a pseudo-potential function, $\\Omega(x,y,z)$, which accounts for both gravitational and centrifugal forces in the rotating frame.

The validation of any high-fidelity catalogue fundamentally rests on examining how well the generated trajectories satisfy these equations of motion over time. The primary metric for this internal consistency check is the Jacobi integral, the sole constant of motion in the conservative CR3BP system.4 For any trajectory claiming high fidelity, the Jacobi constant $C$ must remain invariant along the path.

$$C \= 2\\Omega(x,y,z) \- (\\dot{x}^2 \+ \\dot{y}^2 \+ \\dot{z}^2)$$

Variations in $C$ during propagation are a direct proxy for numerical error. While standard double-precision computations typically yield energy conservation errors on the order of $10^{-15}$, a "High-Fidelity" catalogue—particularly one purporting to support arbitrary precision—must demonstrate stability significantly below this threshold, potentially utilizing extended precision arithmetic to minimize round-off accumulation.5

### **1.2 The Value of Public Demonstration**

Publicly demonstrating accuracy serves multiple strategic goals. First, it builds trust within the astrodynamics community, which is historically skeptical of "black box" solutions. By transparently benchmarking against trusted sources like the JPL Periodic Orbit Catalog, the WP1 catalogue moves from a proprietary dataset to a verifiable scientific resource. Second, it highlights the catalogue's capability to handle "edge cases"—regions of high instability, close encounters with primaries, or complex resonant families—that simpler databases may omit or approximate poorly. Finally, it positions the catalogue as an enabler for third-party research, specifically in machine learning, where the quality of the output model is strictly bounded by the quality of the input training data.6

---

## **2\. Benchmarking Against Institutional Reference Data**

The most direct method for validating a new trajectory catalogue is a comparative analysis against established institutional databases. The NASA JPL Three-Body Periodic Orbit Catalog stands as the gold standard in this domain, offering a comprehensive, albeit discrete, set of reference solutions.

### **2.1 The NASA JPL Three-Body Periodic Orbit Catalog**

The JPL database provides precomputed periodic orbits for a wide variety of three-body systems, including Earth-Moon, Sun-Earth, and various planetary satellite systems like Saturn-Titan and Mars-Phobos.4 This catalog is accessible via a well-documented API, allowing for the programmatic retrieval of initial conditions, periods, stability indices, and Jacobi constants.

#### **2.1.1 Data Structure and Precision**

The JPL catalog data is delivered in a normalized format, using characteristic Length Units (LU) and Time Units (TU) specific to each system.4 A critical aspect of the feasibility study involves analyzing the precision of this reference data. The API returns state vectors in scientific notation with approximately 16-17 significant digits (e.g., 8.2337984140824316E-1), corresponding to standard IEEE 754 double-precision floating-point format.4  
The availability of this data allows for a direct "point-to-point" validation strategy. If WP1 contains, for example, a specific Northern Halo orbit around L1 in the Earth-Moon system, its initial state vector can be directly compared to the nearest equivalent entry in the JPL catalog. The Euclidean distance between the WP1 state and the JPL reference state serves as a primary error metric.

$$\\epsilon\_{state} \= \\| \\mathbf{X}\_{WP1} \- \\mathbf{X}\_{JPL} \\|$$

However, since the JPL catalog represents a discretized set of solutions along a continuous family, exact matches are unlikely. Therefore, validation must also involve interpolation or "manifold fitting," where the WP1 orbit is checked to see if it lies on the continuous curve defined by the JPL data points in the phase space (e.g., plotting $x\_0$ versus Jacobi Constant $C$).8

#### **2.1.2 Scope of Families and Limitations**

The JPL catalog covers a broad spectrum of orbit families, including the canonical Halo, Lyapunov (Vertical and Axial), and more complex families like Butterfly and Dragonfly orbits.7 It also includes resonant families and Distant Retrograde Orbits (DROs). This breadth is advantageous for validation, as it allows WP1 to be tested across different dynamical regimes—from the unstable saddle points of L1/L2 to the stable regions around L4/L5.  
Nevertheless, the JPL catalog has limitations that WP1 can exploit to demonstrate superiority. The reference orbits are often computed with constraints that may exclude certain valid solutions, such as Halo orbits that degrade into other topologies at low energy levels.3 Furthermore, the reliance on double precision in the public output means that for extremely long-duration integrations, the provided initial conditions may eventually diverge due to the chaotic nature of the CR3BP. A "High-Fidelity" catalogue that utilizes arbitrary precision (e.g., quad-double arithmetic) could demonstrate longer coherence times than the public reference data, thereby proving its enhanced efficacy.9

### **2.2 Validation via Peer-Reviewed Literature**

Beyond the centralized JPL database, the academic literature provides a rich repository of specific solution sets and stability maps that can serve as validation benchmarks.

* **Resonant Orbits:** Research into resonant orbits, such as the 3:1 resonance in the Earth-Moon system (relevant for missions like IBEX), provides Poincaré sections and stability analyses that can be replicated using WP1 data.10  
* **Transport Manifolds:** Papers discussing the "Arches of Chaos" and the geometric theory of phase space transport offer high-resolution maps of stable and unstable manifolds.11 Reproducing these structures using WP1 data validates that the catalogue correctly captures the global topology of the phase space, not just individual periodic orbits.  
* **Libration Point Dynamics:** Extensive studies on formation flying near libration points provide control strategies and reference trajectories that rely on high-precision CR3BP models.12 Validating WP1 against these control-theoretic benchmarks demonstrates its utility for practical mission design tasks, such as station-keeping and formation maintenance.

### **2.3 Comparative Table: Reference Data Sources**

| Reference Source | Data Type | Precision | Key Families Covered | Use Case for Validation |
| :---- | :---- | :---- | :---- | :---- |
| **JPL Periodic Orbit Catalog** | API / JSON | Double (\~16 digits) | Halo, Lyapunov, Axial, Butterfly, DRO | Primary baseline for initial conditions and period verification.4 |
| **Literature (e.g., Howell et al.)** | Plots / Tables | Variable | LPOs, Resonant Orbits, Manifolds | Topological validation of family curves and stability transitions.12 |
| **OrbitGPT Datasets** | HDF5 / Tensors | Double | Large-scale training sets (44k+ orbits) | Validation of dataset density and suitability for ML training.1 |
| **Chaos Indicator Maps** | Heatmaps | High-Res Grid | Global stability (MEGNO/FLI) | Visual validation of stable/unstable region identification.15 |

---

## **3\. Advanced Numerical Validation: The Integrator Ecosystem**

A static comparison of initial conditions is necessary but insufficient for a "High-Fidelity" claim. The true test of a trajectory catalogue lies in its dynamical behavior under propagation. This requires benchmarking WP1 against state-of-the-art numerical integrators that define the modern standard for precision in celestial mechanics.

### **3.1 High-Precision Integrators: REBOUND and IAS15**

The open-source N-body package REBOUND serves as a primary tool for this validation phase. Specifically, its IAS15 integrator (Integrator with Adaptive Step-size, 15th order) is widely recognized as a benchmark for high-precision gravitational dynamics.17

* **Mechanism:** IAS15 employs a Gauss-Radau quadrature scheme that allows it to handle non-conservative forces and highly eccentric orbits with machine-precision accuracy.18 It automatically adjusts its time step to maintain error bounds, making it ideal for propagating WP1 orbits that may have close approaches to the primary bodies.  
* **Validation Procedure:** To demonstrate efficacy, one would take an initial state vector from WP1, propagate it for exactly one period $T$ using IAS15, and compute the closure error $\\| \\mathbf{X}(T) \- \\mathbf{X}(0) \\|$. For a high-fidelity catalogue, this error should be dominated by the machine's floating-point epsilon rather than integration artifacts. If the closure error is significant, it implies the catalogue's period or initial state is imprecise.19

### **3.2 The Frontier of Arbitrary Precision: Heyoka and Taylor Methods**

While IAS15 is excellent for double precision, true "High-Fidelity" often demands extended precision to overcome the fundamental limits of 64-bit arithmetic (approx. $10^{-16}$). The library heyoka (and its Python wrapper heyoka.py) represents the cutting edge in this domain, utilizing Taylor series integration methods.20

* **Taylor Series Integration:** Unlike Runge-Kutta methods, Taylor integrators compute the solution by summing the Taylor series of the ODE solution to a very high order. This allows for extremely precise propagation, often maintaining machine precision over tens of billions of time steps.9  
* **Extended Precision:** Crucially, heyoka supports extended precision types, including 80-bit, 128-bit (quadruple precision), and arbitrary-precision floating-point types via the mp++ library.22  
* **Benchmarking Strategy:** A compelling public demonstration would involve propagating WP1 orbits using heyoka in 128-bit precision. If the catalogue data is truly high-fidelity (i.e., generated with similar precision), the trajectory should remain periodic for significantly longer durations than what is possible with standard double precision. This separates "numerical noise" from "catalogue error," proving that the data quality exceeds standard industry norms.24

### **3.3 Symplectic Integration and Shadow Hamiltonians**

For conservative systems like the CR3BP (when viewed in the appropriate Hamiltonian formulation), symplectic integrators offer a unique validation angle. These integrators, such as the Wisdom-Holman mapping or WHFast, preserve the symplectic structure of the phase space, meaning they do not suffer from the secular energy drift characteristic of non-symplectic methods.25

* **Shadow Hamiltonian Analysis:** Backward error analysis reveals that a symplectic integrator exactly solves a "Shadow Hamiltonian" $\\tilde{H}$ that is asymptotic to the true Hamiltonian $H$.26 The error between the shadow and true Hamiltonians can be bounded to extremely low values, such as $10^{-25}$, depending on the order of the integrator and the step size.28  
* **Long-Term Stability Check:** By propagating quasi-periodic or stable orbits from WP1 using a high-order symplectic integrator, one can monitor the energy error (Jacobi constant variation) over extremely long timescales. A flat energy error profile (no drift) confirms that the initial conditions lie precisely on an invariant torus, validating the catalogue's claim to capturing stable dynamical structures correctly.27 This is particularly relevant for validating Halo orbits or resonant orbits intended for long-term station-keeping.

### **3.4 Comparative Performance and Overhead**

Implementing this validation requires understanding the computational trade-offs. While arbitrary precision provides the ultimate accuracy check, it comes with significant performance overhead.

* **Double-Double Arithmetic:** Operations in double-double (approx. 32 decimal digits) or quad-double (approx. 64 decimal digits) precision are significantly slower than hardware-native double precision—often by a factor of 20x to 89x.29  
* **Resource Implications:** This implies that while "High-Fidelity" checks are feasible, they are computationally expensive. Validating the *entire* WP1 catalogue in quad-precision may be prohibitive. The strategy should therefore focus on a representative subset of orbits—perhaps the most unstable or the most operationally critical ones—to demonstrate the capability without incurring excessive compute costs.

---

## **4\. Chaos Detection and Topological Validation**

A catalogue of orbits is more than a list of numbers; it is a representation of the phase space topology. Validating this topology requires tools that can distinguish between regular (stable) and chaotic motion. This is where chaos indicators become essential for public demonstration.

### **4.1 MEGNO: The Mean Exponential Growth Factor of Nearby Orbits**

The MEGNO indicator, denoted as $Y(t)$, is a powerful tool for characterizing the dynamical stability of a system. Introduced by Cincotta and Simó (2000), it provides a fast and robust method to distinguish between chaotic and quasi-periodic motion.32

* **Theoretical Basis:** MEGNO is a time-weighted average of the divergence of nearby orbits. Mathematically, for a stable, quasi-periodic orbit, the time-averaged mean value $\\langle Y(t) \\rangle$ asymptotically converges to 2.0. In contrast, for a chaotic orbit, $\\langle Y(t) \\rangle$ grows linearly with time, with a slope related to the maximum Lyapunov exponent.34  
* **Validation Application:** To validate WP1, one can select specific orbits labeled as "stable" in the catalogue and propagate them while computing the MEGNO signature. If the resulting value converges to 2.0, the classification is verified. If it diverges or oscillates wildly, the catalogue's stability index is suspect. This provides a binary, easy-to-interpret metric for public demonstration: "Green" for 2.0 (Verified Stable), "Red" for divergent (Chaotic).32

### **4.2 FLI: The Fast Lyapunov Indicator**

Similar to MEGNO, the Fast Lyapunov Indicator (FLI) measures the expansion rate of tangent vectors. It is particularly effective at detecting "sticky" chaos—regions where orbits behave regularly for long periods before diffusing into the chaotic sea.35

* **Visualizing Manifolds:** FLI is widely used to generate high-resolution maps of stable and unstable manifolds. By computing the FLI for a grid of initial conditions (e.g., on a Poincaré section), one can visualize the intricate web of transport channels in the CR3BP.16  
* **Overlay Validation:** A powerful validation graphic would involve generating an FLI map of a specific region (e.g., the L4 stability region or the L1 neck) and overlaying the WP1 catalogue points. The points should align perfectly with the "valleys" of stability (dark regions in the map) or the specific manifold structures (light filaments). This visual correlation acts as a strong qualitative proof of fidelity.16

### **4.3 Constructing Stability Maps**

The generation of stability maps (MEGNO or FLI maps) is a resource-intensive but highly effective validation method.

* **Methodology:** A dense grid of initial conditions is defined (e.g., varying $x$ and $\\dot{y}$ while keeping other variables fixed). For each point on the grid, the system is integrated for a fixed duration (e.g., $10^4$ to $10^5$ characteristic time units), and the chaos indicator is computed.15  
* **Resolution and Fidelity:** High-fidelity maps often require grids of $1000 \\times 1000$ pixels or more to resolve fine resonant structures. The sharpness of the features in these maps is a direct reflection of the integrator's precision and the integration time. Validating WP1 against such high-resolution maps proves that the catalogue accurately captures the micro-structure of the phase space, not just the macro-stability.36  
* **Comparison with Literature:** Numerous papers have published standard MEGNO/FLI maps for the Earth-Moon and Sun-Earth systems.8 Reproducing these maps using the same dynamical model assumptions as WP1 ensures consistent validation. Any discrepancies—such as stability islands appearing where chaos is expected—would trigger a review of the catalogue's underlying model or precision.

### **4.4 Topological Feature Extraction**

Advanced visualization techniques can extract topological structures directly from Poincaré maps, such as identifying the centers of resonant islands or the boundaries of chaotic seas.37 Using these algorithms to automatically classify the WP1 orbits adds another layer of automated validation. If the topological algorithm identifies a WP1 orbit as belonging to a specific resonant family (e.g., 3:1 resonance), this independent confirmation reinforces the catalogue's metadata accuracy.37

---

## **5\. The Data-Driven Frontier: Validating for AI Applications**

The user's query hints at modern efficacy, which increasingly intersects with Artificial Intelligence. The astrodynamics community is actively exploring the use of large datasets to train machine learning models for orbit generation and classification. Validating WP1 in this context establishes its relevance for future-proof applications.

### **5.1 The "OrbitGPT" and Generative Design Paradigm**

Recent research, such as the "OrbitGPT" project funded by ESA and work on "Generative Design of Periodic Orbits," utilizes deep learning architectures like Variational Autoencoders (VAEs) and Transformers to learn the underlying manifold structure of the CR3BP.1

* **Dataset Requirements:** These models require massive, high-quality datasets for training. The "Generative Design" paper, for instance, utilized a core dataset of over 44,000 periodic orbits.14 The efficacy of the trained model—its ability to generate valid, novel orbits—is directly proportional to the density, diversity, and accuracy of the training data.1  
* **Validation as a Training Source:** A novel validation strategy involves using a subset of WP1 data to train a standard orbit-generation model (using open-source code from these projects).38 If the model converges quickly and achieves low reconstruction error, it indicates that the WP1 data contains coherent, learnable patterns consistent with the physics of the CR3BP. Conversely, training instability could signal noise or inconsistencies in the catalogue.6

### **5.2 Benchmarking Generative Capabilities**

The "Generative Design" research established metrics for evaluating generated orbits, such as the distribution of Jacobi constants and stability indices.2 By comparing the statistical distributions of WP1 against these published distributions, one can verify that the catalogue covers the expected solution space comprehensively.

* **Latent Space Analysis:** Visualizing the latent space of a VAE trained on WP1 can reveal the family structure of the orbits. Distinct clusters in the latent space should correspond to distinct orbit families (e.g., Halo vs. Butterfly). This topological preservation in the latent space is a sophisticated measure of catalogue fidelity.2

### **5.3 Code and Data Availability for AI Benchmarking**

The availability of code repositories for these AI projects (e.g., on GitHub) facilitates this validation step. The user can leverage existing scripts for data preprocessing, model training, and evaluation, effectively "plugging in" WP1 as the new source.38 This reduces the development burden while providing a high-tech demonstration of the catalogue's efficacy.

---

## **6\. Strategic Execution Framework**

Based on the theoretical and comparative analysis, a structured execution plan is proposed. This framework optimizes for credibility, visual impact, and scientific rigor, while remaining resource-efficient.

### **6.1 Phase 1: Data Acquisition and Harmonization (Weeks 1-2)**

The first step is to establish the "ground truth" environment.

* **JPL API Integration:** Develop Python scripts to programmatically fetch reference data from the JPL Three-Body Periodic Orbit Catalog. The scripts should support filtering by system (Earth-Moon, Sun-Earth), family, and stability branch.4  
* **Normalization Standards:** Rigorously define the Length Units (LU) and Time Units (TU) used in WP1 and ensure they match or are correctly converted to the JPL standards. Mismatches in normalization are a common source of pseudo-errors.  
* **Data Structure Alignment:** Map the WP1 data fields to the JPL JSON structure (state vector, period, stability, Jacobi constant) to facilitate automated comparison.7

### **6.2 Phase 2: Numerical Benchmarking Suite (Weeks 3-5)**

This phase focuses on the "hard math" of validation.

* **Integrator Setup:** Install and configure REBOUND (for IAS15) and heyoka.py (for Taylor methods).22 Ensure dependencies like mp++ are correctly linked for arbitrary precision tests.  
* **Periodicity Checks:** Run a batch process propagating all WP1 orbits for one period $T$ using IAS15. Record the closure error $\\| \\mathbf{X}(T) \- \\mathbf{X}(0) \\|$. Flag any orbits with errors exceeding $10^{-13}$ for closer inspection.  
* **Precision Stress Test:** Select a "Gold Standard" subset of orbits (e.g., 100 diverse samples). Propagate these using heyoka with 128-bit precision. Compare the closure rates against double-precision results to demonstrate the "High-Fidelity" gain.24  
* **Energy Conservation:** Propagate orbits for $100 \\times T$ using a symplectic integrator (e.g., WHFast) and monitor the Jacobi constant drift. This validates long-term stability properties.43

### **6.3 Phase 3: Dynamical Mapping and Visualization (Weeks 6-10)**

Visual proof is often the most compelling. This phase generates the "hero images" for the public demonstration.

* **MEGNO Map Generation:** Allocate compute resources (cloud or local cluster) to generate high-resolution MEGNO maps for key regions (e.g., Earth-Moon L1 Halo region, L4 stable region). Use a grid of at least $1000 \\times 1000$ initial conditions.  
* **Catalogue Overlay:** Plot the WP1 orbits on top of these MEGNO maps. A perfect alignment of catalogue points with stable (blue/dark) regions in the map provides intuitive, undeniable proof of accuracy.16  
* **Poincaré Sections:** Generate Poincaré plots for specific energy levels ($C$) and overlay WP1 intersections. Check for the formation of closed invariant curves, which indicate quasi-periodicity and high fidelity.44

### **6.4 Phase 4: AI Readiness Demonstration (Optional/Advanced, Weeks 11-14)**

To capture the interest of the modern space tech community:

* **VAE Training:** Utilize the "OrbitGPT" or similar open-source code to train a small model on WP1 data.  
* **Generation Test:** Ask the model to generate new orbits and check their validity (Jacobi constant conservation). High validity rates prove the training data (WP1) is clean and robust.2

---

## **7\. Resource Requirements and Feasibility Assessment**

### **7.1 Computational Resources**

The computational demands for this validation are moderate but scale with the ambition of the mapping phase.

* **Standard Validation:** Verifying individual orbits using IAS15 or Heyoka is computationally trivial for a modern workstation. Propagating 44,000 orbits for a few periods can be done in hours.  
* **Dense Mapping:** Generating high-resolution MEGNO/FLI maps is the primary cost driver. A $1000 \\times 1000$ grid requires $10^6$ integrations. If each integration takes 0.1 seconds, the total compute time is \~28 CPU-hours. This is easily parallelizable and can be completed on a 16-core workstation in under 2 hours, or on a standard cloud instance (AWS c5.metal) in minutes.  
* **Extended Precision:** Using quad-double arithmetic increases compute time by a factor of \~20-50x.29 This should be reserved for the "Gold Standard" subset or specific stress tests, rather than the entire map generation.

### **7.2 Financial and Time Budget**

* **Financial:** The software tools (REBOUND, Heyoka, Python) are open-source and free. The JPL data is public domain. The primary financial cost is personnel time and potentially small cloud computing fees for map generation ($\< \\$100$).  
* **Timeline:** A comprehensive validation campaign can be executed in **3 to 4 months**.  
  * *Month 1:* Data pipeline and script development.  
  * *Month 2:* Numerical benchmarking and error analysis.  
  * *Month 3:* Generation of dynamical maps and visualizations.  
  * *Month 4:* Documentation, white paper writing, and public release preparation.

### **7.3 Feasibility Verdict**

The proposed validation strategy is **Highly Feasible**.

* **Technical:** The required tools are mature and well-documented.  
* **Data:** The reference data is accessible and reliable.  
* **Value:** The return on investment is high, as rigorous validation transforms WP1 from a static dataset into a verified, premium resource for mission design and AI research.

## **8\. Conclusion**

The validation of the WP1 High-Fidelity CR3BP Trajectory Catalogue is a necessary and achievable milestone. By leveraging the immense body of public research—from the foundational JPL catalog to the cutting-edge "OrbitGPT" initiatives—the project can construct a multi-layered validation argument. The combination of strict numerical benchmarking using modern Taylor series integrators (Heyoka) and visual verification through chaos maps (MEGNO) will provide incontrovertible evidence of the catalogue's quality. This approach not only confirms the accuracy of the data but also demonstrates its strategic relevance to the future of cislunar exploration and autonomous space operations. The path forward is clear: build the validation suite, generate the maps, and publish the results as a transparent testament to fidelity.

## **9\. Detailed Analysis of Research Snippets**

### **9.1 Data Sources and Catalogues**

* **JPL Three-Body Periodic Orbit Catalog:**.4 Confirms availability of precise initial conditions, periods, and stability indices for multiple systems (Earth-Moon, Sun-Earth, etc.). API allows filtering by family and branch. Precision is standard double (approx 16 digits).  
* **OrbitGPT / Generative AI:**.1 Highlights the need for large datasets (44k+ orbits) for training AI models. Code and data availability (40) allow for direct benchmarking of WP1's utility in this domain.

### **9.2 Numerical Integrators**

* **REBOUND (IAS15):**.9 Establishes IAS15 as the high-order adaptive integrator of choice for N-body precision. Used as a baseline.  
* **Heyoka (Taylor Methods):**.20 Identifies Heyoka as the superior tool for arbitrary/extended precision validation, capable of Taylor series integration which minimizes error over long durations.  
* **Symplectic Integrators:**.25 Provides the theoretical basis for using Shadow Hamiltonians to check long-term energy conservation ($10^{-25}$ error bounds).

### **9.3 Chaos and Stability Indicators**

* **MEGNO:**.15 Defines the MEGNO indicator ($Y(t)$) and its convergence properties (2.0 for stable, linear growth for chaos). Confirms its utility for creating stability maps.  
* **FLI:**.16 Fast Lyapunov Indicator for visualizing manifolds and sticky chaos.  
* **Poincaré Maps:**.13 Standard topological tool for visualizing 2D sections of the phase space. Useful for verifying the geometric structure of families.

### **9.4 Precision Arithmetic**

* **Double-Double / Quad-Double:**.29 Highlights the performance cost (20x-89x slower) but significant precision gain (32-64 decimal digits) of extended precision arithmetic, crucial for "High-Fidelity" claims.

### **9.5 System-Specific Dynamics**

* **Earth-Moon System:**.3 Specific references to L1/L2 Halo orbits, L4 stability, and resonant families in the Earth-Moon system, serving as concrete test cases for validation.

This detailed breakdown confirms that the user's request is fully supported by the available research material, allowing for a rigorous and nuanced report.

#### **Works cited**

1. Generative Design of Periodic Orbits in the Restricted Three-Body Problem \- arXiv, accessed November 27, 2025, [https://arxiv.org/html/2408.03691v1](https://arxiv.org/html/2408.03691v1)  
2. Generative Design of Periodic Orbits in the Restricted Three-Body Problem \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/publication/382944412\_Generative\_Design\_of\_Periodic\_Orbits\_in\_the\_Restricted\_Three-Body\_Problem](https://www.researchgate.net/publication/382944412_Generative_Design_of_Periodic_Orbits_in_the_Restricted_Three-Body_Problem)  
3. A Functional Interpolation Approach to Compute Periodic Orbits in the Circular-Restricted Three-Body Problem \- MDPI, accessed November 27, 2025, [https://www.mdpi.com/2227-7390/9/11/1210](https://www.mdpi.com/2227-7390/9/11/1210)  
4. Three-Body Periodic Orbits \- JPL Solar System Dynamics, accessed November 27, 2025, [https://ssd.jpl.nasa.gov/tools/periodic\_orbits.html](https://ssd.jpl.nasa.gov/tools/periodic_orbits.html)  
5. High precision Symplectic Integrators for the Solar System | Request PDF \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/publication/230609022\_High\_precision\_Symplectic\_Integrators\_for\_the\_Solar\_System](https://www.researchgate.net/publication/230609022_High_precision_Symplectic_Integrators_for_the_Solar_System)  
6. Newton versus the machine: solving the chaotic three-body problem using deep neural networks | Request PDF \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/publication/345343741\_Newton\_versus\_the\_machine\_solving\_the\_chaotic\_three-body\_problem\_using\_deep\_neural\_networks](https://www.researchgate.net/publication/345343741_Newton_versus_the_machine_solving_the_chaotic_three-body_problem_using_deep_neural_networks)  
7. Three-Body Periodic Orbits API, accessed November 27, 2025, [https://ssd-api.jpl.nasa.gov/doc/periodic\_orbits.html](https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html)  
8. \[astro-ph/0612386\] The Earth-Moon CR3BP: A full Atlas of low-energy fast periodic transfer orbits \- arXiv, accessed November 27, 2025, [https://arxiv.org/abs/astro-ph/0612386](https://arxiv.org/abs/astro-ph/0612386)  
9. Benchmarks — heyoka 7.9.0 documentation, accessed November 27, 2025, [https://bluescarni.github.io/heyoka/benchmarks.html](https://bluescarni.github.io/heyoka/benchmarks.html)  
10. Dynamics of Orbits near 3:1 Resonance in the Earth-Moon System1, accessed November 27, 2025, [https://ntrs.nasa.gov/api/citations/20160010593/downloads/20160010593.pdf](https://ntrs.nasa.gov/api/citations/20160010593/downloads/20160010593.pdf)  
11. Transport geometry of the restricted three-body problem \- Shane Ross, accessed November 27, 2025, [https://ross.aoe.vt.edu/papers/fitzgerald-2023-thesis.pdf](https://ross.aoe.vt.edu/papers/fitzgerald-2023-thesis.pdf)  
12. Formations near the Libration Points: Design Strategies Using Natural and Non-Natural Arcs, accessed November 27, 2025, [https://ntrs.nasa.gov/api/citations/20060048521/downloads/20060048521.pdf](https://ntrs.nasa.gov/api/citations/20060048521/downloads/20060048521.pdf)  
13. Poincaré Sections and Resonant Orbits in the Restricted Three-Body Problem \- College of Engineering \- Purdue University, accessed November 27, 2025, [https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2010\_Vaquero.pdf](https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2010_Vaquero.pdf)  
14. \[Literature Review\] Generative Design of Periodic Orbits in the, accessed November 27, 2025, [https://www.themoonlight.io/en/review/generative-design-of-periodic-orbits-in-the-restricted-three-body-problem](https://www.themoonlight.io/en/review/generative-design-of-periodic-orbits-in-the-restricted-three-body-problem)  
15. MEGNO dynamical map similar to top-left panel of figure 1 for an... \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/figure/MEGNO-dynamical-map-similar-to-top-left-panel-of-figure-1-for-an-Earth-mass-planet-with\_fig1\_251876005](https://www.researchgate.net/figure/MEGNO-dynamical-map-similar-to-top-left-panel-of-figure-1-for-an-Earth-mass-planet-with_fig1_251876005)  
16. Cislunar Multiscale Dynamics and Implications for SSA Aaron J. Rosengren University of California San Diego, La Jolla, CA, Unite \- AMOS Conference, accessed November 27, 2025, [https://amostech.com/TechnicalPapers/2021/Cislunar-SSA/Rosengren.pdf](https://amostech.com/TechnicalPapers/2021/Cislunar-SSA/Rosengren.pdf)  
17. Gravity-Bench-v1: A Benchmark on Gravitational Physics Discovery for Agents \- GitHub, accessed November 27, 2025, [https://raw.githubusercontent.com/mlresearch/v267/main/assets/koblischke25a/koblischke25a.pdf](https://raw.githubusercontent.com/mlresearch/v267/main/assets/koblischke25a/koblischke25a.pdf)  
18. High-order symplectic integrators for planetary dynamics and their implementation in rebound \- Oxford Academic, accessed November 27, 2025, [https://academic.oup.com/mnras/article/489/4/4632/5565063](https://academic.oup.com/mnras/article/489/4/4632/5565063)  
19. whfast: a fast and unbiased implementation of a symplectic Wisdom–Holman integrator for long-term gravitational simulations \- Oxford Academic, accessed November 27, 2025, [https://academic.oup.com/mnras/article/452/1/376/1748797](https://academic.oup.com/mnras/article/452/1/376/1748797)  
20. heyoka.py 7.8.1 documentation, accessed November 27, 2025, [https://bluescarni.github.io/heyoka.py/](https://bluescarni.github.io/heyoka.py/)  
21. Revisiting high-order Taylor methods for astrodynamics and celestial mechanics | Request PDF \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/publication/351120373\_Revisiting\_high-order\_Taylor\_methods\_for\_astrodynamics\_and\_celestial\_mechanics](https://www.researchgate.net/publication/351120373_Revisiting_high-order_Taylor_methods_for_astrodynamics_and_celestial_mechanics)  
22. Installation — heyoka.py 7.8.1 documentation, accessed November 27, 2025, [https://bluescarni.github.io/heyoka.py/install.html](https://bluescarni.github.io/heyoka.py/install.html)  
23. Space Trajectory Design in Uncertain Environments \- University of, accessed November 27, 2025, [https://openresearch.surrey.ac.uk/view/pdfCoverPage?instCode=44SUR\_INST\&filePid=13224325390002346\&download=true](https://openresearch.surrey.ac.uk/view/pdfCoverPage?instCode=44SUR_INST&filePid=13224325390002346&download=true)  
24. Computations in extended precision — heyoka.py 7.8.1 documentation, accessed November 27, 2025, [https://bluescarni.github.io/heyoka.py/notebooks/ext\_precision.html](https://bluescarni.github.io/heyoka.py/notebooks/ext_precision.html)  
25. Symplectic integrators for Hamiltonian problems: an overview | Acta Numerica | Cambridge Core, accessed November 27, 2025, [https://www.cambridge.org/core/journals/acta-numerica/article/symplectic-integrators-for-hamiltonian-problems-an-overview/D835AE296BE8F4C76A42888E61E68E90](https://www.cambridge.org/core/journals/acta-numerica/article/symplectic-integrators-for-hamiltonian-problems-an-overview/D835AE296BE8F4C76A42888E61E68E90)  
26. Symplectic integration of learned Hamiltonian systems \- RIS, accessed November 27, 2025, [https://ris.uni-paderborn.de/download/23382/28734/SymplecticShadowIntegration\_AIP.pdf](https://ris.uni-paderborn.de/download/23382/28734/SymplecticShadowIntegration_AIP.pdf)  
27. Perturbation-theory informed integrators for cosmological simulations \- arXiv, accessed November 27, 2025, [https://arxiv.org/html/2301.09655v3](https://arxiv.org/html/2301.09655v3)  
28. Monitoring energy drift with shadow Hamiltonians \- Purdue University, accessed November 27, 2025, [https://bionum.cs.purdue.edu/EnSD05.pdf](https://bionum.cs.purdue.edu/EnSD05.pdf)  
29. Precimonious: Tuning Assistant for Floating-Point Precision \- David H Bailey, accessed November 27, 2025, [https://www.davidhbailey.com/dhbpapers/precimonious.pdf](https://www.davidhbailey.com/dhbpapers/precimonious.pdf)  
30. (PDF) Implementation and Performance Evaluation of an Extended Precision Floating-Point Arithmetic Library for High-Accuracy Semidefinite Programming \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/publication/319412087\_Implementation\_and\_Performance\_Evaluation\_of\_an\_Extended\_Precision\_Floating-Point\_Arithmetic\_Library\_for\_High-Accuracy\_Semidefinite\_Programming](https://www.researchgate.net/publication/319412087_Implementation_and_Performance_Evaluation_of_an_Extended_Precision_Floating-Point_Arithmetic_Library_for_High-Accuracy_Semidefinite_Programming)  
31. Double-double for virtual amplitude evaluation \- CERN Indico, accessed November 27, 2025, [https://indico.cern.ch/event/1538409/contributions/6521988/attachments/3096541/5485852/magerya-dd.pdf](https://indico.cern.ch/event/1538409/contributions/6521988/attachments/3096541/5485852/magerya-dd.pdf)  
32. Examples of typical behaviour of the MEGNO and its comparisons to the... \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/figure/Examples-of-typical-behaviour-of-the-MEGNO-and-its-comparisons-to-the-LCN-computed-in\_fig5\_41714505](https://www.researchgate.net/figure/Examples-of-typical-behaviour-of-the-MEGNO-and-its-comparisons-to-the-LCN-computed-in_fig5_41714505)  
33. Parameter space (h, q) of the logarithmic Hamiltonian (17). The, accessed November 27, 2025, [https://www.researchgate.net/figure/Parameter-space-h-q-of-the-logarithmic-Hamiltonian-17-The-physical-region-is\_fig7\_41712232](https://www.researchgate.net/figure/Parameter-space-h-q-of-the-logarithmic-Hamiltonian-17-The-physical-region-is_fig7_41712232)  
34. The missing rings around Solar System moons \- arXiv, accessed November 27, 2025, [https://arxiv.org/html/2408.10643v1](https://arxiv.org/html/2408.10643v1)  
35. Comparison of chaos detection methods in the circular restricted three-body problem, accessed November 27, 2025, [https://www.researchgate.net/publication/266678803\_Comparison\_of\_chaos\_detection\_methods\_in\_the\_circular\_restricted\_three-body\_problem](https://www.researchgate.net/publication/266678803_Comparison_of_chaos_detection_methods_in_the_circular_restricted_three-body_problem)  
36. Poincaré Maps and Chaos Classification | ACT of ESA \- European Space Agency, accessed November 27, 2025, [https://www.esa.int/gsp/ACT/projects/poincare\_chaos\_classification/](https://www.esa.int/gsp/ACT/projects/poincare_chaos_classification/)  
37. Enhanced Visualization and Autonomous Extraction of Poincaré Map Topology \- CS@Purdue, accessed November 27, 2025, [https://www.cs.purdue.edu/cgvlab/www/resources/papers/Schlei-Journal\_of\_the\_Astronautical\_sciences-2014-Enhanced\_Visualization\_and\_autonomous\_extration\_of\_poincare\_map\_topology.pdf](https://www.cs.purdue.edu/cgvlab/www/resources/papers/Schlei-Journal_of_the_Astronautical_sciences-2014-Enhanced_Visualization_and_autonomous_extration_of_poincare_map_topology.pdf)  
38. Computer Science Aug 2024 \- arXiv, accessed November 27, 2025, [https://arxiv.org/list/cs/2024-08?skip=1500\&show=100](https://arxiv.org/list/cs/2024-08?skip=1500&show=100)  
39. 人工智能2024\_8\_8 \- arXiv每日学术速递, accessed November 27, 2025, [https://arxivdaily.com/thread/58161](https://arxivdaily.com/thread/58161)  
40. Astrophysics Aug 2024 \- arXiv, accessed November 27, 2025, [https://www.arxiv.org/list/astro-ph/2024-08?skip=950\&show=1000](https://www.arxiv.org/list/astro-ph/2024-08?skip=950&show=1000)  
41. 備忘録1: JPL Solar System Dynamics のAPIの使い方 \- Qiita, accessed November 27, 2025, [https://qiita.com/UzTak/items/6e199202989963236737](https://qiita.com/UzTak/items/6e199202989963236737)  
42. Integrators \- REBOUND, accessed November 27, 2025, [https://rebound.readthedocs.io/en/latest/integrators/](https://rebound.readthedocs.io/en/latest/integrators/)  
43. On the accuracy of symplectic integrators for secularly evolving planetary systems \- Oxford Academic, accessed November 27, 2025, [https://academic.oup.com/mnras/article/490/4/5122/5601761](https://academic.oup.com/mnras/article/490/4/5122/5601761)  
44. MULTI-BODY TRAJECTORY DESIGN IN THE EARTH-MOON REGION UTILIZING POINCARÉ MAPS \- Purdue University Graduate School, accessed November 27, 2025, [https://hammer.purdue.edu/articles/thesis/Multi-Body\_Trajectory\_Design\_in\_the\_Earth-Moon\_Region\_Utilizing\_Poincare\_Maps/19651233/1/files/34896288.pdf](https://hammer.purdue.edu/articles/thesis/Multi-Body_Trajectory_Design_in_the_Earth-Moon_Region_Utilizing_Poincare_Maps/19651233/1/files/34896288.pdf)  
45. (Preprint) AAS 21-451 SPACECRAFT FORMATION CONTROL NEAR A PERIODIC ORBIT USING GEOMETRIC RELATIVE COORDINATES \- University of Colorado Boulder, accessed November 27, 2025, [https://www.colorado.edu/faculty/bosanac/sites/default/files/attached-files/2021\_ellbos\_sfm.pdf](https://www.colorado.edu/faculty/bosanac/sites/default/files/attached-files/2021_ellbos_sfm.pdf)  
46. Local Orbital Elements for the Circular Restricted Three-Body Problem | Journal of Guidance, Control, and Dynamics \- Aerospace Research Central, accessed November 27, 2025, [https://arc.aiaa.org/doi/10.2514/1.G007435](https://arc.aiaa.org/doi/10.2514/1.G007435)  
47. A Low-Complexity Algorithm for Trajectory Generation in the Three-Body Problem \- Scholarly Commons, accessed November 27, 2025, [https://commons.erau.edu/cgi/viewcontent.cgi?article=1901\&context=edt](https://commons.erau.edu/cgi/viewcontent.cgi?article=1901&context=edt)  
48. A transport network for in-orbit recycling exploiting natural dynamics \- Glasgow Caledonian University, accessed November 27, 2025, [https://researchonline.gcu.ac.uk/ws/portalfiles/portal/79296154/79294412.pdf](https://researchonline.gcu.ac.uk/ws/portalfiles/portal/79296154/79294412.pdf)  
49. A study of the main resonances outside the geostationary ring \- ResearchGate, accessed November 27, 2025, [https://www.researchgate.net/publication/271448008\_A\_study\_of\_the\_main\_resonances\_outside\_the\_geostationary\_ring](https://www.researchgate.net/publication/271448008_A_study_of_the_main_resonances_outside_the_geostationary_ring)