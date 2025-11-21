"""
Validation module for WP 4.2: Complete Morales-Ramis Test.

This module implements the two-phase Morales-Ramis compatibility test:
- Phase I: Downstairs (proving non-integrability in original coordinates)
- Phase II: Upstairs (proving abelian Galois structure in lifted coordinates)

Submodules:
- periodic_orbits: Library of known periodic solutions (Lagrange, Figure-8, etc.)
- variational_equations: Computation of Normal Variational Equations
- kovacic: Kovacic algorithm for differential Galois groups
- upstairs_variational: Upstairs variational equations in lifted space
- compatibility_test: Complete two-phase validation framework
"""

__all__ = [
    'periodic_orbits',
    'variational_equations',
    'kovacic',
    'upstairs_variational',
    'compatibility_test',
]
