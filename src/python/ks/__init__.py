"""Qualified Kustaanheimo-Stiefel prototype primitives.

This namespace is intentionally separate from ``src.python.regularization``.
The latter contains the exploratory WP2 implementation; this package defines
the conventions used by the WP2Q-KS qualification campaign.
"""

from .canonical import (
    KSPhaseState,
    KeplerPhaseState,
    NegativeEnergyKSSystem,
    ZeroMomentumQuotient,
    canonical_poisson_matrix,
    cotangent_projection_jacobian,
    fiber_generator,
    ks_jacobian,
    ks_position,
    lift_cotangent,
    momentum_map,
    project_cotangent,
    projected_poisson_matrix,
    s1_action,
)

__all__ = [
    "KSPhaseState",
    "KeplerPhaseState",
    "NegativeEnergyKSSystem",
    "ZeroMomentumQuotient",
    "canonical_poisson_matrix",
    "cotangent_projection_jacobian",
    "fiber_generator",
    "ks_jacobian",
    "ks_position",
    "lift_cotangent",
    "momentum_map",
    "project_cotangent",
    "projected_poisson_matrix",
    "s1_action",
]
