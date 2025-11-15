"""
Partial Differential Equation formulation for geometric invariant discovery (WP 3.1).

This module implements:
    - Christoffel symbols computation (symbolic and numerical)
    - Killing vector field equations
    - Killing tensor equations
    - Mesh discretization for PDE solution
    - Symmetry constraints and priors

Mathematical Framework:
    Killing fields K on a Riemannian manifold (Q, g) satisfy:
        ∇_(i K_j) = 0  (symmetrized covariant derivative)

    In coordinates:
        ∂K_j/∂q^i + ∂K_i/∂q^j = 2Γ^k_ij K_k

    This is a system of n(n+1)/2 PDEs for n unknowns.

Task: WP 3.1, Task 3.1.2
"""

from .christoffel_symbols import (
    compute_christoffel_symbolic,
    compute_christoffel_numerical,
    compute_christoffel_field,
    validate_christoffel_symmetry,
    ChristoffelSymbolsNumeric,
)
from .killing_equations import (
    KillingVectorPDE,
    KillingTensorPDE,
    DiscretizedKillingSystem,
    formulate_killing_vector_pde,
    formulate_killing_tensor_pde,
    discretize_killing_vector_pde,
    count_equations_and_unknowns,
    estimate_null_space_dimension,
)

__all__ = [
    # Christoffel symbols
    "compute_christoffel_symbolic",
    "compute_christoffel_numerical",
    "compute_christoffel_field",
    "validate_christoffel_symmetry",
    "ChristoffelSymbolsNumeric",
    # Killing PDEs
    "KillingVectorPDE",
    "KillingTensorPDE",
    "DiscretizedKillingSystem",
    "formulate_killing_vector_pde",
    "formulate_killing_tensor_pde",
    "discretize_killing_vector_pde",
    "count_equations_and_unknowns",
    "estimate_null_space_dimension",
]
