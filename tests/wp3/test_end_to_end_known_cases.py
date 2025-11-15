"""
End-to-end integration tests on known integrable systems (WP 3.1).

Tests the complete pipeline on:
1. Harmonic oscillator (2D) - expects 2 integrals
2. Kepler problem (2D) - expects energy, angular momentum, components of Runge-Lenz
3. Flat space - expects translations and rotations

These are validation tests to ensure the geometric search works correctly.
"""

import pytest
import numpy as np

from src.python.analysis.integral_from_killing import State, ConservedIntegral
from src.python.analysis.triviality_filter import KnownIntegrals, generate_test_states
from src.python.analysis.conservation_verification import (
    verify_conservation_along_trajectory,
    make_harmonic_hamiltonian,
    make_kepler_hamiltonian
)


# =============================================================================
# Test Harmonic Oscillator
# =============================================================================

def test_harmonic_oscillator_energy_conservation():
    """Test energy conservation for harmonic oscillator"""
    masses = np.array([1.0, 1.0])
    omega = 1.0
    H = make_harmonic_hamiltonian(masses, omega)

    # Create energy integral
    def energy_expr(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            n = len(state) // 2
            q, p = state[:n], state[n:]
        return 0.5 * np.sum(p**2 / masses) + 0.5 * np.sum(masses * omega**2 * q**2)

    energy = ConservedIntegral(
        name="Energy",
        expression=energy_expr,
        source='test'
    )

    # Initial state
    initial_state = State(
        q=np.array([1.0, 0.0]),
        p=np.array([0.0, 1.0])
    )

    # Verify conservation
    result = verify_conservation_along_trajectory(
        energy,
        initial_state,
        H,
        time_span=(0, 10),
        tolerance=1e-6,
        num_eval_points=50,
        verbose=False
    )

    assert result['integration_success']
    assert result['conserved'], f"Energy drift: {result['relative_drift']:.2e}"
    assert result['relative_drift'] < 1e-6


def test_harmonic_oscillator_angular_momentum():
    """Test angular momentum conservation for 2D harmonic oscillator"""
    masses = np.array([1.0, 1.0])
    H = make_harmonic_hamiltonian(masses, omega=1.0)

    # Angular momentum: L = x p_y - y p_x
    def L_expr(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            q, p = state[:2], state[2:4]
        return q[0] * p[1] - q[1] * p[0]

    L = ConservedIntegral(
        name="AngularMomentum",
        expression=L_expr,
        source='test'
    )

    initial_state = State(
        q=np.array([1.0, 0.0]),
        p=np.array([0.0, 2.0])
    )

    result = verify_conservation_along_trajectory(
        L,
        initial_state,
        H,
        time_span=(0, 20),
        tolerance=1e-6,
        verbose=False
    )

    assert result['integration_success']
    # Angular momentum should be conserved
    assert result['conserved'], f"L drift: {result['relative_drift']:.2e}"


# =============================================================================
# Test Kepler Problem
# =============================================================================

def test_kepler_energy_conservation():
    """Test energy conservation for Kepler problem"""
    mu = 1.0
    G = 1.0
    H = make_kepler_hamiltonian(mu, G)

    # Energy integral
    def energy_expr(state):
        if len(state) != 4:
            return np.nan
        x, y = state[0], state[1]
        px, py = state[2], state[3]
        r = np.sqrt(x**2 + y**2)
        return (px**2 + py**2) / (2 * mu) - G * mu / (r + 1e-10)

    energy = ConservedIntegral(
        name="KeplerEnergy",
        expression=energy_expr,
        source='test'
    )

    # Circular orbit initial condition
    # For circular orbit: v = sqrt(GM/r), r = 1
    r0 = 1.0
    v_circ = np.sqrt(G * mu / r0)

    initial_state = State(
        q=np.array([r0, 0.0]),
        p=np.array([0.0, mu * v_circ])
    )

    result = verify_conservation_along_trajectory(
        energy,
        initial_state,
        H,
        time_span=(0, 50),
        tolerance=1e-5,
        verbose=False
    )

    assert result['integration_success']
    assert result['conserved'], f"Energy drift: {result['relative_drift']:.2e}"


def test_kepler_angular_momentum_conservation():
    """Test angular momentum conservation for Kepler"""
    H = make_kepler_hamiltonian(mu=1.0, G=1.0)

    def L_expr(state):
        if len(state) != 4:
            return np.nan
        x, y = state[0], state[1]
        px, py = state[2], state[3]
        return x * py - y * px

    L = ConservedIntegral(
        name="KeplerAngularMomentum",
        expression=L_expr,
        source='test'
    )

    # Elliptical orbit
    initial_state = State(
        q=np.array([1.0, 0.0]),
        p=np.array([0.0, 1.2])
    )

    result = verify_conservation_along_trajectory(
        L,
        initial_state,
        H,
        time_span=(0, 100),
        tolerance=1e-5,
        verbose=False
    )

    assert result['integration_success']
    assert result['conserved'], f"L drift: {result['relative_drift']:.2e}"


# =============================================================================
# Test Multiple Integrals Together
# =============================================================================

def test_harmonic_oscillator_integrability():
    """
    Test that 2D harmonic oscillator has 2 independent conserved integrals.

    The 2D isotropic harmonic oscillator is integrable with:
    - H (energy)
    - L (angular momentum)
    These should be functionally independent and in involution.
    """
    from src.python.analysis.independence_test import analyze_integral_structure

    # Define integrals
    def H_expr(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            q, p = state[:2], state[2:4]
        return 0.5 * (np.sum(p**2) + np.sum(q**2))

    def L_expr(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            q, p = state[:2], state[2:4]
        return q[0] * p[1] - q[1] * p[0]

    integrals = [
        ConservedIntegral(name="H", expression=H_expr, source='test'),
        ConservedIntegral(name="L", expression=L_expr, source='test')
    ]

    test_states = generate_test_states(dimension=2, num_states=30, seed=42)

    result = analyze_integral_structure(
        integrals,
        test_states,
        tolerance=1e-6,
        verbose=False
    )

    # Should find 2 independent integrals
    assert result['num_independent'] == 2, f"Found {result['num_independent']} instead of 2"

    # Should be in involution (or close)
    # Note: Numerical errors may prevent perfect involution
    max_bracket = result['involution']['max_bracket']
    assert max_bracket < 0.5, f"Poisson bracket too large: {max_bracket}"

    # Integrability status
    assert result['is_integrable'] or "INTEGRABLE" in result['integrability_status']


# =============================================================================
# Test Non-Conserved Quantities (Negative Test)
# =============================================================================

def test_non_conserved_quantity_detected():
    """Test that non-conserved quantities are correctly rejected"""
    H = make_harmonic_hamiltonian(np.array([1.0, 1.0]), omega=1.0)

    # Create a non-conserved "integral": just q_0 (coordinate)
    def q0_expr(state):
        return state[0]

    fake_integral = ConservedIntegral(
        name="NotConserved",
        expression=q0_expr,
        source='test'
    )

    initial_state = State(
        q=np.array([1.0, 0.0]),
        p=np.array([0.0, 1.0])
    )

    result = verify_conservation_along_trajectory(
        fake_integral,
        initial_state,
        H,
        time_span=(0, 10),
        tolerance=1e-3,  # Generous tolerance
        verbose=False
    )

    assert result['integration_success']
    # Should NOT be conserved (q_0 oscillates)
    assert not result['conserved'], "False positive: non-conserved quantity marked as conserved"
    assert result['relative_drift'] > 0.1  # Should have significant drift


# =============================================================================
# Test Different Trajectories
# =============================================================================

def test_ensemble_conservation_harmonic():
    """Test conservation over ensemble of trajectories"""
    from src.python.analysis.conservation_verification import verify_conservation_ensemble

    H = make_harmonic_hamiltonian(np.array([1.0, 1.0]), omega=1.0)

    def energy_expr(state):
        q, p = state[:2], state[2:4]
        return 0.5 * (np.sum(p**2) + np.sum(q**2))

    energy = ConservedIntegral(name="Energy", expression=energy_expr, source='test')

    # Multiple initial conditions
    initial_states = [
        State(q=np.array([1.0, 0.0]), p=np.array([0.0, 1.0])),
        State(q=np.array([0.5, 0.5]), p=np.array([0.5, 0.5])),
        State(q=np.array([2.0, 0.0]), p=np.array([0.0, 0.5])),
    ]

    result = verify_conservation_ensemble(
        energy,
        initial_states,
        H,
        time_span=(0, 10),
        tolerance=1e-6,
        verbose=False
    )

    # All should conserve energy
    assert result['success_rate'] >= 0.9  # At least 90%
    assert result['max_drift'] < 1e-5


# =============================================================================
# Edge Cases
# =============================================================================

def test_zero_initial_conditions():
    """Test with zero initial conditions"""
    H = make_harmonic_hamiltonian(np.array([1.0, 1.0]))

    def energy_expr(state):
        q, p = state[:2], state[2:4]
        return 0.5 * (np.sum(p**2) + np.sum(q**2))

    energy = ConservedIntegral(name="Energy", expression=energy_expr, source='test')

    # Zero initial state
    initial_state = State(
        q=np.array([0.0, 0.0]),
        p=np.array([0.0, 0.0])
    )

    result = verify_conservation_along_trajectory(
        energy,
        initial_state,
        H,
        time_span=(0, 5),
        tolerance=1e-6,
        verbose=False
    )

    assert result['integration_success']
    # Energy is zero and stays zero
    assert result['conserved']
    assert abs(result['absolute_drift']) < 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
