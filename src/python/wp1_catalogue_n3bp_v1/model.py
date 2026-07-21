"""Canonical state and value objects for WP1-CAT-N3BP-v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]

M3 = 1.0
DISCLOSED_ROOT = (-0.37200864, 1.21800411, 0.45310805, 7.53971451)
MASS_GRID = tuple(float(value) for value in np.linspace(0.97, 1.03, 13))
PLANAR_INDICES = np.array(
    [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16], dtype=np.intp
)


@dataclass(frozen=True, slots=True)
class OrbitParameters:
    """Four corrected section variables at fixed ``m1``, ``m2``, and ``m3=1``."""

    m1: float
    m2: float
    x1: float
    v1: float
    v2: float
    period: float

    def __post_init__(self) -> None:
        values = np.array(
            [self.m1, self.m2, self.x1, self.v1, self.v2, self.period],
            dtype=np.float64,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("orbit parameters must be finite")
        if self.m1 <= 0.0 or self.m2 <= 0.0 or self.period <= 0.0:
            raise ValueError("masses and period must be positive")
        if min(abs(self.x1), abs(self.x1 - 1.0)) <= 1.0e-14:
            raise ValueError("the canonical section may not contain a collision")

    @property
    def masses(self) -> tuple[float, float, float]:
        return (self.m1, self.m2, M3)

    def correction_vector(self) -> FloatArray:
        return np.array([self.x1, self.v1, self.v2, self.period], dtype=np.float64)

    def with_masses(self, m1: float, m2: float) -> OrbitParameters:
        return OrbitParameters(m1, m2, self.x1, self.v1, self.v2, self.period)

    @classmethod
    def disclosed_root(cls) -> OrbitParameters:
        return cls(1.0, 1.0, *DISCLOSED_ROOT)


@dataclass(frozen=True, slots=True)
class CorrectionSettings:
    rtol: float = 2.0e-12
    atol: float = 2.0e-14
    max_step_fraction: float = 1.0 / 128.0
    max_nfev: int = 24
    xtol: float = 1.0e-11
    ftol: float = 1.0e-11
    gtol: float = 1.0e-11
    closure_tolerance: float = 2.0e-8


@dataclass(frozen=True, slots=True)
class CorrectionResult:
    parameters: OrbitParameters
    state: tuple[float, ...]
    residual: tuple[float, ...]
    residual_linf: float
    position_closure_linf: float
    velocity_closure_linf: float
    nfev: int
    success: bool
    message: str


StabilityLabel = Literal["S", "U", "AMBIGUOUS"]


@dataclass(frozen=True, slots=True)
class StabilityResult:
    label: StabilityLabel
    trace: float
    second_trace_invariant: float
    discriminant: float
    reduced_traces: tuple[complex, complex]
    multipliers: tuple[complex, ...]
    symplectic_defect: float
    reciprocal_pair_error: float


@dataclass(frozen=True, slots=True)
class CatalogueCandidate:
    candidate_id: str
    correction: CorrectionResult
    parent_id: str | None
    continuation_axis: Literal["root", "m1", "m2"]
    stability: StabilityResult | None = None


def canonical_section_state(
    m1: float,
    m2: float,
    x1: float,
    v1: float,
    v2: float,
    period: float,
) -> FloatArray:
    """Build the canonical, barycentric full-18D inertial section state.

    State ordering is ``(r1, r2, r3, v1, v2, v3)`` with three Cartesian
    components per vector. The disclosed section is built first and then
    translated and boosted to the barycentric inertial frame.
    """

    parameters = OrbitParameters(m1, m2, x1, v1, v2, period)
    masses = np.asarray(parameters.masses, dtype=np.float64)
    positions = np.array(
        [[x1, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        dtype=np.float64,
    )
    velocities = np.array(
        [
            [0.0, v1, 0.0],
            [0.0, v2, 0.0],
            [0.0, -(m1 * v1 + m2 * v2) / M3, 0.0],
        ],
        dtype=np.float64,
    )
    positions -= np.average(positions, axis=0, weights=masses)
    velocities -= np.average(velocities, axis=0, weights=masses)
    return np.concatenate((positions.reshape(-1), velocities.reshape(-1)))


def state_from_parameters(parameters: OrbitParameters) -> FloatArray:
    return canonical_section_state(
        parameters.m1,
        parameters.m2,
        parameters.x1,
        parameters.v1,
        parameters.v2,
        parameters.period,
    )


def planar_state(state18: FloatArray) -> FloatArray:
    state = np.asarray(state18, dtype=np.float64)
    if state.shape != (18,):
        raise ValueError("full inertial state must have shape (18,)")
    return state[PLANAR_INDICES].copy()

