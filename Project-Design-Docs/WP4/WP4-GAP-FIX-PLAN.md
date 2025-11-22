# Work Package 4: Gap Fix Implementation Plan
## Comprehensive Plan to Address WP4.1 and WP4.3 Gaps

**Created**: 2025-11-22
**Status**: Ready for Implementation
**Priority**: High - Required for Publication Readiness

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Gap Analysis](#gap-analysis)
3. [WP 4.1 Fix Plan: Consolidation and Completion](#wp-41-fix-plan)
4. [WP 4.3 Implementation Plan: Build from Scratch](#wp-43-implementation-plan)
5. [Implementation Timeline](#implementation-timeline)
6. [Success Metrics](#success-metrics)
7. [Testing Strategy](#testing-strategy)
8. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

### Current Status

Based on comprehensive analysis of the codebase and design documents:

- **WP 4.1 (Analytical Vetting)**: 🟡 **60% Complete** - Functional but fragmented
- **WP 4.2 (Morales-Ramis)**: ✅ **100% Complete** - Excellent implementation
- **WP 4.3 (Numerical Robustness)**: ❌ **0% Complete** - Not implemented

### Critical Findings

**WP 4.1 Issue**: The mathematical operations ARE implemented and working, but scattered across `analysis/`, `symbolic/`, and `lifts/` packages. The validation package lacks the unified API structure specified in the design documents.

**WP 4.3 Issue**: Completely missing. Without this, we cannot:
- Demonstrate universal conservation across parameter space
- Provide statistical certification for publication
- Test robustness in extreme scenarios (collisions, chaos)
- Generate publication-quality validation reports

### This Plan

This document provides a **step-by-step implementation plan** to:

1. **Consolidate WP 4.1** into unified validation package (5-7 days)
2. **Implement WP 4.3** from scratch (10-12 days)
3. **Integrate and test** complete WP4 pipeline (3-4 days)

**Total Estimated Time**: 18-23 days (3-4 weeks)

---

## Gap Analysis

### WP 4.1: Analytical Vetting - Detailed Gap Analysis

#### What EXISTS and WORKS

| Component | Location | Lines | Status |
|-----------|----------|-------|--------|
| Poisson Brackets (Symbolic) | `symbolic/validation.py` | ~100 | ✅ Working |
| Poisson Brackets (Numerical) | `analysis/independence_test.py` | ~50 | ✅ Working |
| Poisson Brackets (Bundle) | `lifts/extended_symplectic.py` | ~80 | ✅ Working |
| Conservation Verification | `analysis/conservation_verification.py` | ~425 | ✅ Working |
| Independence Testing | `analysis/independence_test.py` | ~150 | ✅ Working |
| Involution Testing | `analysis/independence_test.py` | ~100 | ✅ Working |
| Enhanced Validation | `symbolic/enhanced_validation.py` | ~340 | ✅ Working |

**Total Existing Code**: ~1,245 lines of functional code

#### What is MISSING

| Component | Expected Location | Expected Lines | Gap |
|-----------|------------------|----------------|-----|
| Unified `PoissonBracketComputer` | `validation/poisson_brackets.py` | ~600 | ❌ Missing |
| Unified `ConservationValidator` | `validation/conservation_validator.py` | ~200 | ❌ Missing |
| Unified `InvolutionTester` | `validation/involution_tester.py` | ~250 | ❌ Missing |
| Refactored `IndependenceTester` | `validation/independence_tester.py` | ~300 | ❌ Missing |
| `AnalyticalVetter` Pipeline | `validation/analytical_vetting.py` | ~200 | ❌ Missing |
| Test Suite | `tests/validation/test_poisson_brackets.py` | ~300 | ❌ Missing |
| Test Suite | `tests/validation/test_analytical_vetting.py` | ~400 | ❌ Missing |

**Total Missing Code**: ~2,250 lines

#### The Problem

The existing implementations are:
1. **Fragmented** - Spread across 5+ different modules
2. **Duplicated** - Poisson brackets implemented 3 times independently
3. **Inconsistent APIs** - Different calling conventions and return types
4. **Poorly Discoverable** - No single entry point for analytical vetting
5. **Untested** - No dedicated test suite for WP 4.1 functionality

#### The Solution

**Consolidate and Unify**: Create a clean, unified API in `validation/` package that:
- Wraps existing functionality where possible
- Provides consistent interfaces
- Adds missing orchestration layer
- Includes comprehensive tests

---

### WP 4.3: Numerical Robustness - Complete Gap Analysis

#### What EXISTS

**Nothing.** WP 4.3 is completely unimplemented.

#### Partial Mitigations (Insufficient)

Some basic capabilities exist but are inadequate:

| Component | Location | Coverage | Gap |
|-----------|----------|----------|-----|
| Small ensemble testing | `analysis/conservation_verification.py` | ~5% | No parameter sweep, no HPC scale |
| Multi-scale testing | `symbolic/enhanced_validation.py` | ~5% | Limited timescales, no statistics |
| Long-time stability | `symbolic/enhanced_validation.py` | ~5% | No shadow Hamiltonian analysis |

**Total WP 4.3 Coverage**: ~10% of required functionality

#### What is MISSING (Everything)

| Component | Expected Location | Lines | Priority |
|-----------|------------------|-------|----------|
| `MonteCarloValidator` | `validation/monte_carlo_validator.py` | ~500 | 🔴 Critical |
| `StressTester` | `validation/stress_tester.py` | ~400 | 🔴 Critical |
| `LongTimeValidator` | `validation/long_time_validator.py` | ~350 | 🟡 High |
| `StatisticalReporter` | `validation/statistical_reporter.py` | ~400 | 🟡 High |
| `ParallelExecutor` | `validation/parallel_executor.py` | ~250 | 🟢 Medium |
| Test Suite | `tests/validation/test_monte_carlo.py` | ~300 | 🟡 High |
| Test Suite | `tests/validation/test_stress_testing.py` | ~250 | 🟢 Medium |

**Total Missing Code**: ~2,450 lines

#### Impact of WP 4.3 Gap

**Cannot Publish Without WP 4.3** because we lack:

1. **Statistical Certification**
   - No proof conservation holds across parameter space
   - No confidence intervals or error bounds
   - No success rate quantification

2. **Robustness Evidence**
   - No testing in extreme scenarios (collisions, chaos)
   - No long-time stability analysis (10⁴-10⁶ periods)
   - No comparison to integrator error

3. **Publication Materials**
   - No statistical validation report
   - No error distribution plots
   - No success rate heatmaps
   - No LaTeX tables for manuscript

---

## WP 4.1 Fix Plan

### Strategy: Consolidate and Extend

**Approach**: Don't rewrite from scratch. Instead:
1. Create unified wrapper classes in `validation/` package
2. Leverage existing implementations from `analysis/` and `symbolic/`
3. Add missing orchestration layer
4. Provide consistent API surface

### Phase 1: Core Unification (3 days)

#### Task 1.1: Create `validation/poisson_brackets.py` (1 day)

**Goal**: Unified Poisson bracket computation with symbolic and numerical modes

**Implementation Strategy**:
```python
# Wrap existing implementations:
# - symbolic/validation.py::compute_poisson_bracket_symbolic()
# - analysis/independence_test.py::compute_poisson_bracket()
# - lifts/extended_symplectic.py::poisson_bracket_on_bundle()

class PoissonBracketComputer:
    """Unified Poisson bracket interface."""

    def __init__(self, mode='auto', coordinate_system='canonical'):
        self.mode = mode  # 'symbolic', 'numerical', 'auto'
        self.coordinate_system = coordinate_system

    def compute_bracket(self, f, g, variables=None):
        """Compute {f, g} using best available method."""
        if self.mode == 'symbolic' or self.mode == 'auto':
            # Try symbolic first (wrap existing symbolic implementation)
            try:
                from ..symbolic.validation import compute_poisson_bracket_symbolic
                return self._wrap_symbolic(f, g, variables)
            except Exception as e:
                if self.mode == 'symbolic':
                    raise
                # Fall back to numerical

        # Use numerical (wrap existing numerical implementation)
        from ..analysis.independence_test import compute_poisson_bracket
        return self._wrap_numerical(f, g, variables)
```

**Files to Create**:
- `src/python/validation/poisson_brackets.py` (~600 lines)
  - `PoissonBracketComputer` class
  - `PoissonBracketResult` dataclass
  - `test_conservation()` convenience function
  - Batch evaluation methods

**Deliverables**:
- [ ] Unified Poisson bracket API
- [ ] Wraps all 3 existing implementations
- [ ] Consistent return type (`PoissonBracketResult`)
- [ ] Documentation and examples

---

#### Task 1.2: Create `validation/conservation_validator.py` (1 day)

**Goal**: Batch conservation testing with unified reporting

**Implementation Strategy**:
```python
# Wrap existing conservation_verification.py capabilities

from ..analysis.conservation_verification import (
    verify_conservation_along_trajectory,
    verify_conservation_ensemble
)
from .poisson_brackets import PoissonBracketComputer

class ConservationValidator:
    """Validate conservation for candidates."""

    def __init__(self, hamiltonian, tolerance=1e-12):
        self.hamiltonian = hamiltonian
        self.tolerance = tolerance
        self.bracket_computer = PoissonBracketComputer()

    def validate_candidates(self, candidates):
        """
        Test conservation for list of candidates.

        Two-stage approach:
        1. Symbolic/numerical Poisson bracket test
        2. Trajectory integration test (existing functionality)
        """
        results = {}

        for name, candidate in candidates.items():
            # Stage 1: Bracket test
            bracket_result = self.bracket_computer.compute_bracket(
                candidate, self.hamiltonian
            )

            # Stage 2: Trajectory test (if bracket passed)
            if bracket_result.success:
                trajectory_result = verify_conservation_along_trajectory(
                    candidate, self.hamiltonian
                )
                results[name] = (bracket_result, trajectory_result)
            else:
                results[name] = (bracket_result, None)

        return results
```

**Files to Create**:
- `src/python/validation/conservation_validator.py` (~200 lines)

**Deliverables**:
- [ ] Batch conservation testing
- [ ] Integrates bracket and trajectory tests
- [ ] Unified reporting format
- [ ] Success/failure classification

---

#### Task 1.3: Create `validation/involution_tester.py` (1 day)

**Goal**: Pairwise involution testing for all integral combinations

**Implementation Strategy**:
```python
# Leverage PoissonBracketComputer for pairwise tests

from .poisson_brackets import PoissonBracketComputer
from itertools import combinations

class InvolutionTester:
    """Test mutual involution of integrals."""

    def test_involution(self, integrals):
        """
        Test {I_i, I_j} = 0 for all pairs.

        Returns:
            all_in_involution: bool
            bracket_matrix: dict of pairwise results
        """
        computer = PoissonBracketComputer()
        results = {}

        for (name_i, I_i), (name_j, I_j) in combinations(integrals.items(), 2):
            bracket = computer.compute_bracket(I_i, I_j)
            results[(name_i, name_j)] = bracket

        all_pass = all(r.success for r in results.values())

        return all_pass, results
```

**Files to Create**:
- `src/python/validation/involution_tester.py` (~250 lines)

**Deliverables**:
- [ ] Pairwise bracket testing
- [ ] Involution matrix construction
- [ ] Clear pass/fail reporting
- [ ] Visualization of results

---

### Phase 2: Independence Testing (2 days)

#### Task 2.1: Refactor `validation/independence_tester.py` (2 days)

**Goal**: Move and enhance existing independence test functionality

**Implementation Strategy**:
```python
# Move from analysis/independence_test.py to validation/
# Enhance with better error handling and reporting

class IndependenceTester:
    """Test functional independence via Jacobian rank."""

    def test_independence(self, integrals, variables, n_samples=10000):
        """
        Jacobian rank test on random samples.

        Enhanced from existing implementation with:
        - Better sampling strategies
        - Clearer reporting
        - Consistent API with other validators
        """
        # Use existing compute_jacobian logic
        # Add stratified sampling
        # Add clear success criteria
        pass
```

**Files to Modify/Create**:
- Move functionality from `analysis/independence_test.py`
- Create `src/python/validation/independence_tester.py` (~300 lines)
- Add deprecation warning to old location

**Deliverables**:
- [ ] Unified location in validation package
- [ ] Enhanced sampling strategies
- [ ] Better documentation
- [ ] Consistent API

---

### Phase 3: Orchestration Layer (2 days)

#### Task 3.1: Create `validation/analytical_vetting.py` (2 days)

**Goal**: Complete WP 4.1 pipeline orchestration

**Implementation Strategy**:
```python
from .conservation_validator import ConservationValidator
from .involution_tester import InvolutionTester
from .independence_tester import IndependenceTester

class AnalyticalVetter:
    """
    Complete WP 4.1 pipeline.

    Runs three-stage gauntlet:
    1. Conservation test
    2. Involution test
    3. Independence test
    """

    def __init__(self, hamiltonian, known_integrals, variables):
        self.hamiltonian = hamiltonian
        self.known_integrals = known_integrals
        self.variables = variables

    def vet_candidates(self, new_candidates, verbose=True):
        """
        Run complete analytical vetting.

        Returns:
            passed_candidates: List of candidates passing all tests
            detailed_results: Full test results for documentation
        """
        # Stage 1: Conservation
        conservation_validator = ConservationValidator(self.hamiltonian)
        conservation_results = conservation_validator.validate_candidates(
            new_candidates
        )

        # Filter: Only conserved candidates proceed
        conserved = {
            name: expr for name, expr in new_candidates.items()
            if conservation_results[name][0].success
        }

        if not conserved:
            return [], conservation_results

        # Stage 2: Involution
        all_integrals = {**self.known_integrals, **conserved}
        involution_tester = InvolutionTester()
        in_involution, involution_results = involution_tester.test_involution(
            all_integrals
        )

        # Stage 3: Independence
        independence_tester = IndependenceTester()
        is_independent, independence_stats = independence_tester.test_independence(
            all_integrals, self.variables
        )

        # Final verdict
        if in_involution and is_independent:
            passed = list(conserved.keys())
        else:
            passed = []

        return passed, {
            'conservation': conservation_results,
            'involution': involution_results,
            'independence': independence_stats
        }
```

**Files to Create**:
- `src/python/validation/analytical_vetting.py` (~200 lines)

**Deliverables**:
- [ ] Complete three-stage pipeline
- [ ] Clear pass/fail determination
- [ ] Detailed results for documentation
- [ ] Integration with existing WP3 output

---

### Phase 4: Testing and Documentation (2 days)

#### Task 4.1: Create Test Suite (1.5 days)

**Files to Create**:
- `tests/validation/test_poisson_brackets.py` (~300 lines)
  - Test symbolic computation
  - Test numerical fallback
  - Test on known systems (harmonic oscillator, Kepler)

- `tests/validation/test_analytical_vetting.py` (~400 lines)
  - Test complete pipeline
  - Test on integrable systems (should pass)
  - Test on non-integrable systems (should fail)

**Test Coverage Goals**:
- Known integrable: Harmonic oscillator, Kepler problem
- Known non-integrable: Hénon-Heiles
- Edge cases: Degenerate integrals, nearly-conserved quantities

#### Task 4.2: Documentation (0.5 days)

**Files to Create/Update**:
- `validation/README.md` - Package overview
- API documentation (docstrings)
- Tutorial: "Using WP 4.1 Analytical Vetting"

**Deliverables**:
- [ ] Complete test suite
- [ ] >80% code coverage
- [ ] Comprehensive documentation
- [ ] Usage examples

---

## WP 4.3 Implementation Plan

### Strategy: Build from Scratch

WP 4.3 is completely missing, so we build from the ground up following the design document.

### Phase 1: Monte Carlo Infrastructure (4 days)

#### Task 1.1: Parameter Space Sampling (1 day)

**File**: `src/python/validation/monte_carlo_validator.py`

**Implementation**:
```python
@dataclass
class MonteCarloConfig:
    """Monte Carlo validation configuration."""
    n_mass_ratios: int = 30
    n_energies: int = 15
    n_angular_momenta: int = 10
    n_ics_per_config: int = 100
    integration_periods: float = 1e4
    tolerance: float = 1e-6
    integrator: str = 'dop853'
    rtol: float = 1e-12
    atol: float = 1e-14

class ParameterSampler:
    """Generate stratified parameter space samples."""

    def __init__(self, config: MonteCarloConfig):
        self.config = config

    def generate_parameter_grid(self):
        """
        Generate parameter combinations.

        Returns list of (mu, E, L) tuples covering:
        - Mass ratios: log-uniform in [1e-3, 0.5]
        - Energies: Around Lagrange point energies
        - Angular momenta: [0.1, 2.0]
        """
        mu_vals = np.logspace(-3, np.log10(0.5), self.config.n_mass_ratios)

        # Energy range (CR3BP Jacobi constant range)
        E_vals = np.linspace(-2.0, -0.5, self.config.n_energies)

        # Angular momentum range
        L_vals = np.linspace(0.1, 2.0, self.config.n_angular_momenta)

        return list(itertools.product(mu_vals, E_vals, L_vals))

    def generate_initial_conditions(self, mu, E, L, n_samples):
        """
        Generate n_samples initial conditions for given parameters.

        Uses rejection sampling to satisfy energy and angular momentum.
        """
        # Implementation of IC generation with constraints
        pass
```

**Deliverables**:
- [ ] Parameter space sampler
- [ ] Initial condition generator
- [ ] Constraint satisfaction (E, L)

---

#### Task 1.2: Trajectory Integration and Drift Measurement (2 days)

**Implementation**:
```python
class TrajectoryIntegrator:
    """Integrate trajectories and measure conservation drift."""

    def integrate_and_measure(self, ic, integral_func, hamiltonian_func, t_max):
        """
        Integrate trajectory and monitor integral.

        Returns:
            drift: max|I(t) - I(0)| / |I(0)|
            trajectory: Full trajectory data (optional)
            success: Integration succeeded
        """
        from scipy.integrate import solve_ivp

        # Initial values
        I_0 = integral_func(ic)
        E_0 = hamiltonian_func(ic)

        # Integration
        def rhs(t, y):
            return hamiltonian_rhs(t, y, hamiltonian_func)

        sol = solve_ivp(
            rhs, [0, t_max], ic,
            rtol=1e-12, atol=1e-14,
            method='DOP853'
        )

        if not sol.success:
            return None, None, False

        # Measure drift
        I_vals = [integral_func(y) for y in sol.y.T]
        E_vals = [hamiltonian_func(y) for y in sol.y.T]

        drift_I = np.max(np.abs(I_vals - I_0)) / np.abs(I_0)
        drift_E = np.max(np.abs(E_vals - E_0)) / np.abs(E_0)

        return drift_I, drift_E, True
```

**Deliverables**:
- [ ] High-precision integration
- [ ] Drift measurement (relative error)
- [ ] Energy comparison (sanity check)

---

#### Task 1.3: Monte Carlo Orchestration (1 day)

**Implementation**:
```python
class MonteCarloValidator:
    """Large-scale Monte Carlo validation."""

    def __init__(self, config: MonteCarloConfig):
        self.config = config
        self.sampler = ParameterSampler(config)
        self.integrator = TrajectoryIntegrator(config)

    def validate_integral(self, integral_func, hamiltonian_func, output_file=None):
        """
        Run complete Monte Carlo validation.

        Returns:
            results: Dict with statistics
        """
        param_grid = self.sampler.generate_parameter_grid()
        n_total = len(param_grid) * self.config.n_ics_per_config

        print(f"Monte Carlo Validation: {n_total:,} trajectories")

        errors = []
        n_conserved = 0
        n_failed_integration = 0

        for i, (mu, E, L) in enumerate(param_grid):
            if i % 100 == 0:
                print(f"Progress: {i}/{len(param_grid)} parameter sets")

            # Generate ICs
            ics = self.sampler.generate_initial_conditions(mu, E, L,
                                                           self.config.n_ics_per_config)

            for ic in ics:
                drift, energy_drift, success = self.integrator.integrate_and_measure(
                    ic, integral_func, hamiltonian_func,
                    self.config.integration_periods
                )

                if not success:
                    n_failed_integration += 1
                    continue

                errors.append(drift)
                if drift < self.config.tolerance:
                    n_conserved += 1

        # Statistics
        errors = np.array(errors)
        success_rate = n_conserved / n_total

        results = {
            'n_total': n_total,
            'n_conserved': n_conserved,
            'n_failed': n_failed_integration,
            'success_rate': success_rate,
            'errors': errors,
            'mean_error': np.mean(errors),
            'median_error': np.median(errors),
            'p95_error': np.percentile(errors, 95),
            'p99_error': np.percentile(errors, 99)
        }

        # Save to HDF5 if requested
        if output_file:
            self._save_results(results, output_file)

        return results

    def _save_results(self, results, filename):
        """Save results to HDF5."""
        import h5py
        with h5py.File(filename, 'w') as f:
            f.create_dataset('errors', data=results['errors'])
            f.attrs['n_total'] = results['n_total']
            f.attrs['success_rate'] = results['success_rate']
            # ... other metadata
```

**Deliverables**:
- [ ] Complete Monte Carlo pipeline
- [ ] Progress tracking
- [ ] Result persistence (HDF5)
- [ ] Statistics calculation

---

### Phase 2: Stress Testing (3 days)

#### Task 2.1: Near-Collision Testing (1 day)

**File**: `src/python/validation/stress_tester.py`

**Implementation**:
```python
class StressTester:
    """Test conservation in extreme scenarios."""

    def test_near_collision(self, integral_func, hamiltonian_func, r_min=1e-3):
        """
        Test conservation during close encounters.

        Strategy:
        1. Initialize with r12 ≈ r_min
        2. Use KS regularization for integration
        3. Verify integral conserved through collision
        """
        from ..regularization.ks_transform import KSTransform

        # Generate near-collision ICs
        ics_collision = self._generate_collision_ics(r_min, n=100)

        results = []
        for ic in ics_collision:
            # Transform to KS coordinates
            ks = KSTransform()
            ic_ks = ks.transform_state(ic)

            # Integrate in KS (regularized)
            # ...

            # Measure conservation
            drift = self._measure_drift(trajectory, integral_func)
            results.append(drift)

        return {
            'n_tested': len(results),
            'max_drift': np.max(results),
            'mean_drift': np.mean(results),
            'success_rate': np.sum(np.array(results) < 1e-6) / len(results)
        }
```

**Deliverables**:
- [ ] Near-collision IC generation
- [ ] KS regularization integration
- [ ] Conservation verification through collision

---

#### Task 2.2: Chaotic Region Testing (1 day)

**Implementation**:
```python
def test_chaotic_region(self, integral_func, hamiltonian_func):
    """
    Test conservation in chaotic regions.

    Strategy:
    1. Identify chaotic ICs (positive Lyapunov exponent)
    2. Integrate for extended periods
    3. Verify conservation despite chaos
    """
    from ..chaos.lyapunov import compute_lyapunov_exponent

    # Generate candidate ICs
    ics = self._generate_random_ics(n=1000)

    # Filter for chaotic (λ > 0.01)
    chaotic_ics = []
    for ic in ics:
        lambda_max = compute_lyapunov_exponent(ic, hamiltonian_func, t_max=100)
        if lambda_max > 0.01:
            chaotic_ics.append((ic, lambda_max))

    print(f"Found {len(chaotic_ics)} chaotic ICs")

    # Test conservation on chaotic trajectories
    results = []
    for ic, lambda_max in chaotic_ics:
        drift = self._measure_conservation_drift(ic, integral_func, t_max=1e4)
        results.append({'lyapunov': lambda_max, 'drift': drift})

    return results
```

**Deliverables**:
- [ ] Lyapunov exponent computation
- [ ] Chaotic IC selection
- [ ] Chaos-drift correlation analysis

---

#### Task 2.3: High Eccentricity Testing (1 day)

**Implementation**:
```python
def test_high_eccentricity(self, integral_func, hamiltonian_func, e_min=0.95):
    """
    Test high eccentricity orbits.

    Strategy:
    1. Generate ICs with e > e_min
    2. Verify conservation at perihelion and aphelion
    3. Test for oscillatory drift patterns
    """
    # Generate high-e ICs
    high_e_ics = self._generate_eccentric_ics(e_min=e_min, n=100)

    results = []
    for ic in high_e_ics:
        # Integrate one orbit
        trajectory = self._integrate_one_period(ic, hamiltonian_func)

        # Find perihelion and aphelion
        peri_idx = np.argmin(trajectory['r'])
        apo_idx = np.argmax(trajectory['r'])

        # Check conservation at extrema
        I_0 = integral_func(ic)
        I_peri = integral_func(trajectory['state'][peri_idx])
        I_apo = integral_func(trajectory['state'][apo_idx])

        drift = max(abs(I_peri - I_0), abs(I_apo - I_0)) / abs(I_0)
        results.append(drift)

    return {
        'n_tested': len(results),
        'max_drift': np.max(results),
        'success_rate': np.sum(np.array(results) < 1e-6) / len(results)
    }
```

**Deliverables**:
- [ ] High eccentricity IC generation
- [ ] Perihelion/aphelion detection
- [ ] Conservation verification at extrema

---

### Phase 3: Long-Time Validation (4 days)

#### Task 3.1: Extended Integration (2 days)

**File**: `src/python/validation/long_time_validator.py`

**Implementation**:
```python
class LongTimeValidator:
    """Long-time integration and drift analysis."""

    def validate_long_time(
        self,
        integral_func,
        hamiltonian_func,
        ic,
        t_max=1e6,
        n_checkpoints=1000
    ):
        """
        Integrate for very long times (10⁶ periods).

        Monitor:
        - Drift in integral I(t)
        - Drift in energy E(t)
        - Ratio: drift_I / drift_E

        Acceptance: drift_I ≈ drift_E (both ~ integrator error)
        """
        # Checkpoints for monitoring
        t_eval = np.linspace(0, t_max, n_checkpoints)

        # Initial values
        I_0 = integral_func(ic)
        E_0 = hamiltonian_func(ic)

        # Integrate with high precision
        sol = solve_ivp(
            lambda t, y: hamiltonian_rhs(t, y, hamiltonian_func),
            [0, t_max],
            ic,
            t_eval=t_eval,
            rtol=1e-13,
            atol=1e-15,
            method='DOP853'
        )

        # Monitor conservation
        I_vals = [integral_func(y) for y in sol.y.T]
        E_vals = [hamiltonian_func(y) for y in sol.y.T]

        drift_I = np.array(I_vals) - I_0
        drift_E = np.array(E_vals) - E_0

        # Analyze drift patterns
        drift_ratio = np.abs(drift_I) / (np.abs(drift_E) + 1e-16)

        # Linear fit to detect secular drift
        t_fit = sol.t
        drift_I_rate = np.polyfit(t_fit, drift_I, 1)[0]  # Linear coefficient
        drift_E_rate = np.polyfit(t_fit, drift_E, 1)[0]

        return {
            't': sol.t,
            'drift_I': drift_I,
            'drift_E': drift_E,
            'drift_ratio': drift_ratio,
            'drift_I_rate': drift_I_rate,
            'drift_E_rate': drift_E_rate,
            'max_drift_I': np.max(np.abs(drift_I)) / np.abs(I_0),
            'max_drift_E': np.max(np.abs(drift_E)) / np.abs(E_0)
        }
```

**Deliverables**:
- [ ] Long-time integration (10⁶ periods)
- [ ] Drift monitoring
- [ ] Secular drift detection
- [ ] I vs E drift comparison

---

#### Task 3.2: Shadow Hamiltonian Analysis (2 days)

**Implementation**:
```python
def shadow_hamiltonian_analysis(self, trajectory, hamiltonian_func):
    """
    Backward error analysis.

    Concept: Numerical trajectory is exact solution of nearby "shadow" Hamiltonian.

    Test: Is drift in I consistent with integrator error in H?
    """
    # Extract trajectory
    times = trajectory['t']
    states = trajectory['states']

    # Compute energy along trajectory
    E_vals = [hamiltonian_func(state) for state in states]
    E_mean = np.mean(E_vals)
    E_std = np.std(E_vals)

    # Shadow Hamiltonian estimate: H_shadow ≈ E_mean
    H_shadow = E_mean

    # Energy error: |E(t) - H_shadow|
    energy_error = np.abs(np.array(E_vals) - H_shadow)

    # For symplectic integrators, expect:
    # energy_error ~ O(h^p) where h = step size, p = order
    # and error is BOUNDED, not growing

    # Check boundedness
    is_bounded = self._check_bounded_error(energy_error)

    # Compare to integral drift
    # If I is truly conserved, its drift should match energy drift

    return {
        'H_shadow': H_shadow,
        'energy_error_mean': np.mean(energy_error),
        'energy_error_max': np.max(energy_error),
        'is_bounded': is_bounded
    }

def _check_bounded_error(self, errors, window=100):
    """
    Check if error is bounded (not growing secularly).

    Method: Compare error in first window vs last window.
    """
    error_early = np.max(errors[:window])
    error_late = np.max(errors[-window:])

    # If error grows by >10x, it's secular drift
    growth_factor = error_late / (error_early + 1e-16)

    return growth_factor < 10.0
```

**Deliverables**:
- [ ] Shadow Hamiltonian estimation
- [ ] Backward error analysis
- [ ] Bounded vs secular drift detection
- [ ] Integrator error characterization

---

### Phase 4: Statistical Reporting (2 days)

#### Task 4.1: Statistical Analysis and Plots (1.5 days)

**File**: `src/python/validation/statistical_reporter.py`

**Implementation**:
```python
class StatisticalReporter:
    """Generate publication-quality validation reports."""

    def __init__(self, output_dir='./validation_report'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(
        self,
        monte_carlo_results,
        stress_test_results,
        long_time_results,
        integral_name="I"
    ):
        """
        Complete validation report.

        Generates:
        1. Error distribution histogram
        2. Success rate heatmap (mu vs E)
        3. Long-time drift plot
        4. Stress test summary
        5. Statistical tables
        6. LaTeX summary
        """
        # 1. Error distribution
        self._plot_error_distribution(monte_carlo_results, integral_name)

        # 2. Success rate heatmap
        self._plot_success_heatmap(monte_carlo_results, integral_name)

        # 3. Long-time drift
        self._plot_drift_analysis(long_time_results, integral_name)

        # 4. Stress test summary
        self._plot_stress_test_summary(stress_test_results, integral_name)

        # 5. Statistical tables
        self._generate_statistics_table(monte_carlo_results)

        # 6. LaTeX summary
        self._generate_latex_report(
            monte_carlo_results,
            stress_test_results,
            long_time_results,
            integral_name
        )

        print(f"Report generated in {self.output_dir}/")

    def _plot_error_distribution(self, results, integral_name):
        """Histogram of conservation errors."""
        errors = results['errors']

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.hist(errors, bins=50, edgecolor='black', alpha=0.7)
        ax.axvline(results['median_error'], color='red', linestyle='--',
                   label=f"Median: {results['median_error']:.2e}")
        ax.axvline(results['p95_error'], color='orange', linestyle='--',
                   label=f"95th percentile: {results['p95_error']:.2e}")

        ax.set_xlabel(f'Conservation Error: |Δ{integral_name}|/|{integral_name}₀|')
        ax.set_ylabel('Count')
        ax.set_yscale('log')
        ax.set_title(f'Distribution of Conservation Errors ({results["n_total"]:,} trajectories)')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/error_distribution.png', dpi=300)
        plt.savefig(f'{self.output_dir}/error_distribution.pdf')
        plt.close()

    def _plot_success_heatmap(self, results, integral_name):
        """Success rate as function of (mu, E)."""
        # Reshape results into 2D grid
        # Plot heatmap
        # ...
        pass

    def _generate_latex_report(self, mc_results, stress_results, lt_results, name):
        """Generate LaTeX summary table."""
        latex = r"""
\begin{table}[h]
\centering
\caption{Statistical Validation Results for """ + name + r"""}
\begin{tabular}{lc}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
Total Trajectories & """ + f"{mc_results['n_total']:,}" + r""" \\
Success Rate & """ + f"{100*mc_results['success_rate']:.1f}\\%" + r""" \\
Median Error & """ + f"${mc_results['median_error']:.2e}$" + r""" \\
95th Percentile Error & """ + f"${mc_results['p95_error']:.2e}$" + r""" \\
\hline
\end{tabular}
\end{table}
"""

        with open(f'{self.output_dir}/validation_table.tex', 'w') as f:
            f.write(latex)
```

**Deliverables**:
- [ ] Error distribution plots (PNG + PDF)
- [ ] Success rate heatmaps
- [ ] Long-time drift plots
- [ ] Stress test visualizations
- [ ] LaTeX tables for publication

---

#### Task 4.2: Confidence Intervals (0.5 days)

**Implementation**:
```python
def compute_confidence_intervals(self, errors, confidence=0.95):
    """
    Compute confidence intervals for error statistics.

    Uses bootstrap resampling for robustness.
    """
    from scipy import stats

    # Bootstrap resampling
    n_bootstrap = 10000
    n_samples = len(errors)

    median_samples = []
    mean_samples = []

    for _ in range(n_bootstrap):
        sample = np.random.choice(errors, size=n_samples, replace=True)
        median_samples.append(np.median(sample))
        mean_samples.append(np.mean(sample))

    # Confidence intervals
    alpha = 1 - confidence
    median_ci = np.percentile(median_samples, [100*alpha/2, 100*(1-alpha/2)])
    mean_ci = np.percentile(mean_samples, [100*alpha/2, 100*(1-alpha/2)])

    return {
        'median': np.median(errors),
        'median_ci': median_ci,
        'mean': np.mean(errors),
        'mean_ci': mean_ci,
        'confidence': confidence
    }
```

**Deliverables**:
- [ ] Bootstrap confidence intervals
- [ ] Error bar computation
- [ ] Statistical significance testing

---

### Phase 5: Parallelization (Optional - 2 days)

#### Task 5.1: Parallel Executor for HPC (2 days)

**File**: `src/python/validation/parallel_executor.py`

**Implementation**:
```python
from multiprocessing import Pool
import numpy as np

class ParallelExecutor:
    """
    Distribute Monte Carlo tasks across multiple cores/nodes.

    Supports:
    - Multiprocessing (single node)
    - MPI (multi-node HPC)
    - Job arrays (SLURM, PBS)
    """

    def __init__(self, n_workers=None, backend='multiprocessing'):
        self.n_workers = n_workers or os.cpu_count()
        self.backend = backend

    def parallel_validate(self, validator, integral_func, hamiltonian_func, ics):
        """
        Run validation in parallel over initial conditions.

        Returns aggregated results.
        """
        if self.backend == 'multiprocessing':
            return self._parallel_multiprocessing(validator, integral_func,
                                                   hamiltonian_func, ics)
        elif self.backend == 'mpi':
            return self._parallel_mpi(validator, integral_func,
                                      hamiltonian_func, ics)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _parallel_multiprocessing(self, validator, integral_func, hamiltonian_func, ics):
        """Multiprocessing backend."""
        def worker(ic):
            return validator.validate_single_trajectory(ic, integral_func,
                                                        hamiltonian_func)

        with Pool(self.n_workers) as pool:
            results = pool.map(worker, ics)

        return self._aggregate_results(results)
```

**Deliverables**:
- [ ] Multiprocessing support
- [ ] Optional MPI support
- [ ] Progress tracking across workers
- [ ] Result aggregation

---

## Implementation Timeline

### Gantt Chart Overview

```
Week 1: WP 4.1 Consolidation
├─ Days 1-3: Core unification (poisson_brackets, conservation_validator, involution_tester)
├─ Days 4-5: Independence testing refactor
├─ Days 6-7: Orchestration layer + initial tests

Week 2: WP 4.1 Completion + WP 4.3 Start
├─ Days 8-9: Complete WP 4.1 tests and documentation
├─ Days 10-11: WP 4.3 Phase 1 - Monte Carlo infrastructure (parameter sampling)
├─ Days 12-13: WP 4.3 Phase 1 - Trajectory integration
├─ Day 14: WP 4.3 Phase 1 - Monte Carlo orchestration

Week 3: WP 4.3 Core Implementation
├─ Days 15-17: WP 4.3 Phase 2 - Stress testing (collisions, chaos, eccentricity)
├─ Days 18-21: WP 4.3 Phase 3 - Long-time validation and shadow Hamiltonian

Week 4: WP 4.3 Completion and Integration
├─ Days 22-23: WP 4.3 Phase 4 - Statistical reporting
├─ Days 24-25: (Optional) Parallelization
├─ Days 26-27: Integration testing and documentation
├─ Day 28: Final validation and handoff
```

### Critical Path

```
WP 4.1 Core → WP 4.1 Tests → WP 4.3 Monte Carlo → WP 4.3 Stress Testing →
WP 4.3 Long-Time → WP 4.3 Reporting → Complete WP4 Pipeline
```

**Total Duration**: 20-28 days (3-4 weeks)

### Parallelization Opportunities

- WP 4.1 and WP 4.3 Phase 1 can overlap (days 10-14)
- WP 4.3 stress testing, long-time, and reporting can partially overlap
- Testing can run concurrently with documentation

---

## Success Metrics

### WP 4.1 Success Criteria

**Minimum Success**:
- [ ] All three test types implemented (conservation, involution, independence)
- [ ] Can test candidates from WP3
- [ ] Pass/fail determination works

**Target Success**:
- [ ] Unified API in `validation/` package
- [ ] >80% test coverage
- [ ] Symbolic and numerical modes working
- [ ] Clear documentation and examples

**Exceptional Success**:
- [ ] Symbolic proofs for simple cases
- [ ] Automatic simplification working
- [ ] Publication-quality certification documents

### WP 4.3 Success Criteria

**Minimum Success**:
- [ ] 10⁴ trajectories tested
- [ ] Basic error distribution computed
- [ ] Success rate calculated

**Target Success**:
- [ ] 10⁵ trajectories tested across parameter space
- [ ] Success rate >95%
- [ ] Stress tests completed (collisions, chaos, eccentricity)
- [ ] Long-time validation (10⁴ periods)
- [ ] Statistical report with plots

**Exceptional Success**:
- [ ] 10⁶ trajectories
- [ ] Success rate >99%
- [ ] Error < 10⁻⁸ for 95th percentile
- [ ] Shadow Hamiltonian analysis completed
- [ ] HPC parallelization working
- [ ] Publication-ready figures and tables

### Overall WP4 Success Criteria

**Publication Readiness**:
- [ ] All WP3 candidates tested
- [ ] At least one candidate passes all tests
- [ ] Conservation < 10⁻¹⁰ demonstrated
- [ ] Statistical validation on >10⁵ trajectories
- [ ] Confidence intervals computed
- [ ] LaTeX tables and figures ready for manuscript

---

## Testing Strategy

### Unit Tests

**WP 4.1**:
- Test each component on known integrable systems
  - Harmonic oscillator (1D, 2D, 3D)
  - Kepler problem
  - Free particle
- Test on known non-integrable systems (should fail)
  - Hénon-Heiles
  - Störmer problem
- Edge cases
  - Degenerate integrals
  - Nearly-conserved quantities

**WP 4.3**:
- Test parameter sampling (coverage, distributions)
- Test integration (accuracy, error handling)
- Test drift measurement (known conserved quantities)
- Test statistical computations (known distributions)

### Integration Tests

- Complete WP 4.1 pipeline on toy system
- Complete WP 4.3 pipeline on small sample (100 trajectories)
- WP 4.1 → WP 4.3 handoff
- End-to-end: WP3 candidates → WP4 validation → report

### Validation Tests

- Cross-check with existing scattered implementations
- Verify conservation of known integrals (E, L)
- Verify non-conservation of known non-integrals
- Compare numerical and symbolic results where both available

---

## Risk Mitigation

### Risk 1: WP 4.1 Consolidation Breaks Existing Code

**Probability**: Medium (30%)
**Impact**: Medium

**Mitigation**:
- Don't delete existing implementations immediately
- Add deprecation warnings
- Provide compatibility layer
- Extensive testing before removal

### Risk 2: WP 4.3 Computationally Too Expensive

**Probability**: Medium (25%)
**Impact**: High

**Mitigation**:
- Start with 10⁴ trajectories (feasible on laptop)
- Scale up incrementally to 10⁵
- Use HPC resources if available
- Can publish with 10⁴ if necessary (reduced confidence)

### Risk 3: Symbolic Computation Intractable

**Probability**: Medium (40%)
**Impact**: Low

**Mitigation**:
- Numerical validation is acceptable alternative
- Use timeout mechanisms
- Simplification strategies (SymPy simplification tactics)
- Manual symbolic proofs for key cases

### Risk 4: Integration Failures in Edge Cases

**Probability**: High (50%)
**Impact**: Low

**Mitigation**:
- Robust error handling
- Multiple integrators (DOP853, Radau, etc.)
- Adaptive tolerance
- KS regularization for collisions
- Track and report failure rates

### Risk 5: Timeline Overrun

**Probability**: Medium (30%)
**Impact**: Medium

**Mitigation**:
- Prioritize WP 4.1 first (blocks WP 4.3)
- WP 4.3 can scale down (10⁴ instead of 10⁵)
- Parallelization is optional
- Documentation can be minimal initially

---

## Deliverables Checklist

### Code Deliverables

**WP 4.1**:
- [ ] `validation/poisson_brackets.py` (~600 lines)
- [ ] `validation/conservation_validator.py` (~200 lines)
- [ ] `validation/involution_tester.py` (~250 lines)
- [ ] `validation/independence_tester.py` (~300 lines)
- [ ] `validation/analytical_vetting.py` (~200 lines)
- [ ] `tests/validation/test_poisson_brackets.py` (~300 lines)
- [ ] `tests/validation/test_analytical_vetting.py` (~400 lines)

**WP 4.3**:
- [ ] `validation/monte_carlo_validator.py` (~500 lines)
- [ ] `validation/stress_tester.py` (~400 lines)
- [ ] `validation/long_time_validator.py` (~350 lines)
- [ ] `validation/statistical_reporter.py` (~400 lines)
- [ ] `validation/parallel_executor.py` (~250 lines, optional)
- [ ] `tests/validation/test_monte_carlo.py` (~300 lines)
- [ ] `tests/validation/test_stress_testing.py` (~250 lines)

**Total New Code**: ~4,700 lines

### Documentation Deliverables

- [ ] `validation/README.md` - Package overview
- [ ] API documentation (docstrings, Sphinx)
- [ ] Tutorial: "Analytical Vetting Workflow"
- [ ] Tutorial: "Monte Carlo Validation Workflow"
- [ ] Statistical validation report (PDF)

### Validation Deliverables

- [ ] Test coverage report (>80%)
- [ ] Validation on known integrable systems
- [ ] Validation on WP3 candidates
- [ ] Statistical validation report
- [ ] Publication figures (10+ plots)
- [ ] LaTeX tables for manuscript

---

## Next Steps

### Immediate Actions (This Week)

1. **Review and approve this plan**
2. **Set up development branch**
3. **Begin WP 4.1 Phase 1** (Days 1-3)
   - Create `validation/poisson_brackets.py`
   - Create `validation/conservation_validator.py`
   - Create `validation/involution_tester.py`

### Week 2 Actions

4. **Complete WP 4.1** (Days 4-9)
5. **Begin WP 4.3 Monte Carlo** (Days 10-14)

### Weeks 3-4 Actions

6. **Complete WP 4.3** (Days 15-23)
7. **Integration and testing** (Days 24-28)
8. **Final documentation and handoff**

---

## Conclusion

This plan provides a **comprehensive roadmap** to address all identified gaps in WP4:

1. **WP 4.1**: Consolidate and complete analytical vetting infrastructure
2. **WP 4.3**: Implement complete numerical robustness validation from scratch

**Expected Outcome**: Publication-ready validation infrastructure capable of:
- Rigorously vetting candidate integrals from WP3
- Providing statistical certification across parameter space
- Generating publication-quality validation reports

**Timeline**: 20-28 days of focused implementation

**Priority**: High - This is a **prerequisite for publication**

---

**Document Status**: ✅ Complete Implementation Plan
**Ready for**: Review and Implementation
**Created**: 2025-11-22
**Next**: Approve plan and begin implementation
