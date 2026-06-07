# Normal Variational Equations (NVE) Computation

Methods for computing and analyzing Normal Variational Equations along periodic orbits.

## Overview

The Normal Variational Equations describe the linearized dynamics of perturbations away from a reference trajectory. For the Morales-Ramis test, we need NVE along periodic orbits.

## Mathematical Formulation

### General Variational Equations

For a dynamical system ẋ = f(x), the variational equations along a solution φ(t) are:

```
d(δx)/dt = Df(φ(t)) · δx
```

where Df is the Jacobian matrix of f.

### For Hamiltonian Systems

Given Hamilton's equations:
```
q̇ = ∂H/∂p = H_p
ṗ = -∂H/∂q = -H_q
```

The variational equations are:
```
d/dt [δq]   [H_qp   H_pp ] [δq]
     [δp] = [-H_qq  -H_qp] [δp]
```

Equivalently, with state x = (q, p):
```
δẋ = J · ∇²H(φ(t)) · δx
```

where J is the symplectic matrix:
```
J = [ 0   I ]
    [-I   0 ]
```

### Normal vs Full Variational

**Full VE**: All 2n dimensions of perturbations

**Normal VE**: Perturbations orthogonal to the trajectory and energy surface

For periodic orbits, the NVE has dimension 2n-2 (removing trivial directions).

## Implementation

### Computing the Hessian

```python
import numpy as np
import sympy as sp
from typing import Callable, Tuple

def compute_hessian_numerical(
    H_func: Callable,
    state: np.ndarray,
    mu: float,
    epsilon: float = 1e-7
) -> np.ndarray:
    """
    Compute Hessian ∇²H numerically via central differences.

    Parameters:
        H_func: Hamiltonian function H(state, mu) -> float
        state: Point at which to evaluate
        mu: System parameter
        epsilon: Finite difference step

    Returns:
        n×n Hessian matrix
    """
    n = len(state)
    H = np.zeros((n, n))

    for i in range(n):
        for j in range(i, n):
            # Second partial derivative via central differences
            if i == j:
                # Diagonal: (f(x+h) - 2f(x) + f(x-h))/h²
                state_plus = state.copy()
                state_minus = state.copy()
                state_plus[i] += epsilon
                state_minus[i] -= epsilon

                H[i,i] = (H_func(state_plus, mu) - 2*H_func(state, mu) +
                          H_func(state_minus, mu)) / epsilon**2
            else:
                # Off-diagonal: (f(x+h_i+h_j) - f(x+h_i-h_j) - f(x-h_i+h_j) + f(x-h_i-h_j))/(4h²)
                s_pp = state.copy(); s_pp[i] += epsilon; s_pp[j] += epsilon
                s_pm = state.copy(); s_pm[i] += epsilon; s_pm[j] -= epsilon
                s_mp = state.copy(); s_mp[i] -= epsilon; s_mp[j] += epsilon
                s_mm = state.copy(); s_mm[i] -= epsilon; s_mm[j] -= epsilon

                H[i,j] = (H_func(s_pp, mu) - H_func(s_pm, mu) -
                          H_func(s_mp, mu) + H_func(s_mm, mu)) / (4*epsilon**2)
                H[j,i] = H[i,j]

    return H


def compute_hessian_symbolic(H_expr, variables):
    """
    Compute Hessian symbolically using SymPy.

    Parameters:
        H_expr: SymPy expression for Hamiltonian
        variables: List of SymPy symbols [q1, q2, ..., p1, p2, ...]

    Returns:
        SymPy Matrix for Hessian
    """
    n = len(variables)
    H = sp.Matrix(n, n, lambda i, j: sp.diff(sp.diff(H_expr, variables[i]), variables[j]))
    return H
```

### Building the VE Coefficient Matrix

```python
def ve_coefficient_matrix(
    hessian: np.ndarray,
    n_dof: int
) -> np.ndarray:
    """
    Build variational equation coefficient matrix A from Hessian.

    For Hamiltonian system: A = J · ∇²H

    Parameters:
        hessian: 2n × 2n Hessian matrix
        n_dof: Number of degrees of freedom (n)

    Returns:
        2n × 2n coefficient matrix A
    """
    n = n_dof

    # Symplectic matrix
    J = np.block([
        [np.zeros((n, n)), np.eye(n)],
        [-np.eye(n), np.zeros((n, n))]
    ])

    A = J @ hessian
    return A
```

### Computing NVE Along Orbit

```python
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d

class NVESystem:
    """
    Normal Variational Equations along a periodic orbit.
    """

    def __init__(
        self,
        orbit: 'PeriodicOrbit',
        H_func: Callable,
        mu: float,
        n_samples: int = 1000
    ):
        self.orbit = orbit
        self.H_func = H_func
        self.mu = mu
        self.period = orbit.period

        # Sample orbit and compute A(t) matrices
        self.times = np.linspace(0, orbit.period, n_samples)
        self.A_matrices = []

        for t in self.times:
            state = orbit.state_at(t)
            hessian = compute_hessian_numerical(H_func, state, mu)
            A = ve_coefficient_matrix(hessian, n_dof=len(state)//2)
            self.A_matrices.append(A)

        # Create interpolator for A(t)
        self._A_interp = self._build_interpolator()

    def _build_interpolator(self):
        """Build interpolator for coefficient matrix."""
        A_stack = np.array(self.A_matrices)
        interpolators = {}

        n = A_stack.shape[1]
        for i in range(n):
            for j in range(n):
                interpolators[(i,j)] = interp1d(
                    self.times, A_stack[:, i, j],
                    kind='cubic', fill_value='extrapolate'
                )

        return interpolators

    def A(self, t: float) -> np.ndarray:
        """Evaluate A(t) at time t (mod period)."""
        t_mod = t % self.period
        n = self.A_matrices[0].shape[0]
        A = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                A[i,j] = self._A_interp[(i,j)](t_mod)

        return A

    def rhs(self, t: float, y: np.ndarray) -> np.ndarray:
        """Right-hand side of NVE: ẏ = A(t)y."""
        return self.A(t) @ y
```

## Monodromy Matrix Computation

### Fundamental Matrix Solution

```python
def compute_fundamental_matrix(
    nve: NVESystem,
    n_periods: int = 1
) -> np.ndarray:
    """
    Compute fundamental matrix solution Φ(t) of NVE.

    Solves: dΦ/dt = A(t)Φ with Φ(0) = I

    Returns:
        Fundamental matrix at t = n_periods * T
    """
    n = nve.A_matrices[0].shape[0]

    # Initial condition: identity matrix (flattened)
    Y0 = np.eye(n).flatten()

    # Integrate
    t_span = (0, n_periods * nve.period)

    def matrix_ode(t, Y_flat):
        Y = Y_flat.reshape((n, n))
        dY = nve.A(t) @ Y
        return dY.flatten()

    sol = solve_ivp(
        matrix_ode, t_span, Y0,
        method='DOP853',
        rtol=1e-12, atol=1e-14,
        dense_output=True
    )

    return sol.y[:, -1].reshape((n, n))


def compute_monodromy_matrix(nve: NVESystem) -> np.ndarray:
    """
    Compute monodromy matrix M = Φ(T) where T is period.
    """
    return compute_fundamental_matrix(nve, n_periods=1)
```

### Floquet Analysis

```python
from dataclasses import dataclass
from typing import List

@dataclass
class FloquetResult:
    monodromy_matrix: np.ndarray
    eigenvalues: np.ndarray
    floquet_multipliers: np.ndarray
    floquet_exponents: np.ndarray
    stability_type: str

def floquet_analysis(nve: NVESystem) -> FloquetResult:
    """
    Perform Floquet analysis of NVE.

    Floquet multipliers: eigenvalues of monodromy matrix
    Floquet exponents: μ such that λ = exp(μT)
    """
    M = compute_monodromy_matrix(nve)

    # Eigenvalues (Floquet multipliers)
    eigenvalues = np.linalg.eigvals(M)

    # Sort by magnitude
    idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues = eigenvalues[idx]
    floquet_multipliers = eigenvalues

    # Floquet exponents
    T = nve.period
    floquet_exponents = np.log(eigenvalues) / T

    # Stability classification
    mags = np.abs(eigenvalues)
    if np.all(np.abs(mags - 1) < 1e-8):
        stability = 'stable'
    elif np.any(mags > 1 + 1e-8):
        stability = 'unstable'
    else:
        stability = 'marginally_stable'

    return FloquetResult(
        monodromy_matrix=M,
        eigenvalues=eigenvalues,
        floquet_multipliers=floquet_multipliers,
        floquet_exponents=floquet_exponents,
        stability_type=stability
    )
```

## Lifted Space NVE

### S¹-Bundle Lift

```python
def compute_s1_lifted_nve(
    base_orbit: 'PeriodicOrbit',
    H_func: Callable,
    A_connection: Callable,
    mu: float,
    angular_momentum: float
) -> NVESystem:
    """
    Compute NVE in S¹-bundle lifted space.

    Lifted Hamiltonian: H̃ = H + p_θ · A(q, p)

    Parameters:
        base_orbit: Periodic orbit in base space
        H_func: Base Hamiltonian
        A_connection: Connection 1-form A(q, p)
        angular_momentum: Value of L for the lift
    """
    def H_lifted(lifted_state, mu):
        """Extended Hamiltonian."""
        # Split state: [q, θ, p, p_θ]
        n_base = (len(lifted_state) - 2) // 2
        q = lifted_state[:n_base]
        theta = lifted_state[n_base]
        p = lifted_state[n_base+1:-1]
        p_theta = lifted_state[-1]

        base_state = np.concatenate([q, p])

        H_base = H_func(base_state, mu)
        A_val = A_connection(base_state, mu)

        return H_base + p_theta * A_val

    # Lift orbit
    lifted_orbit = lift_orbit_to_s1(base_orbit, angular_momentum)

    # Build NVE system
    return NVESystem(
        orbit=lifted_orbit,
        H_func=H_lifted,
        mu=mu,
        n_samples=1000
    )
```

### KS-Spinor Lift

```python
def compute_ks_lifted_nve(
    base_orbit: 'PeriodicOrbit',
    mu: float,
    mass_pair: Tuple[float, float] = None
) -> NVESystem:
    """
    Compute NVE in KS-regularized (spinor) space.

    KS transformation: r = |u|², p_r = (u·p_u)/(2|u|²)
    """
    from src.python.lifts.ks_transform import KSTransform

    ks = KSTransform()

    def H_ks(ks_state, mu):
        """KS-regularized Hamiltonian."""
        u, pu = ks_state[:4], ks_state[4:]
        r, p = ks.to_physical(u, pu)

        # Base Hamiltonian
        H_base = 0.5 * np.dot(p, p) - 1.0 / np.linalg.norm(r)

        # KS time rescaling factor
        h = -H_base  # Bound orbit: H < 0

        return 0.5 * np.dot(pu, pu) - 2 * h * np.dot(u, u)

    # Lift orbit to KS space
    ks_orbit = ks.lift_orbit(base_orbit)

    return NVESystem(
        orbit=ks_orbit,
        H_func=H_ks,
        mu=mu,
        n_samples=1000
    )
```

## Reduction to Scalar Form

For Kovacic algorithm, we need to reduce 2n-dim NVE to scalar 2nd-order ODE.

### Symplectic Reduction

```python
def reduce_nve_to_scalar(nve: NVESystem) -> Tuple[Callable, Callable]:
    """
    Reduce NVE to scalar second-order equation.

    For 2D Hamiltonian (4D phase space), normal directions give
    scalar equation: z'' = r(t)z

    Returns:
        (a_coeff, b_coeff) functions such that y'' + a(t)y' + b(t)y = 0
    """
    # Extract normal block from A(t)
    # For planar problem, A is 4×4, normal block is 2×2

    def extract_normal_block(t):
        A = nve.A(t)
        # Assume coordinates ordered as [q_tangent, q_normal, p_tangent, p_normal]
        # Normal block is A[1,1], A[1,3], A[3,1], A[3,3] (indices for 2×2 normal)
        A_normal = np.array([
            [A[1,1], A[1,3]],
            [A[3,1], A[3,3]]
        ])
        return A_normal

    # For 2×2 symplectic block:
    # [q̇]   [A11  A12] [q]
    # [ṗ] = [A21  A22] [p]
    #
    # This gives: q̈ = (A11' + A11² + A12*A21)q + (A12' + A11*A12 + A12*A22)ṗ/A12
    # Which is messy. Better to use standard form.

    def r_coeff(t):
        """Coefficient r(t) in reduced equation z'' = r(t)z."""
        A_n = extract_normal_block(t)
        # For symplectic 2×2: z'' = (A11' + A11² + A12*A21)z
        # after eliminating p
        A11, A12 = A_n[0, 0], A_n[0, 1]
        A21, A22 = A_n[1, 0], A_n[1, 1]

        # Compute A11' numerically
        dt = nve.period / 10000
        A11_plus = extract_normal_block(t + dt)[0, 0]
        A11_minus = extract_normal_block(t - dt)[0, 0]
        A11_dot = (A11_plus - A11_minus) / (2*dt)

        return A11_dot + A11**2 + A12 * A21

    # For standard form y'' + a(t)y' + b(t)y = 0:
    # a = 0 (in reduced form)
    # b = -r

    return lambda t: 0, lambda t: -r_coeff(t)
```

## Numerical Stability

### High-Precision Integration

```python
from mpmath import mp, mpf, matrix as mpmatrix

def compute_monodromy_high_precision(
    nve: NVESystem,
    precision: int = 50
) -> np.ndarray:
    """
    Compute monodromy matrix with extended precision.

    Uses mpmath for arbitrary precision arithmetic.
    """
    mp.dps = precision

    n = nve.A_matrices[0].shape[0]
    dt = mpf(str(nve.period)) / 1000

    # Initialize with identity
    Phi = mpmatrix(np.eye(n).tolist())

    t = mpf('0')
    for _ in range(1000):
        A = nve.A(float(t))
        A_mp = mpmatrix(A.tolist())

        # RK4 step for matrix ODE
        k1 = A_mp * Phi
        k2 = mpmatrix((nve.A(float(t + dt/2)).tolist())) * (Phi + dt/2 * k1)
        k3 = mpmatrix((nve.A(float(t + dt/2)).tolist())) * (Phi + dt/2 * k2)
        k4 = mpmatrix((nve.A(float(t + dt)).tolist())) * (Phi + dt * k3)

        Phi = Phi + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        t += dt

    # Convert back to numpy
    result = np.array([[float(Phi[i,j]) for j in range(n)] for i in range(n)])
    return result
```

### Symplectic Integrator

For preserving symplectic structure:

```python
def compute_monodromy_symplectic(
    nve: NVESystem,
    n_steps: int = 10000
) -> np.ndarray:
    """
    Compute monodromy using symplectic integrator.

    Preserves det(M) = 1 property.
    """
    from scipy.linalg import expm

    n = nve.A_matrices[0].shape[0]
    dt = nve.period / n_steps

    Phi = np.eye(n)

    for i in range(n_steps):
        t = i * dt
        A = nve.A(t)

        # Symplectic exponential: exp(A*dt)
        Phi = expm(A * dt) @ Phi

    # Verify symplectic property
    J = np.block([
        [np.zeros((n//2, n//2)), np.eye(n//2)],
        [-np.eye(n//2), np.zeros((n//2, n//2))]
    ])

    error = np.linalg.norm(Phi.T @ J @ Phi - J)
    if error > 1e-8:
        print(f"Warning: Symplectic error = {error:.2e}")

    return Phi
```

## References

- Hairer, E., Lubich, C., & Wanner, G. (2006). *Geometric Numerical Integration*, Ch. V-VI
- Meyer, K.R. & Hall, G.R. (1992). *Introduction to Hamiltonian Dynamical Systems*, Ch. 2
- Yakubovich, V.A. & Starzhinskii, V.M. (1975). *Linear Differential Equations with Periodic Coefficients*
- Morales-Ruiz, J.J. (1999). *Differential Galois Theory and Non-integrability*, Ch. 2
