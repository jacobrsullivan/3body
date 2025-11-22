# WP1 Gap-Fixing Implementation Plan
## 22nd November 2025

**Status**: 🔴 **ACTIONABLE PLAN** - Ready for Implementation
**Priority**: 🔥 **CRITICAL** - Blocks WP1 Production Runs
**Target Completion**: 6-8 weeks (based on WP1 original timeline)

---

## Executive Summary

This document provides a comprehensive, prioritized implementation plan to address all identified gaps in Work Package 1 (High-Fidelity CR3BP Trajectory Catalogue). The current implementation is at **60% completion** with excellent foundations but missing critical WP1-specific deliverables.

**Key Metrics**:
- **13 identified gaps** (5 critical, 5 quality-affecting, 3 minor)
- **Estimated effort**: 6-8 weeks FTE
- **Dependencies**: Variational equation infrastructure (✅ exists)
- **Blockers**: None - all prerequisites met

**Success Criteria**:
- ✅ All Tier 1 (10⁵ orbits, ΔC < 10⁻¹⁴) production runs enabled
- ✅ All Tier 2 (10⁴ orbits, ΔC < 10⁻²⁵) "gold standard" runs enabled
- ✅ Complete chaos characterization (MEGNO + FLI) operational
- ✅ Rigorous validation framework (shadow Hamiltonian, time reversibility) implemented
- ✅ ML-ready data pipeline (HDF5 + Parquet) complete

---

## Gap Classification and Prioritization

### Critical Gaps (Blocks Production Runs) - Priority P0

| # | Gap | Blocks | Effort | Dependencies |
|---|-----|--------|--------|--------------|
| 1 | MEGNO Chaos Indicator | Tier 1 chaos maps | 1 week | Variational equations (✅) |
| 2 | FLI Chaos Indicator | Resonance identification | 1 week | Variational equations (✅) |
| 3 | Adaptive Symplectic Integrator | Tier 2 gold standard | 2 weeks | Sundman (✅), RATTLE (✅) |
| 4 | Shadow Hamiltonian Analysis | Tier 2 validation | 1.5 weeks | Integrators (✅) |
| 5 | Production Pipeline | Tier 1/2 orchestration | 1.5 weeks | All above |

**Total P0 Effort**: 7 weeks

### Quality Gaps (At Risk) - Priority P1

| # | Gap | Impact | Effort | Dependencies |
|---|-----|--------|--------|--------------|
| 6 | Sobol Sequences | Non-optimal sampling | 0.5 weeks | None |
| 7 | Time Reversibility Tests | Cannot verify 10⁻²⁰ accuracy | 0.5 weeks | Integrators (✅) |
| 8 | Poincaré Sections | Cannot reproduce literature | 1 week | None |
| 9 | Adaptive Sampling | Cannot refine separatrices | 1 week | MEGNO/FLI |
| 10 | Known Periodic Orbit Library | Missing reference orbits | 1.5 weeks | Literature + integrators |

**Total P1 Effort**: 4.5 weeks

### Convenience Gaps (Nice-to-Have) - Priority P2

| # | Gap | Impact | Effort | Dependencies |
|---|-----|--------|--------|--------------|
| 11 | Parquet Export Completion | ML pipeline convenience | 0.5 weeks | HDF5 (✅) |
| 12 | Dense Output | Close encounter capture | 1 week | Integrators |
| 13 | Regularization Switching | Smooth coordinate transitions | 1 week | KS/LC (✅) |

**Total P2 Effort**: 2.5 weeks

---

## Phase 1: Critical Chaos Indicators (Weeks 1-2)

### Task 1.1: MEGNO Implementation

**Objective**: Implement Mean Exponential Growth of Nearby Orbits to distinguish regular vs chaotic motion.

**Mathematical Background**:
```
MEGNO(t) = 2/t ∫₀ᵗ δ(s)/||δ(s)|| · d||δ(s)||/ds · s ds

where δ(t) is the tangent vector evolving via variational equations
```

**Implementation Strategy**:

1. **Create Module Structure** (0.5 days)
   ```python
   # src/python/validation/chaos_indicators.py
   - MEGNOIndicator class
   - FLIIndicator class
   - ChaosAnalyzer orchestrator
   ```

2. **MEGNO Core Algorithm** (1.5 days)
   - Extend variational equation integrator (`variational_equations.py`)
   - Implement running MEGNO accumulation
   - Track deviation vector normalization
   - Compute time-weighted integral

3. **Integration with Existing Integrators** (1 day)
   - Hook into IAS15 integrator
   - Hook into Yoshida8 integrator
   - Add MEGNO computation to integration callbacks

4. **Classification Criteria** (0.5 days)
   ```
   MEGNO ≈ 2.0: Regular/quasi-periodic motion
   MEGNO > 2.0: Chaotic motion (grows logarithmically with time)
   ```

5. **Testing and Validation** (1 day)
   - Known chaotic orbit (L1 Lyapunov unstable)
   - Known regular orbit (stable prograde)
   - Compare against REBOUND's built-in MEGNO
   - Verify convergence behavior

**Deliverables**:
- ✅ `src/python/validation/chaos_indicators.py` (MEGNO class)
- ✅ Test suite with 10+ test cases
- ✅ Example notebook demonstrating usage
- ✅ Performance benchmark (< 30% overhead vs pure integration)

**Success Criteria**:
- MEGNO values within 1% of REBOUND reference for test cases
- Correct classification of 10 known regular orbits (MEGNO < 2.1)
- Correct classification of 10 known chaotic orbits (MEGNO > 3.0)

---

### Task 1.2: FLI Implementation

**Objective**: Implement Fast Lyapunov Indicator for rapid resonance structure identification.

**Mathematical Background**:
```
FLI(t) = log₁₀(||δ(t)||)

where δ(t) evolves via variational equations with ||δ(0)|| = 1
```

**Implementation Strategy**:

1. **FLI Core Algorithm** (1 day)
   - Reuse variational equation infrastructure from MEGNO
   - Track maximum deviation vector norm
   - Compute logarithmic growth rate

2. **Resonance Detection Heuristics** (1 day)
   - FLI maps on parameter space slices
   - Color-coding by FLI value
   - Identify sharp transitions (separatrices)

3. **Integration with Parameter Sampling** (0.5 days)
   - Hook into `parameter_sampling.py`
   - Generate FLI maps for pilot runs
   - Export results for adaptive refinement

4. **Comparison with MEGNO** (0.5 days)
   - Verify FLI and MEGNO agree on chaos classification
   - Document computational efficiency difference
   - Create comparison visualization

5. **Testing and Validation** (1 day)
   - Reproduce Lega et al. (2016) FLI maps
   - Verify resonance structure matches literature
   - Test computational performance

**Deliverables**:
- ✅ FLI indicator class in `chaos_indicators.py`
- ✅ FLI map generation utilities
- ✅ Comparison with MEGNO validation
- ✅ Resonance identification examples

**Success Criteria**:
- FLI computation < 10% overhead vs pure integration
- Resonance structures match literature (Contopoulos et al.)
- FLI < 2 for regular motion, FLI > 4 for chaotic (for t = 10⁴ periods)

---

## Phase 2: Adaptive Symplectic Integration (Weeks 3-4)

### Task 2.1: Sundman-Transformed Symplectic Integrator

**Objective**: Implement adaptive symplectic integrator using Sundman time regularization to achieve Tier 2 "gold standard" precision.

**Mathematical Background**:
```
Sundman transformation: dt/ds = Ω(q)
where Ω(q) is time dilation factor (e.g., Ω = r for single body, Ω = Σᵢⱼ rᵢⱼ for N-body)

Transformed Hamiltonian: K(q,p,s) = Ω(q)·H(q,p)
Still symplectic in (q,p,s) coordinates with appropriate integrator
```

**Implementation Strategy**:

1. **Review Existing Infrastructure** (0.5 days)
   - Audit `sundman.py` - already implements time dilation strategies
   - Audit `time_regularized_dynamics.py` - framework exists
   - Identify what needs completion vs what needs integration

2. **Complete Time-Regularized Dynamics** (2 days)
   - Finish `threebody_time_regularized.py` implementation
   - Implement extended phase space Hamiltonian K = Ω·H
   - Add time synchronization tracking (s → t mapping)
   - Implement constraint preservation (energy-like invariant)

3. **Adaptive Timestep Strategy** (1.5 days)
   - Variable ds selection based on local error estimate
   - Sundman factor Ω(q) provides natural adaptivity
   - Implement step size control algorithm
   - Safety limiters (ds_min, ds_max)

4. **Symplectic Composition Method** (2 days)
   - Use Yoshida8 or similar as base composition
   - Apply to transformed Hamiltonian K
   - Verify symplecticity preservation
   - Test on Kepler problem (analytical solution)

5. **Integration Pipeline** (1.5 days)
   - Create unified interface matching IAS15/Yoshida8 API
   - Add to integrator registry
   - Implement in `AdaptiveSymplecticIntegrator` class
   - Hook into trajectory integration pipeline

6. **Close Encounter Handling** (1 day)
   - Automatic Sundman factor increase near collisions
   - Smooth transition to regularized coordinates if needed
   - Verify no precision loss at singularities

7. **High-Precision Integration** (1.5 days)
   - Integrate with QD library (dd_real support)
   - Test Tier 2 precision target (ΔC < 10⁻²⁵)
   - Benchmark performance vs IAS15

8. **Testing and Validation** (2 days)
   - Kepler problem: verify energy conservation < 10⁻²⁸
   - CR3BP test cases: verify Jacobi drift < 10⁻²⁵
   - Long-term stability test (10⁶ periods)
   - Comparison with IAS15 (accuracy vs cost)

**Deliverables**:
- ✅ `src/python/integrators/adaptive_symplectic.py`
- ✅ Completed `threebody_time_regularized.py`
- ✅ High-precision (dd_real) integration support
- ✅ Test suite with Tier 2 precision validation
- ✅ Performance benchmark report

**Success Criteria**:
- Jacobi constant drift ΔC < 10⁻²⁵ for 10⁴ periods (Tier 2 target)
- Symplecticity verified via phase space volume conservation
- Handles close encounters without precision loss
- Performance within 5x of IAS15 for equivalent accuracy

**Fallback Plan**:
If implementation proves intractable within timeline:
- Document theoretical approach and partial implementation
- Use IAS15 with tighter tolerances for Tier 2 (ε = 10⁻¹⁶)
- Acknowledge non-symplecticity but verify backward error analysis
- Revisit in WP1.5 extension if needed

---

## Phase 3: Validation Framework (Week 5)

### Task 3.1: Shadow Hamiltonian Analysis

**Objective**: Implement backward error analysis to verify numerical trajectory is exact solution of nearby Hamiltonian.

**Mathematical Background**:
```
Theorem (Backward Error Analysis):
For symplectic integrator with step h, numerical trajectory is exact solution of
H̃ = H + h²·H₂ + h⁴·H₄ + ...

Goal: Compute and verify shadow Hamiltonian H̃ is bounded and drift-free
```

**Implementation Strategy**:

1. **Literature Review and Method Selection** (1 day)
   - Review Hairer, Lubich, Wanner (2006) Chapter IX
   - Select practical shadow Hamiltonian computation method
   - Decide on order of approximation (h² or h⁴)

2. **Shadow Hamiltonian Computation** (2 days)
   - Implement H₂ term (second-order correction)
   - Use finite difference or automatic differentiation
   - Compute along numerical trajectory
   - Track temporal evolution

3. **Drift Analysis** (1 day)
   - Compute shadow Hamiltonian at all timesteps
   - Measure secular drift (linear regression)
   - Compare to original Hamiltonian drift
   - Verify bounded behavior

4. **Tier 2 Validation** (1.5 days)
   - Apply to subset of chaotic orbits (most stringent test)
   - Verify shadow H̃ drift < 10⁻²⁵ for Tier 2 orbits
   - Document results in validation report
   - Create visualization utilities

5. **Testing and Documentation** (1 day)
   - Test on known integrable systems
   - Verify theoretical scaling (h² for 2nd order, h⁴ for 4th order)
   - Create example notebook
   - Write technical documentation

**Deliverables**:
- ✅ `src/python/validation/shadow_hamiltonian.py`
- ✅ Backward error analysis for Tier 2 subset
- ✅ Validation report with drift statistics
- ✅ Example notebook with visualizations

**Success Criteria**:
- Shadow Hamiltonian drift < 10⁻²⁵ for Tier 2 orbits (10⁴ periods)
- H̃ values bounded (no secular growth)
- Method scales correctly with timestep (h² or h⁴)
- Successfully applied to 100+ Tier 2 orbits

**Complexity Assessment**: **Medium-High**
- Requires careful implementation of Hamiltonian derivatives
- Numerical stability critical for high-order corrections
- May require symbolic computation for H₂ term

---

### Task 3.2: Time Reversibility Tests

**Objective**: Implement forward-backward integration test to verify 10⁻²⁰ accuracy for Tier 2.

**Implementation Strategy**:

1. **Test Framework** (0.5 days)
   ```python
   # src/python/validation/time_reversibility.py
   class TimeReversibilityTest:
       def run_test(state0, integrator, t_forward, tolerance):
           # Integrate forward
           state_forward = integrator.integrate(state0, t_forward)
           # Negate velocities
           state_reversed = negate_velocities(state_forward)
           # Integrate backward
           state_final = integrator.integrate(state_reversed, t_forward)
           # Compute error
           rms_error = compute_rms_position_error(state0, state_final)
           return rms_error < tolerance
   ```

2. **Integration with Test Suite** (0.5 days)
   - Add to `tests/validation/test_reversibility.py`
   - Test all integrators (IAS15, Yoshida8, AdaptiveSymplectic)
   - Create pytest fixtures for standard test cases

3. **Tier 2 Validation** (1 day)
   - Run on subset of Tier 2 orbits (100 orbits)
   - Target: RMS error < 10⁻²⁰
   - Document pass/fail statistics
   - Investigate failures (if any)

4. **Visualization and Reporting** (0.5 days)
   - Histogram of RMS errors
   - Comparison across integrators
   - Correlation with orbit type (regular vs chaotic)

**Deliverables**:
- ✅ `src/python/validation/time_reversibility.py`
- ✅ Test suite with 10+ test cases
- ✅ Tier 2 validation report
- ✅ Visualization notebook

**Success Criteria**:
- RMS error < 10⁻²⁰ for Tier 2 orbits with adaptive symplectic
- RMS error < 10⁻¹⁴ for Tier 1 orbits with IAS15
- 95th percentile meets targets
- Failures (if any) understood and documented

---

## Phase 4: Production Pipeline (Week 6)

### Task 4.1: Production Orchestration

**Objective**: Implement Dask/Snakemake pipeline for parallel execution of 10⁵ Tier 1 + 10⁴ Tier 2 orbits.

**Implementation Strategy**:

1. **Select Orchestration Framework** (0.5 days)
   - **Option A**: Dask for pure Python workflow
   - **Option B**: Snakemake for reproducible research
   - **Decision criteria**: HPC compatibility, resumability, logging
   - **Recommendation**: Snakemake (better for reproducibility)

2. **Snakemake Pipeline Structure** (1.5 days)
   ```python
   # Snakefile
   rule all:
       input:
           "data/tier1/complete.flag",
           "data/tier2/complete.flag",
           "data/parquet/tier1.parquet",
           "data/parquet/tier2.parquet"

   rule generate_tier1_parameters:
       output: "data/tier1/parameters.h5"
       run: generate_sobol_samples(n=100000, mu_range, C_range)

   rule integrate_tier1_orbit:
       input: "data/tier1/parameters.h5"
       output: "data/tier1/orbit_{mu}_{C}_{ic}.h5"
       run: integrate_orbit_with_chaos(params, integrator="IAS15")

   rule aggregate_tier1:
       input: expand("data/tier1/orbit_{orbit_id}.h5", orbit_id=ORBIT_IDS)
       output: "data/tier1/complete.flag"

   rule select_tier2_subset:
       input: "data/tier1/complete.flag"
       output: "data/tier2/parameters.h5"
       run: select_dynamically_interesting(tier1_data, n=10000)

   rule integrate_tier2_orbit:
       input: "data/tier2/parameters.h5"
       output: "data/tier2/orbit_{orbit_id}.h5"
       run: integrate_orbit_hp(params, integrator="AdaptiveSymplectic")

   rule export_parquet:
       input: "data/tier{tier}/complete.flag"
       output: "data/parquet/tier{tier}.parquet"
       run: convert_hdf5_to_parquet(input)
   ```

3. **Parallel Execution Configuration** (0.5 days)
   - Dask cluster setup for local development
   - SLURM integration for HPC submission
   - Resource allocation (CPU, memory per orbit)
   - Checkpoint/restart capability

4. **Integration Wrapper Functions** (1 day)
   ```python
   # src/python/pipeline/integration_tasks.py
   def integrate_orbit_with_chaos(params, integrator_name, precision="double"):
       """
       Integrate single orbit with MEGNO and FLI computation.
       Returns: state trajectory, MEGNO(t), FLI(t), metadata
       """

   def integrate_orbit_hp(params, integrator_name="AdaptiveSymplectic"):
       """
       Integrate single orbit in double-double precision.
       Returns: high-precision trajectory, validation metrics
       """
   ```

5. **Data Management** (1 day)
   - HDF5 hierarchical structure: `/mu_{i}/C_{j}/orbit_{k}/`
   - Metadata tracking: integration time, precision achieved
   - Checkpointing for long runs
   - Cleanup utilities

6. **Logging and Monitoring** (0.5 days)
   - Progress tracking (completed orbits / total)
   - Error logging (failed integrations)
   - Performance metrics (wall time per orbit)
   - Resource utilization monitoring

7. **Testing and Dry Runs** (1 day)
   - Mini pipeline: 100 Tier 1 + 10 Tier 2 orbits
   - Verify checkpoint/restart works
   - Test on local machine + HPC cluster
   - Benchmark scaling (1 CPU, 4 CPU, 16 CPU, 64 CPU)

**Deliverables**:
- ✅ `Snakefile` - Complete pipeline definition
- ✅ `src/python/pipeline/` - Integration and orchestration utilities
- ✅ `config/pipeline_config.yaml` - Parameter specifications
- ✅ `docs/pipeline_usage.md` - User documentation
- ✅ Dry run validation report

**Success Criteria**:
- Successfully completes 100-orbit dry run
- Checkpoint/restart works correctly
- Scales linearly up to 64 cores
- Failed orbit handling graceful (logged but doesn't crash pipeline)
- Resource usage within HPC limits

---

## Phase 5: Quality Improvements (Weeks 7-8)

### Task 5.1: Sobol Sequence Sampling

**Objective**: Replace LHS with Sobol sequences for low-discrepancy parameter space coverage.

**Implementation**: (0.5 weeks)

```python
# src/python/ml/parameter_sampling.py

from scipy.stats import qmc

def generate_sobol_samples(n_samples, param_ranges):
    """
    Generate Sobol low-discrepancy sequence for parameter space.

    Parameters:
    -----------
    n_samples : int
        Number of samples (should be power of 2 for optimal coverage)
    param_ranges : dict
        {"mu": (mu_min, mu_max, "log"),
         "C": (C_min, C_max, "linear"),
         ...}

    Returns:
    --------
    samples : np.ndarray, shape (n_samples, n_params)
    """
    n_params = len(param_ranges)
    sampler = qmc.Sobol(d=n_params, scramble=True)
    samples_unit = sampler.random(n_samples)

    # Transform to actual ranges (log-uniform for mu, linear for others)
    samples = transform_to_ranges(samples_unit, param_ranges)

    return samples
```

**Testing**:
- Compare Sobol vs LHS coverage using discrepancy metrics
- Visualize 2D projections (mu vs C)
- Verify low-discrepancy properties

**Success Criteria**:
- Star discrepancy < 10⁻³ for 10⁵ samples
- Better coverage than LHS in high-dimensional space

---

### Task 5.2: Poincaré Section Utilities

**Objective**: Implement standard Poincaré sections for validation and literature comparison.

**Implementation**: (1 week)

```python
# src/python/utils/poincare.py

class PoincareSection:
    """
    Compute Poincaré section crossings for CR3BP.

    Standard sections:
    - y = 0, vy > 0 (x-vx section)
    - x = 1-mu (Lagrange point section)
    - z = 0, vz > 0 (equatorial section)
    """

    def __init__(self, section_type="y_zero_up"):
        self.section_type = section_type

    def detect_crossings(self, trajectory):
        """Find all Poincaré section crossings."""
        crossings = []
        for i in range(len(trajectory)-1):
            if self._crosses_section(trajectory[i], trajectory[i+1]):
                crossing_state = self._interpolate_crossing(
                    trajectory[i], trajectory[i+1]
                )
                crossings.append(crossing_state)
        return crossings
```

**Validation**:
- Reproduce standard Poincaré sections from literature
- Compare with Contopoulos et al. classical results
- Verify section structure for known orbit families

**Success Criteria**:
- Visual match with literature Poincaré sections
- Correct identification of stable/unstable manifolds
- Periodic orbit returns match expected period

---

### Task 5.3: Adaptive Sampling Strategy

**Objective**: Implement dynamically-informed parameter refinement near separatrices and resonances.

**Implementation**: (1 week)

```python
# src/python/pipeline/adaptive_sampling.py

def adaptive_refinement_step(pilot_results, refinement_factor=2):
    """
    Refine sampling in regions of high FLI/MEGNO gradients.

    Strategy:
    1. Compute FLI/MEGNO gradient on parameter space grid
    2. Identify high-gradient regions (separatrices, resonances)
    3. Add new samples in these regions
    4. Return combined parameter set
    """
    # Compute gradients
    fli_gradient = compute_parameter_gradient(pilot_results["FLI"])

    # Identify refinement regions (top 10% gradient magnitude)
    threshold = np.percentile(fli_gradient, 90)
    refine_mask = fli_gradient > threshold

    # Generate additional samples in refinement regions
    additional_samples = generate_local_samples(
        pilot_results[refine_mask],
        n_per_region=refinement_factor
    )

    return additional_samples
```

**Workflow**:
1. Pilot run: 5000 orbits with Sobol sampling
2. Compute FLI maps
3. Identify resonance structures
4. Adaptive refinement: 2x sampling density in resonant regions
5. Final run: 100,000 orbits total

**Success Criteria**:
- Resonance structures well-sampled (>100 points per resonance)
- Separatrices clearly resolved
- Reduced total samples for equivalent coverage (vs uniform sampling)

---

### Task 5.4: Known Periodic Orbit Library

**Objective**: Catalog and integrate known periodic orbit families (Lyapunov, Halo, etc.) for validation.

**Implementation**: (1.5 weeks)

1. **Literature Survey** (0.5 weeks)
   - Compile list of classical families (Earth-Moon, Sun-Jupiter)
   - Extract initial conditions from papers
   - Document stability properties

2. **Orbit Generation** (0.5 weeks)
   ```python
   # src/python/orbits/periodic_families.py

   class PeriodicOrbitFamily:
       """Generate and store periodic orbit families."""

       def generate_lyapunov_family(mu, C_range, n_orbits=100):
           """Generate Lyapunov family around L1/L2."""

       def generate_halo_family(mu, amplitude_range, n_orbits=100):
           """Generate 3D Halo family around L1/L2."""
   ```

3. **Validation Suite** (0.5 weeks)
   - Verify periodicity (return map error < 10⁻¹²)
   - Verify stability indices match literature
   - Integration test (10⁴ periods, verify Jacobi conservation)

**Deliverables**:
- Database of 500+ known periodic orbits
- Automated generation utilities
- Validation test suite
- Literature reference documentation

**Success Criteria**:
- 100% of cataloged orbits verify as periodic (< 10⁻¹² error)
- Stability indices match literature values
- Coverage of all major families (Lyapunov, Halo, Vertical, Axial)

---

### Task 5.5: Parquet Export Completion

**Objective**: Complete Parquet export pipeline for ML-ready data format.

**Implementation**: (0.5 weeks)

```python
# src/python/ml/parquet_exporter.py

import pyarrow as pa
import pyarrow.parquet as pq

def export_to_parquet(hdf5_path, parquet_path, chunk_size=10000):
    """
    Convert HDF5 trajectory archive to flattened Parquet format.

    Schema:
    - orbit_id: int
    - mu: float64
    - C: float64
    - t: float64
    - x, y, z, vx, vy, vz: float32 (positions and velocities)
    - x_inertial, y_inertial, ...: float32 (inertial frame)
    - MEGNO: float32
    - FLI: float32
    - chaos_class: category ("regular", "chaotic")
    """

    schema = pa.schema([
        ("orbit_id", pa.int64()),
        ("mu", pa.float64()),
        ("C", pa.float64()),
        ("t", pa.float64()),
        ("x", pa.float32()),
        # ... (all state variables)
        ("MEGNO", pa.float32()),
        ("FLI", pa.float32()),
        ("chaos_class", pa.dictionary(pa.int8(), pa.string()))
    ])

    with pq.ParquetWriter(parquet_path, schema) as writer:
        for chunk in read_hdf5_chunks(hdf5_path, chunk_size):
            table = pa.Table.from_pandas(chunk, schema=schema)
            writer.write_table(table)
```

**Features**:
- Columnar storage for efficient ML I/O
- Compression (snappy or gzip)
- Partitioning by mu and C for query efficiency
- Cloud-optimized format

**Success Criteria**:
- Successfully converts full Tier 1 dataset (10⁵ orbits)
- File size < 50% of HDF5 (due to compression)
- Load time in PyTorch DataLoader < 10s for training batch

---

### Task 5.6: Dense Output Implementation

**Objective**: Implement adaptive interpolation to capture close encounter dynamics without excessive storage.

**Implementation**: (1 week)

```python
# src/python/integrators/dense_output.py

class DenseOutputIntegrator:
    """
    Wrapper around integrators to provide interpolated dense output.

    Strategy:
    - Normal timesteps: dt = 0.1 (sparse)
    - Close encounter detected: dt = 0.001 (dense)
    - Trigger: distance to primary < r_critical
    """

    def integrate_with_dense_output(self, state0, t_final, r_critical=0.01):
        """
        Integrate with adaptive output density.

        Returns:
        --------
        times: array of output times (variable density)
        states: corresponding states
        is_dense: boolean mask (True = dense output region)
        """
```

**Trigger Criteria**:
- Distance to primary < r_critical (e.g., 0.01 normalized units)
- High acceleration magnitude (> 100 × background)
- KS regularization automatically triggered

**Success Criteria**:
- Captures close encounter details (periastron to < 10⁻⁴ resolution)
- Storage increase < 2x vs fixed stride
- No missed close encounters in validation set

---

### Task 5.7: Regularization Switching

**Objective**: Implement smooth automatic switching between coordinate systems.

**Implementation**: (1 week)

```python
# src/python/regularization/automatic_switching.py

class AdaptiveRegularizationIntegrator:
    """
    Automatically switch between Cartesian and regularized coordinates.

    Switching criteria (Mikkola's approach):
    - Distance to primary < r_switch_on → activate KS/LC
    - Distance to primary > r_switch_off → deactivate
    - Hysteresis: r_switch_off = 2 × r_switch_on
    """

    def integrate_with_switching(self, state0, t_final):
        state = state0
        is_regularized = False

        while t < t_final:
            r = compute_distance_to_primary(state)

            if not is_regularized and r < r_switch_on:
                state = transform_to_ks(state)
                is_regularized = True

            if is_regularized and r > r_switch_off:
                state = transform_from_ks(state)
                is_regularized = False

            # Integrate one step in current coordinates
            state = integrator.step(state, dt)
```

**Smooth Transition**:
- Blending function for forces near transition
- Verify energy conservation at switch points
- Test continuity of trajectory

**Success Criteria**:
- Energy error at switch < 10⁻¹⁴
- Position discontinuity < 10⁻¹²
- Handles 100 switches without precision degradation

---

## Phase 6: Testing and Validation (Week 8+)

### Task 6.1: Integration Testing

**Comprehensive Test Suite**:

1. **Unit Tests**
   - Each module has >80% code coverage
   - All public APIs tested

2. **Integration Tests**
   - End-to-end pipeline (parameter generation → integration → export)
   - Verify data integrity (HDF5 → Parquet → ML ingestion)

3. **Validation Tests**
   - 100 Tier 1 orbits meet ΔC < 10⁻¹⁴
   - 100 Tier 2 orbits meet ΔC < 10⁻²⁵
   - MEGNO/FLI classification matches manual inspection
   - Shadow Hamiltonian bounded for all test cases
   - Time reversibility < 10⁻²⁰ for Tier 2

4. **Regression Tests**
   - Reproduce known results from literature
   - Compare with REBOUND reference implementations
   - Verify precision targets maintained across updates

**Deliverables**:
- ✅ Comprehensive test suite (>500 tests)
- ✅ CI/CD integration (GitHub Actions)
- ✅ Test coverage report (>80% target)
- ✅ Validation report documenting all criteria

---

### Task 6.2: Documentation

**Required Documentation**:

1. **User Guide**
   - Installation instructions
   - Quick start tutorial
   - Pipeline usage examples
   - FAQ

2. **API Reference**
   - Auto-generated from docstrings (Sphinx)
   - Type annotations
   - Usage examples

3. **Technical Documentation**
   - Mathematical background
   - Implementation details
   - Validation methodology
   - Performance benchmarks

4. **Data Documentation**
   - Dataset schema (HDF5 and Parquet)
   - Metadata descriptions
   - Usage examples for ML
   - Citation information

**Deliverables**:
- ✅ Complete documentation website (ReadTheDocs or GitHub Pages)
- ✅ Example notebooks (10+ Jupyter notebooks)
- ✅ Data descriptor paper draft

---

## Implementation Timeline

### Gantt Chart Overview

```
Week 1: ████ MEGNO Implementation
Week 2: ████ FLI Implementation
Week 3: ████ Adaptive Symplectic (Part 1)
Week 4: ████ Adaptive Symplectic (Part 2)
Week 5: ████ Shadow Hamiltonian + Time Reversibility
Week 6: ████ Production Pipeline
Week 7: ███░ Sobol + Poincaré + Adaptive Sampling
Week 8: ███░ Periodic Orbits + Parquet + Dense Output
Week 9: ██░░ Testing and Validation
Week 10: █░░░ Documentation and Release
```

### Critical Path

```
MEGNO → FLI → Adaptive Symplectic → Shadow Hamiltonian → Production Pipeline
  ↓       ↓                                                      ↓
  └───────┴────────────────────────────────────────────────→ Tier 1 Run
                                                                  ↓
                                                             Tier 2 Run
```

**Critical Dependencies**:
- Production Pipeline blocked on MEGNO/FLI + Adaptive Symplectic
- Tier 2 runs blocked on Adaptive Symplectic + Shadow Hamiltonian
- Adaptive Sampling blocked on FLI pilot runs

---

## Resource Requirements

### Computational Resources

**Development/Testing** (Weeks 1-8):
- Local workstation: 8-16 cores, 32 GB RAM
- Development cost: Minimal (personal hardware)

**Pilot Runs** (Week 6):
- 5,000 orbits × 30 min/orbit = 2,500 CPU-hours
- Small HPC allocation or cloud instance

**Production Runs** (Week 9+):
- **Tier 1**: 100,000 orbits × 30 min/orbit = 50,000 CPU-hours
- **Tier 2**: 10,000 orbits × 3 hours/orbit = 30,000 CPU-hours
- **Total**: 80,000 CPU-hours ≈ 3,300 CPU-days

**Storage**:
- HDF5: ~500 GB (Tier 1) + ~200 GB (Tier 2) = 700 GB
- Parquet: ~300 GB (compressed)
- Total: ~1 TB

### Human Resources

**Primary Developer** (1 FTE, 8-10 weeks):
- Implement critical components (MEGNO, FLI, Adaptive Symplectic)
- Validation framework
- Pipeline orchestration

**Optional Support**:
- Scientific Computing Consultant (0.1 FTE): HPC optimization
- Documentation Specialist (0.1 FTE): User guide and tutorials

---

## Risk Assessment and Mitigation

### High-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Adaptive Symplectic complexity exceeds timeline | Medium | High | Fallback to IAS15 with tight tolerances |
| Shadow Hamiltonian implementation issues | Medium | Medium | Implement 2nd-order only (skip h⁴ term) |
| HPC resource availability | Low | High | Secure allocation early, have cloud backup |
| dd_real performance bottleneck | Low | Medium | Profile and optimize critical loops |

### Medium-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Sobol sampling not significantly better than LHS | Medium | Low | Document comparison, use best available |
| Known periodic orbit generation difficult | Medium | Low | Use literature ICs directly vs generation |
| Parquet export memory issues | Low | Low | Implement streaming/chunked processing |

### Low-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Testing reveals minor bugs | High | Low | Allocate buffer time for bug fixes |
| Documentation takes longer than expected | Medium | Low | Prioritize critical sections first |
| Time reversibility tests fail for some orbits | Low | Low | Investigate and document failure modes |

---

## Success Metrics

### Quantitative Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Tier 1 Precision** | ΔC < 10⁻¹⁴ | 95th percentile of Jacobi drift |
| **Tier 2 Precision** | ΔC < 10⁻²⁵ | 95th percentile of Jacobi drift |
| **MEGNO Accuracy** | Within 1% of reference | Comparison with REBOUND |
| **Time Reversibility** | RMS error < 10⁻²⁰ | Forward-backward integration |
| **Shadow H Drift** | < 10⁻²⁵ (Tier 2) | Linear regression of H̃(t) |
| **Pipeline Throughput** | >1000 orbits/day | Wall-clock production runs |
| **Test Coverage** | >80% | pytest-cov report |
| **Documentation** | 100% API coverage | Sphinx build verification |

### Qualitative Targets

- ✅ Reproducibility: Independent researcher can regenerate 1% of data bit-for-bit
- ✅ Usability: ML practitioner can load Parquet data in <10 lines of code
- ✅ Validation: All WP1 assessment criteria met (see Section 4 of WP1 spec)
- ✅ Publication: Data descriptor paper accepted to peer-reviewed journal

---

## Deliverables Checklist

### Code Deliverables

- [ ] `src/python/validation/chaos_indicators.py` - MEGNO + FLI
- [ ] `src/python/integrators/adaptive_symplectic.py` - Adaptive symplectic integrator
- [ ] `src/python/validation/shadow_hamiltonian.py` - Backward error analysis
- [ ] `src/python/validation/time_reversibility.py` - Reversibility tests
- [ ] `src/python/pipeline/` - Production orchestration
- [ ] `src/python/ml/parameter_sampling.py` - Sobol sequences
- [ ] `src/python/utils/poincare.py` - Poincaré sections
- [ ] `src/python/pipeline/adaptive_sampling.py` - Adaptive refinement
- [ ] `src/python/orbits/periodic_families.py` - Periodic orbit catalog
- [ ] `src/python/ml/parquet_exporter.py` - Parquet export
- [ ] `src/python/integrators/dense_output.py` - Dense output
- [ ] `src/python/regularization/automatic_switching.py` - Regularization switching
- [ ] `Snakefile` - Pipeline definition

### Data Deliverables

- [ ] Tier 1 Dataset (100,000 orbits, HDF5 + Parquet)
- [ ] Tier 2 Dataset (10,000 orbits, HDF5 + Parquet)
- [ ] Known Periodic Orbit Library (500+ orbits)
- [ ] Validation Report (precision statistics, shadow H analysis)
- [ ] Metadata and Schema Documentation

### Documentation Deliverables

- [ ] User Guide (installation, quick start, tutorials)
- [ ] API Reference (Sphinx-generated)
- [ ] Technical Documentation (math background, validation)
- [ ] Pipeline Usage Guide (Snakemake workflow)
- [ ] Data Descriptor Paper (draft for submission)
- [ ] Example Jupyter Notebooks (10+)

### Testing Deliverables

- [ ] Test Suite (>500 tests, >80% coverage)
- [ ] CI/CD Configuration (GitHub Actions)
- [ ] Validation Test Results
- [ ] Performance Benchmarks

---

## Post-Implementation Review Criteria

After completion, assess success via:

1. **Precision Verification**
   - Run 100 random Tier 1 orbits → verify ΔC < 10⁻¹⁴
   - Run 100 random Tier 2 orbits → verify ΔC < 10⁻²⁵
   - Generate precision histogram → verify 95th percentile meets targets

2. **Chaos Indicator Validation**
   - Reproduce literature FLI/MEGNO maps
   - Verify classification accuracy on known orbits
   - Compare with REBOUND's chaos detection

3. **Production Run**
   - Successfully complete full Tier 1 run (100,000 orbits)
   - Successfully complete full Tier 2 run (10,000 orbits)
   - Verify data integrity (no corrupted files)
   - Export to Parquet successfully

4. **External Validation**
   - Independent researcher attempts data regeneration
   - ML practitioner tests data loading and training
   - Peer review of technical approach

5. **Documentation Review**
   - Technical reviewer assesses mathematical correctness
   - User tester follows tutorials successfully
   - API documentation completeness check

---

## Conclusion

This implementation plan provides a comprehensive roadmap to complete WP1 from **60% to 100%** over **6-8 weeks**. The plan prioritizes critical gaps that block production runs, while also addressing quality improvements and convenience features.

**Key Strengths**:
- ✅ Excellent existing foundations (QD library, integrators, regularization)
- ✅ Variational equation infrastructure ready for chaos indicators
- ✅ Clear success criteria and validation framework
- ✅ Realistic timeline with contingency plans

**Key Risks**:
- ⚠️ Adaptive symplectic integrator complexity (mitigation: IAS15 fallback)
- ⚠️ Shadow Hamiltonian implementation effort (mitigation: 2nd-order only)
- ⚠️ HPC resource availability (mitigation: secure early, cloud backup)

**Next Steps**:
1. Review and approve this plan
2. Secure HPC resource allocation
3. Begin Phase 1: MEGNO implementation (Week 1)
4. Establish weekly progress reviews
5. Maintain agile flexibility for scope adjustments

**Estimated Completion Date**: 8 weeks from start
**Confidence Level**: **High** (85%) - based on existing infrastructure quality

---

**Document Status**: ✅ READY FOR IMPLEMENTATION
**Last Updated**: November 22, 2025
**Author**: WP1 Implementation Team
**Version**: 1.0
