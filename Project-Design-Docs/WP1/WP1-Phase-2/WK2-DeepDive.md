This implementation plan details the execution of Week 2 (Days 6-10) for Work Package 1 (WP1). The focus is on developing the benchmark harness and implementing the three candidate integrators in standard double precision (DP). This plan is designed for researchers or engineers who may be new to these concepts, providing explanations for each step.

### Week 2 Overview: Double Precision and Harness Development

**Prerequisites:** Successful completion of Week 1 (Environment setup, Git repository initialized, Conda environment `wp1_env` active, CI running, basic C++/pybind11 functionality verified).
**Goal:** Implement a standardized, automated system for comparing integrators and establish baseline performance for the three candidates (IAS15, Symplectic Composition, Sundman Adaptive) in double precision.

***

#### Day 6: Kick-off & Benchmark Harness Skeleton

**Objective:** Define the standard test cases, create the automated script (the harness), and implement the mandatory coordinate transformations.

**1. Concepts**

*   **Benchmark Harness:** An automated script that runs different integrators under identical conditions and records their performance (accuracy and speed) to ensure a fair, reproducible comparison.
*   **YAML Specification:** We use YAML files to define the physical parameters of the test cases, separating configuration from code.
*   **Coordinate Frames (CR3BP):** The Circular Restricted Three-Body Problem (CR3BP) is typically integrated in the **Co-rotating Frame**, where the two massive bodies are stationary. However, the project requires storing data in the **Inertial Frame** (where the center of mass is stationary), as fundamental symmetries might be hidden by the fictitious forces in the co-rotating frame.

**2. Action Items**

1.  **Git Workflow:** Start a new feature branch: `git checkout -b feature/integrator-harness`.
2.  **Define the Benchmark Specification (YAML):**
    *   Create `benchmarks/cr3bp_smoke.yaml`. Use a known stable orbit (e.g., near the L4 Lagrange point) for this initial test.
    ```yaml
    name: "EarthMoon_L4_Stable"
    # Mass parameter mu (M2 / (M1 + M2)) for Earth-Moon system
    mu: 0.0121505856
    # Initial conditions in the co-rotating frame (Example near L4)
    initial_conditions: {x: 0.4878, y: 0.8660, vx: 0.0, vy: 0.0}
    # Duration: 1000 characteristic periods (T=2*Pi in normalized units)
    duration: 6283.1853
    ```
3.  **Implement the Harness Skeleton:**
    *   Create `scripts/run_benchmark.py`.
    *   Use `argparse` for command-line arguments (`--backend`, `--spec`, `--output`).
    *   Use `PyYAML` (install via `poetry add pyyaml`) to parse the YAML file.
4.  **Implement Coordinate Transformation Utility:**
    *   Create `src/python/utils/coordinates.py`.
    *   Implement `corotating_to_inertial(state, t, mu)`. This involves applying a time-dependent rotation matrix and shifting the origin to the barycenter.

**3. Verification**

*   The harness skeleton runs and parses the YAML without error.
*   Write a unit test (`tests/test_coordinates.py`) to verify the coordinate transformation is correct (e.g., check the positions of the primaries in the inertial frame over time).

***

#### Day 7: IAS15 (Baseline) Integration

**Objective:** Implement the first integrator using the `REBOUND` package as the baseline.

**1. Concepts**

*   **IAS15:** A high-order (15th), robust integrator. It uses **adaptive time-stepping** but is **not** symplectic. It provides excellent energy conservation.
*   **Integrator Interface (Abstract Base Class - ABC):** A standard "contract" that all integrators must follow, allowing the harness to swap them easily.
*   **Jacobi Constant (C):** The only known conserved quantity in the CR3BP. The drift in $C$ is our primary measure of numerical error.

**2. Action Items**

1.  **Define the Standard Integrator Interface:**
    *   Create `src/python/integrators/base.py`.
    *   Define the ABC `IntegratorBase` with required methods `__init__` and `integrate`.
2.  **Implement the IAS15 Wrapper:**
    *   Create `src/python/integrators/ias15.py`.
    *   Implement `IAS15Integrator(IntegratorBase)`.
    *   Use the `rebound` library to configure and run the simulation (select `integrator='ias15'`).
3.  **Implement Data Handling and Transformation:**
    *   **[Critical Requirement]** The `integrate` method must save the trajectory data and then transform it. The output must include datasets for both the co-rotating and inertial frames.
4.  **Implement Metrics and Harness Integration:**
    *   In `src/python/utils/dynamics.py`, implement `calculate_jacobi(state, mu)`.
    *   Update `run_benchmark.py` to use the IAS15 backend.
    *   Calculate the relative error: $|\Delta C / C_0|$ and measure wall-clock time.
    *   Save metrics to `results/ias15_dp_smoke.json` and trajectory data (HDF5).

**3. Verification**

*   The harness runs successfully with IAS15.
*   The output HDF5 file contains both `state_corotating` and `state_inertial` datasets.
*   The relative Jacobi drift is near machine precision ($< 10^{-14}$).

***

#### Day 8: High-Order Symplectic Composition (C++)

**Objective:** Implement a fixed-step, high-order symplectic integrator in C++ and expose it to Python.

**1. Concepts**

*   **Symplectic Integrators:** Algorithms that exactly conserve geometric properties of the phase space, preventing long-term systematic energy drift.
*   **The CR3BP Hamiltonian Challenge:** The CR3BP Hamiltonian in the co-rotating frame is **non-separable**. It cannot be written simply as Kinetic Energy $T(p)$ + Potential Energy $V(q)$ due to the rotation terms ($y p_x - x p_y$). Standard "Leapfrog" methods fail here.
*   **Correct Symplectic Splitting for CR3BP:** We must split the Hamiltonian into integrable parts:
    *   $H_A$: Kinetic + Rotation terms. (The flow is an exact rotation in phase space).
    *   $H_B$: Potential terms (The flow is a standard gravitational "kick").
*   **C++, CMake, pybind11:** C++ for performance and later high-precision work; CMake for building; pybind11 for Python interfacing.

**2. Action Items**

*(Note: This is intensive. The goal is a functional C++ implementation.)*

1.  **C++ Build System (CMake):**
    *   Set up `CMakeLists.txt` in `src/cpp/` to manage the build and link `pybind11`.
2.  **C++ Implementation (Hamiltonian Splitting):**
    *   Create `src/cpp/cr3bp_symp.cpp`.
    *   Implement the exact flow for $H_A$ (rotation). This requires applying rotation matrices to both positions and momenta.
    *   Implement the exact flow for $H_B$ (potential kick). This involves calculating the gravitational forces and updating the momenta.
3.  **C++ Implementation (Composition Scheme):**
    *   Implement an 8th-order composition scheme (using Yoshida's coefficients) by sequencing the flows for $H_A$ and $H_B$. Use standard `double`.
4.  **pybind11 Wrapping:**
    *   Expose the C++ integrator class (e.g., `SympCompositionIntegrator`) to Python.
5.  **Python Wrapper and Tuning:**
    *   Create `src/python/integrators/composition.py` (inheriting from `IntegratorBase`).
    *   *Tuning:* Choose a fixed time step `dt` (e.g., $T/1000$) that yields accuracy $< 10^{-13}$.

**3. Verification**

*   The C++ module compiles and is importable in Python.
*   The harness runs with `--backend composition`. Verify the energy error is bounded (oscillates but does not drift linearly).

***

#### Day 9: Adaptive Symplectic Prototype (Implementation)

**Objective:** Implement the core mechanism for an adaptive-step symplectic integrator in C++.

**1. Concepts**

*   **The Adaptivity/Symplecticity Conflict:** Standard adaptive stepping breaks symplecticity.
*   **Sundman Transform (Time Reparametrization):** We achieve adaptivity by changing the independent variable from physical time $t$ to a "fictitious time" $\tau$, such that $dt = g(q) d\tau$.
*   **Monitor Function $g(q)$:** This function controls the step size. We make $g(q)$ small when dynamics are fast (e.g., near a massive body), so $dt$ shrinks while the fictitious step $d\tau$ remains constant.
*   **Transformed Hamiltonian:** This technique requires integrating a new, transformed Hamiltonian $\widetilde{H}$ in an extended phase space.

**2. Action Items**

*(Note: This is mathematically complex. Focus on implementing the transformed equations of motion.)*

1.  **Theoretical Review:** Review the theory of symplectic integration via time transformation (Reference: Hairer, Lubich, Wanner).
2.  **C++ Implementation (Transformed System):**
    *   Create `src/cpp/sundman_adaptive.cpp`.
    *   Implement the monitor function $g(q)$. A common choice depends on the distance to the primaries or the potential energy.
    *   Implement the equations of motion derived from the transformed Hamiltonian $\widetilde{H}$.
3.  **Integration Core:**
    *   Apply a fixed-step symplectic scheme (like the structure from Day 8) to the transformed Hamiltonian $\widetilde{H}$.
    *   Ensure physical time $t$ is integrated alongside the state variables ($dt/d\tau = g(q)$).

**3. Verification**

*   The C++ code compiles successfully.
*   A very short integration (1 period) completes, verifying the basic mechanics of the transformed system and the advancement of physical time $t$.

***

#### Day 10: Adaptive Symplectic (Tuning) and Harness v1

**Objective:** Tune the adaptive integrator, verify its adaptivity, and finalize the harness V1.

**1. Concepts**

*   **Tuning:** The monitor function $g(q)$ has parameters that control the aggressiveness of the adaptation. We must optimize these.
*   **Efficiency Metric:** We aim to minimize the "cost score": (Error $\times$ CPU Time).

**2. Action Items**

1.  **pybind11 and Python Wrapper:**
    *   Add pybind11 bindings for the Sundman integrator and update CMake.
    *   Implement `src/python/integrators/sundman.py`.
2.  **Tuning the Monitor Function:**
    *   In a notebook (`notebooks/sundman_tuning.ipynb`), sweep through the parameters of $g(q)$ and the base step size $d\tau$.
    *   Identify the parameters that minimize the efficiency metric for the smoke test.
3.  **Verify Adaptivity:**
    *   Run a test case involving a close encounter (create a temporary YAML spec).
    *   Plot the physical time step $dt$ versus time $t$.
4.  **Harness Consolidation and CI:**
    *   Finalize `run_benchmark.py` to run all three backends sequentially.
    *   Aggregate all JSON results into a single CSV: `results/week2_dp_comparison.csv`.
    *   Update the GitHub Actions CI workflow (`.github/workflows/ci.yml`) to automatically run this DP benchmark on every push.

**3. Verification**

*   The adaptivity plot clearly shows $dt$ decreasing significantly during close encounters.
*   `results/week2_dp_comparison.csv` is generated, comparing IAS15, Composition, and Sundman.
*   The CI pipeline passes on GitHub. Open a Pull Request for the `feature/integrator-harness` branch.
