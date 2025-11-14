"""
S¹ "Untwisting" Lift for the Three-Body Problem.

This module implements the principal S¹ bundle construction over shape space,
providing a higher-dimensional phase space where the dynamics may be integrable.

Mathematical Framework:
    - Base space: S (shape space, 3D for planar case)
    - Total space: P = S × S¹ (4D)
    - Fiber: S¹ = ℝ/2πℤ (circle)
    - Extended symplectic form: ω̃ = ω_shape + dθ ∧ d(L·A)

The key hypothesis: By explicitly tracking the "winding" accumulated through
the connection A, we may eliminate the obstruction to integrability.

Task: WP 2.2 - S¹ Lift Construction
"""

from .s1_bundle import (
    BundleState,
    S1Bundle,
    BundleChart,
    create_bundle_state,
    project_to_base,
)
from .extended_symplectic import (
    ExtendedSymplecticForm,
    compute_extended_symplectic_form,
    poisson_bracket_on_bundle,
)
from .lifted_hamiltonian import (
    LiftedHamiltonian,
    integrate_bundle_dynamics,
    BundleTrajectory,
)
from .integrability import (
    verify_basic_integrals,
    check_functional_independence,
    verify_involution,
)

__all__ = [
    # Bundle structures
    "BundleState",
    "S1Bundle",
    "BundleChart",
    "create_bundle_state",
    "project_to_base",
    # Extended symplectic form
    "ExtendedSymplecticForm",
    "compute_extended_symplectic_form",
    "poisson_bracket_on_bundle",
    # Lifted dynamics
    "LiftedHamiltonian",
    "integrate_bundle_dynamics",
    "BundleTrajectory",
    # Integrability tests
    "verify_basic_integrals",
    "check_functional_independence",
    "verify_involution",
]
