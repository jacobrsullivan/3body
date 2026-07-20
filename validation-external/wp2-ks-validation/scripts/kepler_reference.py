"""Independent analytic reference for bound two-body Kepler motion.

This module is validation-side code.  It deliberately imports nothing from
``src/python`` and does not use any KS or production dynamics implementation.

Conventions
-----------
States are relative, specific (per unit reduced mass) Cartesian states ordered
as ``[x, y, z, vx, vy, vz]`` in a right-handed inertial frame.  The equation of
motion is ``r_ddot = -mu * r / |r|**3``, where ``mu = G * (m1 + m2)``.  Length,
time, and mass units are arbitrary but must be mutually consistent.

Classical elliptic elements use radians and the standard active rotation
``R3(Omega) R1(i) R3(omega)`` from perifocal to inertial coordinates.  Mean
anomaly evolves as ``M(t) = M0 + sqrt(mu/a**3) * (t - epoch)`` and eccentric
anomaly solves ``M = E - e sin(E)``.  The Laplace-Runge-Lenz vector reported by
this module is the specific dimensional vector
``A = v x h - mu * r/|r|``; dividing it by ``mu`` gives the eccentricity vector.
Only collision-free elliptic motion (``a > 0`` and ``0 <= e < 1``) is in scope.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]
_TWO_PI = 2.0 * math.pi
_MACHINE_EPSILON = np.finfo(np.float64).eps


@dataclass(frozen=True)
class EllipticElements:
    """Classical elements for one bound relative Kepler orbit."""

    mu: float
    semi_major_axis: float
    eccentricity: float
    inclination: float = 0.0
    longitude_of_ascending_node: float = 0.0
    argument_of_periapsis: float = 0.0
    mean_anomaly_at_epoch: float = 0.0
    epoch: float = 0.0

    def __post_init__(self) -> None:
        values = (
            self.mu,
            self.semi_major_axis,
            self.eccentricity,
            self.inclination,
            self.longitude_of_ascending_node,
            self.argument_of_periapsis,
            self.mean_anomaly_at_epoch,
            self.epoch,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("all orbital elements must be finite")
        if self.mu <= 0.0:
            raise ValueError("mu must be positive")
        if self.semi_major_axis <= 0.0:
            raise ValueError("semi-major axis must be positive")
        if not 0.0 <= self.eccentricity < 1.0:
            raise ValueError("elliptic eccentricity must satisfy 0 <= e < 1")

    @property
    def mean_motion(self) -> float:
        """Return ``sqrt(mu/a**3)`` in radians per unit time."""

        return math.sqrt(self.mu / self.semi_major_axis**3)

    @property
    def period(self) -> float:
        """Return the analytic orbital period."""

        return _TWO_PI / self.mean_motion

    @property
    def periapsis_radius(self) -> float:
        """Return ``a * (1 - e)``."""

        return self.semi_major_axis * (1.0 - self.eccentricity)

    @property
    def apoapsis_radius(self) -> float:
        """Return ``a * (1 + e)``."""

        return self.semi_major_axis * (1.0 + self.eccentricity)


@dataclass(frozen=True)
class KeplerDiagnostics:
    """Specific invariants evaluated from one Cartesian state."""

    radius: float
    speed: float
    specific_energy: float
    angular_momentum: FloatArray
    angular_momentum_magnitude: float
    laplace_runge_lenz: FloatArray
    eccentricity_vector: FloatArray
    eccentricity: float


@dataclass(frozen=True)
class PeriodClosure:
    """Cartesian mismatch after an integer number of analytic periods."""

    periods: int
    elapsed_time: float
    initial_state: FloatArray
    final_state: FloatArray
    position_error: float
    velocity_error: float
    state_error: float
    relative_state_error: float


def solve_kepler_elliptic(
    mean_anomaly: float,
    eccentricity: float,
    *,
    tolerance: float = 8.0 * _MACHINE_EPSILON,
    max_iterations: int = 96,
) -> float:
    """Solve ``E - e sin(E) = M`` with safeguarded Newton iteration.

    The monotonic elliptic equation is bracketed on ``[-pi, pi]`` after phase
    reduction.  Newton steps that leave the bracket fall back to bisection.
    The removed whole-revolution offset is restored in the returned anomaly.
    This remains reliable for eccentricities close to one and mean anomalies
    close to periapsis, where an unsafeguarded Newton solve can fail.
    """

    if not math.isfinite(mean_anomaly):
        raise ValueError("mean anomaly must be finite")
    if not math.isfinite(eccentricity) or not 0.0 <= eccentricity < 1.0:
        raise ValueError("elliptic eccentricity must satisfy 0 <= e < 1")
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be positive and finite")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if eccentricity == 0.0:
        return float(mean_anomaly)

    reduced_mean_anomaly = math.remainder(mean_anomaly, _TWO_PI)
    revolution_offset = mean_anomaly - reduced_mean_anomaly

    if reduced_mean_anomaly == 0.0:
        return revolution_offset
    if abs(reduced_mean_anomaly) == math.pi:
        return revolution_offset + reduced_mean_anomaly

    lower = -math.pi
    upper = math.pi
    if eccentricity < 0.8:
        estimate = reduced_mean_anomaly
    else:
        estimate = math.copysign(0.5 * math.pi, reduced_mean_anomaly)

    for _ in range(max_iterations):
        residual = (
            estimate
            - eccentricity * math.sin(estimate)
            - reduced_mean_anomaly
        )
        if residual == 0.0:
            return revolution_offset + estimate

        if residual < 0.0:
            lower = estimate
        else:
            upper = estimate

        derivative = 1.0 - eccentricity * math.cos(estimate)
        newton_step = residual / derivative
        candidate = estimate - newton_step
        if not lower < candidate < upper or not math.isfinite(candidate):
            candidate = 0.5 * (lower + upper)

        step_tolerance = tolerance * max(1.0, abs(candidate))
        if abs(candidate - estimate) <= step_tolerance:
            return revolution_offset + candidate
        estimate = candidate

    raise RuntimeError(
        "elliptic Kepler solver did not converge within "
        f"{max_iterations} iterations"
    )


def eccentric_anomaly_at_time(elements: EllipticElements, time: float) -> float:
    """Return the continuous eccentric anomaly at an inertial time."""

    if not math.isfinite(time):
        raise ValueError("time must be finite")
    mean_anomaly = elements.mean_anomaly_at_epoch + elements.mean_motion * (
        time - elements.epoch
    )
    return solve_kepler_elliptic(mean_anomaly, elements.eccentricity)


def _perifocal_to_inertial(elements: EllipticElements) -> FloatArray:
    """Construct ``R3(Omega) R1(i) R3(omega)``."""

    omega_node = elements.longitude_of_ascending_node
    inclination = elements.inclination
    omega_periapsis = elements.argument_of_periapsis

    c_node = math.cos(omega_node)
    s_node = math.sin(omega_node)
    c_inc = math.cos(inclination)
    s_inc = math.sin(inclination)
    c_peri = math.cos(omega_periapsis)
    s_peri = math.sin(omega_periapsis)

    return np.array(
        [
            [
                c_node * c_peri - s_node * s_peri * c_inc,
                -c_node * s_peri - s_node * c_peri * c_inc,
                s_node * s_inc,
            ],
            [
                s_node * c_peri + c_node * s_peri * c_inc,
                -s_node * s_peri + c_node * c_peri * c_inc,
                -c_node * s_inc,
            ],
            [s_peri * s_inc, c_peri * s_inc, c_inc],
        ],
        dtype=np.float64,
    )


def cartesian_from_eccentric_anomaly(
    elements: EllipticElements,
    eccentric_anomaly: float,
) -> FloatArray:
    """Generate one inertial Cartesian state from eccentric anomaly."""

    if not math.isfinite(eccentric_anomaly):
        raise ValueError("eccentric anomaly must be finite")

    a = elements.semi_major_axis
    e = elements.eccentricity
    cosine = math.cos(eccentric_anomaly)
    sine = math.sin(eccentric_anomaly)
    beta = math.sqrt((1.0 - e) * (1.0 + e))
    radius_factor = 1.0 - e * cosine
    eccentric_anomaly_rate = elements.mean_motion / radius_factor

    position_perifocal = np.array(
        [a * (cosine - e), a * beta * sine, 0.0],
        dtype=np.float64,
    )
    velocity_perifocal = np.array(
        [
            -a * sine * eccentric_anomaly_rate,
            a * beta * cosine * eccentric_anomaly_rate,
            0.0,
        ],
        dtype=np.float64,
    )
    rotation = _perifocal_to_inertial(elements)
    return np.concatenate(
        (rotation @ position_perifocal, rotation @ velocity_perifocal)
    )


def cartesian_state_at_time(
    elements: EllipticElements,
    time: float,
) -> FloatArray:
    """Propagate analytically to ``time`` and return a six-component state."""

    eccentric_anomaly = eccentric_anomaly_at_time(elements, time)
    return cartesian_from_eccentric_anomaly(elements, eccentric_anomaly)


def propagate_elliptic(
    elements: EllipticElements,
    times: ArrayLike | Iterable[float],
) -> FloatArray:
    """Propagate to scalar or array-like times.

    A scalar input returns shape ``(6,)``.  An input with shape ``S`` returns
    states with shape ``S + (6,)``.
    """

    time_array = np.asarray(times, dtype=np.float64)
    if not np.all(np.isfinite(time_array)):
        raise ValueError("all propagation times must be finite")
    if time_array.size == 0:
        return np.empty(time_array.shape + (6,), dtype=np.float64)
    flat_states = np.stack(
        [cartesian_state_at_time(elements, float(time)) for time in time_array.flat]
    )
    states = flat_states.reshape(time_array.shape + (6,))
    if time_array.ndim == 0:
        return states.reshape(6)
    return states


def orbital_diagnostics(state: ArrayLike, mu: float) -> KeplerDiagnostics:
    """Evaluate energy, angular momentum, and LRL invariants from a state."""

    state_array = np.asarray(state, dtype=np.float64)
    if state_array.shape != (6,):
        raise ValueError("state must have shape (6,)")
    if not np.all(np.isfinite(state_array)):
        raise ValueError("state must contain only finite values")
    if not math.isfinite(mu) or mu <= 0.0:
        raise ValueError("mu must be positive and finite")

    position = state_array[:3]
    velocity = state_array[3:]
    radius = float(np.linalg.norm(position))
    if radius == 0.0:
        raise ValueError("diagnostics are undefined at collision")
    speed = float(np.linalg.norm(velocity))
    angular_momentum = np.cross(position, velocity)
    angular_momentum_magnitude = float(np.linalg.norm(angular_momentum))
    specific_energy = 0.5 * speed**2 - mu / radius
    laplace_runge_lenz = (
        np.cross(velocity, angular_momentum) - mu * position / radius
    )
    eccentricity_vector = laplace_runge_lenz / mu

    return KeplerDiagnostics(
        radius=radius,
        speed=speed,
        specific_energy=float(specific_energy),
        angular_momentum=angular_momentum,
        angular_momentum_magnitude=angular_momentum_magnitude,
        laplace_runge_lenz=laplace_runge_lenz,
        eccentricity_vector=eccentricity_vector,
        eccentricity=float(np.linalg.norm(eccentricity_vector)),
    )


def period_closure(
    elements: EllipticElements,
    *,
    periods: int = 1,
) -> PeriodClosure:
    """Measure analytic Cartesian closure after whole orbital periods."""

    if isinstance(periods, bool) or not isinstance(periods, int) or periods < 1:
        raise ValueError("periods must be a positive integer")
    elapsed_time = periods * elements.period
    initial_state = cartesian_state_at_time(elements, elements.epoch)
    final_state = cartesian_state_at_time(
        elements,
        elements.epoch + elapsed_time,
    )
    difference = final_state - initial_state
    position_error = float(np.linalg.norm(difference[:3]))
    velocity_error = float(np.linalg.norm(difference[3:]))
    state_error = float(np.linalg.norm(difference))
    state_scale = max(float(np.linalg.norm(initial_state)), _MACHINE_EPSILON)

    return PeriodClosure(
        periods=periods,
        elapsed_time=elapsed_time,
        initial_state=initial_state,
        final_state=final_state,
        position_error=position_error,
        velocity_error=velocity_error,
        state_error=state_error,
        relative_state_error=state_error / state_scale,
    )
