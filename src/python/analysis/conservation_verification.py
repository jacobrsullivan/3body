"""
Conservation verification via numerical trajectory integration (WP 3.1, Task 3.1.4, Part D).

Verifies that candidate integrals are truly conserved by:
1. Integrating equations of motion numerically
2. Evaluating integral along trajectory
3. Checking |I(t) - I(0)| < tolerance

This is the ultimate test - if dI/dt ≠ 0, it's not a true conserved quantity.
"""

from typing import List, Tuple, Dict, Optional, Callable
import numpy as np
from scipy.integrate import solve_ivp

from .integral_from_killing import ConservedIntegral, State


# =============================================================================
# Part D1: Single Trajectory Verification
# =============================================================================

def verify_conservation_along_trajectory(
    integral: ConservedIntegral,
    initial_state: State,
    hamiltonian: Callable[[np.ndarray], float],
    time_span: Tuple[float, float],
    *,
    integrator: str = 'DOP853',
    rtol: float = 1e-9,
    atol: float = 1e-9,
    tolerance: float = 1e-6,
    num_eval_points: int = 100,
    verbose: bool = False
) -> Dict:
    """
    Integrate trajectory and verify dI/dt ≈ 0.

    Protocol:
    1. Set up Hamilton's equations: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q
    2. Integrate from initial_state over time_span
    3. Evaluate integral at sampled time points
    4. Compute drift: |I(t) - I(0)| / |I(0)|

    Args:
        integral: Candidate conserved quantity
        initial_state: Initial condition (q_0, p_0)
        hamiltonian: H(q, p) function
        time_span: (t_start, t_end)
        integrator: ODE solver ('DOP853', 'LSODA', 'Radau', etc.)
        rtol, atol: Integration tolerances (should be << conservation tolerance)
        tolerance: Maximum relative drift allowed
        num_eval_points: Number of points to evaluate integral
        verbose: Print diagnostics

    Returns:
        {
            'conserved': bool,
            'relative_drift': float,  # max |I(t) - I(0)| / |I(0)|
            'absolute_drift': float,  # max |I(t) - I(0)|
            'times': np.ndarray,
            'integral_values': np.ndarray,
            'energy_values': np.ndarray,  # For comparison
            'integration_success': bool
        }
    """
    n = initial_state.dimension

    if verbose:
        print(f"Verifying conservation of {integral.name}:")
        print(f"  Time span: {time_span}")
        print(f"  Integrator: {integrator}")

    # Define Hamilton's equations
    def hamilton_rhs(t, y):
        """
        Right-hand side of Hamilton's equations.

        y = [q, p] (length 2n)
        dy/dt = [dq/dt, dp/dt] = [∂H/∂p, -∂H/∂q]
        """
        q = y[:n]
        p = y[n:]

        # Compute gradients of Hamiltonian
        eps = 1e-7
        dH_dq = np.zeros(n)
        dH_dp = np.zeros(n)

        H_0 = hamiltonian(y)

        # ∂H/∂q
        for i in range(n):
            q_plus = q.copy()
            q_plus[i] += eps
            y_plus = np.concatenate([q_plus, p])
            H_plus = hamiltonian(y_plus)
            dH_dq[i] = (H_plus - H_0) / eps

        # ∂H/∂p
        for i in range(n):
            p_plus = p.copy()
            p_plus[i] += eps
            y_plus = np.concatenate([q, p_plus])
            H_plus = hamiltonian(y_plus)
            dH_dp[i] = (H_plus - H_0) / eps

        # Hamilton's equations
        dq_dt = dH_dp
        dp_dt = -dH_dq

        return np.concatenate([dq_dt, dp_dt])

    # Initial conditions
    y0 = initial_state.to_array()

    # Integrate
    solution = solve_ivp(
        hamilton_rhs,
        time_span,
        y0,
        method=integrator,
        rtol=rtol,
        atol=atol,
        dense_output=True,
        max_step=np.inf
    )

    if not solution.success:
        if verbose:
            print(f"  ✗ Integration failed: {solution.message}")

        return {
            'conserved': False,
            'relative_drift': np.inf,
            'absolute_drift': np.inf,
            'times': np.array([]),
            'integral_values': np.array([]),
            'energy_values': np.array([]),
            'integration_success': False,
            'message': solution.message
        }

    # Evaluate integral and energy at sampled points
    t_eval = np.linspace(time_span[0], time_span[1], num_eval_points)
    y_eval = solution.sol(t_eval)  # (2n, num_eval_points)

    integral_values = np.zeros(num_eval_points)
    energy_values = np.zeros(num_eval_points)

    for i in range(num_eval_points):
        state_i = y_eval[:, i]
        integral_values[i] = integral(state_i)
        energy_values[i] = hamiltonian(state_i)

    # Compute drift
    I_0 = integral_values[0]
    absolute_drift = np.max(np.abs(integral_values - I_0))
    relative_drift = absolute_drift / (np.abs(I_0) + 1e-12)

    # Energy drift (for comparison)
    E_0 = energy_values[0]
    energy_drift = np.max(np.abs(energy_values - E_0)) / (np.abs(E_0) + 1e-12)

    conserved = (relative_drift < tolerance)

    if verbose:
        print(f"  I(0) = {I_0:.6e}")
        print(f"  |ΔI|_abs = {absolute_drift:.2e}")
        print(f"  |ΔI|_rel = {relative_drift:.2e}")
        print(f"  |ΔE|_rel = {energy_drift:.2e} (for comparison)")
        print(f"  Conserved: {'✓' if conserved else '✗'}")

    return {
        'conserved': conserved,
        'relative_drift': relative_drift,
        'absolute_drift': absolute_drift,
        'times': t_eval,
        'integral_values': integral_values,
        'energy_values': energy_values,
        'integration_success': True,
        'message': 'Success'
    }


# =============================================================================
# Part D2: Ensemble Verification
# =============================================================================

def verify_conservation_ensemble(
    integral: ConservedIntegral,
    initial_states: List[State],
    hamiltonian: Callable,
    time_span: Tuple[float, float],
    *,
    tolerance: float = 1e-6,
    integrator: str = 'DOP853',
    verbose: bool = False
) -> Dict:
    """
    Verify conservation over ensemble of trajectories.

    Motivation:
        Single trajectory may pass accidentally (special initial condition).
        Ensemble test is more robust.

    Args:
        integral: Candidate integral
        initial_states: List of initial conditions
        hamiltonian: Hamiltonian function
        time_span: Integration time
        tolerance: Conservation tolerance
        integrator: ODE solver
        verbose: Print per-trajectory results

    Returns:
        {
            'success_rate': float,  # Fraction conserved
            'mean_drift': float,
            'max_drift': float,
            'min_drift': float,
            'per_trajectory_results': List[Dict]
        }
    """
    if verbose:
        print(f"Ensemble verification for {integral.name}:")
        print(f"  Trajectories: {len(initial_states)}")
        print()

    results = []
    successful_count = 0

    for idx, state in enumerate(initial_states):
        if verbose:
            print(f"  Trajectory {idx+1}/{len(initial_states)}")

        result = verify_conservation_along_trajectory(
            integral,
            state,
            hamiltonian,
            time_span,
            tolerance=tolerance,
            integrator=integrator,
            verbose=verbose
        )

        results.append(result)

        if result['conserved']:
            successful_count += 1

        if verbose:
            print()

    # Aggregate statistics
    success_rate = successful_count / len(initial_states)

    drifts = [r['relative_drift'] for r in results if r['integration_success']]
    mean_drift = np.mean(drifts) if drifts else np.nan
    max_drift = np.max(drifts) if drifts else np.nan
    min_drift = np.min(drifts) if drifts else np.nan

    if verbose:
        print("="*70)
        print(f"ENSEMBLE RESULTS:")
        print(f"  Success rate: {success_rate:.1%} ({successful_count}/{len(initial_states)})")
        print(f"  Mean drift: {mean_drift:.2e}")
        print(f"  Max drift: {max_drift:.2e}")
        print(f"  Min drift: {min_drift:.2e}")
        print("="*70)

    return {
        'success_rate': success_rate,
        'mean_drift': mean_drift,
        'max_drift': max_drift,
        'min_drift': min_drift,
        'per_trajectory_results': results
    }


# =============================================================================
# Batch Verification
# =============================================================================

def verify_integrals_batch(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    hamiltonian: Callable,
    *,
    time_span: Tuple[float, float] = (0, 100),
    tolerance: float = 1e-6,
    success_threshold: float = 0.95,
    verbose: bool = True
) -> Tuple[List[ConservedIntegral], Dict]:
    """
    Verify conservation for multiple integrals.

    Args:
        integrals: List of candidate integrals
        test_states: Test initial conditions
        hamiltonian: System Hamiltonian
        time_span: Integration time
        tolerance: Conservation tolerance
        success_threshold: Minimum success rate to accept (e.g., 0.95 = 95%)
        verbose: Print results

    Returns:
        (verified_integrals, verification_report)
    """
    verified = []
    report = {
        'total_candidates': len(integrals),
        'verified_count': 0,
        'per_integral_results': []
    }

    if verbose:
        print("="*70)
        print("BATCH CONSERVATION VERIFICATION")
        print("="*70)
        print(f"  Integrals to test: {len(integrals)}")
        print(f"  Test trajectories: {len(test_states)}")
        print(f"  Success threshold: {success_threshold:.1%}")
        print()

    for idx, integral in enumerate(integrals):
        if verbose:
            print(f"[{idx+1}/{len(integrals)}] Testing: {integral.name}")
            print("-"*70)

        ensemble_result = verify_conservation_ensemble(
            integral,
            test_states,
            hamiltonian,
            time_span,
            tolerance=tolerance,
            verbose=verbose
        )

        # Update integral residual
        integral.residual = ensemble_result['max_drift']

        # Check if passes threshold
        if ensemble_result['success_rate'] >= success_threshold:
            verified.append(integral)
            report['verified_count'] += 1

            if verbose:
                print(f"  ✓ VERIFIED")
        else:
            if verbose:
                print(f"  ✗ REJECTED (success rate: {ensemble_result['success_rate']:.1%})")

        report['per_integral_results'].append({
            'name': integral.name,
            'success_rate': ensemble_result['success_rate'],
            'mean_drift': ensemble_result['mean_drift'],
            'max_drift': ensemble_result['max_drift'],
            'verified': ensemble_result['success_rate'] >= success_threshold
        })

        if verbose:
            print()

    if verbose:
        print("="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        print(f"  Verified: {report['verified_count']}/{len(integrals)}")
        print("="*70)

    return verified, report


# =============================================================================
# Utility: Simple Hamiltonian Definitions
# =============================================================================

def make_harmonic_hamiltonian(
    masses: np.ndarray,
    omega: float = 1.0
) -> Callable:
    """
    Simple harmonic oscillator Hamiltonian (for testing).

    H = sum_i (p_i²/(2m_i) + (1/2) m_i ω² q_i²)
    """
    def H(y: np.ndarray) -> float:
        n = len(y) // 2
        q = y[:n]
        p = y[n:]

        T = np.sum(p**2 / (2 * masses))
        V = 0.5 * np.sum(masses * omega**2 * q**2)

        return T + V

    return H


def make_kepler_hamiltonian(
    mu: float = 1.0,
    G: float = 1.0
) -> Callable:
    """
    Kepler problem Hamiltonian (2D).

    H = (p_x² + p_y²)/(2μ) - G μ / sqrt(x² + y²)
    """
    def H(y: np.ndarray) -> float:
        if len(y) != 4:
            raise ValueError("Kepler Hamiltonian is 2D (4 variables)")

        x, y_pos = y[0], y[1]
        px, py = y[2], y[3]

        r = np.sqrt(x**2 + y_pos**2)

        T = (px**2 + py**2) / (2 * mu)
        V = -G * mu / (r + 1e-10)  # Regularization

        return T + V

    return H
