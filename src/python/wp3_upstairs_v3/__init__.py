"""Exact-module parameter-aware polynomial screening upstairs."""

from .features import (
    UpstairsV3FeatureEvaluation,
    evaluate_upstairs_v3_features,
    feature_descriptors,
    feature_names,
    known_module_coefficients,
    parameter_values,
    s1_generator,
)

__all__ = [
    "UpstairsV3FeatureEvaluation",
    "evaluate_upstairs_v3_features",
    "feature_descriptors",
    "feature_names",
    "known_module_coefficients",
    "parameter_values",
    "s1_generator",
]
