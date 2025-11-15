"""
Partial Differential Equation formulation for geometric invariant discovery (WP 3.1).

This module implements:
    - Christoffel symbols computation (symbolic and numerical)
    - Killing vector field equations
    - Killing tensor equations
    - Mesh discretization for PDE solution
    - Numerical solution via null space computation
    - Regularization and filtering
    - Complete solver pipeline

Mathematical Framework:
    Killing fields K on a Riemannian manifold (Q, g) satisfy:
        ∇_(i K_j) = 0  (symmetrized covariant derivative)

    In coordinates:
        ∂K_j/∂q^i + ∂K_i/∂q^j = 2Γ^k_ij K_k

    This is a system of n(n+1)/2 PDEs for n unknowns.

Tasks: WP 3.1, Tasks 3.1.2 & 3.1.3
"""

# Task 3.1.2: PDE Formulation
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

# Task 3.1.3: Numerical Solution
from .mesh_generation import (
    Mesh,
    S1BundleMesh,
    KSSpinorMesh,
    generate_s1_bundle_mesh,
    generate_ks_spinor_mesh,
    compute_mesh_spacing,
)
from .system_assembly import (
    assemble_killing_vector_system,
    assemble_killing_tensor_system,
    estimate_assembly_memory,
    validate_system_assembly,
)
from .null_space import (
    compute_null_space_svd,
    compute_null_space_iterative,
    verify_null_space,
    estimate_null_space_dimension_theoretical,
)
from .regularization import (
    apply_smoothness_regularization,
    apply_physical_priors,
    compute_mesh_laplacian,
)
from .killing_solver import (
    solve_killing_fields,
    KillingSolution,
)

__all__ = [
    # Christoffel symbols (Task 3.1.2)
    "compute_christoffel_symbolic",
    "compute_christoffel_numerical",
    "compute_christoffel_field",
    "validate_christoffel_symmetry",
    "ChristoffelSymbolsNumeric",
    # Killing PDEs (Task 3.1.2)
    "KillingVectorPDE",
    "KillingTensorPDE",
    "DiscretizedKillingSystem",
    "formulate_killing_vector_pde",
    "formulate_killing_tensor_pde",
    "discretize_killing_vector_pde",
    "count_equations_and_unknowns",
    "estimate_null_space_dimension",
    # Mesh generation (Task 3.1.3)
    "Mesh",
    "S1BundleMesh",
    "KSSpinorMesh",
    "generate_s1_bundle_mesh",
    "generate_ks_spinor_mesh",
    "compute_mesh_spacing",
    # System assembly (Task 3.1.3)
    "assemble_killing_vector_system",
    "assemble_killing_tensor_system",
    "estimate_assembly_memory",
    "validate_system_assembly",
    # Null space computation (Task 3.1.3)
    "compute_null_space_svd",
    "compute_null_space_iterative",
    "verify_null_space",
    "estimate_null_space_dimension_theoretical",
    # Regularization (Task 3.1.3)
    "apply_smoothness_regularization",
    "apply_physical_priors",
    "compute_mesh_laplacian",
    # Main solver (Task 3.1.3)
    "solve_killing_fields",
    "KillingSolution",
]
