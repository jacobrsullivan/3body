"""
Symbolic Lift Hamiltonians for WP 4.2 Phase II (Upstairs Analysis).

This module provides symbolic (SymPy-based) implementations of extended
Hamiltonians for the S¹ bundle and KS-Spinor lifts constructed in WP2.

The symbolic approach enables:
- Exact computation of Hessians ∇²H̃
- Derivation of upstairs variational equations
- Application of Kovacic algorithm to upstairs NVEs
- Verification of abelian Galois structure in lifted space

Submodules:
- s1_symbolic: S¹ bundle extended Hamiltonian
- ks_symbolic: KS-Spinor extended Hamiltonian ✅ COMPLETE
- common: Shared symbolic utilities
"""

from . import s1_symbolic
from . import ks_symbolic
from . import common

# Import main classes from S¹ symbolic
from .s1_symbolic import (
    S1BundleHamiltonian,
    create_s1_hamiltonian_cr3bp,
    create_s1_hamiltonian_general_3bp
)

# Import main classes from KS symbolic
from .ks_symbolic import (
    KSSpinorHamiltonian,
    KSPairwiseHamiltonian,
    create_ks_hamiltonian_kepler,
    create_ks_pairwise_3bp,
    levi_civita_matrix,
    bilinear_relation_symbolic,
    ks_transform_symbolic,
    ks_inverse_symbolic,
    prepare_ks_for_upstairs_mr_test,
    verify_bilinear_relation_symbolic
)

# Import common utilities
from .common import (
    SymbolicHamiltonianSystem,
    compute_symplectic_gradient,
    compute_hessian
)

__all__ = [
    # Modules
    's1_symbolic',
    'ks_symbolic',
    'common',
    # S¹ bundle
    'S1BundleHamiltonian',
    'create_s1_hamiltonian_cr3bp',
    'create_s1_hamiltonian_general_3bp',
    # KS-Spinor
    'KSSpinorHamiltonian',
    'KSPairwiseHamiltonian',
    'create_ks_hamiltonian_kepler',
    'create_ks_pairwise_3bp',
    'levi_civita_matrix',
    'bilinear_relation_symbolic',
    'ks_transform_symbolic',
    'ks_inverse_symbolic',
    'prepare_ks_for_upstairs_mr_test',
    'verify_bilinear_relation_symbolic',
    # Common utilities
    'SymbolicHamiltonianSystem',
    'compute_symplectic_gradient',
    'compute_hessian',
]
