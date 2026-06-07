# Validation Methods

Comprehensive validation for candidate conserved quantities.

## Table of Contents

1. [Overview](#overview)
2. [Multi-Scale Conservation](#multi-scale-conservation)
3. [Long-Time Stability](#long-time-stability)
4. [Quasi-Periodic Detection](#quasi-periodic-detection)
5. [Statistical Validation](#statistical-validation)
6. [Interpretability Scoring](#interpretability-scoring)

---

## Overview

### The Validation Problem

A function I(x) that appears conserved numerically may be:
1. **True integral**: dI/dt = 0 exactly
2. **Slow drift**: dI/dt ≈ 0 but not zero (slowly varying)
3. **Numerical artifact**: Conservation due to finite precision
4. **Periodic**: I oscillates with trajectory period

### Validation Pipeline

```
Candidate I(x)
     │
     ▼
┌────────────────────┐
│ Multi-Scale Test   │ → Reject if fails at any scale
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Long-Time Test     │ → Reject if drift > threshold
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Statistical Test   │ → Reject if variance too high
└─────────┬──────────┘
          │
          ▼
      Validated!
```

---

## Multi-Scale Conservation

### Theory

A true conserved quantity should remain constant at ALL timescales:
- dt = 0.01 (short-scale)
- dt = 0.1 (medium-scale)
- dt = 1.0 (long-scale)
- dt = 10.0 (very long-scale)

A slowly-varying function may appear conserved at short scales but drift at longer scales.

### Implementation

```python
def multi_scale_conservation_test(candidate_func, times, states,
                                   scales=[0.01, 0.1, 1.0, 10.0],
                                   tolerance=1e-10):
    """
    Test conservation at multiple timescales.

    Args:
        candidate_func: Function I(state) → value
        times: Time array
        states: State array (N × dim)
        scales: Timescales to test (in time units)
        tolerance: Conservation threshold

    Returns:
        Dict mapping scale → (passed, error)
    """
    results = {}

    # Evaluate candidate on full trajectory
    I_values = candidate_func(states)
    dt = times[1] - times[0]

    for scale in scales:
        # Subsample at this scale
        step = max(1, int(scale / dt))
        I_sub = I_values[::step]

        # Compute conservation error
        mean_I = np.mean(I_sub)
        max_deviation = np.max(np.abs(I_sub - mean_I))
        relative_error = max_deviation / (np.abs(mean_I) + 1e-15)

        passed = relative_error < tolerance
        results[scale] = {
            'passed': passed,
            'error': relative_error,
            'max_deviation': max_deviation,
            'mean': mean_I
        }

    return results
```

### Interpretation

| Scale Result | Interpretation |
|--------------|----------------|
| All pass | Likely true integral |
| Short pass, long fail | Slowly varying function |
| All fail | Not conserved |
| Oscillating error | Periodic, not conserved |

---

## Long-Time Stability

### Theory

Integrate for many orbital periods and track cumulative drift:
```
Drift = I(t_final) - I(t_initial)
Drift rate = Drift / (number of periods)
```

A true integral has drift_rate → 0 as precision increases.

### Implementation

```python
def long_time_stability(candidate_func, times, states,
                        n_periods=1000, period_estimate=None):
    """
    Test long-time conservation stability.

    Args:
        candidate_func: Function I(state) → value
        times: Time array
        states: State array
        n_periods: Number of orbital periods to analyze
        period_estimate: Estimated orbital period (auto-detect if None)

    Returns:
        StabilityResult with drift metrics
    """
    # Evaluate candidate
    I_values = candidate_func(states)

    # Estimate period if not provided
    if period_estimate is None:
        period_estimate = estimate_period(times, states)

    # Compute drift over periods
    total_time = times[-1] - times[0]
    n_actual_periods = total_time / period_estimate

    # Linear regression for drift rate
    from scipy.stats import linregress
    slope, intercept, r_value, p_value, std_err = linregress(times, I_values)

    drift_per_period = slope * period_estimate
    total_drift = I_values[-1] - I_values[0]

    # Stability criterion
    mean_I = np.mean(I_values)
    relative_drift = np.abs(total_drift) / (np.abs(mean_I) + 1e-15)

    is_stable = relative_drift < 1e-10 * n_actual_periods

    return {
        'is_stable': is_stable,
        'drift_rate': drift_per_period,
        'total_drift': total_drift,
        'relative_drift': relative_drift,
        'n_periods': n_actual_periods,
        'r_squared': r_value**2,
        'period': period_estimate
    }

def estimate_period(times, states):
    """Estimate orbital period from trajectory."""
    from scipy.fft import fft, fftfreq

    # Use radial distance
    r = np.linalg.norm(states[:, :3], axis=1)
    r_centered = r - np.mean(r)

    dt = times[1] - times[0]
    spectrum = np.abs(fft(r_centered))[:len(r)//2]
    freqs = fftfreq(len(r), dt)[:len(r)//2]

    # Find dominant frequency
    peak_idx = np.argmax(spectrum[1:]) + 1  # Skip DC
    dominant_freq = freqs[peak_idx]

    return 1.0 / dominant_freq if dominant_freq > 0 else times[-1]
```

---

## Quasi-Periodic Detection

### Theory

Quasi-periodic motion has multiple incommensurable frequencies. The power spectrum shows discrete peaks at non-rationally-related frequencies.

**Implications**:
- Quasi-periodic → likely KAM torus → may have additional integrals
- Chaotic → continuous spectrum → unlikely to have hidden integrals

### Implementation

```python
def detect_quasi_periodic(times, states, frequency_threshold=0.1,
                          rationality_threshold=0.01):
    """
    Detect quasi-periodic motion via FFT analysis.

    Args:
        times: Time array
        states: State array
        frequency_threshold: Minimum peak amplitude (relative)
        rationality_threshold: Tolerance for rational frequency ratio

    Returns:
        QuasiPeriodicResult
    """
    from scipy.fft import fft, fftfreq

    # Use radial distance as observable
    r = np.linalg.norm(states[:, :3], axis=1)
    r_centered = r - np.mean(r)

    dt = times[1] - times[0]
    n = len(r)

    # FFT
    spectrum = np.abs(fft(r_centered))[:n//2]
    freqs = fftfreq(n, dt)[:n//2]

    # Find peaks
    threshold = frequency_threshold * np.max(spectrum)
    peaks = []

    for i in range(1, len(spectrum) - 1):
        if (spectrum[i] > threshold and
            spectrum[i] > spectrum[i-1] and
            spectrum[i] > spectrum[i+1]):
            peaks.append({
                'frequency': freqs[i],
                'amplitude': spectrum[i],
                'index': i
            })

    # Sort by amplitude
    peaks.sort(key=lambda x: -x['amplitude'])

    if len(peaks) < 2:
        return {
            'is_quasi_periodic': False,
            'reason': 'Not enough frequency peaks',
            'frequencies': [p['frequency'] for p in peaks],
            'n_peaks': len(peaks)
        }

    # Check if top 2 frequencies are incommensurable
    f1, f2 = peaks[0]['frequency'], peaks[1]['frequency']
    ratio = max(f1, f2) / min(f1, f2)

    # Test against simple rationals
    is_rational = False
    for p in range(1, 10):
        for q in range(1, 10):
            if abs(ratio - p/q) < rationality_threshold:
                is_rational = True
                break

    # Estimate elliptic parameter from frequency ratio
    # m ≈ 16 * (1 - T2/T1)^2 for small eccentricity
    elliptic_m = min(0.99, max(0.01, 16 * (1 - min(f1, f2)/max(f1, f2))**2))

    return {
        'is_quasi_periodic': not is_rational and len(peaks) >= 2,
        'frequencies': [p['frequency'] for p in peaks[:5]],
        'frequency_ratio': ratio,
        'n_peaks': len(peaks),
        'elliptic_parameter': elliptic_m,
        'suggested_m': elliptic_m
    }
```

---

## Statistical Validation

### Variance-Based Test

```python
def variance_conservation_test(candidate_func, states, tolerance=1e-10):
    """
    Test conservation using variance.

    A conserved quantity has zero variance.
    """
    I_values = candidate_func(states)

    mean_I = np.mean(I_values)
    variance = np.var(I_values)
    std = np.std(I_values)

    # Relative variance
    rel_variance = variance / (mean_I**2 + 1e-15)

    passed = rel_variance < tolerance

    return {
        'passed': passed,
        'mean': mean_I,
        'variance': variance,
        'std': std,
        'relative_variance': rel_variance,
        'cv': std / (np.abs(mean_I) + 1e-15)  # Coefficient of variation
    }
```

### Kolmogorov-Smirnov Test

```python
def ks_conservation_test(candidate_func, states):
    """
    Test if I(x) distribution is consistent with constant.

    Use KS test against constant distribution.
    """
    from scipy.stats import kstest

    I_values = candidate_func(states)
    mean_I = np.mean(I_values)

    # Normalize to [0, 1]
    I_min, I_max = np.min(I_values), np.max(I_values)
    if I_max - I_min < 1e-15:
        return {'passed': True, 'p_value': 1.0, 'statistic': 0.0}

    I_normalized = (I_values - I_min) / (I_max - I_min)

    # KS test against uniform (constant would give degenerate distribution)
    statistic, p_value = kstest(I_normalized, 'uniform')

    # High statistic = not uniform = possibly constant
    # This is inverse: we WANT high statistic

    return {
        'passed': statistic > 0.9,  # Very concentrated distribution
        'statistic': statistic,
        'p_value': p_value,
        'range': I_max - I_min
    }
```

---

## Interpretability Scoring

### Function Type Classification

```python
FUNCTION_TYPES = {
    'polynomial': ['x', 'y', 'z', '**2', '**3', 'x*y'],
    'rational': ['1/', '/x', '/y', '/r'],
    'trigonometric': ['sin', 'cos', 'tan'],
    'exponential': ['exp', 'log'],
    'spinor': ['u1', 'u2', 'u3', 'norm'],
    'elliptic': ['sn', 'cn', 'dn'],
    'theta': ['theta'],
}

def classify_function(expression_str):
    """
    Classify expression into function type.
    """
    expr_lower = expression_str.lower()

    scores = {}
    for func_type, keywords in FUNCTION_TYPES.items():
        score = sum(1 for kw in keywords if kw in expr_lower)
        scores[func_type] = score

    if max(scores.values()) == 0:
        return 'unknown'

    return max(scores.keys(), key=lambda k: scores[k])
```

### Interpretability Score

```python
INTERPRETABILITY_SCORES = {
    'polynomial': 1.0,
    'rational': 0.9,
    'trigonometric': 0.85,
    'spinor': 0.8,
    'exponential': 0.75,
    'elliptic': 0.7,
    'theta': 0.6,
    'unknown': 0.3,
}

def interpretability_score(expression_str):
    """
    Score expression interpretability (0 to 1).
    """
    func_type = classify_function(expression_str)
    base_score = INTERPRETABILITY_SCORES.get(func_type, 0.3)

    # Penalize complexity
    n_terms = expression_str.count('+') + expression_str.count('-') + 1
    complexity_penalty = min(0.3, 0.05 * n_terms)

    # Penalize nesting
    n_parens = expression_str.count('(')
    nesting_penalty = min(0.2, 0.02 * n_parens)

    return max(0.1, base_score - complexity_penalty - nesting_penalty)
```

### Physical Symmetry Detection

```python
def detect_physical_symmetry(expression_str, variables=['x', 'y', 'z']):
    """
    Detect physical symmetries in expression.
    """
    symmetries = []

    # Rotation invariance: depends only on r = sqrt(x² + y² + z²)
    if 'sqrt(x**2 + y**2 + z**2)' in expression_str or 'r' in expression_str:
        symmetries.append('rotation_invariant')

    # Translation invariance: depends only on differences
    if all(v not in expression_str for v in variables):
        symmetries.append('translation_invariant')

    # Parity: even in all coordinates
    # (Would need symbolic analysis for proper detection)

    return symmetries
```

---

## Complete Validation Pipeline

```python
class ValidationPipeline:
    """Complete validation pipeline for candidate integrals."""

    def __init__(self, multi_scale_tol=1e-10, drift_tol=1e-12):
        self.multi_scale_tol = multi_scale_tol
        self.drift_tol = drift_tol

    def validate(self, candidate_func, times, states):
        """
        Run full validation pipeline.
        """
        results = {}

        # Multi-scale test
        results['multi_scale'] = multi_scale_conservation_test(
            candidate_func, times, states,
            tolerance=self.multi_scale_tol
        )

        # Long-time stability
        results['stability'] = long_time_stability(
            candidate_func, times, states
        )

        # Statistical test
        results['variance'] = variance_conservation_test(
            candidate_func, states
        )

        # Quasi-periodic check
        results['quasi_periodic'] = detect_quasi_periodic(times, states)

        # Overall verdict
        multi_pass = all(r['passed'] for r in results['multi_scale'].values())
        stability_pass = results['stability']['is_stable']
        variance_pass = results['variance']['passed']

        results['passed'] = multi_pass and stability_pass and variance_pass

        return results
```

---

## References

- Hairer, E. et al. (2006). *Geometric Numerical Integration*
- Meiss, J.D. (1992). "Symplectic maps, variational principles, and transport"
- Skokos, C. (2010). "The Lyapunov characteristic exponents and their computation"
