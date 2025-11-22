"""
Validation module for WP 4.2: Complete Morales-Ramis Test.

This module implements the complete two-phase Morales-Ramis compatibility test:
- Phase I: Downstairs (proving non-integrability in original coordinates)
- Phase II: Upstairs (proving abelian Galois structure in lifted coordinates)

All phases (1-6) are now COMPLETE:
✅ Phase 1: Periodic orbit library
✅ Phase 2: Variational equations (downstairs)
✅ Phase 3: Kovacic algorithm and Morales-Ramis validator
✅ Phase 4: Symbolic lift Hamiltonians (S¹ bundle)
✅ Phase 5: Upstairs variational equations
✅ Phase 6: Complete compatibility test

Submodules:
- periodic_orbits: Library of known periodic solutions
- variational_equations: Downstairs Normal Variational Equations
- kovacic: Kovacic algorithm for differential Galois groups
- morales_ramis_validator: Downstairs Morales-Ramis test orchestration
- upstairs_variational: Upstairs variational equations in lifted space
- compatibility_test: Complete two-phase validation framework
"""

# Phase 1-3 modules (IMPLEMENTED)
from . import periodic_orbits
from . import variational_equations
from . import kovacic
from . import morales_ramis_validator

# Phase 5-6 modules (IMPLEMENTED)
from . import upstairs_variational
from . import compatibility_test

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

from .upstairs_variational import (
    UpstirsVariationalEquationComputer,
    UpstirsOrbitData,
    UpstirsNormalVariationalEquation,
    create_upstairs_ve_computer_for_s1_cr3bp
)

from .compatibility_test import (
    CompatibilityTestValidator,
    CompatibilityTestReport,
    CompatibilityVerdict,
    TwoPhaseResult,
    create_compatibility_validator_for_cr3bp
)

__all__ = [
    # Modules
    'periodic_orbits',
    'variational_equations',
    'kovacic',
    'morales_ramis_validator',
    'upstairs_variational',
    'compatibility_test',
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
    # Upstairs variational
    'UpstirsVariationalEquationComputer',
    'UpstirsOrbitData',
    'UpstirsNormalVariationalEquation',
    'create_upstairs_ve_computer_for_s1_cr3bp',
    # Compatibility test
    'CompatibilityTestValidator',
    'CompatibilityTestReport',
    'CompatibilityVerdict',
    'TwoPhaseResult',
    'create_compatibility_validator_for_cr3bp',
]
