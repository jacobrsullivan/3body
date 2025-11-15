"""
Test suite for triviality filtering and independence testing (WP 3.1, Task 3.1.4).

Tests:
- Known integrals database
- Triviality detection (coordinates, known integrals, constants)
- Functional independence (Jacobian rank)
- Poisson brackets and involution
"""

import pytest
import numpy as np

from src.python.analysis.triviality_filter import (
    KnownIntegrals,
    is_trivial_coordinate,
    is_trivial_known,
    is_constant_on_shell,
    filter_trivial_integrals,
    generate_test_states
)
from src.python.analysis.independence_test import (
    test_functional_independence,
    compute_poisson_bracket,
    test_involution,
    analyze_integral_structure
)
from src.python.analysis.integral_from_killing import (
    ConservedIntegral,
    State
)


# =============================================================================
# Test Known Integrals Database
# =============================================================================

def test_energy_integral():
    """Test energy integral creation"""
    masses = np.array([1.0, 1.0, 1.0])
    energy = KnownIntegrals.energy(masses)

    assert isinstance(energy, ConservedIntegral)
    assert energy.name == "Energy"
    assert energy.source == 'known'

    # Test evaluation
    state = State(q=np.array([1.0, 0.0]), p=np.array([1.0, 0.0]))
    E = energy(state.to_array())
    assert np.isfinite(E)


def test_angular_momentum():
    """Test angular momentum components"""
    L_components = KnownIntegrals.angular_momentum_components()

    assert len(L_components) >= 1
    assert all(isinstance(L, ConservedIntegral) for L in L_components)
    assert all(L.source == 'known' for L in L_components)


def test_get_all_known():
    """Test retrieving all known integrals"""
    masses = np.array([1.0, 1.0, 1.0])

    # Generic manifold
    known_generic = KnownIntegrals.get_all_known('generic', masses)
    assert len(known_generic) >= 2  # At least E and L_z

    # S¹ bundle (should include p_θ)
    known_s1 = KnownIntegrals.get_all_known('s1_bundle', masses)
    assert len(known_s1) > len(known_generic)


# =============================================================================
# Test Triviality Detection
# =============================================================================

def test_is_trivial_coordinate():
    """Test coordinate function detection"""
    # Create integral that's just q_0
    def q0_integral(state):
        if isinstance(state, State):
            return state.q[0]
        return state[0]

    integral = ConservedIntegral(
        name="q0",
        expression=q0_integral,
        source='test'
    )

    # Generate test states
    test_states = generate_test_states(dimension=2, num_states=50, seed=42)

    # Should detect as coordinate
    is_triv, coord_name = is_trivial_coordinate(integral, test_states)
    assert is_triv
    assert coord_name == 'q_0'


def test_is_trivial_known():
    """Test detection of known integrals"""
    # Create integral that's exactly energy
    masses = np.array([1.0, 1.0])
    energy = KnownIntegrals.energy(masses)

    # Create duplicate with different name
    duplicate = ConservedIntegral(
        name="MyEnergy",
        expression=energy.expression,
        source='test'
    )

    test_states = generate_test_states(dimension=2, num_states=50)
    known_integrals = [energy]

    is_triv, match = is_trivial_known(duplicate, known_integrals, test_states)
    assert is_triv
    assert match == "Energy"


def test_is_constant_on_shell():
    """Test constant detection"""
    # Create constant integral
    def constant_integral(state):
        return 42.0

    integral = ConservedIntegral(
        name="Constant",
        expression=constant_integral,
        source='test'
    )

    test_states = generate_test_states(dimension=2, num_states=50)

    is_const = is_constant_on_shell(integral, test_states, tolerance=1e-6)
    assert is_const


def test_filter_trivial_integrals():
    """Test complete triviality filtering pipeline"""
    # Create mix of trivial and non-trivial integrals
    def non_trivial_expr(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            n = len(state) // 2
            q, p = state[:n], state[n:]
        # Some nonlinear combination
        return q[0]**2 + p[1]**2

    def coordinate_expr(state):
        if isinstance(state, State):
            return state.q[0]
        return state[0]

    candidates = [
        ConservedIntegral(name="NonTrivial", expression=non_trivial_expr, source='test'),
        ConservedIntegral(name="Coordinate", expression=coordinate_expr, source='test'),
    ]

    masses = np.array([1.0, 1.0])
    known = KnownIntegrals.get_all_known('generic', masses)
    test_states = generate_test_states(dimension=2, num_states=50)

    non_trivial, rejections = filter_trivial_integrals(
        candidates,
        known,
        test_states,
        verbose=False
    )

    # Coordinate should be rejected
    assert len(non_trivial) < len(candidates)
    assert any(r['reason'].startswith('coordinate') for r in rejections)


# =============================================================================
# Test Functional Independence
# =============================================================================

def test_functional_independence_independent_set():
    """Test independence of truly independent integrals"""
    # q_0 and p_0 are independent
    def I1(state):
        return state[0]  # q_0

    def I2(state):
        return state[2]  # p_0

    integrals = [
        ConservedIntegral(name="I1", expression=I1, source='test'),
        ConservedIntegral(name="I2", expression=I2, source='test')
    ]

    test_states = generate_test_states(dimension=2, num_states=30)

    result = test_functional_independence(integrals, test_states, verbose=False)

    assert result['independent']
    assert result['rank'] == 2
    assert result['expected_rank'] == 2


def test_functional_independence_dependent_set():
    """Test detection of dependent integrals"""
    # I1 = q_0, I2 = 2*q_0 (linearly dependent)
    def I1(state):
        return state[0]

    def I2(state):
        return 2.0 * state[0]

    integrals = [
        ConservedIntegral(name="I1", expression=I1, source='test'),
        ConservedIntegral(name="I2", expression=I2, source='test')
    ]

    test_states = generate_test_states(dimension=2, num_states=30)

    result = test_functional_independence(integrals, test_states, tolerance=1e-6, verbose=False)

    assert not result['independent']
    assert result['rank'] == 1  # Only one independent
    assert result['expected_rank'] == 2


# =============================================================================
# Test Poisson Brackets
# =============================================================================

def test_poisson_bracket_coordinates():
    """Test Poisson bracket of canonical coordinates"""
    # {q_i, p_j} = δ_ij
    def q0(state):
        return state[0]

    def p0(state):
        return state[2]

    def p1(state):
        return state[3]

    I_q0 = ConservedIntegral(name="q0", expression=q0, source='test')
    I_p0 = ConservedIntegral(name="p0", expression=p0, source='test')
    I_p1 = ConservedIntegral(name="p1", expression=p1, source='test')

    state = State(q=np.array([1.0, 2.0]), p=np.array([3.0, 4.0]))

    # {q_0, p_0} should be ~ 1
    bracket_00 = compute_poisson_bracket(I_q0, I_p0, state)
    assert abs(bracket_00 - 1.0) < 0.1

    # {q_0, p_1} should be ~ 0
    bracket_01 = compute_poisson_bracket(I_q0, I_p1, state)
    assert abs(bracket_01) < 0.1


def test_involution_harmonic_oscillator():
    """Test involution for harmonic oscillator integrals"""
    # Energy and angular momentum should be in involution for 2D harmonic oscillator
    # H = (p_x² + p_y²)/2 + (x² + y²)/2
    # L = x p_y - y p_x

    def energy(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            n = len(state) // 2
            q, p = state[:n], state[n:]
        return 0.5 * (np.sum(p**2) + np.sum(q**2))

    def ang_mom(state):
        if isinstance(state, State):
            q, p = state.q, state.p
        else:
            q, p = state[:2], state[2:4]
        return q[0] * p[1] - q[1] * p[0]

    integrals = [
        ConservedIntegral(name="E", expression=energy, source='test'),
        ConservedIntegral(name="L", expression=ang_mom, source='test')
    ]

    test_states = generate_test_states(dimension=2, num_states=20)

    result = test_involution(integrals, test_states, tolerance=0.1, verbose=False)

    # {E, L} should be ~ 0 for harmonic oscillator
    assert result['in_involution'] or result['max_bracket'] < 0.5


# =============================================================================
# Test Complete Structure Analysis
# =============================================================================

def test_analyze_integral_structure():
    """Test complete structure analysis"""
    # Create set of integrals
    def I1(state):
        return state[0]  # q_0

    def I2(state):
        return state[2]  # p_0

    integrals = [
        ConservedIntegral(name="q0", expression=I1, source='test'),
        ConservedIntegral(name="p0", expression=I2, source='test')
    ]

    test_states = generate_test_states(dimension=2, num_states=30)

    result = analyze_integral_structure(integrals, test_states, verbose=False)

    assert 'independence' in result
    assert 'involution' in result
    assert 'integrability_status' in result
    assert result['num_independent'] == 2
    assert result['phase_space_dim'] == 4  # 2D system


# =============================================================================
# Test Generate Test States
# =============================================================================

def test_generate_test_states():
    """Test random state generation"""
    states = generate_test_states(dimension=3, num_states=50, seed=42)

    assert len(states) == 50
    assert all(isinstance(s, State) for s in states)
    assert all(s.dimension == 3 for s in states)

    # Check determinism with seed
    states2 = generate_test_states(dimension=3, num_states=50, seed=42)
    for s1, s2 in zip(states, states2):
        assert np.allclose(s1.q, s2.q)
        assert np.allclose(s1.p, s2.p)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
