"""Generic SO(3)-quotient flow with body-frame reconstruction dynamics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.python.threebody_reduction import (
    EuclideanQuotientState,
    TranslationQuotientState,
    canonical_body_frame,
)

from .canonical import canonical_jacobi_flow


FloatArray: TypeAlias = NDArray[np.float64]


def _array(value: ArrayLike, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite with shape {shape}")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result


def _unit_derivative(vector: FloatArray, derivative: FloatArray) -> FloatArray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ZeroDivisionError("unit-vector derivative is undefined at zero")
    unit = vector / norm
    return (derivative - unit * float(np.dot(unit, derivative))) / norm


def _frame_and_derivative(
    rho: FloatArray,
    lambda_vector: FloatArray,
    rho_dot: FloatArray,
    lambda_dot: FloatArray,
    *,
    relative_tolerance: float,
) -> tuple[FloatArray, FloatArray]:
    frame = canonical_body_frame(
        rho, lambda_vector, relative_tolerance=relative_tolerance
    )
    e1 = frame[:, 0]
    e3 = frame[:, 2]
    e1_dot = _unit_derivative(rho, rho_dot)
    normal = np.cross(rho, lambda_vector)
    normal_dot = np.cross(rho_dot, lambda_vector) + np.cross(rho, lambda_dot)
    e3_dot = _unit_derivative(normal, normal_dot)
    e2_dot = np.cross(e3_dot, e1) + np.cross(e3, e1_dot)
    frame_dot = np.column_stack((e1_dot, e2_dot, e3_dot))
    return frame, frame_dot


def _angular_velocity_body(frame: FloatArray, frame_dot: FloatArray) -> FloatArray:
    skew = frame.T @ frame_dot
    return np.array([skew[2, 1], skew[0, 2], skew[1, 0]])


@dataclass(frozen=True)
class EuclideanReducedFlow:
    """Derivative of the nine quotient coordinates and discarded rotation."""

    quotient: EuclideanQuotientState
    quotient_derivative: ArrayLike
    body_frame: ArrayLike
    body_frame_derivative: ArrayLike
    angular_velocity_body: ArrayLike

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "quotient_derivative",
            _array(self.quotient_derivative, (9,), "quotient_derivative"),
        )
        object.__setattr__(
            self, "body_frame", _array(self.body_frame, (3, 3), "body_frame")
        )
        object.__setattr__(
            self,
            "body_frame_derivative",
            _array(
                self.body_frame_derivative, (3, 3), "body_frame_derivative"
            ),
        )
        object.__setattr__(
            self,
            "angular_velocity_body",
            _array(self.angular_velocity_body, (3,), "angular_velocity_body"),
        )


def euclidean_reduced_flow(
    state: TranslationQuotientState,
    *,
    relative_tolerance: float = 1e-12,
) -> EuclideanReducedFlow:
    """Push the canonical Jacobi flow through the generic body-frame chart."""

    canonical = canonical_jacobi_flow(state)
    rho, lambda_vector, p_rho, p_lambda = canonical.state.reshape(4, 3)
    rho_dot, lambda_dot, p_rho_dot, p_lambda_dot = canonical.derivative.reshape(
        4, 3
    )
    frame, frame_dot = _frame_and_derivative(
        rho,
        lambda_vector,
        rho_dot,
        lambda_dot,
        relative_tolerance=relative_tolerance,
    )

    def body(vector: FloatArray) -> FloatArray:
        return frame.T @ vector

    def body_dot(vector: FloatArray, derivative: FloatArray) -> FloatArray:
        return frame_dot.T @ vector + frame.T @ derivative

    rho_body = body(rho)
    lambda_body = body(lambda_vector)
    p_rho_body = body(p_rho)
    p_lambda_body = body(p_lambda)
    quotient = EuclideanQuotientState(
        parameters=state.parameters,
        rho_body=rho_body,
        lambda_body=lambda_body,
        p_rho_body=p_rho_body,
        p_lambda_body=p_lambda_body,
        chart_tolerance=max(1e-11, relative_tolerance * 10.0),
    )
    rho_body_dot = body_dot(rho, rho_dot)
    lambda_body_dot = body_dot(lambda_vector, lambda_dot)
    quotient_derivative = np.concatenate(
        (
            [rho_body_dot[0], lambda_body_dot[0], lambda_body_dot[1]],
            body_dot(p_rho, p_rho_dot),
            body_dot(p_lambda, p_lambda_dot),
        )
    )
    return EuclideanReducedFlow(
        quotient=quotient,
        quotient_derivative=quotient_derivative,
        body_frame=frame,
        body_frame_derivative=frame_dot,
        angular_velocity_body=_angular_velocity_body(frame, frame_dot),
    )
