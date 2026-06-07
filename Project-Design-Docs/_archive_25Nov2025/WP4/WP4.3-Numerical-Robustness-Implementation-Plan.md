# WP 4.3: Numerical Robustness and Generalization
## Complete Implementation Plan

**Duration**: 10-12 days
**Prerequisites**: WP 4.1 complete (candidates passed analytical vetting)
**Objective**: Demonstrate conservation holds statistically across parameter space, long time scales, and extreme scenarios

---

## Overview

WP 4.3 provides **statistical certification** of candidate integrals through large-scale numerical validation. While WP 4.1 proves conservation symbolically or on samples, WP 4.3 demonstrates it holds **universally** across the entire three-body problem parameter space.

### Validation Philosophy

**Cannot prove conservation everywhere numerically** → **Statistically certify** on representative sample

**Requirements**:
1. Test on 10⁵-10⁶ trajectories spanning parameter space
2. Long-time integration (10⁴-10⁶ orbital periods)
3. Stress testing (collisions, chaos, high eccentricity)
4. Drift analysis compared to integrator error

---

## Four-Task Structure

```
WP 4.3: Numerical Robustness (4 parallel → synthesis tasks)
│
├── Task 4.3.1: Monte Carlo Parameter Sweep (4 days)
│   ├── Sample parameter space (masses, energies, L)
│   ├── Integrate 10⁵ trajectories
│   └── Measure conservation drift
│
├── Task 4.3.2: Stress Testing (3 days)
│   ├── Near-collision scenarios
│   ├── Chaotic regions (positive Lyapunov)
│   └── High eccentricity orbits
│
├── Task 4.3.3: Long-Time Invariance (4 days)
│   ├── Extended integration (10⁶ periods)
│   ├── Shadow Hamiltonian analysis
│   └── Drift vs. integrator error
│
└── Task 4.3.4: Statistical Analysis (2 days)
    ├── Error distributions
    ├── Confidence intervals
    └── Publication-quality report
```

---

## Task 4.3.1: Monte Carlo Parameter Sweep

**File**: `src/python/validation/monte_carlo_validator.py`

```python
"""
Large-scale Monte Carlo validation of candidate integrals.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Callable
import h5py


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo sweep."""
    n_mass_ratios: int = 30
    n_energies: int = 15
    n_angular_momenta: int = 10
    n_initial_conditions_per_config: int = 100
    integration_time: float = 1e4  # Orbital periods
    tolerance: float = 1e-6


class MonteCarloValidator:
    """Monte Carlo validation across parameter space."""

    def __init__(self, config: MonteCarloConfig):
        self.config = config

    def generate_parameter_samples(self) -> List[Dict]:
        """Generate stratified parameter space samples."""
        # Mass ratios (log-uniform)
        mu_vals = np.logspace(-3, np.log10(0.5), self.config.n_mass_ratios)

        # Energies (bracket Lagrange points)
        E_vals = np.linspace(-2.0, -0.5, self.config.n_energies)

        # Angular momenta
        L_vals = np.linspace(0.1, 2.0, self.config.n_angular_momenta)

        samples = []
        for mu in mu_vals:
            for E in E_vals:
                for L in L_vals:
                    samples.append({'mu': mu, 'E': E, 'L': L})

        return samples

    def validate_candidate(
        self,
        integral_func: Callable,
        hamiltonian_func: Callable,
        verbose: bool = True
    ) -> Dict:
        """
        Validate candidate integral across parameter space.

        Returns statistics dictionary with:
            - n_total: Total trajectories tested
            - n_conserved: Number passing tolerance
            - success_rate: Fraction passing
            - error_distribution: Histogram of errors
        """
        param_samples = self.generate_parameter_samples()
        n_total = len(param_samples) * self.config.n_initial_conditions_per_config

        if verbose:
            print(f"Monte Carlo Validation: {n_total} trajectories")

        errors = []
        n_conserved = 0

        for i, params in enumerate(param_samples):
            if verbose and i % 100 == 0:
                print(f"  Progress: {i}/{len(param_samples)} parameter sets")

            # Generate initial conditions for this parameter set
            ics = self._generate_initial_conditions(params)

            for ic in ics:
                # Integrate and measure drift
                drift = self._measure_conservation_drift(
                    ic, integral_func, hamiltonian_func
                )

                errors.append(drift)
                if drift < self.config.tolerance:
                    n_conserved += 1

        success_rate = n_conserved / n_total

        return {
            'n_total': n_total,
            'n_conserved': n_conserved,
            'success_rate': success_rate,
            'errors': np.array(errors),
            'mean_error': np.mean(errors),
            'median_error': np.median(errors),
            'p95_error': np.percentile(errors, 95)
        }
```

---

## Task 4.3.2: Stress Testing

**File**: `src/python/validation/stress_tester.py`

```python
"""
Stress testing: collisions, chaos, extreme orbits.
"""

class StressTester:
    """Test conservation in extreme scenarios."""

    def test_near_collision(self, integral_func, r_min=1e-3):
        """Test conservation during close encounter."""
        # Initialize with r12 ≈ r_min
        # Use KS regularization
        # Verify integral conserved through collision
        pass

    def test_chaotic_region(self, integral_func):
        """Test in chaotic regions (λ_max > 0)."""
        # Select ICs with positive Lyapunov exponent
        # Verify conservation despite chaos
        pass

    def test_high_eccentricity(self, integral_func, e=0.99):
        """Test high eccentricity orbits."""
        # Initialize with e ≈ 1
        # Verify conservation at perihelion and aphelion
        pass
```

---

## Task 4.3.3: Long-Time Invariance

**File**: `src/python/validation/long_time_validator.py`

```python
"""
Long-time integration and shadow Hamiltonian analysis.
"""

class LongTimeValidator:
    """Validate conservation over extended timescales."""

    def validate_long_time(
        self,
        integral_func,
        hamiltonian_func,
        t_max=1e6,
        rtol=1e-12
    ):
        """
        Integrate for t_max periods with high precision.

        Compare drift in integral vs. drift in energy.
        """
        # Long integration
        # Monitor I(t) and E(t)
        # Compute: drift_I / drift_E
        # Accept if ratio ≈ O(1)
        pass

    def shadow_hamiltonian_analysis(self, trajectory):
        """
        Backward error analysis.

        Determine if numerical trajectory is exact solution
        of nearby "shadow" Hamiltonian.
        """
        # Estimate H_shadow from trajectory
        # Verify I(H_shadow) ≈ I(H_true)
        pass
```

---

## Task 4.3.4: Statistical Analysis

**File**: `src/python/validation/statistical_reporter.py`

```python
"""
Statistical analysis and reporting.
"""

import matplotlib.pyplot as plt
import scipy.stats as stats


class StatisticalReporter:
    """Generate publication-quality validation report."""

    def generate_report(
        self,
        monte_carlo_results: Dict,
        stress_test_results: Dict,
        long_time_results: Dict,
        output_path: str = "./validation_report"
    ):
        """
        Generate comprehensive validation report.

        Includes:
        - Error distributions
        - Success rate vs. parameters
        - Confidence intervals
        - Publication figures
        """
        # Error histogram
        self._plot_error_distribution(monte_carlo_results)

        # Success rate heatmap (mass ratio vs energy)
        self._plot_success_heatmap(monte_carlo_results)

        # Long-time drift
        self._plot_drift_analysis(long_time_results)

        # Statistical tests
        self._compute_confidence_intervals(monte_carlo_results)

        # LaTeX table for publication
        self._generate_latex_table(monte_carlo_results)

    def _plot_error_distribution(self, results):
        """Histogram of conservation errors."""
        plt.figure(figsize=(8, 6))
        plt.hist(results['errors'], bins=50, edgecolor='black')
        plt.xlabel('Conservation Error')
        plt.ylabel('Count')
        plt.yscale('log')
        plt.title('Distribution of Conservation Errors')
        plt.savefig('error_distribution.png', dpi=300)
```

---

## Integration: Complete WP 4.3 Pipeline

```python
from validation.monte_carlo_validator import MonteCarloValidator, MonteCarloConfig
from validation.stress_tester import StressTester
from validation.long_time_validator import LongTimeValidator
from validation.statistical_reporter import StatisticalReporter

# Configure
config = MonteCarloConfig(
    n_mass_ratios=30,
    n_initial_conditions_per_config=1000
)

# Run validations
mc_validator = MonteCarloValidator(config)
mc_results = mc_validator.validate_candidate(integral_func, hamiltonian_func)

stress_tester = StressTester()
stress_results = stress_tester.run_all_tests(integral_func)

lt_validator = LongTimeValidator()
lt_results = lt_validator.validate_long_time(integral_func, hamiltonian_func)

# Generate report
reporter = StatisticalReporter()
reporter.generate_report(mc_results, stress_results, lt_results)

# Summary
print(f"Success rate: {mc_results['success_rate']:.1%}")
print(f"Median error: {mc_results['median_error']:.2e}")
```

---

## Deliverables

### Code Modules (5 files)
- [ ] `monte_carlo_validator.py` (~500 lines)
- [ ] `stress_tester.py` (~400 lines)
- [ ] `long_time_validator.py` (~350 lines)
- [ ] `statistical_reporter.py` (~400 lines)
- [ ] `parallel_executor.py` (~250 lines)

**Total**: ~1,900 lines

### Documentation
- [ ] Statistical validation report (PDF)
- [ ] Publication figures (10+ plots)
- [ ] Data archive (HDF5, ~10-100 GB)

---

## Success Criteria

### Minimum Success
- [ ] 10⁴ trajectories tested
- [ ] Error distribution documented
- [ ] Success rate >80%

### Target Success
- [ ] 10⁵ trajectories tested
- [ ] Success rate >95%
- [ ] Conservation error < 10⁻⁶ for 95th percentile

### Stretch Success
- [ ] 10⁶ trajectories
- [ ] Success rate >99%
- [ ] Error < 10⁻⁸ for 95th percentile

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Implementation Plan
**Estimated Implementation Time**: 10-12 days
