# WP3 Phase 1: Critical Gap Fixes - Implementation Roadmap
## Detailed Technical Guide

**Date**: November 22, 2025
**Estimated Duration**: 3 days (24 hours)
**Priority**: P0-P1 (Critical Path)

---

## Overview

This document provides detailed, code-level guidance for fixing the 5 most critical gaps in WP3 that prevent end-to-end execution of the discovery pipeline.

**Goals**:
1. Enable complete WP3.1 (Geometric Search) execution
2. Support both Killing vector and tensor searches
3. Validate on known test cases
4. Prepare handoff to WP3.3 (Symbolic Regression)

---

## Gap C1: Connect Killing PDE Solver
**Priority**: P0 - CRITICAL
**Effort**: 2 hours
**File**: `src/python/pde/killing_equations.py`

### Current State
```python
# Line 252
def solve(self, mesh, method='svd'):
    """Solve the Killing vector PDE."""
    raise NotImplementedError("PDE solution in Task 3.1.3")
```

### Problem
The `KillingVectorPDE.solve()` method is a stub, but the actual solver exists in `killing_solver.py`. They just need to be connected.

### Solution

**Step 1**: Import the main solver at the top of `killing_equations.py`
```python
# Add to imports section (around line 10)
from typing import Optional, Dict, List
```

**Step 2**: Replace the `solve()` method in `KillingVectorPDE` class:
```python
def solve(
    self,
    mesh,
    method: str = 'svd',
    regularization: Optional[dict] = None,
    verbose: bool = False
) -> 'KillingSolution':
    """
    Solve the Killing vector PDE on the given mesh.

    This method delegates to the main solver pipeline in killing_solver.py.

    Args:
        mesh: Mesh on which to solve (S1BundleMesh or KSSpinorMesh)
        method: Solution method ('svd', 'iterative', or 'randomized')
        regularization: Optional regularization parameters
        verbose: Print progress information

    Returns:
        KillingSolution containing discovered Killing vector fields

    Raises:
        ValueError: If mesh type doesn't match PDE manifold type
    """
    from .killing_solver import solve_killing_fields
    from .mesh_generation import S1BundleMesh, KSSpinorMesh

    # Determine manifold type from mesh
    if isinstance(mesh, S1BundleMesh):
        manifold_type = 's1_bundle'
    elif isinstance(mesh, KSSpinorMesh):
        manifold_type = 'ks_spinor'
    else:
        raise ValueError(f"Unknown mesh type: {type(mesh)}")

    # Extract parameters from mesh metadata
    masses = mesh.metadata.get('masses')
    energy = mesh.metadata.get('energy')
    L_magnitude = mesh.metadata.get('L_magnitude')

    if masses is None or energy is None:
        raise ValueError("Mesh must contain 'masses' and 'energy' in metadata")

    # Determine resolution from mesh
    if manifold_type == 's1_bundle':
        resolution = {
            'shape_coarse': mesh.metadata.get('shape_coarse', 20),
            'shape_fine': mesh.num_points,
            'fiber': mesh.metadata.get('fiber_points', 16)
        }
    else:  # ks_spinor
        resolution = {
            'spinor_coarse': mesh.metadata.get('spinor_coarse', 20),
            'spinor_fine': mesh.num_points
        }

    # Call main solver
    return solve_killing_fields(
        manifold_type=manifold_type,
        masses=masses,
        energy=energy,
        resolution=resolution,
        field_type='vector',
        L_magnitude=L_magnitude,
        regularization=regularization,
        verbose=verbose
    )
```

**Step 3**: Add similar method for `KillingTensorPDE.solve()`:
```python
def solve(
    self,
    mesh,
    method: str = 'svd',
    regularization: Optional[dict] = None,
    verbose: bool = False
) -> 'KillingSolution':
    """Solve the Killing tensor PDE (similar to vector case)."""
    from .killing_solver import solve_killing_fields
    from .mesh_generation import S1BundleMesh, KSSpinorMesh

    # Same logic as KillingVectorPDE.solve() but with field_type='tensor'
    # [Copy implementation from above, change field_type='tensor']

    return solve_killing_fields(
        manifold_type=manifold_type,
        masses=masses,
        energy=energy,
        resolution=resolution,
        field_type='tensor',  # <-- Only difference
        L_magnitude=L_magnitude,
        regularization=regularization,
        verbose=verbose
    )
```

### Testing
```python
# tests/wp3/test_killing_pde.py
def test_solve_killing_vector_pde():
    """Test that KillingVectorPDE.solve() executes without error."""
    from pde.killing_equations import formulate_killing_vector_pde
    from pde.mesh_generation import generate_s1_bundle_mesh

    # Generate simple mesh
    mesh = generate_s1_bundle_mesh(
        masses=np.array([1.0, 1.0, 1.0]),
        energy=-1.0,
        L_magnitude=1.0,
        resolution={'shape_coarse': 10, 'shape_fine': 50, 'fiber': 8}
    )

    # Formulate PDE
    pde = formulate_killing_vector_pde(manifold_type='s1_bundle')

    # Solve (should not raise NotImplementedError)
    solution = pde.solve(mesh, method='svd', verbose=True)

    # Basic checks
    assert solution is not None
    assert solution.mesh == mesh
    assert len(solution.killing_fields) >= 0
```

**Completion Criteria**:
- [ ] `KillingVectorPDE.solve()` executes without error
- [ ] `KillingTensorPDE.solve()` executes without error
- [ ] Test case passes
- [ ] Returns `KillingSolution` object

---

## Gap C3: Complete Killing Tensor System Assembly
**Priority**: P1 - HIGH
**Effort**: 8 hours
**File**: `src/python/pde/system_assembly.py`

### Current State
```python
# Line 312
def assemble_killing_tensor_system(...):
    # TODO: Implement full assembly (similar structure to vector case)
    pass
```

### Problem
Killing tensor assembly is incomplete. Need to build sparse system for rank-2 symmetric tensors.

### Mathematical Background

**Killing Tensor Equation**:
$$\nabla_{(k} K_{ij)} = 0$$

Expanded:
$$\frac{\partial K_{ij}}{\partial q^k} + \frac{\partial K_{ik}}{\partial q^j} + \frac{\partial K_{jk}}{\partial q^i} - \Gamma^l_{ki} K_{lj} - \Gamma^l_{kj} K_{il} - \Gamma^l_{ij} K_{kl} = 0$$

For symmetric tensor: $K_{ij} = K_{ji}$

**Number of equations**: For n-dimensional manifold:
- Unknowns: $\frac{n(n+1)}{2}$ (symmetric tensor components)
- Equations per point: $\frac{n(n+1)(n+2)}{6}$ (symmetric in all 3 indices)
- System is overdetermined

### Solution

**Step 1**: Study the vector case implementation (lines 100-280)
```python
# Current vector assembly structure:
# 1. Loop over mesh points
# 2. Compute Christoffel symbols at each point
# 3. Build finite difference stencils
# 4. Assemble sparse matrix A
# 5. Return sparse system
```

**Step 2**: Implement tensor assembly:
```python
def assemble_killing_tensor_system(
    mesh: Mesh,
    metric_func: Callable,
    christoffel_func: Callable,
    fd_order: int = 2,
    sparse_format: str = 'csr',
    verbose: bool = False
) -> Tuple[sparse.spmatrix, np.ndarray]:
    """
    Assemble sparse linear system for Killing tensor PDE.

    Returns:
        A: Sparse matrix (M × N) where M >> N (overdetermined system)
        b: Zero vector (homogeneous system)

    System structure:
        For each point i in mesh:
            For each triple (k,i,j) with k ≤ i ≤ j:
                Add equation: ∇_k K_ij + ∇_i K_kj + ∇_j K_ki = ...
    """
    n = mesh.dimension
    N = mesh.num_points

    # Number of unknowns: n(n+1)/2 components per point
    n_components = n * (n + 1) // 2
    n_unknowns = N * n_components

    # Number of equations: n(n+1)(n+2)/6 per point (symmetric in k,i,j)
    n_eqs_per_point = n * (n + 1) * (n + 2) // 6
    n_equations = N * n_eqs_per_point

    if verbose:
        print(f"Assembling Killing tensor system:")
        print(f"  Dimension: {n}")
        print(f"  Mesh points: {N}")
        print(f"  Unknowns: {n_unknowns} ({n_components} components × {N} points)")
        print(f"  Equations: {n_equations} ({n_eqs_per_point} per point)")
        print(f"  Sparsity: ~{100*(1 - n**3/(n_equations*n_unknowns)):.1f}%")

    # Storage for sparse matrix in COO format
    row_indices = []
    col_indices = []
    values = []

    # Helper: Map symmetric tensor indices (i,j) to linear index
    def tensor_idx(i, j):
        """Map (i,j) with i ≤ j to linear index in [0, n(n+1)/2)."""
        if i > j:
            i, j = j, i
        return i * n - i * (i - 1) // 2 + (j - i)

    # Loop over mesh points
    equation_index = 0

    for pt_idx, point in enumerate(mesh.points):
        if verbose and pt_idx % 1000 == 0:
            print(f"  Processing point {pt_idx}/{N}...")

        # Compute metric and Christoffel symbols at this point
        g = metric_func(point)
        Gamma = christoffel_func(point, g)  # Shape: (n, n, n)

        # Get neighbor indices for finite differences
        neighbors = mesh.get_neighbors(pt_idx)

        # Loop over all symmetric triples (k, i, j) with k ≤ i ≤ j
        for k in range(n):
            for i in range(k, n):
                for j in range(i, n):
                    # This is one equation: ∇_k K_ij + ∇_i K_kj + ∇_j K_ki = RHS

                    # Derivative terms (finite differences)
                    # ∂K_ij/∂q^k
                    for neighbor_idx in neighbors:
                        h = mesh.spacing(pt_idx, neighbor_idx)
                        direction = mesh.direction(pt_idx, neighbor_idx)

                        if direction == k:  # Derivative in k direction
                            # Contribution from ∂K_ij/∂q^k
                            unknown_idx = neighbor_idx * n_components + tensor_idx(i, j)

                            if fd_order == 2:
                                coeff = fd_coefficients_centered(h, order=1)[1]  # First derivative
                            else:
                                coeff = fd_coefficients_fourth_order(h, order=1)[1]

                            row_indices.append(equation_index)
                            col_indices.append(unknown_idx)
                            values.append(coeff)

                    # Similar for ∂K_ik/∂q^j and ∂K_jk/∂q^i
                    # [Add similar blocks]

                    # Connection terms: -Γ^l_ki K_lj - Γ^l_kj K_il - Γ^l_ij K_kl
                    for l in range(n):
                        # -Γ^l_ki K_lj
                        lj_idx = pt_idx * n_components + tensor_idx(l, j)
                        row_indices.append(equation_index)
                        col_indices.append(lj_idx)
                        values.append(-Gamma[l, k, i])

                        # -Γ^l_kj K_il
                        il_idx = pt_idx * n_components + tensor_idx(i, l)
                        row_indices.append(equation_index)
                        col_indices.append(il_idx)
                        values.append(-Gamma[l, k, j])

                        # -Γ^l_ij K_kl
                        kl_idx = pt_idx * n_components + tensor_idx(k, l)
                        row_indices.append(equation_index)
                        col_indices.append(kl_idx)
                        values.append(-Gamma[l, i, j])

                    equation_index += 1

    # Build sparse matrix
    A = sparse.coo_matrix(
        (values, (row_indices, col_indices)),
        shape=(n_equations, n_unknowns)
    )

    # Convert to requested format
    if sparse_format == 'csr':
        A = A.tocsr()
    elif sparse_format == 'csc':
        A = A.tocsc()

    # Right-hand side (homogeneous system)
    b = np.zeros(n_equations)

    if verbose:
        print(f"Assembly complete:")
        print(f"  Matrix shape: {A.shape}")
        print(f"  Non-zeros: {A.nnz}")
        print(f"  Sparsity: {100 * (1 - A.nnz / (A.shape[0] * A.shape[1])):.2f}%")

    return A, b
```

**Step 3**: Add helper functions:
```python
def fd_coefficients_centered(h: float, order: int) -> np.ndarray:
    """Finite difference coefficients for centered stencil."""
    if order == 1:  # First derivative
        return np.array([-1/(2*h), 0, 1/(2*h)])
    elif order == 2:  # Second derivative
        return np.array([1/h**2, -2/h**2, 1/h**2])
    else:
        raise ValueError(f"Order {order} not implemented")

def fd_coefficients_fourth_order(h: float, order: int) -> np.ndarray:
    """Fourth-order finite difference coefficients."""
    if order == 1:
        return np.array([1/(12*h), -2/(3*h), 0, 2/(3*h), -1/(12*h)])
    else:
        raise NotImplementedError(f"Fourth-order for order {order}")
```

### Testing
```python
# tests/wp3/test_system_assembly.py
def test_killing_tensor_assembly():
    """Test Killing tensor system assembly."""
    from pde.system_assembly import assemble_killing_tensor_system
    from pde.mesh_generation import generate_flat_space_mesh

    # Simple flat space mesh
    mesh = generate_flat_space_mesh(dimension=2, num_points=100)

    # Flat metric
    def metric_func(point):
        return np.eye(2)

    # Flat Christoffel (all zeros)
    def christoffel_func(point, g):
        return np.zeros((2, 2, 2))

    # Assemble
    A, b = assemble_killing_tensor_system(
        mesh=mesh,
        metric_func=metric_func,
        christoffel_func=christoffel_func,
        verbose=True
    )

    # Checks
    assert A.shape[0] > A.shape[1]  # Overdetermined
    assert b.shape[0] == A.shape[0]
    assert np.allclose(b, 0)  # Homogeneous system

    # For flat space, expect many Killing tensors
    # (metric itself, products of Killing vectors, etc.)
    null_dim = compute_null_space_dimension(A)
    assert null_dim > 0
```

**Completion Criteria**:
- [ ] `assemble_killing_tensor_system()` fully implemented
- [ ] Returns sparse matrix A and vector b
- [ ] System is overdetermined (M > N)
- [ ] Test case passes on flat space
- [ ] Validates on sphere (expect symmetric tensors)

---

## Gap H1: Permutation Symmetry Projection
**Priority**: P1 - HIGH
**Effort**: 6 hours
**File**: `src/python/pde/regularization.py`

### Current State
```python
# Line 275
# TODO: Implement permutation symmetry projection
```

### Problem
For identical particles, Killing fields should respect permutation symmetry: $K(\sigma \cdot q) = \sigma \cdot K(q)$ for permutations $\sigma$.

### Mathematical Background

**Permutation Group**: For 3 identical particles, $S_3$ has 6 elements:
- Identity: $e$
- Transpositions: $(12), (23), (13)$
- 3-cycles: $(123), (132)$

**Projection onto Symmetric Subspace**:
$$K_{sym} = \frac{1}{|G|} \sum_{\sigma \in G} \sigma \cdot K$$

where $\sigma \cdot K$ is the permuted Killing field.

### Solution

**Step 1**: Implement permutation group representation:
```python
def generate_permutation_group(n_particles: int) -> List[np.ndarray]:
    """
    Generate all permutation matrices for n particles.

    Returns:
        List of (n! × n!) permutation matrices for coordinate transformations

    For 3 particles: Returns 6 permutation matrices
    """
    from itertools import permutations

    all_perms = list(permutations(range(n_particles)))
    matrices = []

    for perm in all_perms:
        # Build permutation matrix
        # For 3-body shape space (3 coordinates), need 3×3 matrix
        P = np.zeros((n_particles, n_particles))
        for i, j in enumerate(perm):
            P[i, j] = 1
        matrices.append(P)

    return matrices

def permute_state(state: np.ndarray, perm_matrix: np.ndarray) -> np.ndarray:
    """Apply permutation to state vector."""
    # For shape space: permute distance coordinates
    # s = (r_12, r_23, r_31) -> permute according to particle exchange
    return perm_matrix @ state
```

**Step 2**: Implement projection:
```python
def apply_permutation_symmetry(
    killing_field: np.ndarray,
    mesh: Mesh,
    masses: np.ndarray,
    tolerance: float = 1e-10
) -> np.ndarray:
    """
    Project Killing field onto permutation-symmetric subspace.

    Args:
        killing_field: (n × N) array of vector field components
        mesh: Mesh on which field is defined
        masses: Particle masses
        tolerance: Tolerance for identifying identical particles

    Returns:
        Projected field respecting permutation symmetry
    """
    # Identify identical particles
    identical_groups = identify_identical_particles(masses, tolerance)

    if not identical_groups:
        # No identical particles, return as is
        return killing_field

    # For now, assume all particles identical (equal mass case)
    if len(identical_groups) == 1 and len(identical_groups[0]) == len(masses):
        n_particles = len(masses)
        perm_group = generate_permutation_group(n_particles)

        # Project onto symmetric subspace
        K_sym = np.zeros_like(killing_field)

        for perm_matrix in perm_group:
            # Apply permutation to each mesh point
            K_permuted = permute_killing_field(
                killing_field,
                mesh,
                perm_matrix
            )
            K_sym += K_permuted

        # Average
        K_sym /= len(perm_group)

        return K_sym
    else:
        # Partial symmetry (some particles identical)
        raise NotImplementedError("Partial permutation symmetry not yet implemented")

def identify_identical_particles(
    masses: np.ndarray,
    tolerance: float = 1e-10
) -> List[List[int]]:
    """
    Identify groups of identical particles.

    Returns:
        List of lists, each sublist contains indices of identical particles
        Example: [[0,1,2]] for three equal masses
                 [[0,1], [2]] for two equal, one different
    """
    groups = []
    used = set()

    for i in range(len(masses)):
        if i in used:
            continue

        group = [i]
        for j in range(i+1, len(masses)):
            if abs(masses[i] - masses[j]) < tolerance:
                group.append(j)
                used.add(j)

        groups.append(group)
        used.add(i)

    # Only return groups with >1 particle
    return [g for g in groups if len(g) > 1]

def permute_killing_field(
    killing_field: np.ndarray,
    mesh: Mesh,
    perm_matrix: np.ndarray
) -> np.ndarray:
    """
    Apply permutation to Killing field.

    Strategy:
    1. For each mesh point q
    2. Find permuted point σ(q)
    3. Interpolate killing_field at σ(q)
    4. Transform vector components
    """
    from scipy.interpolate import LinearNDInterpolator

    n_components, n_points = killing_field.shape
    K_permuted = np.zeros_like(killing_field)

    # Build interpolators for each component
    interpolators = []
    for comp in range(n_components):
        interp = LinearNDInterpolator(
            mesh.points,
            killing_field[comp, :]
        )
        interpolators.append(interp)

    # Apply permutation
    for i, point in enumerate(mesh.points):
        # Permute point coordinates
        point_permuted = permute_state(point, perm_matrix)

        # Interpolate field at permuted point
        for comp in range(n_components):
            K_permuted[comp, i] = interpolators[comp](point_permuted)

        # Transform vector components according to permutation
        K_permuted[:, i] = perm_matrix @ K_permuted[:, i]

    return K_permuted
```

**Step 3**: Integrate into regularization pipeline:
```python
# In src/python/pde/regularization.py, update apply_physical_priors()

def apply_physical_priors(
    null_space_basis: np.ndarray,
    mesh: Mesh,
    masses: Optional[np.ndarray] = None,
    priors: Optional[dict] = None
) -> np.ndarray:
    """Apply physical constraints to null space basis."""
    # ... existing code ...

    # Add permutation symmetry projection
    if masses is not None and priors is not None:
        if priors.get('permutation_symmetry', False):
            # Project each basis vector onto symmetric subspace
            basis_symmetric = []
            for i in range(null_space_basis.shape[1]):
                K = null_space_basis[:, i].reshape((mesh.dimension, mesh.num_points))
                K_sym = apply_permutation_symmetry(K, mesh, masses)
                basis_symmetric.append(K_sym.flatten())

            null_space_basis = np.column_stack(basis_symmetric)

    return null_space_basis
```

### Testing
```python
# tests/wp3/test_regularization.py
def test_permutation_symmetry():
    """Test permutation symmetry projection."""
    from pde.regularization import apply_permutation_symmetry
    from pde.mesh_generation import generate_s1_bundle_mesh

    # Equal mass system
    masses = np.array([1.0, 1.0, 1.0])

    mesh = generate_s1_bundle_mesh(
        masses=masses,
        energy=-1.0,
        L_magnitude=1.0,
        resolution={'shape_coarse': 10, 'shape_fine': 50, 'fiber': 8}
    )

    # Create asymmetric test field
    n = mesh.dimension
    N = mesh.num_points
    K_asym = np.random.randn(n, N)

    # Apply projection
    K_sym = apply_permutation_symmetry(K_asym, mesh, masses)

    # Verify symmetry
    perm_group = generate_permutation_group(3)
    for perm in perm_group:
        K_permuted = permute_killing_field(K_sym, mesh, perm)
        assert np.allclose(K_permuted, K_sym, rtol=1e-3)
```

**Completion Criteria**:
- [ ] Permutation group generation works
- [ ] Projection onto symmetric subspace implemented
- [ ] Test case verifies symmetry property
- [ ] Integrated into regularization pipeline

---

## Gap H2: Geometric Invariant Coordinate Transforms
**Priority**: P1 - HIGH
**Effort**: 5 hours
**File**: `src/python/symbolic/geometric_invariants.py`

### Current State
```python
# Line 98
# TODO: Implement Jacobi → Cartesian transformation

# Line 105
# TODO: Implement proper reconstruction
```

### Problem
Need to convert geometric invariants between coordinate systems for cross-validation.

### Solution

**Step 1**: Implement Jacobi to Cartesian:
```python
def jacobi_to_cartesian_positions(
    jacobi_coords: np.ndarray,
    masses: np.ndarray
) -> np.ndarray:
    """
    Convert Jacobi coordinates to Cartesian positions.

    Args:
        jacobi_coords: (3, n) for planar or (3, 3, n) for 3D
            [ρ_1, ρ_2, R_CM] where:
            - ρ_1: relative position of body 2 w.r.t. body 1
            - ρ_2: relative position of body 3 w.r.t. CoM of 1,2
            - R_CM: center of mass position
        masses: (3,) particle masses

    Returns:
        Cartesian positions: (3, 3) or (3, 3, n) [x_1, x_2, x_3]
    """
    m1, m2, m3 = masses
    M_total = m1 + m2 + m3

    # Extract Jacobi coordinates
    if jacobi_coords.ndim == 2:  # Planar
        rho1 = jacobi_coords[:, 0]  # m2 - m1
        rho2 = jacobi_coords[:, 1]  # m3 - CoM(m1, m2)
        R_CM = jacobi_coords[:, 2]  # Center of mass
    else:  # 3D
        rho1 = jacobi_coords[:, :, 0]
        rho2 = jacobi_coords[:, :, 1]
        R_CM = jacobi_coords[:, :, 2]

    # Reconstruct Cartesian positions
    # Body 1: r_1 = R_CM - (m2/M12) ρ_1 - (m3/M_total) ρ_2
    # Body 2: r_2 = R_CM + (m1/M12) ρ_1 - (m3/M_total) ρ_2
    # Body 3: r_3 = R_CM + ((m1+m2)/M_total) ρ_2

    M12 = m1 + m2

    r1 = R_CM - (m2/M12) * rho1 - (m3/M_total) * rho2
    r2 = R_CM + (m1/M12) * rho1 - (m3/M_total) * rho2
    r3 = R_CM + (M12/M_total) * rho2

    if jacobi_coords.ndim == 2:
        return np.column_stack([r1, r2, r3])
    else:
        return np.stack([r1, r2, r3], axis=-1)

def cartesian_to_jacobi_coordinates(
    positions: np.ndarray,
    masses: np.ndarray
) -> np.ndarray:
    """Inverse transformation: Cartesian → Jacobi."""
    m1, m2, m3 = masses
    M_total = m1 + m2 + m3
    M12 = m1 + m2

    # Extract positions
    if positions.ndim == 2:  # Single snapshot
        r1, r2, r3 = positions[:, 0], positions[:, 1], positions[:, 2]
    else:  # Time series
        r1, r2, r3 = positions[:, :, 0], positions[:, :, 1], positions[:, :, 2]

    # Compute Jacobi coordinates
    rho1 = r2 - r1
    R_CM = (m1*r1 + m2*r2 + m3*r3) / M_total
    R_12 = (m1*r1 + m2*r2) / M12
    rho2 = r3 - R_12

    if positions.ndim == 2:
        return np.column_stack([rho1, rho2, R_CM])
    else:
        return np.stack([rho1, rho2, R_CM], axis=-1)
```

**Step 2**: Implement shape space conversions:
```python
def shape_space_to_cartesian(
    shape_coords: np.ndarray,
    masses: np.ndarray,
    theta: float = 0.0
) -> np.ndarray:
    """
    Convert shape space coordinates to Cartesian.

    Args:
        shape_coords: (3,) array [r_12, r_23, r_31]
        masses: (3,) particle masses
        theta: Orientation angle (for S¹ bundle)

    Returns:
        Cartesian positions: (3, 2) for planar case
    """
    from ..coordinates.shape_space import shape_distances_to_cartesian_canonical

    # Use existing function
    positions = shape_distances_to_cartesian_canonical(
        r_12=shape_coords[0],
        r_23=shape_coords[1],
        r_31=shape_coords[2],
        masses=masses,
        theta=theta
    )

    return positions
```

**Step 3**: Add validation:
```python
def validate_coordinate_transform(
    original: np.ndarray,
    transformed_back: np.ndarray,
    tolerance: float = 1e-10
) -> bool:
    """
    Validate that coordinate transformation is invertible.

    Check: transform(inverse_transform(x)) ≈ x
    """
    return np.allclose(original, transformed_back, rtol=tolerance, atol=tolerance)
```

### Testing
```python
# tests/wp3/test_geometric_invariants.py
def test_jacobi_cartesian_roundtrip():
    """Test Jacobi ↔ Cartesian transformation."""
    masses = np.array([1.0, 2.0, 3.0])

    # Random Cartesian positions
    r_cart = np.random.randn(2, 3)  # 2D positions for 3 bodies

    # Convert to Jacobi
    r_jacobi = cartesian_to_jacobi_coordinates(r_cart, masses)

    # Convert back
    r_cart_reconstructed = jacobi_to_cartesian_positions(r_jacobi, masses)

    # Validate
    assert np.allclose(r_cart, r_cart_reconstructed, rtol=1e-12)

def test_shape_space_reconstruction():
    """Test shape space to Cartesian."""
    masses = np.array([1.0, 1.0, 1.0])

    # Equilateral triangle
    r_12 = r_23 = r_31 = 1.0
    shape_coords = np.array([r_12, r_23, r_31])

    # Convert to Cartesian
    positions = shape_space_to_cartesian(shape_coords, masses, theta=0.0)

    # Verify distances
    d_12 = np.linalg.norm(positions[:, 1] - positions[:, 0])
    d_23 = np.linalg.norm(positions[:, 2] - positions[:, 1])
    d_31 = np.linalg.norm(positions[:, 0] - positions[:, 2])

    assert np.isclose(d_12, r_12)
    assert np.isclose(d_23, r_23)
    assert np.isclose(d_31, r_31)
```

**Completion Criteria**:
- [ ] Jacobi ↔ Cartesian transformations implemented
- [ ] Shape space to Cartesian works
- [ ] Round-trip validation passes
- [ ] Test cases cover edge cases

---

## Gap H3: Numerical Equivalence Verification
**Priority**: P1 - HIGH
**Effort**: 3 hours
**File**: `src/python/symbolic/simplification.py`

### Current State
```python
# Line 185
numerical_equivalence=True  # TODO: Verify numerically
```

### Problem
When simplifying expressions, need to verify they're numerically equivalent to the original.

### Solution

**Step 1**: Implement verification function:
```python
def verify_numerical_equivalence(
    expr_original: sp.Expr,
    expr_simplified: sp.Expr,
    variables: List[sp.Symbol],
    n_test_points: int = 1000,
    domain: Dict[sp.Symbol, Tuple[float, float]] = None,
    tolerance: float = 1e-10
) -> Tuple[bool, float]:
    """
    Verify that simplified expression is numerically equivalent to original.

    Args:
        expr_original: Original SymPy expression
        expr_simplified: Simplified expression
        variables: List of free symbols
        n_test_points: Number of random test points
        domain: Optional domain for each variable {symbol: (min, max)}
        tolerance: Relative error tolerance

    Returns:
        (is_equivalent, max_error): True if equivalent, plus max relative error
    """
    import sympy as sp
    import numpy as np

    # Lambdify for fast evaluation
    f_original = sp.lambdify(variables, expr_original, 'numpy')
    f_simplified = sp.lambdify(variables, expr_simplified, 'numpy')

    # Generate random test points
    if domain is None:
        # Default: [-10, 10] for each variable
        domain = {var: (-10.0, 10.0) for var in variables}

    test_points = []
    for _ in range(n_test_points):
        point = {}
        for var in variables:
            low, high = domain.get(var, (-10.0, 10.0))
            point[var] = np.random.uniform(low, high)
        test_points.append(point)

    # Evaluate at test points
    errors = []
    for point in test_points:
        args = [point[var] for var in variables]

        try:
            val_orig = f_original(*args)
            val_simp = f_simplified(*args)

            # Relative error
            if abs(val_orig) > tolerance:
                rel_error = abs(val_simp - val_orig) / abs(val_orig)
            else:
                rel_error = abs(val_simp - val_orig)

            errors.append(rel_error)

        except (ValueError, ZeroDivisionError, OverflowError):
            # Skip problematic points
            continue

    if not errors:
        return False, float('inf')

    max_error = max(errors)
    is_equivalent = max_error < tolerance

    return is_equivalent, max_error
```

**Step 2**: Integrate into simplification:
```python
def simplify_with_verification(
    expr: sp.Expr,
    variables: List[sp.Symbol],
    simplify_strategy: str = 'standard',
    verify: bool = True,
    verification_tolerance: float = 1e-10
) -> Tuple[sp.Expr, dict]:
    """
    Simplify expression and verify numerical equivalence.

    Returns:
        (simplified_expr, metadata) where metadata contains:
            - 'verified': bool
            - 'max_error': float
            - 'simplification_ratio': float (complexity reduction)
    """
    # Apply simplification
    if simplify_strategy == 'standard':
        expr_simplified = sp.simplify(expr)
    elif simplify_strategy == 'aggressive':
        expr_simplified = sp.simplify(expr, rational=True, inverse=True)
    elif simplify_strategy == 'trig':
        expr_simplified = sp.trigsimp(expr)
    else:
        expr_simplified = expr

    metadata = {}

    # Complexity comparison
    complexity_orig = count_operations(expr)
    complexity_simp = count_operations(expr_simplified)
    metadata['simplification_ratio'] = 1 - (complexity_simp / complexity_orig)
    metadata['operations_original'] = complexity_orig
    metadata['operations_simplified'] = complexity_simp

    # Numerical verification
    if verify and len(variables) > 0:
        is_equivalent, max_error = verify_numerical_equivalence(
            expr,
            expr_simplified,
            variables,
            tolerance=verification_tolerance
        )
        metadata['verified'] = is_equivalent
        metadata['max_error'] = max_error

        if not is_equivalent:
            # Simplification changed numerical behavior
            print(f"Warning: Simplification changed numerical values (max error: {max_error:.2e})")
            print(f"  Original: {expr}")
            print(f"  Simplified: {expr_simplified}")
            # Return original expression
            return expr, metadata
    else:
        metadata['verified'] = None
        metadata['max_error'] = None

    return expr_simplified, metadata
```

**Step 3**: Update existing simplification calls:
```python
# In src/python/symbolic/simplification.py
# Replace line 185 with:

result, metadata = simplify_with_verification(
    expr=candidate_expr,
    variables=state_variables,
    simplify_strategy='standard',
    verify=True,
    verification_tolerance=1e-10
)

# Store metadata
candidate.metadata['simplification_verified'] = metadata['verified']
candidate.metadata['simplification_error'] = metadata['max_error']
```

### Testing
```python
# tests/wp3/test_simplification.py
def test_numerical_equivalence_verification():
    """Test that verification catches incorrect simplifications."""
    import sympy as sp

    x, y = sp.symbols('x y')

    # Case 1: Correct simplification
    expr_orig = x**2 - y**2
    expr_simp = (x-y)*(x+y)

    is_equiv, error = verify_numerical_equivalence(expr_orig, expr_simp, [x, y])
    assert is_equiv
    assert error < 1e-12

    # Case 2: Incorrect simplification
    expr_wrong = x**2 + y**2  # Different!

    is_equiv, error = verify_numerical_equivalence(expr_orig, expr_wrong, [x, y])
    assert not is_equiv
    assert error > 0.1

def test_simplify_with_verification():
    """Test integrated simplification with verification."""
    import sympy as sp

    x = sp.Symbol('x')
    expr = (x**2 + 2*x + 1) / (x + 1)

    expr_simp, metadata = simplify_with_verification(expr, [x], verify=True)

    assert metadata['verified'] is True
    assert metadata['max_error'] < 1e-10
    assert metadata['simplification_ratio'] > 0  # Should be simpler
```

**Completion Criteria**:
- [ ] `verify_numerical_equivalence()` implemented
- [ ] `simplify_with_verification()` integrated
- [ ] Test cases pass (correct and incorrect simplifications)
- [ ] Metadata includes verification results

---

## Integration and Testing

### End-to-End Test: Kepler Problem

**Purpose**: Validate full pipeline on known integrable system

```python
# tests/integration/test_wp3_kepler.py
def test_wp3_kepler_discovery():
    """
    End-to-end test: Discover integrals of Kepler problem.

    Expected results:
    - Energy E (trivial)
    - Angular momentum L (3 components)
    - Runge-Lenz vector A (3 components)
    Total: 7 integrals, 6 functionally independent
    """
    from pde.killing_solver import solve_killing_fields
    from analysis.integral_pipeline import discover_integrals_from_killing_solution

    # Kepler problem setup
    masses = np.array([1.0, 1e-6, 0.0])  # Sun + planet (test particle limit)
    energy = -0.5  # Bound orbit
    L_magnitude = 1.0

    # Solve for Killing fields
    solution = solve_killing_fields(
        manifold_type='ks_spinor',  # Use KS for Kepler
        masses=masses,
        energy=energy,
        resolution={'spinor_coarse': 20, 'spinor_fine': 100},
        field_type='vector',
        verbose=True
    )

    # Discover integrals
    result = discover_integrals_from_killing_solution(
        killing_solution=solution,
        metric_func=kepler_metric,
        hamiltonian=kepler_hamiltonian,
        masses=masses,
        test_trajectory_count=20,
        verbose=True
    )

    # Validate
    assert len(result.conserved) >= 6  # At least 6 independent integrals
    assert result.integrability_status in ['integrable', 'superintegrable']

    # Check for known integrals
    integral_names = [integral.name for integral in result.conserved]
    assert 'energy' in integral_names or 'E' in integral_names
    assert any('angular' in name.lower() for name in integral_names)

    print(f"✅ Kepler test passed: Found {len(result.conserved)} conserved integrals")
```

### Regression Test Suite

**After each fix, run**:
```bash
# Unit tests
pytest tests/wp3/test_killing_pde.py -v
pytest tests/wp3/test_system_assembly.py -v
pytest tests/wp3/test_regularization.py -v
pytest tests/wp3/test_geometric_invariants.py -v
pytest tests/wp3/test_simplification.py -v

# Integration tests
pytest tests/integration/test_wp3_kepler.py -v
pytest tests/integration/test_wp3_quick_validation.py -v

# Full suite
pytest tests/wp3/ -v
```

---

## Success Criteria (Phase 1)

### Code Quality
- [ ] Zero `NotImplementedError` in critical path (C1, C3)
- [ ] All new functions have docstrings
- [ ] Type hints on public APIs
- [ ] No lint warnings

### Functionality
- [ ] `KillingVectorPDE.solve()` executes without error
- [ ] `KillingTensorPDE.solve()` executes without error
- [ ] Tensor system assembly complete
- [ ] Permutation symmetry works for equal masses
- [ ] Coordinate transforms validated
- [ ] Simplification verification implemented

### Testing
- [ ] All unit tests pass
- [ ] Kepler problem integration test passes
- [ ] Regression tests pass (no breaks)
- [ ] Test coverage > 85% for modified modules

### Documentation
- [ ] Implementation notes updated
- [ ] API documentation generated
- [ ] Known issues documented

---

## Timeline and Milestones

### Day 1 (8 hours)
**Morning** (4h):
- Fix C1: Killing solver connection (2h)
- Write tests for C1 (1h)
- Begin C3: Tensor assembly (1h)

**Afternoon** (4h):
- Continue C3: Complete tensor assembly (4h)

**Milestone**: Can solve Killing vector PDEs end-to-end

---

### Day 2 (8 hours)
**Morning** (4h):
- Finish C3: Tensor assembly testing (2h)
- Fix H1: Permutation symmetry (2h)

**Afternoon** (4h):
- Complete H1: Testing and integration (2h)
- Fix H2: Coordinate transforms (2h)

**Milestone**: Tensor search works, symmetry projection complete

---

### Day 3 (8 hours)
**Morning** (4h):
- Complete H2: Transform validation (2h)
- Fix H3: Simplification verification (2h)

**Afternoon** (4h):
- Integration testing: Kepler problem (2h)
- Regression testing and bug fixes (2h)

**Milestone**: Full Phase 1 complete, all tests passing

---

## Next Steps After Phase 1

### Immediate
1. Update Implementation Status document
2. Run full validation on known cases
3. Begin Phase 2 (high-value features)

### Medium-term
4. Deploy on real three-body trajectories
5. Compare with WP3.2 (ML) results
6. Prepare handoff to WP3.3 (Symbolic Regression)

### Long-term
7. Optimize performance
8. Add advanced features (Phase 3)
9. Publication preparation

---

**Document Version**: 1.0
**Created**: November 22, 2025
**Status**: Ready for Implementation
**Estimated Duration**: 3 days (24 hours)
**Next Action**: Begin Day 1 implementation
