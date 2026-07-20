"""Deterministic near-null Lie-derivative screening for WP3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import null_space


FloatArray: TypeAlias = NDArray[np.float64]
EXPLORATION_STATUS = "EXPLORATORY_ONLY"


def _readonly_vector(value: ArrayLike, size: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,):
        raise ValueError(f"{name} must have shape ({size},), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    result = np.array(array, copy=True)
    result.setflags(write=False)
    return result


def _readonly_matrix(value: ArrayLike, columns: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != columns:
        raise ValueError(
            f"{name} must be a two-dimensional array with {columns} columns"
        )
    if array.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one row")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _residual_metrics(matrix: FloatArray, coefficients: FloatArray) -> dict[str, float]:
    residual = _matrix_vector(matrix, coefficients)
    return {
        "lie_rms": float(np.sqrt(np.mean(np.square(residual)))),
        "lie_max_abs": float(np.max(np.abs(residual))),
    }


def _matrix_vector(matrix: FloatArray, vector: FloatArray) -> FloatArray:
    """Contract without macOS Accelerate's spurious matmul FPE warnings."""

    return np.einsum("ij,j->i", matrix, vector, optimize=False)


def _matrix_matrix(first: FloatArray, second: FloatArray) -> FloatArray:
    """Contract two matrices with a deterministic, warning-clean path."""

    return np.einsum("ij,jk->ik", first, second, optimize=False)


@dataclass(frozen=True)
class NearNullMode:
    """One ranked screening direction after known controls are removed."""

    rank: int
    coefficients: ArrayLike
    standardized_singular_value: float
    training_lie_rms: float
    training_lie_max_abs: float
    calibration_lie_rms: float
    calibration_lie_max_abs: float
    training_value_std: float
    calibration_value_std: float
    known_control_overlap_max: float
    interpretation_status: str = EXPLORATION_STATUS

    def __post_init__(self) -> None:
        coefficients = np.asarray(self.coefficients, dtype=np.float64)
        if coefficients.ndim != 1 or coefficients.size == 0:
            raise ValueError("coefficients must be a non-empty vector")
        object.__setattr__(
            self,
            "coefficients",
            _readonly_vector(coefficients, coefficients.size, "coefficients"),
        )
        if self.rank < 1:
            raise ValueError("rank must be positive")
        if self.interpretation_status != EXPLORATION_STATUS:
            raise ValueError("near-null modes must remain exploratory")

    def top_terms(
        self,
        names: tuple[str, ...],
        *,
        count: int = 12,
    ) -> list[dict[str, float | str]]:
        if len(names) != self.coefficients.size:
            raise ValueError("feature names do not match coefficients")
        if count < 1:
            raise ValueError("count must be positive")
        indices = np.argsort(np.abs(self.coefficients))[::-1][:count]
        return [
            {
                "feature": names[int(index)],
                "coefficient": float(self.coefficients[index]),
            }
            for index in indices
        ]


@dataclass(frozen=True)
class SearchResult:
    """Known-control diagnostics and ranked exploratory near-null modes."""

    feature_names: tuple[str, ...]
    derivative_scales: ArrayLike
    standardized_singular_values: ArrayLike
    numerical_nullity: int
    nullity_relative_tolerance: float
    control_metrics: Mapping[str, Mapping[str, float]]
    modes: tuple[NearNullMode, ...]
    interpretation_status: str = EXPLORATION_STATUS

    def __post_init__(self) -> None:
        feature_count = len(self.feature_names)
        object.__setattr__(
            self,
            "derivative_scales",
            _readonly_vector(
                self.derivative_scales, feature_count, "derivative_scales"
            ),
        )
        singular_values = np.asarray(
            self.standardized_singular_values, dtype=np.float64
        )
        if singular_values.ndim != 1 or not np.all(np.isfinite(singular_values)):
            raise ValueError("standardized_singular_values must be a finite vector")
        singular_values = np.array(singular_values, copy=True)
        singular_values.setflags(write=False)
        object.__setattr__(self, "standardized_singular_values", singular_values)
        if self.numerical_nullity < 0:
            raise ValueError("numerical_nullity must be non-negative")
        if self.interpretation_status != EXPLORATION_STATUS:
            raise ValueError("search results must remain exploratory")

    def as_dict(self, *, top_term_count: int = 12) -> dict[str, object]:
        return {
            "interpretation_status": self.interpretation_status,
            "feature_count": len(self.feature_names),
            "feature_names": list(self.feature_names),
            "derivative_scales": self.derivative_scales.tolist(),
            "standardized_singular_values": (
                self.standardized_singular_values.tolist()
            ),
            "numerical_nullity_after_known_controls": self.numerical_nullity,
            "nullity_relative_tolerance": self.nullity_relative_tolerance,
            "known_control_metrics": {
                name: dict(metrics) for name, metrics in self.control_metrics.items()
            },
            "near_null_modes": [
                {
                    "rank": mode.rank,
                    "interpretation_status": mode.interpretation_status,
                    "standardized_singular_value": (
                        mode.standardized_singular_value
                    ),
                    "training_lie_rms": mode.training_lie_rms,
                    "training_lie_max_abs": mode.training_lie_max_abs,
                    "calibration_lie_rms": mode.calibration_lie_rms,
                    "calibration_lie_max_abs": mode.calibration_lie_max_abs,
                    "training_value_std": mode.training_value_std,
                    "calibration_value_std": mode.calibration_value_std,
                    "known_control_overlap_max": mode.known_control_overlap_max,
                    "coefficients": mode.coefficients.tolist(),
                    "top_terms": mode.top_terms(
                        self.feature_names, count=top_term_count
                    ),
                }
                for mode in self.modes
            ],
        }


def search_near_null_modes(
    training_features: ArrayLike,
    training_lie_derivatives: ArrayLike,
    calibration_features: ArrayLike,
    calibration_lie_derivatives: ArrayLike,
    *,
    feature_names: tuple[str, ...],
    control_coefficients: Mapping[str, ArrayLike],
    mode_count: int = 5,
    nullity_relative_tolerance: float = 1.0e-10,
) -> SearchResult:
    """Rank low-residual directions without interpreting them as invariants.

    Columns are scaled by training derivative RMS. Any supplied known-control
    directions are then projected out in that scaled coefficient geometry
    before the SVD is computed.
    """

    feature_count = len(feature_names)
    if feature_count == 0 or len(set(feature_names)) != feature_count:
        raise ValueError("feature_names must be non-empty and unique")
    if mode_count < 1:
        raise ValueError("mode_count must be positive")
    if not 0.0 < nullity_relative_tolerance < 1.0:
        raise ValueError("nullity_relative_tolerance must lie between zero and one")

    train_features = _readonly_matrix(
        training_features, feature_count, "training_features"
    )
    train_derivatives = _readonly_matrix(
        training_lie_derivatives, feature_count, "training_lie_derivatives"
    )
    calibration_features_array = _readonly_matrix(
        calibration_features, feature_count, "calibration_features"
    )
    calibration_derivatives = _readonly_matrix(
        calibration_lie_derivatives,
        feature_count,
        "calibration_lie_derivatives",
    )
    if train_features.shape[0] != train_derivatives.shape[0]:
        raise ValueError("training feature and derivative row counts differ")
    if calibration_features_array.shape[0] != calibration_derivatives.shape[0]:
        raise ValueError("calibration feature and derivative row counts differ")
    derivative_rms = np.sqrt(np.mean(np.square(train_derivatives), axis=0))
    positive = derivative_rms[derivative_rms > 0.0]
    if positive.size == 0:
        raise ValueError("all training Lie-derivative columns are zero")
    floor = max(float(np.median(positive)) * 1.0e-12, np.finfo(float).tiny)
    derivative_scales = np.maximum(derivative_rms, floor)
    standardized_derivatives = train_derivatives / derivative_scales

    scaled_controls = []
    control_metrics: dict[str, dict[str, float]] = {}
    for name, coefficients in control_coefficients.items():
        vector = _readonly_vector(coefficients, feature_count, name)
        scaled_controls.append(derivative_scales * vector)
        training_metrics = _residual_metrics(train_derivatives, vector)
        calibration_metrics = _residual_metrics(calibration_derivatives, vector)
        control_metrics[name] = {
            "training_lie_rms": training_metrics["lie_rms"],
            "training_lie_max_abs": training_metrics["lie_max_abs"],
            "calibration_lie_rms": calibration_metrics["lie_rms"],
            "calibration_lie_max_abs": calibration_metrics["lie_max_abs"],
            "training_value_std": float(
                np.std(_matrix_vector(train_features, vector))
            ),
            "calibration_value_std": float(
                np.std(_matrix_vector(calibration_features_array, vector))
            ),
        }

    if scaled_controls:
        scaled_control_matrix = np.column_stack(scaled_controls)
        control_rank = int(np.linalg.matrix_rank(scaled_control_matrix))
        if control_rank != scaled_control_matrix.shape[1]:
            raise ValueError(
                "known control coefficient vectors are linearly dependent"
            )
        control_basis, _ = np.linalg.qr(scaled_control_matrix, mode="reduced")
        complement = null_space(control_basis.T)
    else:
        control_basis = np.empty((feature_count, 0), dtype=np.float64)
        complement = np.eye(feature_count, dtype=np.float64)
    if complement.shape[1] == 0:
        raise ValueError("known controls span the entire feature library")

    reduced_operator = _matrix_matrix(standardized_derivatives, complement)
    _, singular_values, right_vectors = np.linalg.svd(
        reduced_operator, full_matrices=False
    )
    if singular_values.size == 0:
        raise ValueError("near-null search produced no singular values")
    largest = float(singular_values[0])
    threshold = largest * nullity_relative_tolerance
    numerical_nullity = int(np.count_nonzero(singular_values <= threshold))

    modes: list[NearNullMode] = []
    indices = np.argsort(singular_values)[: min(mode_count, singular_values.size)]
    for rank, singular_index in enumerate(indices, start=1):
        scaled_coefficients = _matrix_vector(
            complement, right_vectors[singular_index]
        )
        coefficients = scaled_coefficients / derivative_scales
        values = _matrix_vector(train_features, coefficients)
        value_scale = float(np.std(values))
        if value_scale <= np.finfo(float).eps:
            value_scale = float(np.linalg.norm(coefficients))
        if value_scale <= np.finfo(float).tiny:
            raise ArithmeticError("near-null mode has zero coefficient scale")
        coefficients = coefficients / value_scale
        dominant = int(np.argmax(np.abs(coefficients)))
        if coefficients[dominant] < 0.0:
            coefficients = -coefficients

        training_metrics = _residual_metrics(train_derivatives, coefficients)
        calibration_metrics = _residual_metrics(
            calibration_derivatives, coefficients
        )
        scaled_candidate = derivative_scales * coefficients
        scaled_candidate /= np.linalg.norm(scaled_candidate)
        overlap = (
            float(
                np.max(
                    np.abs(
                        _matrix_vector(control_basis.T, scaled_candidate)
                    )
                )
            )
            if control_basis.shape[1]
            else 0.0
        )
        modes.append(
            NearNullMode(
                rank=rank,
                coefficients=coefficients,
                standardized_singular_value=float(
                    singular_values[singular_index]
                    / np.sqrt(train_derivatives.shape[0])
                ),
                training_lie_rms=training_metrics["lie_rms"],
                training_lie_max_abs=training_metrics["lie_max_abs"],
                calibration_lie_rms=calibration_metrics["lie_rms"],
                calibration_lie_max_abs=calibration_metrics["lie_max_abs"],
                training_value_std=float(
                    np.std(_matrix_vector(train_features, coefficients))
                ),
                calibration_value_std=float(
                    np.std(
                        _matrix_vector(
                            calibration_features_array, coefficients
                        )
                    )
                ),
                known_control_overlap_max=overlap,
            )
        )

    return SearchResult(
        feature_names=feature_names,
        derivative_scales=derivative_scales,
        standardized_singular_values=(
            singular_values / np.sqrt(train_derivatives.shape[0])
        ),
        numerical_nullity=numerical_nullity,
        nullity_relative_tolerance=nullity_relative_tolerance,
        control_metrics=control_metrics,
        modes=tuple(modes),
    )
