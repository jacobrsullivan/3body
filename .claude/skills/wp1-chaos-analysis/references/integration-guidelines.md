# Integration Time Guidelines for Chaos Analysis

Guidelines for selecting integration times, period estimation, and handling special cases in chaos indicator computation.

## Table of Contents

1. [Period Estimation Methods](#period-estimation-methods)
2. [Integration Time Selection](#integration-time-selection)
3. [Timestep Selection](#timestep-selection)
4. [Special Cases](#special-cases)
5. [Convergence Criteria](#convergence-criteria)
6. [Performance Optimization](#performance-optimization)

---

## Period Estimation Methods

### Method 1: Jacobi Constant Based

For orbits far from the primaries, use the linearized period near the Lagrange points:

```python
def estimate_period_jacobi(C, mu, L_point='L2'):
    """
    Estimate orbital period from Jacobi constant.

    Works best for orbits near Lagrange points.
    """
    from src.python.utils.equilibrium import get_lagrange_point, linearized_frequency

    # Get Lagrange point location
    L_pos = get_lagrange_point(mu, L_point)

    # Linearized frequency at L point
    omega = linearized_frequency(mu, L_point)

    # Approximate period
    T_approx = 2 * np.pi / omega

    return T_approx
```

### Method 2: Initial Velocity Based

For general orbits, estimate from initial kinetic energy:

```python
def estimate_period_velocity(state0, mu):
    """
    Estimate period from initial state.

    Uses characteristic velocity and distance scales.
    """
    x, y, z, vx, vy, vz = state0

    # Distance to primaries
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)

    # Characteristic distance
    r_char = min(r1, r2)

    # Velocity magnitude
    v = np.sqrt(vx**2 + vy**2 + vz**2)

    # Kepler-like estimate: T ~ 2π * r^(3/2) / sqrt(GM)
    # In normalized units, GM ~ 1
    T_kepler = 2 * np.pi * r_char**1.5

    # Correction for CR3BP (empirical)
    T_approx = T_kepler * (1 + 0.5 * (1 - r_char))

    return T_approx
```

### Method 3: Numerical Detection

Most accurate but requires short integration:

```python
def estimate_period_numerical(state0, mu, max_periods=5):
    """
    Estimate period by detecting Poincaré section crossings.

    Most accurate for quasi-periodic and periodic orbits.
    """
    from src.python.utils.poincare import detect_crossings

    # Rough initial estimate
    T_rough = estimate_period_velocity(state0, mu)

    # Integrate for ~5 rough periods
    integrator = IAS15Integrator(mu=mu)
    times, states = integrator.integrate(
        state0,
        t_span=(0, max_periods * T_rough),
        dt=T_rough / 100
    )

    # Detect y=0 crossings (Poincaré section)
    crossings = detect_crossings(times, states, plane='y')

    if len(crossings) >= 2:
        # Period from crossing times
        periods = np.diff(crossings)
        T_estimated = np.median(periods)
    else:
        # Fall back to rough estimate
        T_estimated = T_rough

    return T_estimated
```

### Recommended Approach

```python
def estimate_orbital_period(state0, mu, method='auto'):
    """
    Estimate orbital period using appropriate method.

    Parameters:
        state0: Initial state [x, y, z, vx, vy, vz]
        mu: Mass ratio
        method: 'auto', 'velocity', 'numerical', or 'jacobi'

    Returns:
        T_period: Estimated orbital period
    """
    if method == 'auto':
        # Use velocity method as default (fast, reasonably accurate)
        T_velocity = estimate_period_velocity(state0, mu)

        # Refine with numerical detection if orbit is bounded
        try:
            T_numerical = estimate_period_numerical(state0, mu)
            # Use numerical if it's close to velocity estimate
            if 0.5 < T_numerical / T_velocity < 2.0:
                return T_numerical
        except:
            pass

        return T_velocity

    elif method == 'velocity':
        return estimate_period_velocity(state0, mu)

    elif method == 'numerical':
        return estimate_period_numerical(state0, mu)

    elif method == 'jacobi':
        C = jacobi_constant(state0, mu)
        return estimate_period_jacobi(C, mu)
```

---

## Integration Time Selection

### By Indicator Type

| Indicator | Minimum Time | Recommended Time | Extended Time |
|-----------|--------------|------------------|---------------|
| FLI | 20 periods | 50 periods | 100 periods |
| MEGNO | 50 periods | 100 periods | 500 periods |
| OFLI | 30 periods | 50 periods | 100 periods |
| SALI | 50 periods | 100 periods | 500 periods |

### By Use Case

| Use Case | Integration Time | Rationale |
|----------|------------------|-----------|
| Quick screening | 50 T | Fast FLI evaluation |
| Final classification | 100 T | MEGNO convergence |
| Parameter space mapping | 50 T | Balance speed/accuracy |
| WP4 preparation | 1000 T | High-precision validation |
| Weak chaos detection | 500 T | SALI convergence |
| Near-resonance | 500 T | Resonant dynamics slower |

### Implementation

```python
def get_integration_time(
    T_period,
    use_case='classification',
    indicator='megno'
):
    """
    Get recommended integration time.

    Parameters:
        T_period: Orbital period
        use_case: 'screening', 'classification', 'validation', 'wp4'
        indicator: 'fli', 'megno', 'ofli', 'sali'

    Returns:
        t_max: Recommended integration time
    """
    # Base multipliers by indicator
    base_periods = {
        'fli': 50,
        'megno': 100,
        'ofli': 50,
        'sali': 100
    }

    # Use case multipliers
    use_case_factor = {
        'screening': 0.5,
        'classification': 1.0,
        'mapping': 0.5,
        'validation': 5.0,
        'wp4': 10.0
    }

    n_periods = base_periods.get(indicator, 100)
    factor = use_case_factor.get(use_case, 1.0)

    return n_periods * factor * T_period
```

---

## Timestep Selection

### General Guidelines

| Precision Tier | Timestep (dt/T) | Absolute dt |
|----------------|-----------------|-------------|
| Tier 1 | T/100 - T/50 | 0.01 - 0.1 |
| Tier 2 | T/1000 - T/500 | 0.001 - 0.01 |

### Adaptive vs Fixed

**IAS15 (Adaptive)**:
- Internal timestep adapts automatically
- `dt` parameter is output sampling rate only
- Recommended: dt = T/100 for output

**Yoshida8 (Fixed)**:
- Timestep affects accuracy directly
- Recommended: dt = T/500 for standard, dt = T/1000 for high precision

**AdaptiveSymplectic**:
- Error-controlled adaptive stepping
- `tol` parameter controls accuracy
- Recommended: tol = 1e-14 (Tier 1), tol = 1e-20 (Tier 2)

### Implementation

```python
def get_timestep(T_period, integrator='ias15', tier='tier1'):
    """
    Get recommended timestep.

    Parameters:
        T_period: Orbital period
        integrator: 'ias15', 'yoshida8', 'adaptive_symplectic'
        tier: 'tier1' or 'tier2'

    Returns:
        dt: Recommended timestep
    """
    if integrator == 'ias15':
        # Output timestep (internal is adaptive)
        return T_period / 100

    elif integrator == 'yoshida8':
        if tier == 'tier1':
            return T_period / 500
        else:
            return T_period / 1000

    elif integrator == 'adaptive_symplectic':
        # Return tolerance instead
        if tier == 'tier1':
            return 1e-14  # This is tol, not dt
        else:
            return 1e-20
```

---

## Special Cases

### Near-Resonance Orbits

Orbits near mean-motion resonances require extended integration:

```python
def handle_near_resonance(state0, mu, base_t_max):
    """
    Adjust integration time for near-resonance orbits.
    """
    from src.python.utils.resonance import detect_resonance

    resonance = detect_resonance(state0, mu, max_order=10)

    if resonance['is_resonant']:
        # Resonance order affects required time
        order = resonance['order']
        strength = resonance['strength']

        # Higher order or stronger resonance needs more time
        multiplier = 2 + order + 3 * strength

        print(f"Near {resonance['ratio']} resonance (order={order})")
        print(f"Extending integration time by factor {multiplier:.1f}")

        return base_t_max * multiplier

    return base_t_max
```

### Close Encounters

Orbits with close approaches need careful timestep control:

```python
def handle_close_encounters(state0, mu, base_dt):
    """
    Adjust timestep for close encounter orbits.
    """
    x, y, z = state0[:3]

    # Distance to primaries
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    r_min = min(r1, r2)

    # Hill radius (approximate)
    r_hill = (mu / 3)**(1/3)

    if r_min < 5 * r_hill:
        # Close to a primary - reduce timestep
        factor = r_min / (5 * r_hill)
        adjusted_dt = base_dt * factor

        print(f"Close encounter detected (r_min={r_min:.4f})")
        print(f"Reducing timestep by factor {factor:.2f}")

        return adjusted_dt

    return base_dt
```

### Escape Detection

Stop integration early if orbit escapes:

```python
def check_escape(state, mu, escape_radius=10.0):
    """
    Check if orbit has escaped the system.
    """
    x, y, z = state[:3]
    r = np.sqrt(x**2 + y**2 + z**2)

    # Check distance from barycenter
    if r > escape_radius:
        return True

    # Check Jacobi constant (if C < C_L1, escape possible)
    C = jacobi_constant(state, mu)
    C_L1 = jacobi_constant_at_lagrange(mu, 'L1')

    if C < C_L1:
        # Escape energetically possible
        vx, vy, vz = state[3:]
        v_radial = (x*vx + y*vy + z*vz) / r

        if v_radial > 0 and r > 2.0:
            return True

    return False
```

### Periodic Orbit Integration

For monodromy matrix computation, integrate exactly one period:

```python
def integrate_periodic_orbit(state0, period, mu, tol=1e-10):
    """
    Integrate periodic orbit for exactly one period.

    Returns state at t=T and monodromy matrix.
    """
    from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator

    integrator = AdaptiveSymplecticIntegrator(
        mu=mu,
        order=6,
        tol=tol
    )

    # Integrate state + variational equations
    times, states, Phi = integrator.integrate_with_variational(
        state0,
        t_span=(0, period),
        return_fundamental=True
    )

    # Check periodicity
    closure_error = np.linalg.norm(states[-1] - state0)
    if closure_error > 1e-8:
        print(f"Warning: Orbit not closed (error={closure_error:.2e})")

    # Monodromy matrix is fundamental matrix at t=T
    monodromy = Phi[-1]

    return states[-1], monodromy
```

---

## Convergence Criteria

### MEGNO Convergence

```python
def check_megno_convergence(megno_history, times, window=10):
    """
    Check if MEGNO has converged.

    Parameters:
        megno_history: Array of ⟨Y⟩(t) values
        times: Time array
        window: Number of periods to check

    Returns:
        converged: Boolean
        classification: 'regular', 'chaotic', or 'borderline'
    """
    # Get last N periods
    T_period = times[-1] / len(times) * 100  # Rough estimate
    idx_window = int(window * len(times) / (times[-1] / T_period))

    recent_megno = megno_history[-idx_window:]

    # Check stability
    mean_megno = np.mean(recent_megno)
    std_megno = np.std(recent_megno)

    # Convergence criteria
    if std_megno < 0.1:
        converged = True

        if mean_megno < 2.5:
            classification = 'regular'
        elif mean_megno > 3.0:
            classification = 'chaotic'
        else:
            classification = 'borderline'
    else:
        converged = False
        classification = 'not_converged'

    return converged, classification
```

### FLI Convergence

```python
def check_fli_convergence(fli_history, times):
    """
    Check FLI growth rate for classification.

    Linear growth → chaotic
    Logarithmic growth → regular
    """
    # Fit growth model
    log_times = np.log(times[10:])  # Skip initial transient
    fli_values = fli_history[10:]

    # Linear fit: FLI = a * t + b
    linear_fit = np.polyfit(times[10:], fli_values, 1)
    linear_slope = linear_fit[0]

    # Log fit: FLI = a * log(t) + b
    log_fit = np.polyfit(log_times, fli_values, 1)
    log_slope = log_fit[0]

    # Compare residuals
    linear_residual = np.std(fli_values - np.polyval(linear_fit, times[10:]))
    log_residual = np.std(fli_values - np.polyval(log_fit, log_times))

    if linear_residual < log_residual:
        # Linear growth dominates → chaotic
        return True, 'chaotic', linear_slope
    else:
        # Log growth dominates → regular
        return True, 'regular', log_slope
```

---

## Performance Optimization

### Batch Processing

```python
def optimize_batch_analysis(initial_conditions, mu):
    """
    Optimize batch chaos analysis.
    """
    # Sort by estimated period (similar orbits together)
    periods = [estimate_period_velocity(ic, mu) for ic in initial_conditions]
    sorted_idx = np.argsort(periods)

    # Process in batches of similar periods
    batch_size = 100
    results = [None] * len(initial_conditions)

    for i in range(0, len(sorted_idx), batch_size):
        batch_idx = sorted_idx[i:i+batch_size]
        batch_ics = [initial_conditions[j] for j in batch_idx]

        # Use common integration time for batch
        T_batch = np.mean([periods[j] for j in batch_idx])
        t_max = 100 * T_batch

        # Process batch
        batch_results = analyze_batch(batch_ics, mu, t_max)

        for j, result in zip(batch_idx, batch_results):
            results[j] = result

    return results
```

### Early Termination

```python
def analyze_with_early_termination(state0, mu, t_max, check_interval=10):
    """
    Analyze with early termination when classification is confident.
    """
    T_period = estimate_orbital_period(state0, mu)

    analyzer = create_cr3bp_chaos_analyzer(mu=mu)

    current_t = 0
    increment = check_interval * T_period

    while current_t < t_max:
        result = analyzer.analyze(
            state0,
            t_max=current_t + increment
        )
        current_t += increment

        # Check if we can classify confidently
        if result['megno'] > 4.0:
            # Clearly chaotic
            return result, 'early_chaotic'

        if result['megno'] < 2.1 and current_t > 50 * T_period:
            # Likely regular (need some integration time)
            return result, 'early_regular'

    return result, 'full_integration'
```

### Memory-Efficient Analysis

```python
def analyze_memory_efficient(state0, mu, t_max, dt):
    """
    Analyze without storing full trajectory.

    Useful for very long integrations.
    """
    from src.python.validation.chaos_indicators import (
        MEGNOIndicator,
        FLIIndicator
    )

    megno = MEGNOIndicator(dynamics_func=cr3bp_dynamics, mu=mu)
    fli = FLIIndicator(dynamics_func=cr3bp_dynamics, mu=mu)

    # Stream processing - don't store full trajectory
    result = {
        'megno': megno.compute_streaming(state0, t_max, dt),
        'fli': fli.compute_streaming(state0, t_max, dt)
    }

    # Classify
    if result['megno'] < 2.5 and result['fli'] < 3.0:
        result['classification'] = 'regular'
    elif result['megno'] > 3.0 or result['fli'] > 4.0:
        result['classification'] = 'chaotic'
    else:
        result['classification'] = 'borderline'

    return result
```
