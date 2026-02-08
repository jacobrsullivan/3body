## Phase 2: Integrator Shoot-out, Precision Budget & Regularization Plan (Weeks 2-4)

### Overview
This document specifies the detailed implementation plan for Phase 2 of WP1 (Weeks 2-4), focused on integrator evaluation, high-precision arithmetic, and regularization. This phase culminates in the selection and validation of a production integrator that satisfies the precision, robustness, and reproducibility requirements for the CR3BP trajectory catalogue.

---

### 0. Learning Objectives
By Day 20, participants will:
- Differentiate between symplectic, adaptive, and high-order integrators
- Execute and interpret performance benchmarks (drift, reversibility, shadow Hamiltonian)
- Quantify numerical error in DP vs DD across test cases
- Implement Levi-Civita (LC) switching regularization
- Deliver a production-grade integrator pipeline with CI validation

---

### 1. Daily Implementation Plan

#### Week 2: Double Precision & Harness Development

**Day 6** – Benchmark Harness Skeleton & Inertial Frame Output
- Draft YAML spec (`cr3bp_smoke.yaml`) for standard CR3BP orbit
- Create `scripts/run_benchmark.py`
- Save both co-rotating and inertial frame outputs
- Commit and push branch `feature/integrator-harness`

**Day 7** – IAS15 (Double Precision Only)
- Wrap REBOUND IAS15 as Python backend
- Smoke test orbit; record drift and CPU
- Save result as `results/ias15_DP.json`

**Day 8** – High-Order Composition (Yoshida-8, DP)
- Compile C++ implementation
- Wrap with pybind11 (`Integrator` API)
- Sweep dt; tune for drift < 1e-13
- Save result as `results/yosh8_DP.json`

**Days 9-10** – Adaptive Symplectic (Sundman, DP)
- Implement Sundman-transformed leapfrog integrator
- Sweep monitor parameter α to minimize CPU × drift
- Verify dt adaptation near primary
- Save result as `results/sundman_DP.json`

---

#### Week 3: High-Precision, Regularization, and Stress Testing

**Day 11** – Double-Double Arithmetic (Yoshida & Sundman only)
- Enable DD via `typedef` or template specialization
- Link to QD library; verify compilation
- Produce `yosh8_DD.json` and `sundman_DD.json`

**Day 12** – Harness Consolidation and CI
- Unify harness to iterate backends × precisions
- Output: `results/master.csv`
- CI: Run DP on push, DD nightly (self-hosted)

**Day 13** – Levi-Civita Switching Regularization
- Implement LC transform in 2D
- Compose with Sundman backend using switching function s(r)
- Save as `sundman_lc_DP.json` and `sundman_lc_DD.json`

**Day 14** – Stress Cases and Regularization Benchmark
- Define: Close Approach, Chaotic Halo, Long-Term cases
- Run all backends; focus comparison on LC vs non-LC
- Save expanded `master.csv` with new metrics

**Day 15** – Cost vs Precision Sweep and Midpoint Report
- Parameter sweeps: dt/tol vs drift & CPU
- Generate log-log plots for each backend
- Compile `reports/midpoint_report.html`

---

#### Week 4: Stability Metrics, Final Benchmarking, and Release

**Day 16** – Time Reversibility Analysis
- Implement forward-backward runs
- Add `rms_reverse` column to results

**Days 17-18** – Shadow Hamiltonian Analysis (2 Days)
- Compute Ḥ_shadow(t) for symplectic integrators
- Save drift metrics to `shadow_drift`
- Plot and document results

**Day 19** – Final Shoot-out & Decision Matrix
- Matrix: drift, CPU, reversibility, shadow error, regularization
- Apply stakeholder weights, select production integrator
- Save final run as `final_master.csv`

**Day 20** – Merge, Documentation, CI Upgrade
- Memo: `selection_memo.md`
- CI: Add nightly DD stress tests
- Tag GitHub release `v0.2.0-integrator`
- Record 30-min demo walkthrough

---

### 2. Key Deliverables
- `run_benchmark.py` supporting multiple backends and precisions
- DP and DD benchmark datasets (`master.csv`, `final_master.csv`)
- Regularized Sundman integrator (LC switching)
- CI pipelines for DP (push) and DD (nightly)
- `selection_memo.md` and `midpoint_report.html`

---

### 3. Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| IAS15 DD not feasible | Incomplete comparison | Use only as DP baseline |
| LC switching discontinuity | Drift explosion | Use smooth switching (Mikkola) + unit tests |
| QD library fails on CI | CI failure | Use Boost.Multiprecision fallback or self-hosted runners |
| Shadow analysis takes too long | Timeline slip | Pre-derive symbolic expressions offline |

---

### 4. References
- WP1 High-Fidelity CR3BP Catalogue【29†source】
- Week 0-1 High-Precision Setup Plan【30†source】
- A Systematic Search for Hidden Integrability【31†source】

---

### 5. Review Checklist
- [x] Integrator harness saves inertial output
- [x] IAS15 only used in DP
- [x] LC switching benchmarked on close encounters
- [x] All metrics saved to CSV
- [x] Shadow Hamiltonian evaluated
- [x] CI includes DD and DP paths
- [x] GitHub release tagged
