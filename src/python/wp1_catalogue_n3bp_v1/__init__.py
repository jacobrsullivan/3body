"""Production API for the native WP1-CAT-N3BP-v1 campaign."""

from .catalogue import (
    CatalogueProvenance,
    CatalogueRun,
    candidate_id,
    generate_catalogue,
)
from .correction import (
    correct_orbit,
    full_planar_closure,
    inertial_rhs,
    propagate_one_period,
    scaled_planar_closure,
)
from .model import (
    DISCLOSED_ROOT,
    MASS_GRID,
    CatalogueCandidate,
    CorrectionResult,
    CorrectionSettings,
    OrbitParameters,
    StabilityResult,
    canonical_section_state,
    planar_state,
    state_from_parameters,
)
from .payload import (
    canonical_candidate_payload,
    canonical_catalogue_payload,
    candidate_record,
    candidate_sha256,
    catalogue_sha256,
)
from .variational import (
    StabilitySettings,
    canonical_jacobi_transform,
    classify_orbit_stability,
    classify_reduced_monodromy,
    integrate_planar_monodromy,
    planar_rhs,
    planar_variational_jacobian,
    project_translation_quotient_monodromy,
)

__all__ = [
    "DISCLOSED_ROOT",
    "MASS_GRID",
    "CatalogueCandidate",
    "CatalogueProvenance",
    "CatalogueRun",
    "CorrectionResult",
    "CorrectionSettings",
    "OrbitParameters",
    "StabilityResult",
    "StabilitySettings",
    "candidate_id",
    "candidate_record",
    "candidate_sha256",
    "canonical_candidate_payload",
    "canonical_catalogue_payload",
    "canonical_jacobi_transform",
    "canonical_section_state",
    "catalogue_sha256",
    "classify_orbit_stability",
    "classify_reduced_monodromy",
    "correct_orbit",
    "full_planar_closure",
    "generate_catalogue",
    "inertial_rhs",
    "integrate_planar_monodromy",
    "planar_rhs",
    "planar_state",
    "planar_variational_jacobian",
    "project_translation_quotient_monodromy",
    "propagate_one_period",
    "scaled_planar_closure",
    "state_from_parameters",
]

