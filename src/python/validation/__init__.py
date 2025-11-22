"""
Validation module for WP 4: Complete Rigorous Validation and Falsification.

This module implements the complete three-stage validation gauntlet:

WP 4.1 - ANALYTICAL VETTING (Liouville Criteria):
✅ Poisson bracket computation (symbolic + numerical)
✅ Conservation testing: {I, H} = 0
✅ Involution testing: {I_i, I_j} = 0
✅ Functional independence testing (Jacobian rank)
✅ Complete analytical vetting pipeline

WP 4.2 - MORALES-RAMIS TEST (Differential Galois Theory):
✅ Phase 1: Periodic orbit library
✅ Phase 2: Variational equations (downstairs)
✅ Phase 3: Kovacic algorithm and Morales-Ramis validator
✅ Phase 4: Symbolic lift Hamiltonians (S¹ bundle)
✅ Phase 5: Upstairs variational equations
✅ Phase 6: Complete compatibility test

WP 4.3 - NUMERICAL ROBUSTNESS (Statistical Validation):
✅ Monte Carlo parameter sweep (10⁵-10⁶ trajectories)
✅ Stress testing (collisions, chaos, high eccentricity)
✅ Long-time validation (shadow Hamiltonian analysis)
✅ Statistical reporting (plots, tables, LaTeX)

Submodules:
- poisson_brackets: Unified Poisson bracket computation
- conservation_validator: Batch conservation testing
- involution_tester: Pairwise involution testing
- independence_tester: Functional independence via Jacobian rank
- analytical_vetting: Complete WP 4.1 pipeline
- periodic_orbits: Library of known periodic solutions
- variational_equations: Downstairs Normal Variational Equations
- kovacic: Kovacic algorithm for differential Galois groups
- morales_ramis_validator: Downstairs Morales-Ramis test orchestration
- upstairs_variational: Upstairs variational equations in lifted space
- compatibility_test: Complete two-phase validation framework
- monte_carlo_validator: Large-scale Monte Carlo validation
- stress_tester: Extreme scenario testing
- long_time_validator: Long-time integration and shadow Hamiltonian
- statistical_reporter: Publication-quality reports and plots
"""

# WP 4.1 - Analytical Vetting modules
from . import poisson_brackets
from . import conservation_validator
from . import involution_tester
from . import independence_tester
from . import analytical_vetting

# WP 4.2 - Morales-Ramis Test modules
from . import periodic_orbits
from . import variational_equations
from . import kovacic
from . import morales_ramis_validator
from . import upstairs_variational
from . import compatibility_test

# WP 4.3 - Numerical Robustness modules
from . import monte_carlo_validator
from . import stress_tester
from . import long_time_validator
from . import statistical_reporter

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
    # WP 4.1 modules
    'poisson_brackets',
    'conservation_validator',
    'involution_tester',
    'independence_tester',
    'analytical_vetting',
    # WP 4.2 modules
    'periodic_orbits',
    'variational_equations',
    'kovacic',
    'morales_ramis_validator',
    'upstairs_variational',
    'compatibility_test',
    # WP 4.3 modules
    'monte_carlo_validator',
    'stress_tester',
    'long_time_validator',
    'statistical_reporter',
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
