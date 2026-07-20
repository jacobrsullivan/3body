"""Analytic and published benchmarks for the bounded N3BP track."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contract import InertialState, SystemParameters


@dataclass(frozen=True)
class BenchmarkOrbit:
    name: str
    initial_state: InertialState
    parameters: SystemParameters
    period: float
    citation: str

    def __post_init__(self) -> None:
        if not np.isfinite(self.period) or self.period <= 0.0:
            raise ValueError("period must be finite and positive")


def lagrange_equilateral(
    *,
    side_length: float = 1.0,
    mass: float = 1.0,
    gravitational_constant: float = 1.0,
    phase: float = 0.0,
) -> BenchmarkOrbit:
    """Return the equal-mass Lagrange relative equilibrium.

    ``side_length`` is the triangle side, not its circumradius. The angular
    frequency is ``sqrt(G * total_mass / side_length**3)``.
    """

    if not np.isfinite(side_length) or side_length <= 0.0:
        raise ValueError("side_length must be finite and positive")
    parameters = SystemParameters(
        masses=np.full(3, mass, dtype=np.float64),
        gravitational_constant=gravitational_constant,
    )
    angular_frequency = np.sqrt(
        parameters.gravitational_constant
        * parameters.total_mass
        / side_length**3
    )
    circumradius = side_length / np.sqrt(3.0)
    angles = phase + np.arange(3, dtype=np.float64) * (2.0 * np.pi / 3.0)
    positions = circumradius * np.column_stack(
        (np.cos(angles), np.sin(angles), np.zeros(3))
    )
    velocities = angular_frequency * np.column_stack(
        (-positions[:, 1], positions[:, 0], np.zeros(3))
    )
    return BenchmarkOrbit(
        name="lagrange-equilateral-equal-mass",
        initial_state=InertialState.from_components(positions, velocities),
        parameters=parameters,
        period=float(2.0 * np.pi / angular_frequency),
        citation="Lagrange (1772), equal-mass equilateral relative equilibrium",
    )


def lagrange_analytic_state(orbit: BenchmarkOrbit, time: float) -> InertialState:
    """Evaluate the rigidly rotating Lagrange benchmark analytically."""

    if orbit.name != "lagrange-equilateral-equal-mass":
        raise ValueError("orbit is not the Lagrange equilateral benchmark")
    angle = 2.0 * np.pi * float(time) / orbit.period
    cosine = np.cos(angle)
    sine = np.sin(angle)
    rotation = np.array(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]]
    )
    return InertialState.from_components(
        orbit.initial_state.positions @ rotation.T,
        orbit.initial_state.velocities @ rotation.T,
    )


def figure_eight_choreography() -> BenchmarkOrbit:
    """Return the commonly published rounded figure-eight initial state.

    The values are the Chenciner-Montgomery figure-eight data reproduced in
    Table 2 of Hubber et al., A&A 529 A27 (2011), DOI
    10.1051/0004-6361/201014949. They are intentionally not numerically
    corrected here, so periodic closure is bounded by the published digits.
    """

    x = 0.97000436
    y = -0.24308753
    velocity_x = 0.466203685
    velocity_y = 0.43236573
    positions = np.array(
        [[x, y, 0.0], [-x, -y, 0.0], [0.0, 0.0, 0.0]],
        dtype=np.float64,
    )
    velocities = np.array(
        [
            [velocity_x, velocity_y, 0.0],
            [velocity_x, velocity_y, 0.0],
            [-2.0 * velocity_x, -2.0 * velocity_y, 0.0],
        ],
        dtype=np.float64,
    )
    return BenchmarkOrbit(
        name="chenciner-montgomery-figure-eight-published-rounded",
        initial_state=InertialState.from_components(positions, velocities),
        parameters=SystemParameters(np.ones(3), gravitational_constant=1.0),
        period=6.32591398,
        citation=(
            "Chenciner and Montgomery (2000); numerical initial values "
            "reproduced by Hubber et al. (2011), Table 2"
        ),
    )
