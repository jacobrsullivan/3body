"""
Geometric structures on shape space for the three-body problem.

This module implements:
    - Mechanical connection one-form (Task 2.1.2)
    - Curvature two-form (Task 2.1.2)
    - Jacobi-Maupertuis metric (Task 2.1.3)
    - Riemann curvature tensors (Task 2.1.3)

Mathematical Background:
    When we reduce the 3-body problem by translations and rotations,
    we obtain dynamics on a shape space. The geometry of this space
    is encoded in:

    1. Mechanical connection A: couples shape changes to rotations
    2. Curvature F = dA: measures obstruction to integrability
    3. JM metric: Riemannian metric at fixed energy
    4. Scalar curvature R: diagnostic for chaos (R < 0 ⟺ chaos)
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
]
