"""Bounded, disjoint core for the WP1Q-N3BP-v1 qualification track."""

from .benchmarks import (
    BenchmarkOrbit,
    figure_eight_choreography,
    lagrange_analytic_state,
    lagrange_equilateral,
)
from .contract import InertialState, SystemParameters
from .dynamics import (
    CollisionSingularityError,
    newtonian_accelerations,
    newtonian_rhs,
)
from .invariants import (
    ConservedQuantities,
    InvariantDrift,
    angular_momentum,
    center_of_mass_position,
    center_of_mass_velocity,
    conserved_quantities,
    kinetic_energy,
    linear_momentum,
    measure_invariant_drift,
    normalize_center_of_mass,
    potential_energy,
    total_energy,
)
from .propagation import (
    DOP853Config,
    IAS15Config,
    ReferencePropagatorUnavailable,
    Trajectory,
    propagate_dop853,
    propagate_rebound_ias15,
)

__all__ = [
    "BenchmarkOrbit",
    "CollisionSingularityError",
    "ConservedQuantities",
    "DOP853Config",
    "IAS15Config",
    "InertialState",
    "InvariantDrift",
    "ReferencePropagatorUnavailable",
    "SystemParameters",
    "Trajectory",
    "angular_momentum",
    "center_of_mass_position",
    "center_of_mass_velocity",
    "conserved_quantities",
    "figure_eight_choreography",
    "kinetic_energy",
    "lagrange_analytic_state",
    "lagrange_equilateral",
    "linear_momentum",
    "measure_invariant_drift",
    "newtonian_accelerations",
    "newtonian_rhs",
    "normalize_center_of_mass",
    "potential_energy",
    "propagate_dop853",
    "propagate_rebound_ias15",
    "total_energy",
]
