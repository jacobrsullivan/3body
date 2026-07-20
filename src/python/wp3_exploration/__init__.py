"""Qualification-aware exploratory near-null search for WP3."""

from .dynamics import JacobiVectorField, jacobi_vector_field
from .features import (
    DimensionSignature,
    FeatureEvaluation,
    evaluate_invariant_features,
    feature_dimensions,
    feature_names,
    format_dimension_signature,
    known_control_coefficients,
)
from .publication_gate import (
    PublicationGateError,
    evaluate_publication_gate,
    require_publishable,
)
from .search import NearNullMode, SearchResult, search_near_null_modes
from .source_cases import (
    ReservedSplitError,
    SamplePoint,
    build_upstream_case,
    sample_exploration_split,
)

__all__ = [
    "DimensionSignature",
    "FeatureEvaluation",
    "JacobiVectorField",
    "NearNullMode",
    "PublicationGateError",
    "ReservedSplitError",
    "SamplePoint",
    "SearchResult",
    "build_upstream_case",
    "evaluate_invariant_features",
    "evaluate_publication_gate",
    "feature_dimensions",
    "feature_names",
    "format_dimension_signature",
    "jacobi_vector_field",
    "known_control_coefficients",
    "require_publishable",
    "sample_exploration_split",
    "search_near_null_modes",
]
