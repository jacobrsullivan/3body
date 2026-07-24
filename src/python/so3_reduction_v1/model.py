"""Hamiltonian model on the regular non-collinear SO(3) quotient.

The orientation-fixed body chart is

``rho=(r,0,0), lambda=(x,y,0), r>0, y>0``.

The quotient coordinates are ``(r,x,y,pr,px,py,ell_x,ell_y,ell_z)``.
The first six are canonical.  ``ell`` is body angular momentum and carries
the minus Lie-Poisson bracket, so ``ell_dot = ell cross dH/dell``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.n3bp_qualification import SystemParameters
from src.python.threebody_reduction import EuclideanQuotientState


FloatArray: TypeAlias = NDArray[np.float64]
COORDINATE_NAMES = (
    "r",
    "x",
    "y",
    "pr",
    "px",
    "py",
    "ell_x",
    "ell_y",
    "ell_z",
)


def _vector(value: ArrayLike, size: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,):
        raise ValueError(f"{name} must have shape ({size},), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result

def _reduced_masses(parameters: SystemParameters) -> tuple[float, ...]:
    m1, m2, m3 = (float(value) for value in parameters.masses)
    m12 = m1 + m2
    total = m12 + m3
    return (
        m1,
        m2,
        m3,
        m1 * m2 / m12,
        m3 * m12 / total,
        m1 / m12,
        m2 / m12,
    )


@dataclass(frozen=True)
class SO3LeafState:
    """A point in the regular nine-dimensional SO(3) Poisson chart."""

    parameters: SystemParameters
    coordinates: ArrayLike

    def __post_init__(self) -> None:
        coordinates = _vector(self.coordinates, 9, "coordinates")
        if coordinates[0] <= 0.0:
            raise ValueError("body-frame chart requires r > 0")
        if coordinates[2] <= 0.0:
            raise ValueError("body-frame chart requires y > 0")
        object.__setattr__(self, "coordinates", coordinates)

    @classmethod
    def from_euclidean_quotient(
        cls, quotient: EuclideanQuotientState
    ) -> "SO3LeafState":
        """Convert the previously qualified body-frame quotient coordinates."""

        r, x, y = quotient.shape_coordinates
        u = quotient.p_rho_body
        v = quotient.p_lambda_body
        ell = quotient.angular_momentum_body
        return cls(
            quotient.parameters,
            np.array([r, x, y, u[0], v[0], v[1], *ell], dtype=np.float64),
        )

    @property
    def shape_coordinates(self) -> FloatArray:
        return np.array(self.coordinates[:3], copy=True)

    @property
    def shape_momenta(self) -> FloatArray:
        return np.array(self.coordinates[3:6], copy=True)

    @property
    def angular_momentum_body(self) -> FloatArray:
        return np.array(self.coordinates[6:], copy=True)

    @property
    def angular_momentum_magnitude(self) -> float:
        return float(np.linalg.norm(self.coordinates[6:]))

    @property
    def poisson_rank(self) -> int:
        return 6 if np.array_equal(self.coordinates[6:], np.zeros(3)) else 8

    @property
    def symplectic_leaf_dimension(self) -> int:
        return self.poisson_rank

    @property
    def casimir(self) -> float:
        return float(np.dot(self.coordinates[6:], self.coordinates[6:]))

    def to_euclidean_quotient(self) -> EuclideanQuotientState:
        """Invert the cotangent momentum map in the selected body chart."""

        r, x, y, pr, px, py, ell_x, ell_y, ell_z = self.coordinates
        v3 = ell_x / y
        u3 = -(ell_y + x * v3) / r
        u2 = (ell_z - x * py + y * px) / r
        return EuclideanQuotientState(
            parameters=self.parameters,
            rho_body=np.array([r, 0.0, 0.0]),
            lambda_body=np.array([x, y, 0.0]),
            p_rho_body=np.array([pr, u2, u3]),
            p_lambda_body=np.array([px, py, v3]),
        )

    def hamiltonian(self) -> float:
        return hamiltonian(self.coordinates, self.parameters)

    def gradient(self) -> FloatArray:
        return hamiltonian_gradient(self.coordinates, self.parameters)

    def flow(self) -> FloatArray:
        return hamiltonian_flow(self.coordinates, self.parameters)


def _resolved_momenta(coordinates: FloatArray) -> tuple[float, ...]:
    r, x, y, pr, px, py, ell_x, ell_y, ell_z = coordinates
    v3 = ell_x / y
    u3 = -(ell_y + x * v3) / r
    u2 = (ell_z - x * py + y * px) / r
    return pr, u2, u3, px, py, v3


def hamiltonian(
    coordinates: ArrayLike,
    parameters: SystemParameters,
) -> float:
    """Return the reduced Newtonian Hamiltonian in the SO(3) chart."""

    values = SO3LeafState(parameters, coordinates).coordinates
    r, x, y = values[:3]
    pr, u2, u3, px, py, v3 = _resolved_momenta(values)
    m1, m2, m3, mu_rho, mu_lambda, alpha, beta = _reduced_masses(parameters)
    kinetic = (
        (pr * pr + u2 * u2 + u3 * u3) / (2.0 * mu_rho)
        + (px * px + py * py + v3 * v3) / (2.0 * mu_lambda)
    )
    d23 = float(np.hypot(x - alpha * r, y))
    d31 = float(np.hypot(x + beta * r, y))
    potential = -parameters.gravitational_constant * (
        m1 * m2 / r + m2 * m3 / d23 + m3 * m1 / d31
    )
    return float(kinetic + potential)


def hamiltonian_gradient(
    coordinates: ArrayLike,
    parameters: SystemParameters,
) -> FloatArray:
    """Return the analytic gradient in the locked coordinate order."""

    values = SO3LeafState(parameters, coordinates).coordinates
    r, x, y, pr, px, py, ell_x, ell_y, ell_z = values
    _, u2, u3, _, _, v3 = _resolved_momenta(values)
    m1, m2, m3, mu_rho, mu_lambda, alpha, beta = _reduced_masses(parameters)

    gradient = np.empty(9, dtype=np.float64)
    gradient[0] = -(u2 * u2 + u3 * u3) / (mu_rho * r)
    gradient[1] = (-u2 * py - u3 * v3) / (mu_rho * r)
    gradient[2] = (
        u2 * px / (mu_rho * r)
        + u3 * x * v3 / (mu_rho * r * y)
        - v3 * v3 / (mu_lambda * y)
    )
    gradient[3] = pr / mu_rho
    gradient[4] = u2 * y / (mu_rho * r) + px / mu_lambda
    gradient[5] = -u2 * x / (mu_rho * r) + py / mu_lambda
    gradient[6] = (
        -u3 * x / (mu_rho * y * r) + v3 / (mu_lambda * y)
    )
    gradient[7] = -u3 / (mu_rho * r)
    gradient[8] = u2 / (mu_rho * r)

    z23 = x - alpha * r
    z31 = x + beta * r
    d23 = float(np.hypot(z23, y))
    d31 = float(np.hypot(z31, y))
    gravity = parameters.gravitational_constant
    gradient[0] += gravity * (
        m1 * m2 / (r * r)
        - m2 * m3 * alpha * z23 / d23**3
        + m3 * m1 * beta * z31 / d31**3
    )
    gradient[1] += gravity * (
        m2 * m3 * z23 / d23**3 + m3 * m1 * z31 / d31**3
    )
    gradient[2] += gravity * (
        m2 * m3 * y / d23**3 + m3 * m1 * y / d31**3
    )
    gradient.setflags(write=False)
    return gradient


def poisson_tensor(coordinates: ArrayLike) -> FloatArray:
    """Return the canonical plus body Lie-Poisson tensor."""

    values = _vector(coordinates, 9, "coordinates")
    ell_x, ell_y, ell_z = values[6:]
    tensor = np.zeros((9, 9), dtype=np.float64)
    tensor[:3, 3:6] = np.eye(3)
    tensor[3:6, :3] = -np.eye(3)
    tensor[6:, 6:] = np.array(
        [
            [0.0, -ell_z, ell_y],
            [ell_z, 0.0, -ell_x],
            [-ell_y, ell_x, 0.0],
        ]
    )
    tensor.setflags(write=False)
    return tensor


def hamiltonian_flow(
    coordinates: ArrayLike,
    parameters: SystemParameters,
) -> FloatArray:
    """Return ``P(z) grad(H)`` on the regular Poisson quotient."""

    state = SO3LeafState(parameters, coordinates)
    derivative = poisson_tensor(state.coordinates) @ hamiltonian_gradient(
        state.coordinates, parameters
    )
    derivative.setflags(write=False)
    return derivative


def leaf_derivative_from_quotient_flow(
    quotient: EuclideanQuotientState,
    quotient_derivative: ArrayLike,
) -> FloatArray:
    """Push a body-frame quotient tangent into the leaf coordinates."""

    derivative = _vector(quotient_derivative, 9, "quotient_derivative")
    r_dot, x_dot, y_dot = derivative[:3]
    u_dot = derivative[3:6]
    v_dot = derivative[6:9]
    rho = quotient.rho_body
    lam = quotient.lambda_body
    u = quotient.p_rho_body
    v = quotient.p_lambda_body
    rho_dot = np.array([r_dot, 0.0, 0.0])
    lam_dot = np.array([x_dot, y_dot, 0.0])
    ell_dot = (
        np.cross(rho_dot, u)
        + np.cross(rho, u_dot)
        + np.cross(lam_dot, v)
        + np.cross(lam, v_dot)
    )
    result = np.array(
        [r_dot, x_dot, y_dot, u_dot[0], v_dot[0], v_dot[1], *ell_dot]
    )
    result.setflags(write=False)
    return result
