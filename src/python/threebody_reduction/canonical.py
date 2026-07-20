"""Canonical Jacobi and generic Euclidean-orbit reduction for N3BP.

The translation step is an exact linear canonical transformation from
Cartesian positions and canonical momenta ``p_i = m_i v_i`` to

``(R, rho, lambda; P, p_rho, p_lambda)``.

Here ``R`` and ``P`` are the center-of-mass coordinate and total momentum,
``rho = r2-r1``, and ``lambda`` points from the 1-2 center of mass to body 3.
Dropping ``(R, P)`` on the zero-momentum level gives the 12-dimensional
translation-reduced phase space.

The rotation step chooses a body frame on the generic non-collinear stratum.
Its nine body-frame coordinates represent the Poisson quotient by SO(3), not
a canonical Darboux chart.  Fixing nonzero angular-momentum magnitude selects
an eight-dimensional symplectic leaf.  The frame and center-of-mass data are
kept separately so that reduction and reconstruction are not conflated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import InertialState, SystemParameters


FloatArray: TypeAlias = NDArray[np.float64]
VECTOR_SHAPE = (3,)
MATRIX_SHAPE = (3, 3)


class ReductionChartSingularity(ValueError):
    """Raised when the selected generic body-frame chart is undefined."""


def _readonly(value: ArrayLike, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    result = np.array(array, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


def _mass_data(parameters: SystemParameters) -> tuple[float, ...]:
    m1, m2, m3 = (float(value) for value in parameters.masses)
    m12 = m1 + m2
    total = m12 + m3
    mu12 = m1 * m2 / m12
    mu3_12 = m3 * m12 / total
    return m1, m2, m3, m12, total, mu12, mu3_12


def jacobi_coordinate_matrix(parameters: SystemParameters) -> FloatArray:
    """Return the 3x3 body-index matrix mapping ``(r1,r2,r3)`` to Jacobi q.

    The full nine-dimensional position matrix is ``kron(A, I3)``.  Canonical
    momenta transform with ``kron(inv(A).T, I3)``.
    """

    m1, m2, m3, m12, total, _, _ = _mass_data(parameters)
    return np.array(
        [
            [m1 / total, m2 / total, m3 / total],
            [-1.0, 1.0, 0.0],
            [-m1 / m12, -m2 / m12, 1.0],
        ],
        dtype=np.float64,
    )


@dataclass(frozen=True)
class TranslationReconstruction:
    """The canonical pair removed by translation reduction."""

    center_of_mass: ArrayLike
    total_momentum: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "center_of_mass",
            _readonly(self.center_of_mass, VECTOR_SHAPE, "center_of_mass"),
        )
        object.__setattr__(
            self,
            "total_momentum",
            _readonly(self.total_momentum, VECTOR_SHAPE, "total_momentum"),
        )


@dataclass(frozen=True)
class JacobiPhaseState:
    """Complete canonical Jacobi phase state, including center-of-mass data."""

    parameters: SystemParameters
    center_of_mass: ArrayLike
    rho: ArrayLike
    lambda_vector: ArrayLike
    total_momentum: ArrayLike
    p_rho: ArrayLike
    p_lambda: ArrayLike

    def __post_init__(self) -> None:
        for name in (
            "center_of_mass",
            "rho",
            "lambda_vector",
            "total_momentum",
            "p_rho",
            "p_lambda",
        ):
            object.__setattr__(
                self, name, _readonly(getattr(self, name), VECTOR_SHAPE, name)
            )

    @classmethod
    def from_inertial(
        cls,
        state: InertialState,
        parameters: SystemParameters,
    ) -> "JacobiPhaseState":
        positions = state.positions
        velocities = state.velocities
        m1, m2, m3, m12, total, mu12, mu3_12 = _mass_data(parameters)
        center_12 = (m1 * positions[0] + m2 * positions[1]) / m12
        velocity_12 = (m1 * velocities[0] + m2 * velocities[1]) / m12
        return cls(
            parameters=parameters,
            center_of_mass=np.sum(parameters.masses[:, None] * positions, axis=0)
            / total,
            rho=positions[1] - positions[0],
            lambda_vector=positions[2] - center_12,
            total_momentum=np.sum(parameters.masses[:, None] * velocities, axis=0),
            p_rho=mu12 * (velocities[1] - velocities[0]),
            p_lambda=mu3_12 * (velocities[2] - velocity_12),
        )

    @property
    def reconstruction(self) -> TranslationReconstruction:
        return TranslationReconstruction(self.center_of_mass, self.total_momentum)

    @property
    def quotient(self) -> "TranslationQuotientState":
        return TranslationQuotientState(
            parameters=self.parameters,
            rho=self.rho,
            lambda_vector=self.lambda_vector,
            p_rho=self.p_rho,
            p_lambda=self.p_lambda,
        )

    def as_canonical_vector(self) -> FloatArray:
        return np.concatenate(
            (
                self.center_of_mass,
                self.rho,
                self.lambda_vector,
                self.total_momentum,
                self.p_rho,
                self.p_lambda,
            )
        )

    def to_inertial(self) -> InertialState:
        return self.quotient.to_inertial(self.reconstruction)


@dataclass(frozen=True)
class TranslationQuotientState:
    """Canonical 12D translation quotient at total momentum zero."""

    parameters: SystemParameters
    rho: ArrayLike
    lambda_vector: ArrayLike
    p_rho: ArrayLike
    p_lambda: ArrayLike

    def __post_init__(self) -> None:
        for name in ("rho", "lambda_vector", "p_rho", "p_lambda"):
            object.__setattr__(
                self, name, _readonly(getattr(self, name), VECTOR_SHAPE, name)
            )

    @property
    def phase_dimension(self) -> int:
        return 12

    @property
    def configuration_dimension(self) -> int:
        return 6

    def as_canonical_vector(self) -> FloatArray:
        return np.concatenate((self.rho, self.lambda_vector, self.p_rho, self.p_lambda))

    def kinetic_energy(self) -> float:
        *_, mu12, mu3_12 = _mass_data(self.parameters)
        return float(
            np.dot(self.p_rho, self.p_rho) / (2.0 * mu12)
            + np.dot(self.p_lambda, self.p_lambda) / (2.0 * mu3_12)
        )

    def pair_vectors(self) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Return oriented ``(x12,x23,x31)`` with ``xij = rj-ri``."""

        m1, m2, _, m12, _, _, _ = _mass_data(self.parameters)
        x12 = np.array(self.rho, copy=True)
        x23 = self.lambda_vector - (m1 / m12) * self.rho
        x31 = -self.lambda_vector - (m2 / m12) * self.rho
        return x12, x23, x31

    def potential_energy(self) -> float:
        m1, m2, m3, _, _, _, _ = _mass_data(self.parameters)
        x12, x23, x31 = self.pair_vectors()
        distances = tuple(float(np.linalg.norm(value)) for value in (x12, x23, x31))
        if min(distances) == 0.0:
            raise ZeroDivisionError(
                "Newtonian potential is singular at binary collision"
            )
        gravitational_constant = self.parameters.gravitational_constant
        return float(
            -gravitational_constant
            * (m1 * m2 / distances[0] + m2 * m3 / distances[1] + m3 * m1 / distances[2])
        )

    def total_energy(self) -> float:
        return self.kinetic_energy() + self.potential_energy()

    def angular_momentum(self) -> FloatArray:
        return np.cross(self.rho, self.p_rho) + np.cross(
            self.lambda_vector, self.p_lambda
        )

    def to_inertial(
        self,
        reconstruction: TranslationReconstruction | None = None,
    ) -> InertialState:
        if reconstruction is None:
            reconstruction = TranslationReconstruction(np.zeros(3), np.zeros(3))
        m1, m2, m3, m12, total, mu12, mu3_12 = _mass_data(self.parameters)
        center = reconstruction.center_of_mass
        center_velocity = reconstruction.total_momentum / total
        center_12 = center - (m3 / total) * self.lambda_vector
        positions = np.stack(
            (
                center_12 - (m2 / m12) * self.rho,
                center_12 + (m1 / m12) * self.rho,
                center + (m12 / total) * self.lambda_vector,
            )
        )
        rho_velocity = self.p_rho / mu12
        lambda_velocity = self.p_lambda / mu3_12
        velocity_12 = center_velocity - (m3 / total) * lambda_velocity
        velocities = np.stack(
            (
                velocity_12 - (m2 / m12) * rho_velocity,
                velocity_12 + (m1 / m12) * rho_velocity,
                center_velocity + (m12 / total) * lambda_velocity,
            )
        )
        return InertialState.from_components(positions, velocities)


@dataclass(frozen=True)
class TranslationReductionResult:
    """Translation quotient plus the discarded canonical pair."""

    quotient: TranslationQuotientState
    reconstruction: TranslationReconstruction

    def reconstruct(self) -> InertialState:
        return self.quotient.to_inertial(self.reconstruction)


def reduce_translation(
    state: InertialState,
    parameters: SystemParameters,
) -> TranslationReductionResult:
    jacobi = JacobiPhaseState.from_inertial(state, parameters)
    return TranslationReductionResult(jacobi.quotient, jacobi.reconstruction)


def canonical_body_frame(
    rho: ArrayLike,
    lambda_vector: ArrayLike,
    *,
    relative_tolerance: float = 1e-12,
) -> FloatArray:
    """Construct the SO(3)-equivariant frame ``(e1,e2,e3)``.

    The chart requires ``rho != 0`` and ``rho x lambda != 0``.  Collinear
    configurations belong to a singular orbit-type stratum and are rejected
    rather than assigned a discontinuous arbitrary frame.
    """

    if not np.isfinite(relative_tolerance) or relative_tolerance < 0.0:
        raise ValueError("relative_tolerance must be finite and non-negative")
    rho_array = _readonly(rho, VECTOR_SHAPE, "rho")
    lambda_array = _readonly(lambda_vector, VECTOR_SHAPE, "lambda_vector")
    rho_norm = float(np.linalg.norm(rho_array))
    lambda_norm = float(np.linalg.norm(lambda_array))
    if rho_norm == 0.0:
        raise ReductionChartSingularity("body-frame chart is singular at rho=0")
    normal = np.cross(rho_array, lambda_array)
    normal_norm = float(np.linalg.norm(normal))
    scale = rho_norm * lambda_norm
    if scale == 0.0 or normal_norm <= relative_tolerance * scale:
        raise ReductionChartSingularity(
            "body-frame chart requires a non-collinear configuration"
        )
    e1 = rho_array / rho_norm
    e3 = normal / normal_norm
    e2 = np.cross(e3, e1)
    frame = np.column_stack((e1, e2, e3))
    if not np.allclose(frame.T @ frame, np.eye(3), atol=5e-14, rtol=0.0):
        raise ArithmeticError("constructed body frame is not orthogonal")
    if np.linalg.det(frame) <= 0.0:
        raise ArithmeticError("constructed body frame is not a proper rotation")
    return frame


@dataclass(frozen=True)
class EuclideanQuotientState:
    """Nine-coordinate chart on the generic translation-and-rotation quotient."""

    parameters: SystemParameters
    rho_body: ArrayLike
    lambda_body: ArrayLike
    p_rho_body: ArrayLike
    p_lambda_body: ArrayLike
    chart_tolerance: float = 1e-11

    def __post_init__(self) -> None:
        for name in ("rho_body", "lambda_body", "p_rho_body", "p_lambda_body"):
            object.__setattr__(
                self, name, _readonly(getattr(self, name), VECTOR_SHAPE, name)
            )
        tolerance = float(self.chart_tolerance)
        if not np.isfinite(tolerance) or tolerance < 0.0:
            raise ValueError("chart_tolerance must be finite and non-negative")
        object.__setattr__(self, "chart_tolerance", tolerance)
        if self.rho_body[0] <= 0.0:
            raise ValueError("body-frame chart requires rho_body[0] > 0")
        if self.lambda_body[1] <= 0.0:
            raise ValueError("body-frame chart requires lambda_body[1] > 0")
        constrained = np.array(
            [self.rho_body[1], self.rho_body[2], self.lambda_body[2]]
        )
        if np.max(np.abs(constrained)) > tolerance:
            raise ValueError("position vectors do not satisfy the body-frame gauge")

    @property
    def poisson_dimension(self) -> int:
        return 9

    @property
    def generic_fixed_momentum_leaf_dimension(self) -> int:
        return 8

    @property
    def zero_momentum_leaf_dimension(self) -> int:
        return 6

    @property
    def shape_coordinates(self) -> FloatArray:
        return np.array(
            [self.rho_body[0], self.lambda_body[0], self.lambda_body[1]],
            dtype=np.float64,
        )

    @property
    def angular_momentum_body(self) -> FloatArray:
        return np.cross(self.rho_body, self.p_rho_body) + np.cross(
            self.lambda_body, self.p_lambda_body
        )

    @property
    def angular_momentum_magnitude(self) -> float:
        return float(np.linalg.norm(self.angular_momentum_body))

    def as_orbit_coordinates(self) -> FloatArray:
        return np.concatenate(
            (self.shape_coordinates, self.p_rho_body, self.p_lambda_body)
        )

    def to_translation_quotient(
        self, body_frame: ArrayLike
    ) -> TranslationQuotientState:
        frame = _readonly(body_frame, MATRIX_SHAPE, "body_frame")
        if not np.allclose(frame.T @ frame, np.eye(3), atol=5e-12, rtol=0.0):
            raise ValueError("body_frame must be orthogonal")
        if not np.isclose(np.linalg.det(frame), 1.0, atol=5e-12, rtol=0.0):
            raise ValueError("body_frame must have determinant +1")
        return TranslationQuotientState(
            parameters=self.parameters,
            rho=frame @ self.rho_body,
            lambda_vector=frame @ self.lambda_body,
            p_rho=frame @ self.p_rho_body,
            p_lambda=frame @ self.p_lambda_body,
        )

    def kinetic_energy(self) -> float:
        return self.to_translation_quotient(np.eye(3)).kinetic_energy()

    def potential_energy(self) -> float:
        return self.to_translation_quotient(np.eye(3)).potential_energy()

    def total_energy(self) -> float:
        return self.kinetic_energy() + self.potential_energy()


@dataclass(frozen=True)
class EuclideanReconstruction:
    """Rigid data discarded by the Euclidean-orbit quotient."""

    translation: TranslationReconstruction
    body_frame: ArrayLike

    def __post_init__(self) -> None:
        frame = _readonly(self.body_frame, MATRIX_SHAPE, "body_frame")
        if not np.allclose(frame.T @ frame, np.eye(3), atol=5e-12, rtol=0.0):
            raise ValueError("body_frame must be orthogonal")
        if not np.isclose(np.linalg.det(frame), 1.0, atol=5e-12, rtol=0.0):
            raise ValueError("body_frame must have determinant +1")
        object.__setattr__(self, "body_frame", frame)


@dataclass(frozen=True)
class EuclideanReductionResult:
    """Generic Euclidean quotient state with exact reconstruction metadata."""

    quotient: EuclideanQuotientState
    reconstruction: EuclideanReconstruction

    def reconstruct(self) -> InertialState:
        translated = self.quotient.to_translation_quotient(
            self.reconstruction.body_frame
        )
        return translated.to_inertial(self.reconstruction.translation)


def reduce_euclidean(
    state: InertialState,
    parameters: SystemParameters,
    *,
    relative_tolerance: float = 1e-12,
) -> EuclideanReductionResult:
    """Reduce an N3BP state by translations and SO(3) on the generic stratum."""

    translation = reduce_translation(state, parameters)
    reduced = translation.quotient
    frame = canonical_body_frame(
        reduced.rho,
        reduced.lambda_vector,
        relative_tolerance=relative_tolerance,
    )
    rho_norm = float(np.linalg.norm(reduced.rho))
    rho_body = np.array([rho_norm, 0.0, 0.0])
    lambda_body = np.array(
        [
            float(np.dot(frame[:, 0], reduced.lambda_vector)),
            float(np.dot(frame[:, 1], reduced.lambda_vector)),
            0.0,
        ]
    )
    quotient = EuclideanQuotientState(
        parameters=parameters,
        rho_body=rho_body,
        lambda_body=lambda_body,
        p_rho_body=frame.T @ reduced.p_rho,
        p_lambda_body=frame.T @ reduced.p_lambda,
    )
    reconstruction = EuclideanReconstruction(
        translation=translation.reconstruction,
        body_frame=frame,
    )
    return EuclideanReductionResult(quotient, reconstruction)
