"""Acceptance-oriented unit tests for the canonical KS prototype."""

import numpy as np
import pytest

from src.python.ks import (
    KSPhaseState,
    KeplerPhaseState,
    NegativeEnergyKSSystem,
    ZeroMomentumQuotient,
    canonical_poisson_matrix,
    cotangent_projection_jacobian,
    fiber_generator,
    ks_jacobian,
    ks_position,
    lift_cotangent,
    momentum_map,
    project_cotangent,
    projected_poisson_matrix,
    s1_action,
)


def circular_state(radius: float = 2.0, mu: float = 1.0) -> KeplerPhaseState:
    return KeplerPhaseState(
        x=np.array([radius, 0.0, 0.0]),
        p=np.array([0.0, np.sqrt(mu / radius), 0.0]),
    )


def test_position_norm_and_jacobian_identities():
    q = np.array([0.7, -0.2, 1.1, 0.4])
    x = ks_position(q)
    jacobian = ks_jacobian(q)
    radius = np.dot(q, q)

    assert np.linalg.norm(x) == pytest.approx(radius, abs=1e-14)
    assert jacobian @ jacobian.T == pytest.approx(4.0 * radius * np.eye(3))
    assert jacobian @ fiber_generator(q) == pytest.approx(np.zeros(3), abs=1e-14)


@pytest.mark.parametrize("angle", [0.0, 0.3, -1.2, np.pi])
def test_s1_action_is_generated_by_xi_and_leaves_quotient_invariant(angle):
    physical = KeplerPhaseState(
        x=np.array([1.2, -0.7, 0.4]),
        p=np.array([0.3, 0.2, -0.5]),
    )
    lifted = lift_cotangent(physical)
    transformed = s1_action(lifted, angle)

    assert transformed.xi == pytest.approx(lifted.xi, abs=2e-15)
    assert project_cotangent(transformed).as_vector() == pytest.approx(
        physical.as_vector(), abs=2e-14
    )

    epsilon = 1e-7
    derivative = (
        s1_action(lifted, epsilon).q - s1_action(lifted, -epsilon).q
    ) / (2.0 * epsilon)
    assert derivative == pytest.approx(fiber_generator(lifted.q), abs=2e-9)
    momentum_derivative = (
        s1_action(lifted, epsilon).Q - s1_action(lifted, -epsilon).Q
    ) / (2.0 * epsilon)
    assert momentum_derivative == pytest.approx(
        fiber_generator(lifted.Q), abs=2e-9
    )


def test_xi_is_vertical_momentum_and_level_is_selectable():
    physical = circular_state()
    level = 0.37
    lifted = lift_cotangent(physical, momentum_level=level)

    assert momentum_map(lifted.q, lifted.Q) == pytest.approx(level, abs=1e-14)
    with pytest.raises(ValueError, match="not on Xi = 0"):
        project_cotangent(lifted)
    assert project_cotangent(
        lifted, require_zero_level=False
    ).as_vector() == pytest.approx(physical.as_vector(), abs=1e-14)


def test_zero_momentum_quotient_section_and_orbit_equivalence():
    quotient = ZeroMomentumQuotient(level_tolerance=1e-13)
    physical = KeplerPhaseState(
        x=np.array([0.8, -0.4, 1.1]),
        p=np.array([0.2, 0.3, -0.1]),
    )
    first = quotient.section(physical, angle=-0.2)
    second = s1_action(first, 1.7)

    assert quotient.equivalent(first, second)
    assert quotient.reduce(second).as_vector() == pytest.approx(
        physical.as_vector(), abs=2e-14
    )


@pytest.mark.parametrize(
    "physical",
    [
        KeplerPhaseState(np.array([1.0, 0.2, 0.3]), np.array([0.1, 0.4, -0.2])),
        KeplerPhaseState(np.array([0.1, -0.2, -3.0]), np.array([-0.3, 0.2, 0.1])),
        KeplerPhaseState(np.array([-2.0, 0.5, 0.0]), np.array([0.0, -0.2, 0.7])),
    ],
)
def test_cotangent_roundtrip_and_canonical_one_form(physical):
    lifted = lift_cotangent(physical, angle=0.73)
    recovered = project_cotangent(lifted)
    assert lifted.xi == pytest.approx(0.0, abs=2e-15)
    assert recovered.as_vector() == pytest.approx(physical.as_vector(), abs=2e-14)

    tangent_q = np.array([0.2, -0.4, 0.7, 0.1])
    dx = ks_jacobian(lifted.q) @ tangent_q
    assert np.dot(lifted.Q, tangent_q) == pytest.approx(
        np.dot(physical.p, dx), abs=2e-14
    )


def test_reduced_poisson_brackets_are_canonical_on_zero_level():
    lifted = lift_cotangent(
        KeplerPhaseState(
            np.array([1.3, -0.4, 0.8]), np.array([0.2, 0.5, -0.1])
        ),
        angle=-0.4,
    )
    assert projected_poisson_matrix(lifted) == pytest.approx(
        canonical_poisson_matrix(3), abs=2e-14
    )


def test_cotangent_projection_jacobian_matches_finite_difference():
    lifted = lift_cotangent(
        KeplerPhaseState(
            np.array([1.3, -0.4, 0.8]), np.array([0.2, 0.5, -0.1])
        ),
        angle=0.2,
    )
    analytic = cotangent_projection_jacobian(lifted)
    base = lifted.as_vector()
    epsilon = 1e-7
    numerical = np.empty((6, 8))
    for column in range(8):
        plus = base.copy()
        minus = base.copy()
        plus[column] += epsilon
        minus[column] -= epsilon
        projected_plus = project_cotangent(
            KSPhaseState(plus[:4], plus[4:]), require_zero_level=False
        ).as_vector()
        projected_minus = project_cotangent(
            KSPhaseState(minus[:4], minus[4:]), require_zero_level=False
        ).as_vector()
        numerical[:, column] = (projected_plus - projected_minus) / (2.0 * epsilon)

    assert analytic == pytest.approx(numerical, abs=3e-9)


def test_regularized_hamiltonian_is_regular_oscillator_and_matches_kepler_shell():
    mu = 1.7
    physical = circular_state(radius=2.3, mu=mu)
    energy = -mu / (2.0 * physical.radius)
    system = NegativeEnergyKSSystem(kappa=mu, energy=energy)
    lifted = lift_cotangent(physical)

    assert system.kepler_hamiltonian(physical) == pytest.approx(energy, abs=1e-15)
    assert system.regularized_hamiltonian(lifted) == pytest.approx(0.0, abs=1e-14)
    assert system.validate_shell(lifted)

    collision = KSPhaseState(q=np.zeros(4), Q=np.ones(4))
    assert np.isfinite(system.regularized_hamiltonian(collision))


def test_regularized_vector_field_projects_to_sundman_scaled_kepler_field():
    mu = 1.0
    semimajor_axis = 2.0
    eccentricity = 0.5
    periapsis = semimajor_axis * (1.0 - eccentricity)
    speed = np.sqrt(
        mu * (1.0 + eccentricity) / (semimajor_axis * (1.0 - eccentricity))
    )
    physical = KeplerPhaseState(
        x=np.array([periapsis, 0.0, 0.0]),
        p=np.array([0.0, speed, 0.0]),
    )
    system = NegativeEnergyKSSystem(
        kappa=mu, energy=-mu / (2.0 * semimajor_axis)
    )
    lifted = lift_cotangent(physical)
    dq_ds, dQ_ds = system.vector_field(lifted)
    projected = cotangent_projection_jacobian(lifted) @ np.concatenate(
        (dq_ds, dQ_ds)
    )
    kepler_field = np.concatenate(
        (physical.p, -mu * physical.x / physical.radius**3)
    )

    assert system.validate_shell(lifted)
    assert projected == pytest.approx(lifted.radius * kepler_field, abs=2e-14)


def test_nonunit_reduced_mass_uses_canonical_momentum_and_correct_period():
    reduced_mass = 0.25
    kappa = 1.5
    radius = 1.8
    gravitational_parameter = kappa / reduced_mass
    velocity = np.sqrt(gravitational_parameter / radius)
    physical = KeplerPhaseState(
        x=np.array([radius, 0.0, 0.0]),
        p=np.array([0.0, reduced_mass * velocity, 0.0]),
    )
    energy = -kappa / (2.0 * radius)
    system = NegativeEnergyKSSystem(
        kappa=kappa,
        energy=energy,
        reduced_mass=reduced_mass,
    )
    lifted = lift_cotangent(physical)
    expected_period = 2.0 * np.pi * np.sqrt(
        radius**3 / gravitational_parameter
    )

    assert system.kepler_hamiltonian(physical) == pytest.approx(energy, abs=2e-15)
    assert system.regularized_hamiltonian(lifted) == pytest.approx(0.0, abs=2e-15)
    assert system.physical_period(lifted) == pytest.approx(expected_period, rel=2e-15)


def test_exact_oscillator_flow_conserves_k_xi_and_projects_to_circular_kepler_orbit():
    mu = 1.0
    radius = 2.0
    physical = circular_state(radius=radius, mu=mu)
    energy = -mu / (2.0 * radius)
    system = NegativeEnergyKSSystem(kappa=mu, energy=energy)
    lifted = lift_cotangent(physical)
    s = np.linspace(0.0, system.quotient_period(), 257)

    q, Q = system.flow(lifted, s)
    k_values = []
    xi_values = []
    for q_i, Q_i in zip(q, Q):
        state = KSPhaseState(q_i, Q_i)
        k_values.append(system.regularized_hamiltonian(state))
        xi_values.append(state.xi)
    times, positions, momenta = system.trajectory(lifted, s)

    expected_period = 2.0 * np.pi * np.sqrt(radius**3 / mu)
    assert system.physical_period(lifted) == pytest.approx(expected_period, rel=2e-15)
    assert times[-1] == pytest.approx(expected_period, rel=2e-15)
    assert np.max(np.abs(k_values)) < 2e-15
    assert np.max(np.abs(xi_values)) < 2e-15
    assert np.linalg.norm(positions, axis=1) == pytest.approx(
        radius * np.ones(s.size), abs=3e-14
    )
    assert positions[-1] == pytest.approx(positions[0], abs=3e-14)
    assert momenta[-1] == pytest.approx(momenta[0], abs=2e-14)


def test_regularized_radial_collision_crosses_q_zero_smoothly():
    mu = 1.0
    apocenter = 2.0
    energy = -mu / apocenter
    system = NegativeEnergyKSSystem(kappa=mu, energy=energy)
    initial = lift_cotangent(
        KeplerPhaseState(
            x=np.array([0.0, 0.0, apocenter]),
            p=np.zeros(3),
        )
    )
    collision_s = np.pi / (2.0 * system.angular_frequency)
    offsets = np.array([-1e-6, 0.0, 1e-6])
    q, Q = system.flow(initial, collision_s + offsets)

    assert np.linalg.norm(q[1]) < 2e-16
    assert np.linalg.norm(Q[1]) > 0.0
    assert ks_position(q[0])[2] > 0.0
    assert ks_position(q[2])[2] > 0.0
    assert ks_position(q[0]) == pytest.approx(ks_position(q[2]), abs=2e-14)
    for q_i, Q_i in zip(q, Q):
        assert system.regularized_hamiltonian(KSPhaseState(q_i, Q_i)) == pytest.approx(
            0.0, abs=2e-14
        )


def test_system_rejects_nonnegative_energy():
    with pytest.raises(ValueError, match="negative"):
        NegativeEnergyKSSystem(kappa=1.0, energy=0.0)
