This implementation plan details the execution of Week 3 (Days 11-15) for Work Package 1 (WP1). This week involves the most technically challenging aspects of the setup: upgrading the C++ integrators to high precision, implementing mathematical techniques to handle gravitational singularities, and analyzing the computational cost of accuracy.

### Week 3 Overview: High Precision, Regularization, and Cost Analysis

**Prerequisites:** Successful completion of Week 2 (Functional benchmark harness; IAS15, Composition, and Sundman integrators implemented in Double Precision (DP)).
**Goal:** Upgrade C++ integrators to Double-Double (DD) precision, implement Levi-Civita regularization, and quantify the trade-off between precision and cost.

***

#### Day 11: Double-Double (DD) Arithmetic Upgrade (C++ Only)

**Objective:** Modify the C++ integrators (Composition and Sundman) to utilize the high-precision QD library.

**1. Concepts**

*   **The Precision Gap:** Standard "double" precision (DP) (≈16 digits) is insufficient for our $10^{-25}$ error target. We require "Double-Double" (DD) precision (≈31 digits), provided by the QD library installed in Week 1.
*   **Abstraction via `typedef`:** We do not want to maintain two separate versions of the C++ code. We use a C++ `typedef` and compiler flags to define a generic numeric type (e.g., `Real`) that can be switched between standard `double` and the QD type `dd_real` at compile time.
*   **The IAS15 Constraint:** The IAS15 integrator (via the REBOUND package) is compiled for DP. Rewriting it for DD is infeasible; it remains our DP baseline.
*   **The pybind11 Boundary (Crucial):** Python's standard `float` type is only DP. We cannot pass C++ `dd_real` objects directly to Python without losing the extra precision. To transfer the high-precision trajectory data, we must convert the `dd_real` values to strings in C++, pass the strings to Python, and then convert them to a high-precision Python type (like `Decimal`).

**2. Action Items**

1.  **Refactor C++ Code for Precision Flexibility:**
    *   Create a common header file (e.g., `src/cpp/precision.h`):
      ```cpp
      #ifdef USE_DD
      #include <qd/dd_real.h>
      typedef dd_real Real;
      #else
      typedef double Real;
      #endif
      ```
    *   Update the Composition and Sundman C++ source files to include this header and replace all instances of `double` (used for physical variables and calculations) with `Real`.
2.  **Update Build System (CMake):**
    *   Modify `CMakeLists.txt`. Add a build option: `option(BUILD_DD "Build with Double-Double precision" OFF)`.
    *   If `BUILD_DD` is ON:
        *   Add the compile definition (`-DUSE_DD`).
        *   Link against the QD library (`-lqd`).
3.  **Update pybind11 Interface (Data Transfer):**
    *   Modify the pybind11 wrappers. When the C++ integrator returns the trajectory data, if `USE_DD` is active, iterate through the results and convert each `dd_real` to a string before passing it to Python.
4.  **Harness Modification (Python Side):**
    *   Update `scripts/run_benchmark.py` to accept a `--precision {dp, dd}` flag.
    *   Implement logic to skip IAS15 if `dd` is selected.
    *   When receiving data from a DD run, the harness must convert the strings into Python's `Decimal` type (or use `mpmath`) for analysis (e.g., calculating the Jacobi constant) and storage.

**3. Verification**

*   Compile the C++ code successfully in both DP and DD modes by toggling the CMake option.
*   Run the harness in DD mode on the smoke test.
*   *Success Criterion:* The Jacobi drift must drop dramatically (e.g., from $10^{-14}$ in DP to $< 10^{-25}$ in DD).
*   Verify that the CPU time increases significantly (often 10x-50x).

***

#### Day 12: Harness Consolidation and CI Strategy

**Objective:** Finalize the harness to manage the full matrix of tests and establish a strategy for Continuous Integration (CI).

**1. Concepts**

*   **Test Matrix Management:** We now have a complex matrix: (Integrators) × (Precisions) × (Test Cases). The harness must automate this robustly.
*   **Continuous Integration (CI) Challenges:** Running high-precision tests in CI (like GitHub Actions) presents two problems: (1) The CI server needs the QD library installed to compile the code, and (2) DD tests are slow.
*   **Pragmatic CI Strategy:** We will configure CI to install QD and compile both versions (ensuring the code doesn't break), but only run the fast DP tests automatically on every push to save time.

**2. Action Items**

1.  **Harness Refactoring:**
    *   Refactor `scripts/run_benchmark.py` to iterate robustly over the defined test matrix. Ensure clear handling of supported and unsupported combinations.
2.  **Data Aggregation and Storage:**
    *   Ensure the script aggregates all results into `results/master_comparison.csv`, clearly labeling the precision used.
    *   Verify that the trajectory data from DD runs is correctly stored (e.g., in HDF5 as strings) without loss of precision.
3.  **CI Update (Dependency Management):**
    *   Update the CI workflow (`.github/workflows/ci.yml`).
    *   Add steps to the CI pipeline to download, compile, and install the QD library on the CI runner (mirroring the steps from Week 1, Day 3). This ensures the C++ code, which now references QD conditionally, can compile.
    *   Ensure CI runs the full DP test matrix.

**3. Verification**

*   Locally, the harness generates the `master_comparison.csv` with entries for all 5 combinations: IAS15 (DP), Composition (DP/DD), and Sundman (DP/DD).
*   Pushing the code to GitHub triggers the CI pipeline, which successfully installs QD, compiles the code, and passes the DP benchmarks.

***

#### Day 13: Implementing Explicit Regularization (Levi-Civita)

**Objective:** Implement a regularization scheme to handle close encounters with the massive bodies robustly.

**1. Concepts**

*   **The Singularity Problem:** Newtonian gravity ($F \propto 1/r^2$) approaches infinity as the distance $r$ approaches zero. This singularity destroys numerical integrators during close encounters, regardless of precision.
*   **Levi-Civita (LC) Regularization:** A mathematical transformation of both coordinates and time that "unfolds" the singularity. In the new coordinates, the dynamics are smooth.
*   **Switching Regularization:** LC coordinates are computationally expensive. We only activate them when the particle is very close to a primary mass.
*   **Smooth Switching (Mikkola's Method):** Abruptly switching coordinate systems introduces discontinuities that ruin high precision. We must use a smooth transition function (like a sigmoid) to blend the Newtonian and LC dynamics near the switching boundary. For symplectic integrators, it is often preferred to blend the Hamiltonians rather than the forces/equations of motion.

**2. Action Items**

*(Note: This is the most mathematically intensive day.)*

1.  **Implement LC Transformations (C++):**
    *   In `src/cpp/regularization.cpp`, implement the coordinate transformations (Newtonian $\leftrightarrow$ LC). For the 2D problem, this involves complex arithmetic (e.g., $x+iy = (u+iv)^2$).
2.  **Implement Regularized Equations of Motion:**
    *   Implement the Hamiltonian and the resulting equations of motion in the LC coordinates.
3.  **Implement Smooth Switching Functions:**
    *   Implement a smooth transition function $S(r)$ that goes from 0 (far away, Newtonian) to 1 (close, LC).
4.  **Integrate into the Leading Candidate:**
    *   Integrate the LC mechanism into the most promising C++ integrator (likely the Sundman Adaptive).
    *   Implement the blended dynamics. Preferentially blend the Hamiltonians: $H_{blended} = (1-S(r)) H_{Newtonian} + S(r) H_{LC}$, and derive the resulting equations of motion.

**3. Verification**

*   Unit tests for the LC transformations: verify that a round trip (Newtonian -> LC -> Newtonian) recovers the original coordinates to DD precision.
*   Run a simple collision trajectory (e.g., drop a particle toward a primary). Verify the non-regularized integrator fails (huge energy error) while the regularized integrator handles the vicinity smoothly.

***

#### Day 14: Stress-Case Catalogue and Regularization Benchmarking

**Objective:** Define challenging test cases and validate the effectiveness of the regularization.

**1. Concepts**

*   **Stress Testing:** Evaluating integrators on dynamically difficult scenarios to expose weaknesses.
    *   **Close Encounter:** Tests the regularization and adaptivity.
    *   **Chaotic Orbit:** Tests long-term stability and symplecticity (e.g., near the unstable L1 Lagrange point).
    *   **Ultra-Long Duration:** Tests for very slow accumulation of error ($10^5$ periods).

**2. Action Items**

1.  **Define Stress Case YAML Specs:**
    *   Create `benchmarks/stress_close_encounter.yaml`: A highly elliptical orbit passing extremely close to the secondary mass (e.g., $r_{min} < 10^{-4}$).
    *   Create `benchmarks/stress_chaotic_L1.yaml`.
    *   Create `benchmarks/stress_long_term.yaml`.
2.  **Update Harness:**
    *   Ensure the harness can run a suite of YAML files.
    *   Add the regularized integrator (e.g., `Sundman_LC`) as a new backend.
3.  **Regularization Benchmark:**
    *   Run the `stress_close_encounter` case in DD precision using the non-regularized Sundman and the new `Sundman_LC` integrator.
    *   Analyze the results: Compare the Jacobi drift and the CPU time.

**3. Verification**

*   The non-regularized integrator should show a significant spike in error during the close encounter, even in DD precision, and/or take excessive CPU time.
*   *Success Criterion:* The `Sundman_LC` integrator must maintain the $10^{-25}$ error tolerance smoothly through the encounter, demonstrating the robustness of the regularization.

***

#### Day 15: Precision-vs-Cost Curves and Mid-Point Review

**Objective:** Quantify the efficiency of each integrator and generate a midpoint progress report.

**1. Concepts**

*   **Work-Precision Diagram (Precision-Cost Curve):** A standard tool in numerical analysis. It is a log-log plot of the Error (Jacobi drift) versus the Computational Cost (CPU time).
*   **Parameter Sweeping:** To generate the diagram, we run the same test case multiple times, varying the integrator's accuracy parameter (the time step `dt` or `d\tau` for C++ methods, or the error tolerance for IAS15).
*   **Efficiency:** The "best" integrator achieves the desired precision with the lowest CPU cost (the bottom-left of the diagram). The slope of the curve indicates the integrator's order.

**2. Action Items**

1.  **Implement Parameter Sweeping Script:**
    *   Create `scripts/run_work_precision_sweep.py`.
    *   For Composition (fixed step): Sweep `dt` (e.g., logarithmically from $T/100$ to $T/10000$).
    *   For IAS15 and Sundman (adaptive): Sweep the tolerance or monitor function parameters.
    *   Run the sweeps for all applicable precisions (DP and DD) on a representative test case (e.g., the smoke test or the chaotic L1 test). This is computationally intensive.
2.  **Generate Work-Precision Diagrams:**
    *   Create a Jupyter notebook `notebooks/midpoint_analysis.ipynb`.
    *   Load the sweep data and generate the log-log plots. Create separate plots for DP and DD comparisons.
3.  **Generate Midpoint Report:**
    *   Use the notebook to summarize the findings: comparison of DP vs DD performance, the effectiveness of regularization (Day 14 results), and the efficiency curves.
    *   Export the notebook to `reports/midpoint_report.html` and commit it.

**3. Verification**

*   The Work-Precision diagrams clearly illustrate the relationship between cost and error for all candidates.
*   The HTML report provides a clear visual summary of the current standings in the integrator shootout.
