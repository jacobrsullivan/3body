"""Numerical and analytic checks for the independent Kepler reference."""

import math

import numpy as np
import pytest
from scipy.optimize import brentq

from kepler_reference import (
    EllipticElements,
    cartesian_from_eccentric_anomaly,
    cartesian_state_at_time,
    eccentric_anomaly_at_time,
    orbital_diagnostics,
    period_closure,
    propagate_elliptic,
    solve_kepler_elliptic,
)


@pytest.mark.parametrize("eccentricity", [0.0, 0.2, 0.8, 0.97, 0.999999])
@pytest.mark.parametrize(
    "mean_anomaly",
    [
        -8.0 * math.pi - 0.3,
        -math.pi,
        -1.0e-12,
        0.0,
        1.0e-12,
        0.7,
        math.pi,
        10.0 * math.pi + 2.1,
    ],
)
def test_kepler_solver_residual(mean_anomaly, eccentricity):
    eccentric_anomaly = solve_kepler_elliptic(mean_anomaly, eccentricity)
    residual = (
        eccentric_anomaly
        - eccentricity * math.sin(eccentric_anomaly)
        - mean_anomaly
    )
    assert abs(residual) <= 2.0e-14


@pytest.mark.parametrize("eccentricity", [0.2, 0.8, 0.97, 0.999999])
@pytest.mark.parametrize(
    "mean_anomaly",
    [-3.0, -0.2, -1.0e-10, 1.0e-10, 0.2, 2.7],
)
def test_kepler_solver_matches_scipy_brentq(mean_anomaly, eccentricity):
    expected = brentq(
        lambda anomaly: anomaly
        - eccentricity * math.sin(anomaly)
        - mean_anomaly,
        -math.pi,
        math.pi,
        xtol=5.0e-15,
        rtol=4.0 * np.finfo(float).eps,
    )
    actual = solve_kepler_elliptic(mean_anomaly, eccentricity)
    assert actual == pytest.approx(expected, abs=3.0e-13)


def test_circular_orbit_has_known_cardinal_states():
    elements = EllipticElements(mu=4.0, semi_major_axis=2.0, eccentricity=0.0)
    circular_speed = math.sqrt(elements.mu / elements.semi_major_axis)

    initial = cartesian_state_at_time(elements, elements.epoch)
    quarter = cartesian_state_at_time(
        elements,
        elements.epoch + 0.25 * elements.period,
    )

    np.testing.assert_allclose(
        initial,
        [2.0, 0.0, 0.0, 0.0, circular_speed, 0.0],
        atol=2.0e-15,
    )
    np.testing.assert_allclose(
        quarter,
        [0.0, 2.0, 0.0, -circular_speed, 0.0, 0.0],
        atol=2.0e-15,
    )


def test_periapsis_and_apoapsis_states_match_vis_viva():
    elements = EllipticElements(mu=1.7, semi_major_axis=3.0, eccentricity=0.7)

    periapsis = cartesian_from_eccentric_anomaly(elements, 0.0)
    apoapsis = cartesian_from_eccentric_anomaly(elements, math.pi)
    expected_periapsis_speed = math.sqrt(
        elements.mu
        * (1.0 + elements.eccentricity)
        / (elements.semi_major_axis * (1.0 - elements.eccentricity))
    )
    expected_apoapsis_speed = math.sqrt(
        elements.mu
        * (1.0 - elements.eccentricity)
        / (elements.semi_major_axis * (1.0 + elements.eccentricity))
    )

    assert np.linalg.norm(periapsis[:3]) == pytest.approx(
        elements.periapsis_radius
    )
    assert np.linalg.norm(apoapsis[:3]) == pytest.approx(elements.apoapsis_radius)
    assert np.linalg.norm(periapsis[3:]) == pytest.approx(expected_periapsis_speed)
    assert np.linalg.norm(apoapsis[3:]) == pytest.approx(expected_apoapsis_speed)


def test_inertial_orientation_matches_classical_element_normal():
    elements = EllipticElements(
        mu=1.0,
        semi_major_axis=2.0,
        eccentricity=0.4,
        inclination=0.8,
        longitude_of_ascending_node=-0.6,
        argument_of_periapsis=1.2,
    )
    diagnostics = orbital_diagnostics(
        cartesian_from_eccentric_anomaly(elements, 0.4),
        elements.mu,
    )
    actual_normal = (
        diagnostics.angular_momentum / diagnostics.angular_momentum_magnitude
    )
    expected_normal = np.array(
        [
            math.sin(elements.longitude_of_ascending_node)
            * math.sin(elements.inclination),
            -math.cos(elements.longitude_of_ascending_node)
            * math.sin(elements.inclination),
            math.cos(elements.inclination),
        ]
    )
    np.testing.assert_allclose(actual_normal, expected_normal, atol=3.0e-15)


def test_diagnostics_match_closed_form_invariants():
    elements = EllipticElements(
        mu=2.3,
        semi_major_axis=1.8,
        eccentricity=0.72,
        inclination=0.4,
        longitude_of_ascending_node=0.9,
        argument_of_periapsis=-0.3,
        mean_anomaly_at_epoch=1.1,
    )
    states = propagate_elliptic(
        elements,
        elements.epoch + np.linspace(0.0, elements.period, 65),
    )
    expected_energy = -elements.mu / (2.0 * elements.semi_major_axis)
    expected_angular_momentum = math.sqrt(
        elements.mu
        * elements.semi_major_axis
        * (1.0 - elements.eccentricity**2)
    )
    expected_lrl = elements.mu * elements.eccentricity

    for state in states:
        diagnostics = orbital_diagnostics(state, elements.mu)
        assert diagnostics.specific_energy == pytest.approx(
            expected_energy, rel=3.0e-15, abs=3.0e-15
        )
        assert diagnostics.angular_momentum_magnitude == pytest.approx(
            expected_angular_momentum, rel=3.0e-15, abs=3.0e-15
        )
        assert np.linalg.norm(diagnostics.laplace_runge_lenz) == pytest.approx(
            expected_lrl, rel=8.0e-15, abs=3.0e-15
        )
        assert diagnostics.eccentricity == pytest.approx(
            elements.eccentricity, rel=8.0e-15, abs=3.0e-15
        )


def test_period_and_multi_period_closure():
    elements = EllipticElements(
        mu=0.8,
        semi_major_axis=2.2,
        eccentricity=0.9,
        inclination=1.1,
        longitude_of_ascending_node=2.0,
        argument_of_periapsis=-0.7,
        mean_anomaly_at_epoch=0.45,
        epoch=3.0,
    )
    expected_period = 2.0 * math.pi * math.sqrt(
        elements.semi_major_axis**3 / elements.mu
    )
    closure = period_closure(elements, periods=7)

    assert elements.period == pytest.approx(expected_period, rel=2.0e-16)
    assert closure.elapsed_time == pytest.approx(7.0 * expected_period)
    assert closure.position_error < 2.0e-13
    assert closure.velocity_error < 2.0e-13
    assert closure.relative_state_error < 1.0e-13


def test_propagation_shapes_and_continuous_anomaly():
    elements = EllipticElements(mu=1.0, semi_major_axis=1.0, eccentricity=0.4)

    scalar_state = propagate_elliptic(elements, 0.0)
    grid_states = propagate_elliptic(elements, np.zeros((2, 3)))
    empty_states = propagate_elliptic(elements, np.array([]))
    anomaly_0 = eccentric_anomaly_at_time(elements, elements.epoch)
    anomaly_3 = eccentric_anomaly_at_time(
        elements,
        elements.epoch + 3.0 * elements.period,
    )

    assert scalar_state.shape == (6,)
    assert grid_states.shape == (2, 3, 6)
    assert empty_states.shape == (0, 6)
    assert anomaly_3 - anomaly_0 == pytest.approx(6.0 * math.pi, abs=5.0e-15)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mu": 0.0, "semi_major_axis": 1.0, "eccentricity": 0.0},
        {"mu": 1.0, "semi_major_axis": 0.0, "eccentricity": 0.0},
        {"mu": 1.0, "semi_major_axis": 1.0, "eccentricity": -0.1},
        {"mu": 1.0, "semi_major_axis": 1.0, "eccentricity": 1.0},
    ],
)
def test_invalid_elements_are_rejected(kwargs):
    with pytest.raises(ValueError):
        EllipticElements(**kwargs)


def test_diagnostics_reject_collision_state():
    with pytest.raises(ValueError, match="collision"):
        orbital_diagnostics(np.zeros(6), mu=1.0)
