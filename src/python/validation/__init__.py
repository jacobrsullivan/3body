"""
Validation module for WP 4.2: Complete Morales-Ramis Test.

This module implements the two-phase Morales-Ramis compatibility test:
- Phase I: Downstairs (proving non-integrability in original coordinates)
- Phase II: Upstairs (proving abelian Galois structure in lifted coordinates)

Submodules:
- periodic_orbits: Library of known periodic solutions (Lagrange, Figure-8, etc.)
- variational_equations: Computation of Normal Variational Equations
- kovacic: Kovacic algorithm for differential Galois groups
- morales_ramis_validator: Orchestrates Morales-Ramis test on periodic orbits
- upstairs_variational: Upstairs variational equations in lifted space (TODO)
- compatibility_test: Complete two-phase validation framework (TODO)
"""

# Phase 1-3 modules (IMPLEMENTED)
from . import periodic_orbits
from . import variational_equations
from . import kovacic
from . import morales_ramis_validator

# Commonly used classes and functions
from .periodic_orbits import (
    PeriodicOrbit,
    get_orbit_catalog,
    list_available_orbits,
    lagrange_l4_circular_restricted_3bp,
    lagrange_l4_equal_masses,
    euler_collinear_equal_masses,
    figure_8_choreography_approximate
)

from .variational_equations import (
    VariationalEquationComputer,
    VariationalEquationData,
    NormalVariationalEquation
)

from .kovacic import (
    KovacicSolver,
    GaloisGroupType,
    KovacicResult,
    classify_galois_group,
    is_galois_group_abelian,
    morales_ramis_test
)

from .morales_ramis_validator import (
    MoralesRamisValidator,
    MoralesRamisResult,
    create_validator_for_cr3bp
)

__all__ = [
    # Modules
    'periodic_orbits',
    'variational_equations',
    'kovacic',
    'morales_ramis_validator',
    # Periodic orbits
    'PeriodicOrbit',
    'get_orbit_catalog',
    'list_available_orbits',
    'lagrange_l4_circular_restricted_3bp',
    'lagrange_l4_equal_masses',
    'euler_collinear_equal_masses',
    'figure_8_choreography_approximate',
    # Variational equations
    'VariationalEquationComputer',
    'VariationalEquationData',
    'NormalVariationalEquation',
    # Kovacic algorithm
    'KovacicSolver',
    'GaloisGroupType',
    'KovacicResult',
    'classify_galois_group',
    'is_galois_group_abelian',
    'morales_ramis_test',
    # Morales-Ramis validator
    'MoralesRamisValidator',
    'MoralesRamisResult',
    'create_validator_for_cr3bp',
]
