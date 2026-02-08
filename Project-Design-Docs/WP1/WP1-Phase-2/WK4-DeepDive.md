This implementation plan details the execution of Week 4 (Days 16-20) for Work Package 1 (WP1). This final week of the "Integrator Shootout" focuses on applying the most rigorous validation techniques—Time Reversibility and Shadow Hamiltonian Analysis—to objectively select the production integrator.

### Week 4 Overview: Rigorous Validation and Selection

**Prerequisites:** Successful completion of Week 3 (Integrators functional in DP/DD; regularization implemented; Precision-Cost curves generated).
**Goal:** Implement advanced validation techniques, synthesize all data into a weighted decision matrix, select the final integrator, and document the process.

***

#### Day 16: Time Reversibility Analysis

**Objective:** Test how well the integrators respect the time-symmetry of Hamiltonian dynamics.

**1. Concepts**

*   **Time Reversibility:** Newtonian gravity is time-symmetric. If you run a simulation forward, stop, reverse all velocities (momenta), and run it backward, you should return exactly to the starting point.
*   **Numerical Test:** This test reveals hidden numerical dissipation or biases. Symplectic integrators generally excel at this test.
*   **The Challenge of Adaptive Integrators:** For adaptive integrators (IAS15, Sundman), a true reversibility test requires recording the exact sequence of time steps taken during the forward integration and forcing the integrator to use that *exact sequence* (in reverse order) during the backward integration.

**2. Action Items**

1.  **Modify the Benchmark Harness:**
    *   Update `scripts/run_benchmark.py` with a `--reversibility-check` flag.
2.  **Implement Step Recording (Adaptive Methods):**
    *   Modify the C++ Sundman integrator and the Python IAS15 wrapper to optionally record the sequence of time steps ($dt$ or $d\tau$).
    *   Add a "playback mode" where the integrator reads and reuses this sequence instead of calculating steps adaptively.
3.  **Implement the Reversibility Logic:**
    *   **Forward:** Integrate from $t=0$ to $t=T_{end}$, recording steps if adaptive.
    *   **Flip:** Negate the momenta of the final state. Ensure this is done in the correct precision (DD if applicable).
    *   **Backward:** Integrate again for the same duration, forcing the recorded step sequence.
4.  **Metric and Execution:**
    *   Calculate the Root Mean Square (RMS) error between the initial state and the final reversed state.
    *   Run this test on the `stress_chaotic_L1.yaml` case, as chaos amplifies errors.
    *   Record the `RMS_Reversibility_Error` in `master_comparison.csv`.

**3. Verification**

*   Symplectic methods (Composition, Sundman) in DD should show errors near the DD precision limit ($< 10^{-28}$).
*   IAS15 (DP) will likely show significantly larger errors, providing a baseline.

***

#### Day 17: Shadow Hamiltonian Analysis (Part 1: Symbolic Derivation)

**Objective:** Derive the mathematical expressions for the Shadow Hamiltonian using symbolic tools.

**1. Concepts**

*   **Backward Error Analysis (BEA):** Symplectic integrators do not conserve the true Hamiltonian ($H$). However, they exactly (or nearly exactly) conserve a nearby **Shadow Hamiltonian** ($\widetilde{H}$).
*   **Validation Power:** Monitoring $\widetilde{H}$ is the strongest validation of a symplectic integrator's long-term stability.
*   **The Calculation:** $\widetilde{H}$ is a series expansion: $\widetilde{H} = H + h^k H_k + \dots$ (where $h$ is the step size and $k$ is the order). We aim to calculate the leading correction term, $H_k$.
*   **Poisson Brackets and Symbolic Tools:** $H_k$ involves complex nested Poisson brackets of the split Hamiltonian parts ($H_A$ and $H_B$). Deriving these manually is highly error-prone; we will use the symbolic mathematics library SymPy.

**2. Action Items**

1.  **Setup Symbolic Environment:** Ensure SymPy is installed (`poetry add sympy`).
2.  **Define the CR3BP Hamiltonian in SymPy:**
    *   In `notebooks/shadow_derivation.ipynb`, define the coordinates ($x, y, p_x, p_y$) and the mass parameter ($\mu$) as symbols.
    *   Define the split Hamiltonians $H_A$ (Kinetic + Rotation) and $H_B$ (Potential) symbolically.
3.  **Implement Poisson Bracket Operator:**
    *   Define a SymPy function that computes the Poisson bracket $\{F, G\} = \sum_i (\frac{\partial F}{\partial q_i}\frac{\partial G}{\partial p_i} - \frac{\partial F}{\partial p_i}\frac{\partial G}{\partial q_i})$.
4.  **Calculate $H_k$:**
    *   Calculate the required nested Poisson brackets for the specific composition scheme used (Reference: Hairer, Lubich, Wanner, Chapter IX).
    *   Simplify the resulting expression for $H_k$.

**3. Verification**

*   The Jupyter notebook contains the explicit, simplified symbolic expression for the leading correction term $H_k$ for the CR3BP.

***

#### Day 18: Shadow Hamiltonian Analysis (Part 2: Implementation and Validation)

**Objective:** Implement the derived Shadow Hamiltonian calculation in C++ and validate the symplectic integrators.

**1. Action Items**

1.  **Generate C++ Code from SymPy:**
    *   Use SymPy's code generation capabilities (e.g., `sympy.printing.cxxcode`) to automatically convert the symbolic expression for $H_k$ into C++ code. This minimizes transcription errors.
2.  **Implement in C++:**
    *   Integrate the generated C++ code into `src/cpp/`. Ensure it uses the flexible `Real` type (supporting DD precision).
    *   Implement the function `calculate_shadow_H` which computes $\widetilde{H} \approx H + h^k H_k$.
    *   **[Crucial]** Use the correct step size $h$: physical $dt$ for Composition, or fictitious $d\tau$ for Sundman.
3.  **Harness Integration:**
    *   Modify the C++ symplectic integrators to calculate $\widetilde{H}$ at requested output steps.
    *   Update the pybind11 interface and the Python harness to capture the time series of $\widetilde{H}$ (converting to strings for DD).
4.  **Validation Run:**
    *   Execute the `stress_long_term.yaml` benchmark ($10^5$ periods) in DD precision.

**2. Verification (The Crucial Plot)**

*   Generate a plot (`notebooks/shadow_analysis.ipynb`) comparing the evolution of the True Hamiltonian ($H$) and the Shadow Hamiltonian ($\widetilde{H}$).
*   *Success Criterion:* $H(t)$ will show bounded oscillations. $\widetilde{H}(t)$ must be dramatically flatter, conserved near the DD precision limit ($< 10^{-28}$), and show **no secular (linear) drift**. This demonstrates the integrator's geometric integrity.

***

#### Day 19: Decision Matrix and Final Shoot-out

**Objective:** Synthesize all data and objectively select the production integrator using a weighted decision matrix.

**1. Concepts**

*   **Weighted Decision Matrix:** A structured tool to evaluate options against weighted criteria, ensuring an objective decision aligned with project goals (where fidelity is prioritized over speed).

**2. Action Items**

1.  **Define Criteria and Weights:**
    *   Meet with the PI to finalize criteria and weights (totaling 100%). Document in `docs/decision_matrix.md`.
    *   *Example Criteria and Weights:*
        *   Shadow Hamiltonian Conservation (DD Stability): 30%
        *   Jacobi Drift (DD, Long Term): 25%
        *   Regularization Robustness (Drift during Close Encounter): 20%
        *   Time Reversibility RMS (DD): 15%
        *   Computational Cost (CPU time at $10^{-25}$ error): 10%
2.  **Final Authoritative Benchmark Run:**
    *   Ensure the optimal parameters (step size, tolerances) found in Week 3 (Precision-Cost curves) are configured for each integrator.
    *   Execute the harness across the full suite of stress tests in their highest applicable precision.
3.  **Populate the Matrix and Select the Winner:**
    *   Collect the final data and archive it (`results/final_shootout.csv`).
    *   Normalize the scores for each criterion.
    *   Calculate the weighted scores and identify the winner (e.g., `Sundman_LC_DD`).

**3. Verification**

*   A completed Decision Matrix mathematically justifying the selection.

***

#### Day 20: Documentation, Merging, and Release

**Objective:** Finalize the documentation, clean the codebase, merge the feature branch, and configure the CI for long-term stability.

**1. Concepts**

*   **Technical Memo:** A formal document summarizing the methodology, results, and justification. This is the primary deliverable of the shootout phase.
*   **Scheduled CI (Cron Jobs):** Running computationally expensive tests (like DD stress tests) on a schedule (e.g., weekly) rather than on every push, to detect regressions over time without slowing down development.

**2. Action Items**

1.  **Draft the Integrator Selection Memo:**
    *   Write `docs/selection_memo.md`. Include:
        *   Methodology overview (Precision, Regularization, Validation).
        *   Key plots (Work-Precision diagrams, Shadow Hamiltonian verification).
        *   The Decision Matrix and justification.
        *   The final selection and its optimized parameters.
2.  **Code Review and Merge:**
    *   Review the `feature/integrator-harness` Pull Request. Ensure all code is clean, documented, and passes `pre-commit` checks.
    *   Merge the PR into the `main` branch.
3.  **Configure Scheduled CI:**
    *   Create a new CI workflow (e.g., `.github/workflows/weekly_dd_validation.yml`) that runs the DD stress tests using the winning integrator on a schedule trigger.
4.  **Release Tagging:**
    *   Tag the release:
      ```bash
      git tag -a v0.2.0 -m "WP1 Phase 1 Complete: Integrator Selected"
      git push origin v0.2.0
      ```

**3. Verification**

*   The Selection Memo is approved by the PI.
*   The `main` branch is updated, CI passes (DP tests), and the weekly DD job is scheduled.
*   The `v0.2.0` tag is visible on GitHub/GitLab.
