# Floquet Stability Analysis

Theory and computation of Floquet multipliers for periodic orbit stability.

## Overview

Floquet theory describes the behavior of solutions to linear ODEs with periodic coefficients. For validating integrals, Floquet analysis reveals how perturbations evolve near periodic orbits.

## Mathematical Foundation

### Floquet's Theorem

For the linear system with T-periodic coefficients:

```
ẏ = A(t)y,    A(t + T) = A(t)
```

Any fundamental matrix solution Φ(t) satisfies:

```
Φ(t + T) = Φ(t) · M
```

where M = Φ(T) is the **monodromy matrix**.

### Floquet Representation

Solutions have the form:

```
y(t) = P(t) · exp(Bt)
```

where:
- P(t) is T-periodic: P(t + T) = P(t)
- B is constant with M = exp(BT)

### Floquet Multipliers and Exponents

**Floquet multipliers**: Eigenvalues μᵢ of M
**Floquet exponents**: λᵢ such that μᵢ = exp(λᵢT)

For Hamiltonian systems with n DOF:
- Monodromy M ∈ Sp(2n, ℝ)
- Multipliers come in reciprocal pairs: μᵢμⱼ = 1
- Two trivial multipliers = 1 (energy and phase)

### Stability Classification

| Multipliers | Exponents | Stability |
|-------------|-----------|-----------|
| All |μ| = 1 | All Re(λ) = 0 | **Stable** (elliptic) |
| Some |μ| > 1 | Some Re(λ) > 0 | **Unstable** (hyperbolic) |
| |μ| = 1 but defective | λ = 0 repeated | **Marginally unstable** (parabolic) |

## Computing Monodromy Matrix

### Via Numerical Integration

```python
import numpy as np
from scipy.integrate import solve_ivp

def compute_monodromy_matrix(
    orbit: 'PeriodicOrbit',
    mu: float,
    n_dof: int = 3
) -> np.ndarray:
    """
    Compute monodromy matrix by integrating variational equations.
    
    Parameters:
        orbit: Periodic orbit with state_at(t) method
        mu: Mass ratio
        n_dof: Degrees of freedom (3 for spatial CR3BP)
        
    Returns:
        2n × 2n monodromy matrix M
    """
    n = 2 * n_dof  # Phase space dimension
    
    def variational_eom(t, Y_flat):
        """Combined trajectory + variational equations."""
        # First n components: base trajectory state
        # Remaining n² components: Φ matrix (flattened)
        state = Y_flat[:n]
        Phi = Y_flat[n:].reshape((n, n))
        
        # Evaluate Jacobian of EOM at current state
        A = compute_eom_jacobian(state, mu)
        
        # Trajectory evolution
        dstate = cr3bp_eom(state, mu)
        
        # Variational equation: dΦ/dt = A(t)·Φ
        dPhi = A @ Phi
        
        return np.concatenate([dstate, dPhi.flatten()])
    
    # Initial condition: trajectory + identity matrix
    state0 = orbit.state0
    Phi0 = np.eye(n)
    Y0 = np.concatenate([state0, Phi0.flatten()])
    
    # Integrate one period
    sol = solve_ivp(
        variational_eom,
        (0, orbit.period),
        Y0,
        method='DOP853',
        rtol=1e-12,
        atol=1e-14
    )
    
    # Extract monodromy matrix
    M = sol.y[n:, -1].reshape((n, n))
    
    return M


def compute_eom_jacobian(state: np.ndarray, mu: float) -> np.ndarray:
    """
    Compute Jacobian ∂f/∂x of CR3BP equations of motion.
    """
    x, y, z, vx, vy, vz = state
    
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    
    # Partial derivatives of r1, r2
    dr1_dx = (x + mu) / r1
    dr1_dy = y / r1
    dr1_dz = z / r1
    dr2_dx = (x - 1 + mu) / r2
    dr2_dy = y / r2
    dr2_dz = z / r2
    
    # Second derivatives of effective potential
    Uxx = 1 - (1-mu)/r1**3 - mu/r2**3 + 3*(1-mu)*(x+mu)**2/r1**5 + 3*mu*(x-1+mu)**2/r2**5
    Uyy = 1 - (1-mu)/r1**3 - mu/r2**3 + 3*(1-mu)*y**2/r1**5 + 3*mu*y**2/r2**5
    Uzz = -(1-mu)/r1**3 - mu/r2**3 + 3*(1-mu)*z**2/r1**5 + 3*mu*z**2/r2**5
    Uxy = 3*(1-mu)*(x+mu)*y/r1**5 + 3*mu*(x-1+mu)*y/r2**5
    Uxz = 3*(1-mu)*(x+mu)*z/r1**5 + 3*mu*(x-1+mu)*z/r2**5
    Uyz = 3*(1-mu)*y*z/r1**5 + 3*mu*y*z/r2**5
    
    # Jacobian matrix for rotating frame CR3BP
    A = np.array([
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1],
        [Uxx, Uxy, Uxz, 0, 2, 0],
        [Uxy, Uyy, Uyz, -2, 0, 0],
        [Uxz, Uyz, Uzz, 0, 0, 0]
    ])
    
    return A
```

### Floquet Multiplier Extraction

```python
from dataclasses import dataclass
from typing import List

@dataclass
class FloquetAnalysis:
    monodromy_matrix: np.ndarray
    multipliers: np.ndarray
    exponents: np.ndarray
    stability_type: str
    stable_directions: int
    unstable_directions: int
    
def analyze_floquet(
    M: np.ndarray,
    period: float
) -> FloquetAnalysis:
    """
    Extract Floquet data from monodromy matrix.
    """
    # Eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eig(M)
    
    # Sort by magnitude
    idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    multipliers = eigenvalues
    
    # Floquet exponents: λ = log(μ)/T
    # Handle complex logarithm carefully
    exponents = np.log(multipliers) / period
    
    # Count stability
    tol = 1e-8
    n_unstable = np.sum(np.abs(multipliers) > 1 + tol)
    n_stable = np.sum(np.abs(multipliers) < 1 - tol)
    n_marginal = len(multipliers) - n_unstable - n_stable
    
    # Classification
    if n_unstable > 0:
        stability_type = 'unstable'
    elif n_marginal > 2:  # More than trivial unit multipliers
        stability_type = 'marginally_stable'
    else:
        stability_type = 'stable'
    
    return FloquetAnalysis(
        monodromy_matrix=M,
        multipliers=multipliers,
        exponents=exponents,
        stability_type=stability_type,
        stable_directions=n_stable,
        unstable_directions=n_unstable
    )
```

## Symplectic Structure

### Verifying Symplecticity

```python
def verify_symplectic(M: np.ndarray, tol: float = 1e-10) -> dict:
    """
    Verify monodromy matrix is symplectic: M^T J M = J
    """
    n = M.shape[0] // 2
    
    # Standard symplectic matrix
    J = np.block([
        [np.zeros((n, n)), np.eye(n)],
        [-np.eye(n), np.zeros((n, n))]
    ])
    
    # Check symplectic condition
    residual = M.T @ J @ M - J
    max_error = np.max(np.abs(residual))
    
    # Check determinant = 1
    det_error = np.abs(np.linalg.det(M) - 1)
    
    # Check eigenvalue pairing
    eigenvalues = np.linalg.eigvals(M)
    pairs_valid = True
    for ev in eigenvalues:
        # Should have reciprocal
        reciprocal = 1 / ev
        if not np.any(np.abs(eigenvalues - reciprocal) < tol):
            pairs_valid = False
            break
    
    return {
        'symplectic_error': max_error,
        'determinant_error': det_error,
        'eigenvalue_pairing': pairs_valid,
        'is_symplectic': max_error < tol and det_error < tol
    }
```

### Symplectic Eigenvalue Structure

```python
def analyze_symplectic_eigenvalues(M: np.ndarray) -> dict:
    """
    Analyze eigenvalue structure for symplectic matrix.
    
    For Hamiltonian systems:
    - Real eigenvalues come in pairs (λ, 1/λ)
    - Complex eigenvalues on unit circle come in conjugate pairs
    - Complex eigenvalues off unit circle come in quartets (λ, λ*, 1/λ, 1/λ*)
    """
    eigenvalues = np.linalg.eigvals(M)
    
    real_pairs = []
    unit_circle_pairs = []
    quartets = []
    
    processed = set()
    tol = 1e-8
    
    for i, ev in enumerate(eigenvalues):
        if i in processed:
            continue
        
        abs_ev = np.abs(ev)
        
        if np.abs(ev.imag) < tol:
            # Real eigenvalue
            for j, ev2 in enumerate(eigenvalues):
                if j > i and j not in processed:
                    if np.abs(ev * ev2 - 1) < tol:
                        real_pairs.append((ev.real, ev2.real))
                        processed.add(i)
                        processed.add(j)
                        break
        elif np.abs(abs_ev - 1) < tol:
            # On unit circle
            for j, ev2 in enumerate(eigenvalues):
                if j > i and j not in processed:
                    if np.abs(ev - np.conj(ev2)) < tol:
                        unit_circle_pairs.append((ev, ev2))
                        processed.add(i)
                        processed.add(j)
                        break
        else:
            # Off unit circle - find quartet
            quartet = [ev]
            for j, ev2 in enumerate(eigenvalues):
                if j != i and j not in processed:
                    if (np.abs(ev2 - np.conj(ev)) < tol or
                        np.abs(ev2 - 1/ev) < tol or
                        np.abs(ev2 - 1/np.conj(ev)) < tol):
                        quartet.append(ev2)
                        processed.add(j)
            if len(quartet) == 4:
                quartets.append(tuple(quartet))
            processed.add(i)
    
    return {
        'real_pairs': real_pairs,
        'unit_circle_pairs': unit_circle_pairs,
        'quartets': quartets,
        'trivial_count': sum(1 for ev in eigenvalues if np.abs(ev - 1) < tol)
    }
```

## Stability Indices

### Stability Index Computation

```python
def compute_stability_indices(
    M: np.ndarray,
    period: float
) -> dict:
    """
    Compute various stability indices from monodromy matrix.
    """
    n = M.shape[0]
    eigenvalues = np.linalg.eigvals(M)
    
    # Krein signature for unit circle eigenvalues
    def krein_signature(ev, M):
        """Compute Krein signature for eigenvalue on unit circle."""
        # Find eigenvector
        _, vecs = np.linalg.eig(M)
        idx = np.argmin(np.abs(eigenvalues - ev))
        v = vecs[:, idx]
        
        # Symplectic form
        n_half = n // 2
        J = np.block([
            [np.zeros((n_half, n_half)), np.eye(n_half)],
            [-np.eye(n_half), np.zeros((n_half, n_half))]
        ])
        
        # Krein signature = sign(i * v^H J v)
        sig = np.sign((1j * v.conj() @ J @ v).imag)
        return sig
    
    # Maximum Lyapunov exponent
    log_multipliers = np.log(np.abs(eigenvalues))
    max_lyapunov = np.max(log_multipliers.real) / period
    
    # Trace (for 2D systems, determines stability type)
    trace = np.trace(M)
    
    # Stability index (fraction of stable directions)
    n_stable = np.sum(np.abs(eigenvalues) <= 1 + 1e-8)
    stability_index = n_stable / n
    
    return {
        'max_lyapunov_exponent': max_lyapunov,
        'trace': trace,
        'stability_index': stability_index,
        'spectral_radius': np.max(np.abs(eigenvalues)),
        'eigenvalue_magnitudes': np.abs(eigenvalues)
    }
```

## Integral Variation Analysis

### How Integrals Should Behave

For a true integral I:
- I(φ(t)) = constant along periodic orbit
- Perturbations δI should remain bounded
- Integral gradient ∇I should be preserved by Floquet mapping

```python
def analyze_integral_floquet(
    integral_func: callable,
    orbit: 'PeriodicOrbit',
    mu: float,
    M: np.ndarray
) -> dict:
    """
    Analyze how integral behaves under Floquet mapping.
    
    For a true integral:
    1. Value should be constant along orbit
    2. Gradient should be an eigenvector of M (or preserved subspace)
    """
    # Check constancy along orbit
    n_samples = 1000
    times = np.linspace(0, orbit.period, n_samples)
    values = [integral_func(orbit.state_at(t), mu) for t in times]
    
    variation = np.max(values) - np.min(values)
    relative_variation = variation / np.abs(values[0]) if values[0] != 0 else variation
    
    # Compute gradient at initial point
    grad = compute_gradient(integral_func, orbit.state0, mu)
    
    # Apply monodromy
    grad_mapped = M @ grad
    
    # Check if gradient is preserved (up to scaling)
    # For a true integral, M·∇I = λ·∇I for some λ
    # Since I is conserved, we expect λ = 1 (or conjugate pair)
    
    # Compute angle between grad and M·grad
    cos_angle = np.dot(grad, grad_mapped) / (np.linalg.norm(grad) * np.linalg.norm(grad_mapped))
    angle = np.arccos(np.clip(np.abs(cos_angle), 0, 1))
    
    # Scale factor
    scale = np.linalg.norm(grad_mapped) / np.linalg.norm(grad)
    
    return {
        'value_variation': relative_variation,
        'gradient_preserved': angle < 0.01,  # Within ~0.5 degrees
        'gradient_angle_change': np.degrees(angle),
        'gradient_scale_change': scale,
        'is_conserved_on_orbit': relative_variation < 1e-10
    }


def compute_gradient(func, state, mu, epsilon=1e-7):
    """Compute gradient via central differences."""
    n = len(state)
    grad = np.zeros(n)
    
    for i in range(n):
        state_plus = state.copy()
        state_minus = state.copy()
        state_plus[i] += epsilon
        state_minus[i] -= epsilon
        
        grad[i] = (func(state_plus, mu) - func(state_minus, mu)) / (2*epsilon)
    
    return grad
```

## Periodic Orbit Families

### Continuation Along Families

```python
def analyze_stability_along_family(
    orbit_family: List['PeriodicOrbit'],
    mu: float,
    integral_func: callable = None
) -> dict:
    """
    Track stability changes along a family of periodic orbits.
    
    Useful for understanding where integrals may fail or succeed.
    """
    results = {
        'periods': [],
        'jacobi_constants': [],
        'stability_types': [],
        'max_multipliers': [],
        'integral_variations': []
    }
    
    for orbit in orbit_family:
        # Compute monodromy
        M = compute_monodromy_matrix(orbit, mu)
        floquet = analyze_floquet(M, orbit.period)
        
        results['periods'].append(orbit.period)
        results['jacobi_constants'].append(orbit.jacobi_constant)
        results['stability_types'].append(floquet.stability_type)
        results['max_multipliers'].append(np.max(np.abs(floquet.multipliers)))
        
        # Check integral if provided
        if integral_func is not None:
            int_analysis = analyze_integral_floquet(integral_func, orbit, mu, M)
            results['integral_variations'].append(int_analysis['value_variation'])
    
    # Find bifurcations (stability changes)
    stability_changes = []
    for i in range(1, len(results['stability_types'])):
        if results['stability_types'][i] != results['stability_types'][i-1]:
            stability_changes.append(i)
    
    results['bifurcation_indices'] = stability_changes
    
    return results
```

## References

- Floquet, G. (1883). "Sur les équations différentielles linéaires à coefficients périodiques"
- Meyer, K.R. & Hall, G.R. (1992). *Introduction to Hamiltonian Dynamical Systems*, Ch. 3
- Yakubovich, V.A. & Starzhinskii, V.M. (1975). *Linear Differential Equations with Periodic Coefficients*
- Hénon, M. (1997). *Generating Families in the Restricted Three-Body Problem*
