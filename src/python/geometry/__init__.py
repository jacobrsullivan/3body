"""
Geometric structures on shape space for the three-body problem.

This module implements:
    - Mechanical connection one-form (Task 2.1.2)
    - Curvature two-form (Task 2.1.2)
    - Jacobi-Maupertuis metric (Task 2.1.3)
    - Riemann curvature tensors (Task 2.1.3)
    - Lifted JM metrics on S¹ bundle and KS-Spinor manifold (Task 3.1.1)

Mathematical Background:
    When we reduce the 3-body problem by translations and rotations,
    we obtain dynamics on a shape space. The geometry of this space
    is encoded in:

    1. Mechanical connection A: couples shape changes to rotations
    2. Curvature F = dA: measures obstruction to integrability
    3. JM metric: Riemannian metric at fixed energy
    4. Scalar curvature R: diagnostic for chaos (R < 0 ⟺ chaos)

    For WP3 (invariant discovery), we extend this to lifted spaces:
    5. S¹ bundle metric: 4D metric on shape space × S¹
    6. KS-Spinor metric: 9D metric on regularized spinor manifold
"""

from .locked_inertia import compute_locked_inertia_tensor, LockedInertiaTensor
from .connection_form import (
    ConnectionForm,
    compute_connection_coefficients,
    evaluate_connection,
)
from .curvature_form import (
    CurvatureForm,
    compute_curvature,
    validate_stokes_theorem,
)
from .jm_metric import (
    RiemannianMetric,
    compute_jm_metric,
    compute_effective_potential,
)
from .christoffel import (
    ChristoffelSymbols,
    compute_christoffel_symbols,
    compute_metric_derivatives,
)
from .riemann_curvature import (
    CurvatureTensors,
    compute_scalar_curvature,
    compute_ricci_tensor,
)
from .lifted_jm_metric import (
    BundleMetric,
    KSMetric,
    KSSpinorCoords,
    compute_s1_bundle_metric,
    compute_s1_jm_metric,
    compute_ks_mass_matrix,
    compute_ks_potential,
    compute_ks_jm_metric,
    validate_s1_metric_properties,
    compare_s1_vs_base_metric,
)

__all__ = [
    # Locked inertia
    "compute_locked_inertia_tensor",
    "LockedInertiaTensor",
    # Connection
    "ConnectionForm",
    "compute_connection_coefficients",
    "evaluate_connection",
    # Curvature
    "CurvatureForm",
    "compute_curvature",
    "validate_stokes_theorem",
    # JM Metric
    "RiemannianMetric",
    "compute_jm_metric",
    "compute_effective_potential",
    # Christoffel
    "ChristoffelSymbols",
    "compute_christoffel_symbols",
    "compute_metric_derivatives",
    # Riemann curvature
    "CurvatureTensors",
    "compute_scalar_curvature",
    "compute_ricci_tensor",
    # Lifted JM metrics (WP 3.1)
    "BundleMetric",
    "KSMetric",
    "KSSpinorCoords",
    "compute_s1_bundle_metric",
    "compute_s1_jm_metric",
    "compute_ks_mass_matrix",
    "compute_ks_potential",
    "compute_ks_jm_metric",
    "validate_s1_metric_properties",
    "compare_s1_vs_base_metric",
]
