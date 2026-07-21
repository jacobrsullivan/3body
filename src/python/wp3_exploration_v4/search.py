"""Generalized Lie/value search after an observable-function known quotient."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import linalg


FloatArray: TypeAlias = NDArray[np.float64]


def _matrix(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or not array.size or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a nonempty finite matrix")
    return array


def _vector(value: ArrayLike, length: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (length,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector of length {length}")
    return array


def _svd(
    matrix: FloatArray,
    *,
    driver: str,
    full_matrices: bool,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    if driver == "numpy":
        return np.linalg.svd(matrix, full_matrices=full_matrices)
    if driver not in {"gesdd", "gesvd"}:
        raise ValueError(f"unsupported SVD driver: {driver}")
    return linalg.svd(
        matrix,
        full_matrices=full_matrices,
        lapack_driver=driver,
        check_finite=True,
    )


def _rank(singular: FloatArray, relative_tolerance: float) -> int:
    if singular.size == 0 or singular[0] == 0.0:
        return 0
    return int(np.count_nonzero(singular > singular[0] * relative_tolerance))


def _clusters(
    singular: FloatArray,
    *,
    relative_tolerance: float,
    absolute_tolerance: float,
) -> tuple[tuple[int, int], ...]:
    if singular.ndim != 1 or np.any(np.diff(singular) < 0.0):
        raise ValueError("generalized singular values must be sorted")
    if not singular.size:
        return ()
    output: list[tuple[int, int]] = []
    start = 0
    for index in range(1, singular.size):
        scale = max(abs(float(singular[index - 1])), abs(float(singular[index])))
        tolerance = max(absolute_tolerance, relative_tolerance * scale)
        if float(singular[index] - singular[index - 1]) > tolerance:
            output.append((start, index))
            start = index
    output.append((start, singular.size))
    return tuple(output)


def _weighted_std(values: FloatArray, weights: FloatArray) -> float:
    centered = values - float(np.sum(weights * values))
    return float(np.sqrt(np.sum(weights * np.square(centered))))


@dataclass(frozen=True)
class KnownQuotientFit:
    """Complete spectrum and representatives in the observable known quotient."""

    driver: str
    raw_coefficients: tuple[FloatArray, ...]
    normalized_coefficients: tuple[FloatArray, ...]
    generalized_singular_values: FloatArray
    reconstructed_lie_rms: FloatArray
    feature_scales: FloatArray
    value_rank: int
    value_nuisance_nullity: int
    value_nuisance_derivative_rank: int
    known_observable_rank: int
    known_response_projection_residual: float
    known_response_norm: float
    mode_known_response_projection_max: float
    generalized_clusters: tuple[tuple[int, int], ...]
    generalized_spectral_uncertainty: float


def fit_known_quotient_spectrum(
    values: ArrayLike,
    derivatives: ArrayLike,
    weights: ArrayLike,
    known_coefficients: ArrayLike,
    *,
    driver: str,
    value_rank_relative_tolerance: float,
    nuisance_derivative_rank_relative_tolerance: float,
    singular_cluster_relative_tolerance: float,
    singular_cluster_absolute_tolerance: float,
    svd_backward_error_factor: float,
    feature_scales: ArrayLike | None = None,
) -> KnownQuotientFit:
    """Fit the full nonconstant spectrum modulo one known observable response."""

    value_matrix = _matrix(values, "values")
    derivative_matrix = _matrix(derivatives, "derivatives")
    if derivative_matrix.shape != value_matrix.shape:
        raise ValueError("value and derivative matrices differ")
    row_count, feature_count = value_matrix.shape
    weight_vector = _vector(weights, row_count, "weights")
    if np.any(weight_vector <= 0.0) or not np.isclose(
        np.sum(weight_vector), 1.0, atol=2e-15
    ):
        raise ValueError("weights must be positive and sum to one")
    known = _vector(known_coefficients, feature_count, "known_coefficients")
    if feature_scales is None:
        scales = np.sqrt(
            np.sum(weight_vector[:, None] * np.square(value_matrix), axis=0)
        )
    else:
        scales = _vector(feature_scales, feature_count, "feature_scales")
    if np.any(scales <= 1e-14):
        raise ValueError("feature library contains an unobservable column")
    if not np.isfinite(svd_backward_error_factor) or svd_backward_error_factor <= 0:
        raise ValueError("SVD backward-error factor must be positive")

    normalized_values = value_matrix / scales
    normalized_derivatives = derivative_matrix / scales
    mean = np.sum(weight_vector[:, None] * normalized_values, axis=0)
    value_operator = np.sqrt(weight_vector)[:, None] * (
        normalized_values - mean
    )
    derivative_operator = np.sqrt(weight_vector)[:, None] * normalized_derivatives
    value_left, value_singular, value_right = _svd(
        value_operator, driver=driver, full_matrices=True
    )
    value_rank = _rank(value_singular, value_rank_relative_tolerance)
    if value_rank <= 1:
        raise ValueError("observable library has no direction beyond the known response")
    active = value_right[:value_rank].T
    nuisance = value_right[value_rank:].T
    active_singular = value_singular[:value_rank]

    known_normalized = scales * known
    known_active_coordinates = active.T @ known_normalized
    known_standardized = active_singular * known_active_coordinates
    known_response_norm = float(np.linalg.norm(known_standardized))
    if known_response_norm <= 1e-14:
        raise ValueError("known coefficient vector has no observable response")
    known_basis = known_standardized / known_response_norm
    known_complement = linalg.null_space(known_basis[None, :], rcond=1e-12)
    if known_complement.shape != (value_rank, value_rank - 1):
        raise ArithmeticError("known observable quotient did not remove rank one")
    known_direct_response = value_operator @ known_normalized
    known_reconstructed_response = (
        value_left[:, :value_rank] @ known_standardized
    )
    known_projection_residual = float(
        np.linalg.norm(known_direct_response - known_reconstructed_response)
        / max(np.linalg.norm(known_direct_response), np.finfo(float).tiny)
    )

    active_derivative = derivative_operator @ active
    nuisance_derivative = derivative_operator @ nuisance
    nuisance_left = np.empty((row_count, 0), dtype=np.float64)
    nuisance_singular = np.empty(0, dtype=np.float64)
    nuisance_right = np.empty((0, nuisance.shape[1]), dtype=np.float64)
    nuisance_rank = 0
    residual_derivative = active_derivative
    if nuisance_derivative.shape[1]:
        nuisance_left, nuisance_singular, nuisance_right = _svd(
            nuisance_derivative, driver=driver, full_matrices=False
        )
        derivative_reference_scale = max(
            float(np.linalg.norm(active_derivative, ord="fro")),
            float(np.linalg.norm(nuisance_derivative, ord="fro")),
        )
        nuisance_rank = int(
            np.count_nonzero(
                nuisance_singular
                > derivative_reference_scale
                * nuisance_derivative_rank_relative_tolerance
            )
        )
        if nuisance_rank:
            basis = nuisance_left[:, :nuisance_rank]
            residual_derivative = active_derivative - basis @ (
                basis.T @ active_derivative
            )

    standardized_lie_operator = residual_derivative / active_singular
    generalized_operator = standardized_lie_operator @ known_complement
    _, generalized_singular, generalized_right = _svd(
        generalized_operator, driver=driver, full_matrices=False
    )
    order = np.argsort(generalized_singular, kind="stable")
    raw_coefficients: list[FloatArray] = []
    normalized_coefficients: list[FloatArray] = []
    reconstructed_lie: list[float] = []
    selected_singular: list[float] = []
    known_projections: list[float] = []
    for index in order:
        standardized_coordinates = known_complement @ generalized_right[index]
        active_coordinates = standardized_coordinates / active_singular
        nuisance_coordinates = np.zeros(nuisance.shape[1], dtype=np.float64)
        if nuisance_rank:
            target = active_derivative @ active_coordinates
            nuisance_coordinates = -nuisance_right[:nuisance_rank].T @ (
                (nuisance_left[:, :nuisance_rank].T @ target)
                / nuisance_singular[:nuisance_rank]
            )
        normalized = (
            active @ active_coordinates + nuisance @ nuisance_coordinates
        )
        raw = normalized / scales
        value_std = _weighted_std(value_matrix @ raw, weight_vector)
        if value_std <= 1e-14:
            raise ArithmeticError("known-quotient mode has no observable variation")
        raw /= value_std
        normalized = scales * raw
        dominant = int(np.argmax(np.abs(normalized)))
        if normalized[dominant] < 0.0:
            raw = -raw
            normalized = -normalized
            standardized_coordinates = -standardized_coordinates
        raw_coefficients.append(raw)
        normalized_coefficients.append(normalized)
        reconstructed_lie.append(
            float(
                np.sqrt(
                    np.sum(
                        weight_vector
                        * np.square(derivative_matrix @ raw)
                    )
                )
            )
        )
        selected_singular.append(float(generalized_singular[index]))
        known_projections.append(
            abs(float(np.dot(known_basis, standardized_coordinates)))
            / max(float(np.linalg.norm(standardized_coordinates)), np.finfo(float).tiny)
        )
    sorted_singular = np.asarray(selected_singular, dtype=np.float64)
    clusters = _clusters(
        sorted_singular,
        relative_tolerance=singular_cluster_relative_tolerance,
        absolute_tolerance=singular_cluster_absolute_tolerance,
    )
    spectral_uncertainty = float(
        svd_backward_error_factor
        * np.finfo(np.float64).eps
        * max(generalized_operator.shape)
        * (float(np.max(generalized_singular)) if generalized_singular.size else 0.0)
    )
    return KnownQuotientFit(
        driver=driver,
        raw_coefficients=tuple(raw_coefficients),
        normalized_coefficients=tuple(normalized_coefficients),
        generalized_singular_values=sorted_singular,
        reconstructed_lie_rms=np.asarray(reconstructed_lie, dtype=np.float64),
        feature_scales=np.asarray(scales, dtype=np.float64),
        value_rank=value_rank,
        value_nuisance_nullity=nuisance.shape[1],
        value_nuisance_derivative_rank=nuisance_rank,
        known_observable_rank=1,
        known_response_projection_residual=known_projection_residual,
        known_response_norm=known_response_norm,
        mode_known_response_projection_max=max(known_projections, default=0.0),
        generalized_clusters=clusters,
        generalized_spectral_uncertainty=spectral_uncertainty,
    )
