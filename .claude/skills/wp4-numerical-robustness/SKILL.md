---
name: wp4-numerical-robustness
version: 2.0.0
description: >
  Numerical validation pipeline for candidate integrals discovered in WP3.
  Implements trajectory-based conservation tests, Floquet stability analysis,
  and statistical significance testing. Final gate before declaring validated
  lift-integrals. Use when testing conservation along trajectories, computing
  Floquet multipliers, running Monte Carlo validation, or performing statistical
  hypothesis testing on integral candidates.
triggers:
  - numerical validation
  - trajectory conservation
  - floquet multipliers
  - stability analysis
  - monte carlo
  - statistical testing
  - long-time integration
  - conservation error
  - numerical drift
  - robustness test
use_cases:
  - Testing conservation of candidate along integrated trajectories
  - Computing Floquet multipliers and stability indices
  - Running Monte Carlo validation across initial conditions
  - Statistical hypothesis testing for conservation
  - Long-time integration stability assessment
  - Distinguishing true integrals from numerical artifacts
  - Comparing conservation across different integrators
  - Quantifying numerical drift rates
references:
  - references/trajectory-validation.md
  - references/floquet-stability.md
  - references/statistical-testing.md
---

# WP4 Numerical Robustness

Final numerical validation gate for candidate integrals.

## Overview

After analytical vetting (WP4.1) and Morales-Ramis testing (WP4.2), numerical robustness testing provides the final empirical validation. This stage distinguishes true conserved quantities from numerical artifacts or approximate integrals.

### Position in Pipeline

```
┌────────────────────────────────────────────────────────────────────┐
│                      WP4 VALIDATION PIPELINE                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  WP3 Candidates ──► WP4.1 Analytical ──► WP4.2 Morales-Ramis      │
│                     Vetting              Test                      │
│                        │                    │                      │
│                        ▼                    ▼                      │
│              ┌─────────────────────────────────────────┐          │
│              │     WP4.3 NUMERICAL ROBUSTNESS          │          │
│              │  ┌─────────────────────────────────┐    │          │
│              │  │  Stage A: Trajectory Tests      │    │          │
│              │  │  • Short-time conservation      │    │          │
│              │  │  • Long-time integration        │    │          │
│              │  │  • Multi-trajectory sampling    │    │          │
│              │  └─────────────────────────────────┘    │          │
│              │                 │                       │          │
│              │                 ▼                       │          │
│              │  ┌─────────────────────────────────┐    │          │
│              │  │  Stage B: Floquet Analysis      │    │          │
│              │  │  • Stability multipliers        │    │          │
│              │  │  • Near-periodic behavior       │    │          │
│              │  │  • Resonance sensitivity        │    │          │
│              │  └─────────────────────────────────┘    │          │
│              │                 │                       │          │
│              │                 ▼                       │          │
│              │  ┌─────────────────────────────────┐    │          │
│              │  │  Stage C: Statistical Tests     │    │          │
│              │  │  • Monte Carlo validation       │    │          │
│              │  │  • Hypothesis testing           │    │          │
│              │  │  • Confidence intervals         │    │          │
│              │  └─────────────────────────────────┘    │          │
│              └─────────────────────────────────────────┘          │
│                                 │                                  │
│                                 ▼                                  │
│                    ✓ VALIDATED LIFT-INTEGRAL                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Acceptance Criteria

| Test | Criterion | Threshold |
|------|-----------|-----------|
| Short-time conservation | ΔI/I₀ over 100 periods | < 10⁻¹⁰ |
| Long-time conservation | ΔI/I₀ over 10,000 periods | < 10⁻⁶ |
| Drift rate | d(ΔI)/dt trend | < 10⁻¹² per period |
| Monte Carlo pass rate | Fraction passing all tests | > 99.9% |
| Statistical significance | p-value for non-conservation | > 0.99 |

## Quick Start

```python
from src.python.validation.numerical_robustness import NumericalValidator
from src.python.validation.trajectory import TrajectoryIntegrator

mu = 0.012150585609624  # Earth-Moon mass ratio

# Candidate integral from WP3
def candidate_integral(state, mu):
    # ... candidate function
    pass

# Create validator
validator = NumericalValidator(mu=mu)

# Run full validation
result = validator.validate(
    integral_func=candidate_integral,
    n_trajectories=1000,
    short_periods=100,
    long_periods=10000
)

print(f"Passed: {result.passed}")
print(f"Short-time error: {result.short_time_error:.2e}")
print(f"Long-time error: {result.long_time_error:.2e}")
print(f"Drift rate: {result.drift_rate:.2e}")
print(f"Monte Carlo pass rate: {result.mc_pass_rate:.2%}")
print(f"Statistical p-value: {result.p_value:.4f}")
```

## Stage A: Trajectory Conservation Tests

### Short-Time Conservation

Test conservation over moderate time spans with high precision:

```python
import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass
from typing import Callable, List, Optional

@dataclass
class ConservationTestResult:
    """Results from trajectory conservation test."""
    passed: bool
    initial_value: float
    final_value: float
    max_deviation: float
    relative_error: float
    times: np.ndarray
    values: np.ndarray
    deviations: np.ndarray

def test_short_time_conservation(
    integral_func: Callable,
    initial_state: np.ndarray,
    mu: float,
    n_periods: int = 100,
    period: float = None,
    tolerance: float = 1e-10
) -> ConservationTestResult:
    """
    Test conservation over short time span.
    
    Parameters:
        integral_func: Candidate integral I(state, mu) -> float
        initial_state: Starting state [x, y, z, vx, vy, vz]
        mu: Mass ratio parameter
        n_periods: Number of characteristic periods
        period: Orbital period (estimated if None)
        tolerance: Relative error threshold
        
    Returns:
        ConservationTestResult
    """
    # Estimate period if not provided
    if period is None:
        period = estimate_orbital_period(initial_state, mu)
    
    t_span = (0, n_periods * period)
    
    # High-precision integration
    sol = solve_ivp(
        lambda t, y: cr3bp_equations(t, y, mu),
        t_span,
        initial_state,
        method='DOP853',
        rtol=1e-13,
        atol=1e-15,
        dense_output=True
    )
    
    # Sample integral values
    n_samples = n_periods * 100
    times = np.linspace(0, t_span[1], n_samples)
    values = np.array([integral_func(sol.sol(t), mu) for t in times])
    
    # Compute statistics
    I0 = values[0]
    deviations = np.abs(values - I0)
    max_deviation = np.max(deviations)
    relative_error = max_deviation / np.abs(I0) if I0 != 0 else max_deviation
    
    return ConservationTestResult(
        passed=relative_error < tolerance,
        initial_value=I0,
        final_value=values[-1],
        max_deviation=max_deviation,
        relative_error=relative_error,
        times=times,
        values=values,
        deviations=deviations
    )
```

### Long-Time Integration

Test for secular drift over extended periods:

```python
@dataclass
class LongTimeResult:
    """Results from long-time integration test."""
    passed: bool
    initial_value: float
    final_value: float
    drift_rate: float
    total_drift: float
    integration_time: float
    n_periods: int
    drift_history: np.ndarray
    times: np.ndarray

def test_long_time_conservation(
    integral_func: Callable,
    initial_state: np.ndarray,
    mu: float,
    n_periods: int = 10000,
    period: float = None,
    max_drift_rate: float = 1e-12,
    max_total_drift: float = 1e-6
) -> LongTimeResult:
    """
    Test for secular drift over long integration.
    
    Parameters:
        integral_func: Candidate integral
        initial_state: Starting state
        mu: Mass ratio
        n_periods: Number of periods (10,000 typical)
        max_drift_rate: Maximum acceptable d(ΔI)/dt per period
        max_total_drift: Maximum acceptable total relative drift
        
    Returns:
        LongTimeResult
    """
    if period is None:
        period = estimate_orbital_period(initial_state, mu)
    
    T_total = n_periods * period
    
    # Use symplectic integrator for long-time accuracy
    from src.python.integrators.symplectic import SymplecticIntegrator
    
    integrator = SymplecticIntegrator(
        method='yoshida8',  # 8th order symplectic
        dt=period / 100
    )
    
    # Integrate in chunks to track drift
    chunk_size = 100  # periods per chunk
    n_chunks = n_periods // chunk_size
    
    state = initial_state.copy()
    I0 = integral_func(state, mu)
    
    times = [0]
    values = [I0]
    
    for chunk in range(n_chunks):
        # Integrate one chunk
        state = integrator.integrate(
            state, mu, 
            t_span=(0, chunk_size * period)
        )
        
        t_current = (chunk + 1) * chunk_size * period
        I_current = integral_func(state, mu)
        
        times.append(t_current)
        values.append(I_current)
    
    times = np.array(times)
    values = np.array(values)
    
    # Compute drift rate via linear regression
    drift_history = (values - I0) / np.abs(I0) if I0 != 0 else values - I0
    
    # Linear fit: drift = a + b*t
    coeffs = np.polyfit(times / period, drift_history, 1)
    drift_rate = coeffs[0]  # Per period
    
    total_drift = np.abs(drift_history[-1])
    
    passed = (np.abs(drift_rate) < max_drift_rate and 
              total_drift < max_total_drift)
    
    return LongTimeResult(
        passed=passed,
        initial_value=I0,
        final_value=values[-1],
        drift_rate=drift_rate,
        total_drift=total_drift,
        integration_time=T_total,
        n_periods=n_periods,
        drift_history=drift_history,
        times=times
    )
```

### Multi-Trajectory Sampling

Test across diverse initial conditions:

```python
@dataclass
class MultiTrajectoryResult:
    """Results from multi-trajectory conservation test."""
    passed: bool
    n_trajectories: int
    n_passed: int
    pass_rate: float
    worst_error: float
    mean_error: float
    std_error: float
    failed_indices: List[int]
    errors: np.ndarray

def test_multi_trajectory(
    integral_func: Callable,
    mu: float,
    n_trajectories: int = 1000,
    n_periods: int = 100,
    tolerance: float = 1e-10,
    seed: int = 42,
    jacobi_range: tuple = (2.5, 3.5)
) -> MultiTrajectoryResult:
    """
    Test conservation across many initial conditions.
    
    Parameters:
        integral_func: Candidate integral
        mu: Mass ratio
        n_trajectories: Number of test trajectories
        n_periods: Integration length per trajectory
        tolerance: Per-trajectory tolerance
        jacobi_range: Range of Jacobi constants to sample
        
    Returns:
        MultiTrajectoryResult
    """
    np.random.seed(seed)
    
    errors = []
    failed_indices = []
    
    for i in range(n_trajectories):
        # Generate valid initial condition
        state0 = generate_random_state(mu, jacobi_range)
        
        # Run short-time test
        result = test_short_time_conservation(
            integral_func, state0, mu,
            n_periods=n_periods,
            tolerance=tolerance
        )
        
        errors.append(result.relative_error)
        
        if not result.passed:
            failed_indices.append(i)
    
    errors = np.array(errors)
    n_passed = n_trajectories - len(failed_indices)
    pass_rate = n_passed / n_trajectories
    
    return MultiTrajectoryResult(
        passed=pass_rate > 0.999,  # 99.9% pass rate
        n_trajectories=n_trajectories,
        n_passed=n_passed,
        pass_rate=pass_rate,
        worst_error=np.max(errors),
        mean_error=np.mean(errors),
        std_error=np.std(errors),
        failed_indices=failed_indices,
        errors=errors
    )


def generate_random_state(
    mu: float, 
    jacobi_range: tuple,
    region: str = 'l2_vicinity'
) -> np.ndarray:
    """
    Generate random valid initial state.
    
    Parameters:
        mu: Mass ratio
        jacobi_range: (C_min, C_max) for Jacobi constant
        region: 'l2_vicinity', 'l4_l5', 'wide'
    """
    while True:
        if region == 'l2_vicinity':
            x = np.random.uniform(1.0, 1.2)
            y = np.random.uniform(-0.3, 0.3)
        elif region == 'l4_l5':
            # Near triangular Lagrange points
            angle = np.random.choice([np.pi/3, -np.pi/3])
            r = np.random.uniform(0.9, 1.1)
            x = r * np.cos(angle) - mu + 0.5
            y = r * np.sin(angle)
        else:  # wide
            x = np.random.uniform(0.5, 1.5)
            y = np.random.uniform(-1.0, 1.0)
        
        z = np.random.uniform(-0.1, 0.1)
        
        # Check valid position (not too close to primaries)
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        
        if r1 < 0.05 or r2 < 0.05:
            continue
        
        # Compute velocity for desired Jacobi constant
        C_target = np.random.uniform(*jacobi_range)
        Omega = 0.5*(x**2 + y**2) + (1-mu)/r1 + mu/r2
        
        v_squared = 2*Omega - C_target
        if v_squared < 0:
            continue
        
        v_mag = np.sqrt(v_squared)
        
        # Random velocity direction
        phi = np.random.uniform(0, 2*np.pi)
        theta = np.random.uniform(-np.pi/4, np.pi/4)
        
        vx = v_mag * np.cos(phi) * np.cos(theta)
        vy = v_mag * np.sin(phi) * np.cos(theta)
        vz = v_mag * np.sin(theta)
        
        return np.array([x, y, z, vx, vy, vz])
```

## Stage B: Floquet Stability Analysis

### Computing Floquet Multipliers

```python
from src.python.validation.floquet import FloquetAnalyzer

@dataclass
class FloquetResult:
    """Floquet analysis results."""
    multipliers: np.ndarray
    exponents: np.ndarray
    stability_type: str
    monodromy_matrix: np.ndarray
    integral_variation: float  # How much integral varies over period

def analyze_floquet_stability(
    integral_func: Callable,
    orbit: 'PeriodicOrbit',
    mu: float
) -> FloquetResult:
    """
    Analyze Floquet stability of integral along periodic orbit.
    
    For a true integral, its variation should be zero (up to numerical error)
    and this should be reflected in the Floquet structure.
    """
    # Compute monodromy matrix
    M = compute_monodromy_matrix(orbit, mu)
    
    # Floquet multipliers
    eigenvalues = np.linalg.eigvals(M)
    multipliers = np.sort(np.abs(eigenvalues))[::-1]
    
    # Floquet exponents
    T = orbit.period
    exponents = np.log(eigenvalues) / T
    
    # Stability classification
    if np.all(np.abs(multipliers - 1) < 1e-8):
        stability_type = 'neutrally_stable'
    elif np.any(multipliers > 1 + 1e-8):
        stability_type = 'unstable'
    else:
        stability_type = 'stable'
    
    # Compute integral variation over one period
    n_samples = 1000
    times = np.linspace(0, orbit.period, n_samples)
    values = [integral_func(orbit.state_at(t), mu) for t in times]
    integral_variation = np.max(values) - np.min(values)
    
    return FloquetResult(
        multipliers=multipliers,
        exponents=exponents,
        stability_type=stability_type,
        monodromy_matrix=M,
        integral_variation=integral_variation
    )
```

### Near-Periodic Behavior

Test how the integral behaves near periodic orbits:

```python
def test_near_periodic(
    integral_func: Callable,
    orbit: 'PeriodicOrbit',
    mu: float,
    perturbation_sizes: List[float] = [1e-6, 1e-5, 1e-4, 1e-3],
    n_directions: int = 10
) -> dict:
    """
    Test integral behavior for perturbations off periodic orbit.
    
    A true integral should remain nearly constant even when
    perturbed off the periodic orbit.
    """
    results = {}
    
    for eps in perturbation_sizes:
        deviations = []
        
        for _ in range(n_directions):
            # Random perturbation direction
            direction = np.random.randn(6)
            direction /= np.linalg.norm(direction)
            
            # Perturbed initial condition
            state0_perturbed = orbit.state0 + eps * direction
            
            # Integrate perturbed trajectory
            result = test_short_time_conservation(
                integral_func, state0_perturbed, mu,
                n_periods=10
            )
            
            deviations.append(result.relative_error)
        
        results[eps] = {
            'mean_deviation': np.mean(deviations),
            'max_deviation': np.max(deviations),
            'std_deviation': np.std(deviations)
        }
    
    return results
```

### Resonance Sensitivity

Check behavior near resonances where integrals may fail:

```python
def test_resonance_sensitivity(
    integral_func: Callable,
    mu: float,
    resonance_orders: List[tuple] = [(1,1), (2,1), (3,2), (1,2)],
    n_samples: int = 100
) -> dict:
    """
    Test integral near mean-motion resonances.
    
    Some integrals may break down near specific resonances.
    """
    from src.python.orbits.resonances import find_resonant_orbit
    
    results = {}
    
    for p, q in resonance_orders:
        try:
            orbit = find_resonant_orbit(mu, p, q)
            
            # Test conservation near this resonance
            errors = []
            for _ in range(n_samples):
                # Small perturbation from resonant orbit
                state0 = orbit.state0 + 1e-4 * np.random.randn(6)
                
                result = test_short_time_conservation(
                    integral_func, state0, mu, n_periods=50
                )
                errors.append(result.relative_error)
            
            results[f'{p}:{q}'] = {
                'mean_error': np.mean(errors),
                'max_error': np.max(errors),
                'orbit_period': orbit.period
            }
            
        except Exception as e:
            results[f'{p}:{q}'] = {'error': str(e)}
    
    return results
```

## Stage C: Statistical Testing

### Monte Carlo Validation

```python
@dataclass
class MonteCarloResult:
    """Results from Monte Carlo validation."""
    passed: bool
    n_samples: int
    pass_rate: float
    confidence_interval: tuple
    error_distribution: np.ndarray
    percentiles: dict

def monte_carlo_validation(
    integral_func: Callable,
    mu: float,
    n_samples: int = 10000,
    n_periods: int = 100,
    tolerance: float = 1e-10,
    confidence: float = 0.999,
    seed: int = 42
) -> MonteCarloResult:
    """
    Monte Carlo validation of integral conservation.
    
    Parameters:
        integral_func: Candidate integral
        mu: Mass ratio
        n_samples: Number of Monte Carlo samples
        n_periods: Integration time per sample
        tolerance: Conservation tolerance
        confidence: Required confidence level
        
    Returns:
        MonteCarloResult
    """
    np.random.seed(seed)
    
    errors = []
    passes = 0
    
    for i in range(n_samples):
        # Generate random initial condition
        state0 = generate_random_state(mu, jacobi_range=(2.5, 3.5))
        
        # Test conservation
        result = test_short_time_conservation(
            integral_func, state0, mu,
            n_periods=n_periods,
            tolerance=tolerance
        )
        
        errors.append(result.relative_error)
        if result.passed:
            passes += 1
        
        # Progress reporting
        if (i + 1) % 1000 == 0:
            print(f"Monte Carlo: {i+1}/{n_samples} ({100*passes/(i+1):.1f}% passing)")
    
    errors = np.array(errors)
    pass_rate = passes / n_samples
    
    # Confidence interval via Wilson score
    from scipy.stats import norm
    z = norm.ppf(1 - (1 - confidence) / 2)
    n = n_samples
    p = pass_rate
    
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    margin = z * np.sqrt(p * (1-p) / n + z**2 / (4*n**2)) / denom
    
    ci = (center - margin, center + margin)
    
    # Percentiles
    percentiles = {
        '50%': np.percentile(errors, 50),
        '90%': np.percentile(errors, 90),
        '95%': np.percentile(errors, 95),
        '99%': np.percentile(errors, 99),
        '99.9%': np.percentile(errors, 99.9)
    }
    
    return MonteCarloResult(
        passed=ci[0] > confidence,
        n_samples=n_samples,
        pass_rate=pass_rate,
        confidence_interval=ci,
        error_distribution=errors,
        percentiles=percentiles
    )
```

### Hypothesis Testing

```python
from scipy import stats

@dataclass
class HypothesisTestResult:
    """Results from statistical hypothesis test."""
    test_name: str
    null_hypothesis: str
    alternative: str
    statistic: float
    p_value: float
    reject_null: bool
    conclusion: str

def hypothesis_test_conservation(
    integral_func: Callable,
    mu: float,
    n_samples: int = 1000,
    n_periods: int = 100,
    alpha: float = 0.01
) -> HypothesisTestResult:
    """
    Statistical hypothesis test for conservation.
    
    H₀: Integral is NOT conserved (drift rate ≠ 0)
    H₁: Integral IS conserved (drift rate = 0)
    
    We want to REJECT H₀ to conclude conservation.
    """
    np.random.seed(42)
    
    drift_rates = []
    
    for _ in range(n_samples):
        state0 = generate_random_state(mu, jacobi_range=(2.5, 3.5))
        
        # Measure drift rate
        result = test_long_time_conservation(
            integral_func, state0, mu,
            n_periods=n_periods
        )
        drift_rates.append(result.drift_rate)
    
    drift_rates = np.array(drift_rates)
    
    # One-sample t-test: is mean drift significantly different from 0?
    t_stat, p_value_two_sided = stats.ttest_1samp(drift_rates, 0)
    
    # We want drift = 0, so high p-value is GOOD
    # But we're testing if we can REJECT non-conservation
    # So we need the drift to be indistinguishable from 0
    
    # Use equivalence testing (TOST)
    # Define equivalence bounds
    epsilon = 1e-12  # Acceptable drift rate
    
    # TOST: two one-sided t-tests
    t_upper = (np.mean(drift_rates) - epsilon) / (np.std(drift_rates) / np.sqrt(n_samples))
    t_lower = (np.mean(drift_rates) + epsilon) / (np.std(drift_rates) / np.sqrt(n_samples))
    
    p_upper = stats.t.cdf(t_upper, df=n_samples-1)
    p_lower = 1 - stats.t.cdf(t_lower, df=n_samples-1)
    
    p_tost = max(p_upper, p_lower)
    
    reject_null = p_tost < alpha
    
    if reject_null:
        conclusion = "CONSERVED: Drift rate is equivalent to zero"
    else:
        conclusion = "NOT CONSERVED: Cannot establish equivalence to zero drift"
    
    return HypothesisTestResult(
        test_name="TOST Equivalence Test",
        null_hypothesis="Drift rate is NOT equivalent to zero",
        alternative="Drift rate IS equivalent to zero",
        statistic=p_tost,
        p_value=p_tost,
        reject_null=reject_null,
        conclusion=conclusion
    )
```

### Comparing with Known Integrals

```python
def compare_with_jacobi(
    candidate_func: Callable,
    mu: float,
    n_samples: int = 1000,
    n_periods: int = 100
) -> dict:
    """
    Compare candidate's conservation quality with Jacobi constant.
    
    Jacobi constant is known to be exactly conserved, so it sets
    the numerical baseline.
    """
    def jacobi_constant(state, mu):
        x, y, z, vx, vy, vz = state
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        Omega = 0.5*(x**2 + y**2) + (1-mu)/r1 + mu/r2
        return 2*Omega - (vx**2 + vy**2 + vz**2)
    
    jacobi_errors = []
    candidate_errors = []
    
    for _ in range(n_samples):
        state0 = generate_random_state(mu, jacobi_range=(2.5, 3.5))
        
        # Test Jacobi
        jac_result = test_short_time_conservation(
            jacobi_constant, state0, mu, n_periods=n_periods
        )
        jacobi_errors.append(jac_result.relative_error)
        
        # Test candidate
        cand_result = test_short_time_conservation(
            candidate_func, state0, mu, n_periods=n_periods
        )
        candidate_errors.append(cand_result.relative_error)
    
    jacobi_errors = np.array(jacobi_errors)
    candidate_errors = np.array(candidate_errors)
    
    # Paired comparison
    t_stat, p_value = stats.ttest_rel(candidate_errors, jacobi_errors)
    
    # Ratio of errors
    error_ratio = np.median(candidate_errors) / np.median(jacobi_errors)
    
    return {
        'jacobi_median_error': np.median(jacobi_errors),
        'candidate_median_error': np.median(candidate_errors),
        'error_ratio': error_ratio,
        't_statistic': t_stat,
        'p_value': p_value,
        'candidate_as_good': error_ratio < 10,  # Within order of magnitude
        'candidate_better': error_ratio < 1
    }
```

## Complete Validation Pipeline

```python
@dataclass
class ValidationResult:
    """Complete numerical validation results."""
    passed: bool
    short_time: ConservationTestResult
    long_time: LongTimeResult
    multi_trajectory: MultiTrajectoryResult
    floquet: Optional[FloquetResult]
    monte_carlo: MonteCarloResult
    hypothesis: HypothesisTestResult
    jacobi_comparison: dict
    summary: str

class NumericalValidator:
    """Complete numerical validation pipeline."""
    
    def __init__(self, mu: float, verbose: bool = True):
        self.mu = mu
        self.verbose = verbose
    
    def validate(
        self,
        integral_func: Callable,
        n_trajectories: int = 1000,
        short_periods: int = 100,
        long_periods: int = 10000,
        monte_carlo_samples: int = 10000,
        periodic_orbit: 'PeriodicOrbit' = None
    ) -> ValidationResult:
        """
        Run complete numerical validation pipeline.
        """
        if self.verbose:
            print("="*60)
            print("NUMERICAL ROBUSTNESS VALIDATION")
            print("="*60)
        
        # Generate reference initial condition
        state0 = generate_random_state(self.mu, jacobi_range=(3.0, 3.2))
        
        # Stage A: Trajectory Tests
        if self.verbose:
            print("\n--- Stage A: Trajectory Conservation ---")
        
        # A1: Short-time
        if self.verbose:
            print("A1: Short-time conservation test...")
        short_time = test_short_time_conservation(
            integral_func, state0, self.mu, n_periods=short_periods
        )
        if self.verbose:
            print(f"    Relative error: {short_time.relative_error:.2e}")
            print(f"    Passed: {short_time.passed}")
        
        # A2: Long-time
        if self.verbose:
            print("A2: Long-time drift test...")
        long_time = test_long_time_conservation(
            integral_func, state0, self.mu, n_periods=long_periods
        )
        if self.verbose:
            print(f"    Drift rate: {long_time.drift_rate:.2e} per period")
            print(f"    Total drift: {long_time.total_drift:.2e}")
            print(f"    Passed: {long_time.passed}")
        
        # A3: Multi-trajectory
        if self.verbose:
            print(f"A3: Multi-trajectory test ({n_trajectories} trajectories)...")
        multi_traj = test_multi_trajectory(
            integral_func, self.mu, n_trajectories=n_trajectories
        )
        if self.verbose:
            print(f"    Pass rate: {multi_traj.pass_rate:.2%}")
            print(f"    Worst error: {multi_traj.worst_error:.2e}")
            print(f"    Passed: {multi_traj.passed}")
        
        # Stage B: Floquet Analysis
        floquet = None
        if periodic_orbit is not None:
            if self.verbose:
                print("\n--- Stage B: Floquet Analysis ---")
            floquet = analyze_floquet_stability(
                integral_func, periodic_orbit, self.mu
            )
            if self.verbose:
                print(f"    Stability: {floquet.stability_type}")
                print(f"    Integral variation: {floquet.integral_variation:.2e}")
        
        # Stage C: Statistical Tests
        if self.verbose:
            print("\n--- Stage C: Statistical Tests ---")
        
        # C1: Monte Carlo
        if self.verbose:
            print(f"C1: Monte Carlo validation ({monte_carlo_samples} samples)...")
        mc_result = monte_carlo_validation(
            integral_func, self.mu, n_samples=monte_carlo_samples
        )
        if self.verbose:
            print(f"    Pass rate: {mc_result.pass_rate:.4%}")
            print(f"    99.9th percentile error: {mc_result.percentiles['99.9%']:.2e}")
            print(f"    Passed: {mc_result.passed}")
        
        # C2: Hypothesis test
        if self.verbose:
            print("C2: Hypothesis test...")
        hyp_result = hypothesis_test_conservation(
            integral_func, self.mu, n_samples=1000
        )
        if self.verbose:
            print(f"    TOST p-value: {hyp_result.p_value:.4f}")
            print(f"    Conclusion: {hyp_result.conclusion}")
        
        # C3: Jacobi comparison
        if self.verbose:
            print("C3: Comparison with Jacobi constant...")
        jacobi_comp = compare_with_jacobi(
            integral_func, self.mu, n_samples=1000
        )
        if self.verbose:
            print(f"    Error ratio: {jacobi_comp['error_ratio']:.2f}x Jacobi")
            print(f"    As good as Jacobi: {jacobi_comp['candidate_as_good']}")
        
        # Overall verdict
        passed = (
            short_time.passed and
            long_time.passed and
            multi_traj.passed and
            mc_result.passed and
            hyp_result.reject_null and
            jacobi_comp['candidate_as_good']
        )
        
        summary = self._generate_summary(
            passed, short_time, long_time, multi_traj,
            floquet, mc_result, hyp_result, jacobi_comp
        )
        
        if self.verbose:
            print("\n" + "="*60)
            print("VERDICT:", "✓ PASSED" if passed else "✗ FAILED")
            print("="*60)
        
        return ValidationResult(
            passed=passed,
            short_time=short_time,
            long_time=long_time,
            multi_trajectory=multi_traj,
            floquet=floquet,
            monte_carlo=mc_result,
            hypothesis=hyp_result,
            jacobi_comparison=jacobi_comp,
            summary=summary
        )
    
    def _generate_summary(self, passed, short_time, long_time, multi_traj,
                          floquet, mc_result, hyp_result, jacobi_comp) -> str:
        lines = ["Numerical Validation Summary:"]
        lines.append(f"  Overall: {'PASSED' if passed else 'FAILED'}")
        lines.append(f"  Short-time conservation: {'✓' if short_time.passed else '✗'}")
        lines.append(f"  Long-time stability: {'✓' if long_time.passed else '✗'}")
        lines.append(f"  Multi-trajectory: {'✓' if multi_traj.passed else '✗'} ({multi_traj.pass_rate:.1%})")
        lines.append(f"  Monte Carlo: {'✓' if mc_result.passed else '✗'} ({mc_result.pass_rate:.1%})")
        lines.append(f"  Statistical: {'✓' if hyp_result.reject_null else '✗'}")
        lines.append(f"  vs Jacobi: {'✓' if jacobi_comp['candidate_as_good'] else '✗'} ({jacobi_comp['error_ratio']:.1f}x)")
        return "\n".join(lines)
```

## Diagnostic Tools

### Visualizing Conservation

```python
import matplotlib.pyplot as plt

def plot_conservation_history(result: ConservationTestResult, save_path: str = None):
    """Plot integral value over time."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    
    # Raw values
    ax1.plot(result.times, result.values, 'b-', linewidth=0.5)
    ax1.axhline(y=result.initial_value, color='r', linestyle='--', label='Initial')
    ax1.set_ylabel('Integral Value')
    ax1.legend()
    ax1.set_title('Integral Conservation')
    
    # Deviations
    ax2.semilogy(result.times, result.deviations + 1e-16, 'b-', linewidth=0.5)
    ax2.axhline(y=1e-10, color='r', linestyle='--', label='Tolerance')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('|I(t) - I(0)|')
    ax2.legend()
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def plot_drift_analysis(result: LongTimeResult, save_path: str = None):
    """Plot drift over long integration."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(result.times / result.n_periods * 100, result.drift_history * 100, 
            'b-', linewidth=1, label='Measured drift')
    
    # Linear fit
    fit_line = np.polyval(
        [result.drift_rate * result.n_periods / 100, result.drift_history[0] * 100],
        result.times / result.n_periods * 100
    )
    ax.plot(result.times / result.n_periods * 100, fit_line, 
            'r--', label=f'Linear fit (rate={result.drift_rate:.2e}/period)')
    
    ax.set_xlabel('Integration Progress (%)')
    ax.set_ylabel('Relative Drift (%)')
    ax.set_title('Long-Time Drift Analysis')
    ax.legend()
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()


def plot_error_distribution(result: MonteCarloResult, save_path: str = None):
    """Plot error distribution from Monte Carlo."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Histogram
    ax1.hist(np.log10(result.error_distribution + 1e-16), bins=50, 
             density=True, alpha=0.7, color='steelblue')
    ax1.axvline(x=np.log10(1e-10), color='r', linestyle='--', label='Tolerance')
    ax1.set_xlabel('log₁₀(Relative Error)')
    ax1.set_ylabel('Density')
    ax1.set_title('Error Distribution')
    ax1.legend()
    
    # CDF
    sorted_errors = np.sort(result.error_distribution)
    cdf = np.arange(1, len(sorted_errors)+1) / len(sorted_errors)
    ax2.semilogx(sorted_errors, cdf * 100, 'b-')
    ax2.axvline(x=1e-10, color='r', linestyle='--', label='Tolerance')
    ax2.axhline(y=99.9, color='g', linestyle=':', label='99.9% threshold')
    ax2.set_xlabel('Relative Error')
    ax2.set_ylabel('Cumulative %')
    ax2.set_title('Cumulative Distribution')
    ax2.legend()
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()
```

## Tests

```bash
pytest tests/validation/test_trajectory_conservation.py -v
pytest tests/validation/test_long_time_integration.py -v
pytest tests/validation/test_floquet_analysis.py -v
pytest tests/validation/test_monte_carlo_validation.py -v
pytest tests/validation/test_numerical_validator.py -v
```

## References

- `references/trajectory-validation.md` - Trajectory integration methods
- `references/floquet-stability.md` - Floquet multiplier theory
- `references/statistical-testing.md` - Statistical hypothesis testing
- Hairer, E., Lubich, C., & Wanner, G. (2006). *Geometric Numerical Integration*
- Lichtenberg, A.J. & Lieberman, M.A. (1992). *Regular and Chaotic Dynamics*
