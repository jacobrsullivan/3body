# Trajectory Validation Methods

Comprehensive guide to trajectory-based conservation testing.

## Overview

Trajectory validation tests whether a candidate integral remains constant along numerically integrated orbits. This is the most direct empirical test of conservation.

## Integration Methods

### Standard Methods

For moderate precision requirements:

```python
from scipy.integrate import solve_ivp
import numpy as np

def integrate_trajectory(
    state0: np.ndarray,
    mu: float,
    t_span: tuple,
    method: str = 'DOP853',
    rtol: float = 1e-12,
    atol: float = 1e-14
) -> 'OdeResult':
    """
    Integrate CR3BP trajectory.
    
    Parameters:
        state0: Initial state [x, y, z, vx, vy, vz]
        mu: Mass ratio
        t_span: (t0, tf) integration bounds
        method: Integration method
        rtol, atol: Tolerances
        
    Returns:
        scipy OdeResult with solution
    """
    def cr3bp_eom(t, state, mu):
        """CR3BP equations of motion."""
        x, y, z, vx, vy, vz = state
        
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        
        ax = 2*vy + x - (1-mu)*(x+mu)/r1**3 - mu*(x-1+mu)/r2**3
        ay = -2*vx + y - (1-mu)*y/r1**3 - mu*y/r2**3
        az = -(1-mu)*z/r1**3 - mu*z/r2**3
        
        return [vx, vy, vz, ax, ay, az]
    
    return solve_ivp(
        lambda t, y: cr3bp_eom(t, y, mu),
        t_span,
        state0,
        method=method,
        rtol=rtol,
        atol=atol,
        dense_output=True
    )
```

### Symplectic Integrators

For long-time integration preserving structure:

```python
class SymplecticIntegrator:
    """Symplectic integrator for Hamiltonian systems."""
    
    def __init__(self, method: str = 'yoshida4', dt: float = 0.001):
        self.method = method
        self.dt = dt
        self._setup_coefficients()
    
    def _setup_coefficients(self):
        """Setup method coefficients."""
        if self.method == 'leapfrog':
            # 2nd order
            self.c = [0.5, 0.5]
            self.d = [1.0]
        elif self.method == 'yoshida4':
            # 4th order Yoshida
            w1 = 1 / (2 - 2**(1/3))
            w0 = -2**(1/3) * w1
            self.c = [w1/2, (w0+w1)/2, (w0+w1)/2, w1/2]
            self.d = [w1, w0, w1]
        elif self.method == 'yoshida8':
            # 8th order - use stored coefficients
            self.c, self.d = self._yoshida8_coefficients()
    
    def _yoshida8_coefficients(self):
        """8th order Yoshida coefficients."""
        # From Yoshida (1990)
        w = [
            0.311790812418427e0,
            -0.155946803821447e1,
            -0.167896928259640e1,
            0.166335809963315e1,
            -0.106458714789183e1,
            0.136934946416871e1,
            0.629030650210433e0
        ]
        # Symmetric extension
        d = w + w[::-1]
        c = [0.5 * (d[0])]
        for i in range(len(d)-1):
            c.append(0.5 * (d[i] + d[i+1]))
        c.append(0.5 * d[-1])
        return c, d
    
    def step(self, q: np.ndarray, p: np.ndarray, mu: float) -> tuple:
        """Single symplectic step."""
        for i, ci in enumerate(self.c[:-1]):
            # Position kick
            q = q + ci * self.dt * p
            
            # Momentum kick
            force = self._compute_force(q, mu)
            p = p + self.d[i] * self.dt * force
        
        # Final position kick
        q = q + self.c[-1] * self.dt * p
        
        return q, p
    
    def _compute_force(self, q: np.ndarray, mu: float) -> np.ndarray:
        """Compute gravitational + centrifugal + Coriolis forces."""
        x, y, z = q
        
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        
        # Gradient of effective potential (with Coriolis from rotating frame)
        fx = x - (1-mu)*(x+mu)/r1**3 - mu*(x-1+mu)/r2**3
        fy = y - (1-mu)*y/r1**3 - mu*y/r2**3
        fz = -(1-mu)*z/r1**3 - mu*z/r2**3
        
        return np.array([fx, fy, fz])
    
    def integrate(
        self, 
        state0: np.ndarray, 
        mu: float,
        t_span: tuple,
        output_times: np.ndarray = None
    ) -> dict:
        """
        Integrate trajectory.
        
        Returns dict with 'times', 'states', 'final_state'
        """
        q = state0[:3].copy()
        p = state0[3:].copy()
        
        t0, tf = t_span
        n_steps = int((tf - t0) / self.dt)
        
        if output_times is not None:
            output_indices = (output_times - t0) / self.dt
            states = []
            times = []
        
        for step in range(n_steps):
            t = t0 + step * self.dt
            
            # Coriolis correction for rotating frame
            p_corrected = p.copy()
            p_corrected[0] -= q[1]  # vx_eff = vx - y (Coriolis)
            p_corrected[1] += q[0]  # vy_eff = vy + x
            
            q, p = self.step(q, p_corrected, mu)
            
            # Undo Coriolis
            p[0] += q[1]
            p[1] -= q[0]
            
            if output_times is not None and step in output_indices:
                states.append(np.concatenate([q, p]))
                times.append(t + self.dt)
        
        final_state = np.concatenate([q, p])
        
        return {
            'final_state': final_state,
            'states': np.array(states) if output_times is not None else None,
            'times': np.array(times) if output_times is not None else None
        }
```

### Regularized Integration

Near collisions, use regularized coordinates:

```python
class RegularizedIntegrator:
    """Integration with Levi-Civita/KS regularization near primaries."""
    
    def __init__(self, mu: float, regularization: str = 'levi_civita'):
        self.mu = mu
        self.regularization = regularization
    
    def integrate_regularized(
        self, 
        state0: np.ndarray,
        t_span: tuple,
        close_primary: int = None
    ) -> dict:
        """
        Integrate with automatic regularization switching.
        
        Parameters:
            state0: Initial state
            t_span: Integration bounds
            close_primary: Which primary (1 or 2) if known close approach
        """
        # Check proximity to primaries
        x, y, z = state0[:3]
        r1 = np.sqrt((x + self.mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + self.mu)**2 + y**2 + z**2)
        
        threshold = 0.01
        
        if r1 < threshold or close_primary == 1:
            return self._integrate_regularized_p1(state0, t_span)
        elif r2 < threshold or close_primary == 2:
            return self._integrate_regularized_p2(state0, t_span)
        else:
            # Standard integration
            return integrate_trajectory(state0, self.mu, t_span)
    
    def _integrate_regularized_p1(self, state0, t_span):
        """Regularized integration near primary 1 (larger mass)."""
        from src.python.lifts.levi_civita import LeviCivitaTransform
        
        lc = LeviCivitaTransform(center=np.array([-self.mu, 0, 0]))
        
        # Transform to regularized coordinates
        u0, pu0 = lc.to_regularized(state0[:3], state0[3:])
        
        # Integrate in regularized coordinates
        # Note: time is also transformed (dt → ds with dt = r·ds)
        # ... regularized integration ...
        
        # Transform back
        q_final, p_final = lc.from_regularized(u_final, pu_final)
        
        return np.concatenate([q_final, p_final])
```

## Conservation Testing

### Basic Conservation Test

```python
def test_conservation_along_trajectory(
    integral_func: callable,
    trajectory: 'OdeResult',
    mu: float,
    n_samples: int = 1000
) -> dict:
    """
    Test conservation of integral along integrated trajectory.
    
    Parameters:
        integral_func: I(state, mu) -> float
        trajectory: scipy OdeResult with dense_output
        mu: Mass ratio
        n_samples: Number of sample points
        
    Returns:
        Dict with statistics
    """
    t0, tf = trajectory.t[0], trajectory.t[-1]
    times = np.linspace(t0, tf, n_samples)
    
    values = []
    for t in times:
        state = trajectory.sol(t)
        values.append(integral_func(state, mu))
    
    values = np.array(values)
    I0 = values[0]
    
    # Statistics
    deviations = values - I0
    abs_deviations = np.abs(deviations)
    
    return {
        'initial_value': I0,
        'final_value': values[-1],
        'max_absolute_deviation': np.max(abs_deviations),
        'mean_absolute_deviation': np.mean(abs_deviations),
        'rms_deviation': np.sqrt(np.mean(deviations**2)),
        'relative_max_deviation': np.max(abs_deviations) / np.abs(I0) if I0 != 0 else np.max(abs_deviations),
        'times': times,
        'values': values,
        'deviations': deviations
    }
```

### Drift Rate Estimation

```python
def estimate_drift_rate(
    integral_func: callable,
    state0: np.ndarray,
    mu: float,
    period: float,
    n_periods: int = 1000
) -> dict:
    """
    Estimate secular drift rate of integral.
    
    Distinguishes:
    - True integrals: drift = 0 (within numerical precision)
    - Approximate integrals: small but nonzero drift
    - Non-integrals: large/irregular drift
    """
    # Integrate trajectory
    t_span = (0, n_periods * period)
    sol = integrate_trajectory(state0, mu, t_span)
    
    # Sample at each period
    period_times = np.arange(0, n_periods + 1) * period
    period_values = [integral_func(sol.sol(t), mu) for t in period_times]
    period_values = np.array(period_values)
    
    I0 = period_values[0]
    deviations = (period_values - I0) / np.abs(I0) if I0 != 0 else period_values - I0
    
    # Linear regression for drift rate
    coeffs = np.polyfit(np.arange(len(period_values)), deviations, 1)
    drift_rate = coeffs[0]  # Per period
    
    # Quadratic fit to detect acceleration
    coeffs2 = np.polyfit(np.arange(len(period_values)), deviations, 2)
    drift_acceleration = coeffs2[0]
    
    # Classification
    if np.abs(drift_rate) < 1e-14 and np.abs(drift_acceleration) < 1e-14:
        classification = 'true_integral'
    elif np.abs(drift_rate) < 1e-10:
        classification = 'approximate_integral'
    else:
        classification = 'not_integral'
    
    return {
        'drift_rate_per_period': drift_rate,
        'drift_acceleration': drift_acceleration,
        'total_drift': deviations[-1],
        'classification': classification,
        'period_values': period_values
    }
```

## Error Analysis

### Integrator Error Assessment

```python
def assess_integrator_accuracy(
    state0: np.ndarray,
    mu: float,
    t_final: float,
    methods: list = ['DOP853', 'RK45', 'Radau']
) -> dict:
    """
    Compare integrator accuracy using Jacobi constant as reference.
    
    The Jacobi constant is analytically conserved, so its numerical
    drift indicates integrator error.
    """
    def jacobi_constant(state, mu):
        x, y, z, vx, vy, vz = state
        r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
        r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
        Omega = 0.5*(x**2 + y**2) + (1-mu)/r1 + mu/r2
        return 2*Omega - (vx**2 + vy**2 + vz**2)
    
    C0 = jacobi_constant(state0, mu)
    
    results = {}
    for method in methods:
        sol = integrate_trajectory(
            state0, mu, (0, t_final),
            method=method
        )
        
        # Final Jacobi constant
        C_final = jacobi_constant(sol.y[:, -1], mu)
        relative_error = np.abs(C_final - C0) / np.abs(C0)
        
        # Track over trajectory
        times = np.linspace(0, t_final, 1000)
        C_history = [jacobi_constant(sol.sol(t), mu) for t in times]
        max_error = np.max(np.abs(np.array(C_history) - C0)) / np.abs(C0)
        
        results[method] = {
            'final_relative_error': relative_error,
            'max_relative_error': max_error,
            'n_function_evals': sol.nfev,
            'C_history': C_history
        }
    
    return results
```

### Numerical vs Physical Error

```python
def separate_numerical_physical_error(
    candidate_func: callable,
    jacobi_func: callable,
    state0: np.ndarray,
    mu: float,
    t_final: float
) -> dict:
    """
    Separate numerical integration error from physical non-conservation.
    
    Strategy: Compare candidate drift to Jacobi drift.
    Jacobi drift = numerical error only (it's exactly conserved)
    Candidate drift = numerical + physical
    Physical drift = Candidate drift - Jacobi drift (roughly)
    """
    sol = integrate_trajectory(state0, mu, (0, t_final))
    
    times = np.linspace(0, t_final, 1000)
    
    # Jacobi history
    J0 = jacobi_func(state0, mu)
    J_history = np.array([jacobi_func(sol.sol(t), mu) for t in times])
    J_drift = (J_history - J0) / np.abs(J0)
    
    # Candidate history
    I0 = candidate_func(state0, mu)
    I_history = np.array([candidate_func(sol.sol(t), mu) for t in times])
    I_drift = (I_history - I0) / np.abs(I0) if I0 != 0 else I_history - I0
    
    # Estimate physical component
    # Assumption: numerical error affects both similarly
    # So physical drift ≈ |I_drift| - |J_drift|
    physical_drift = np.abs(I_drift) - np.abs(J_drift)
    
    return {
        'jacobi_max_drift': np.max(np.abs(J_drift)),
        'candidate_max_drift': np.max(np.abs(I_drift)),
        'estimated_physical_drift': np.max(physical_drift),
        'numerical_dominated': np.max(np.abs(I_drift)) < 2 * np.max(np.abs(J_drift)),
        'J_history': J_history,
        'I_history': I_history
    }
```

## Multi-Precision Verification

### Extended Precision Integration

```python
from mpmath import mp, mpf

def high_precision_conservation_test(
    integral_func: callable,
    state0: np.ndarray,
    mu: float,
    t_final: float,
    precision: int = 50
) -> dict:
    """
    Test conservation with extended precision arithmetic.
    
    This removes numerical error as a confounding factor.
    """
    mp.dps = precision  # 50 decimal places
    
    # Convert to high precision
    state = [mpf(str(x)) for x in state0]
    mu_hp = mpf(str(mu))
    
    # Simple RK4 in high precision
    dt = mpf('0.001')
    n_steps = int(mpf(str(t_final)) / dt)
    
    def eom_hp(state, mu):
        """EOM in high precision."""
        x, y, z, vx, vy, vz = state
        r1 = ((x + mu)**2 + y**2 + z**2)**mpf('0.5')
        r2 = ((x - 1 + mu)**2 + y**2 + z**2)**mpf('0.5')
        
        ax = 2*vy + x - (1-mu)*(x+mu)/r1**3 - mu*(x-1+mu)/r2**3
        ay = -2*vx + y - (1-mu)*y/r1**3 - mu*y/r2**3
        az = -(1-mu)*z/r1**3 - mu*z/r2**3
        
        return [vx, vy, vz, ax, ay, az]
    
    # Compute initial integral value
    I0 = integral_func([float(x) for x in state], float(mu_hp))
    
    # Integrate
    for _ in range(n_steps):
        k1 = eom_hp(state, mu_hp)
        k2 = eom_hp([s + dt/2*k for s, k in zip(state, k1)], mu_hp)
        k3 = eom_hp([s + dt/2*k for s, k in zip(state, k2)], mu_hp)
        k4 = eom_hp([s + dt*k for s, k in zip(state, k3)], mu_hp)
        
        state = [s + dt/6*(k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) 
                 for i, s in enumerate(state)]
    
    # Final integral value
    I_final = integral_func([float(x) for x in state], float(mu_hp))
    
    relative_error = abs(I_final - I0) / abs(I0) if I0 != 0 else abs(I_final - I0)
    
    return {
        'initial_value': I0,
        'final_value': I_final,
        'relative_error': relative_error,
        'precision_used': precision,
        'is_conserved': relative_error < 10**(-precision/2)
    }
```

## References

- Hairer, E., Nørsett, S.P., & Wanner, G. (1993). *Solving Ordinary Differential Equations I*
- Hairer, E., Lubich, C., & Wanner, G. (2006). *Geometric Numerical Integration*
- Yoshida, H. (1990). "Construction of higher order symplectic integrators"
- McLachlan, R.I. & Atela, P. (1992). "The accuracy of symplectic integrators"
