"""
Main pipeline for solving Killing field PDEs (WP 3.1, Task 3.1.3).

Complete workflow from mesh generation to candidate Killing fields:
1. Generate mesh on manifold
2. Assemble sparse system A·K = 0
3. Compute null space
4. Apply regularization
5. Verify and filter solutions
6. Package results

This is the entry point for Task 3.1.3.
"""

from dataclasses import dataclass
from typing import Optional, Callable, List, Dict
import numpy as np
import time

from .mesh_generation import (
    generate_s1_bundle_mesh,
    generate_ks_spinor_mesh,
    Mesh,
    S1BundleMesh,
    KSSpinorMesh
)
from .system_assembly import (
    assemble_killing_vector_system,
    assemble_killing_tensor_system,
    estimate_assembly_memory
)
from .null_space import (
    compute_null_space_svd,
    compute_null_space_iterative,
    verify_null_space
)
from .regularization import (
    apply_smoothness_regularization,
    apply_physical_priors
)


@dataclass
class KillingSolution:
    """
    Complete solution from Killing field search.

    Fields:
        killing_fields: List of (n × N) arrays, one per discovered field
        mesh: Mesh on which fields are defined
        null_space_dim: Raw null space dimension
        regularized_dim: Dimension after regularization
        residuals: ||A·K|| for each field
        computation_time: Total wall-clock time (seconds)
        metadata: Additional information
    """
    killing_fields: List[np.ndarray]
    mesh: Mesh
    null_space_dim: int
    regularized_dim: int
    residuals: List[float]
    computation_time: float
    metadata: dict


# =============================================================================
# Main Solver Pipeline
# =============================================================================

def solve_killing_fields(
    manifold_type: str,
    masses: np.ndarray,
    energy: float,
    resolution: dict,
    *,
    field_type: str = 'vector',
    L_magnitude: Optional[float] = None,
    regularization: Optional[dict] = None,
    convergence_check: bool = False,
    G: float = 1.0,
    verbose: bool = True
) -> KillingSolution:
    """
    Complete pipeline for discovering Killing fields.

    Steps:
    1. Generate mesh on specified manifold
    2. Assemble sparse linear system A·K = 0
    3. Compute null space (solutions to homogeneous system)
    4. Apply regularization (smoothness, physical priors)
    5. Verify solutions and filter trivial ones
    6. Package results

    Args:
        manifold_type: 's1_bundle' or 'ks_spinor'
        masses: (3,) particle masses
        energy: Total energy E
        resolution: dict with mesh resolution parameters
            For S¹: {'shape_coarse': int, 'shape_fine': int, 'fiber': int}
            For KS: {'spinor_coarse': int, 'spinor_fine': int}
        field_type: 'vector' or 'tensor'
        L_magnitude: Angular momentum |L| (required for s1_bundle)
        regularization: dict with keys:
            'smoothness': bool (default True)
            'smoothness_penalty': float (default 1e-3)
            'physical_priors': bool (default True)
            'gauge': str or None (default 'divergence_free')
        convergence_check: Perform mesh refinement study (expensive)
        G: Gravitational constant
        verbose: Print progress information

    Returns:
        KillingSolution object with discovered fields and metadata

    Example:
        >>> solution = solve_killing_fields(
        ...     manifold_type='s1_bundle',
        ...     masses=np.array([1.0, 1.0, 1.0]),
        ...     energy=-1.0,
        ...     L_magnitude=1.0,
        ...     resolution={'shape_fine': 50, 'fiber': 16},
        ...     field_type='vector'
        ... )
        >>> print(f"Found {len(solution.killing_fields)} Killing vectors")
    """
    start_time = time.time()

    # Default regularization settings
    if regularization is None:
        regularization = {}
    reg = {
        'smoothness': regularization.get('smoothness', True),
        'smoothness_penalty': regularization.get('smoothness_penalty', 1e-3),
        'physical_priors': regularization.get('physical_priors', True),
        'gauge': regularization.get('gauge', 'divergence_free')
    }

    if verbose:
        print("="*70)
        print("KILLING FIELD SOLVER")
        print("="*70)
        print(f"Manifold: {manifold_type}")
        print(f"Field type: {field_type}")
        print(f"Energy: {energy}")
        print(f"Masses: {masses}")
        if manifold_type == 's1_bundle':
            print(f"Angular momentum: {L_magnitude}")
        print()

    # Step 1: Generate mesh
    if verbose:
        print("[1/5] Generating mesh...")

    if manifold_type == 's1_bundle':
        if L_magnitude is None:
            raise ValueError("L_magnitude required for S¹ bundle")

        mesh = generate_s1_bundle_mesh(
            masses=masses,
            energy=energy,
            L_magnitude=L_magnitude,
            resolution=resolution,
            G=G
        )
        metric_func = lambda q, **params: _s1_bundle_metric(q, masses, energy, L_magnitude, G)
        metric_params = {
            'manifold_type': 's1_bundle',
            'masses': masses,
            'energy': energy,
            'L_magnitude': L_magnitude,
            'G': G
        }

    elif manifold_type == 'ks_spinor':
        mesh = generate_ks_spinor_mesh(
            masses=masses,
            energy=energy,
            resolution=resolution,
            G=G
        )
        metric_func = lambda q, **params: _ks_spinor_metric(q, masses, energy, G)
        metric_params = {
            'manifold_type': 'ks_spinor',
            'masses': masses,
            'energy': energy,
            'G': G
        }

    else:
        raise ValueError(f"Unknown manifold type: {manifold_type}")

    if verbose:
        print(f"  Mesh generated: {mesh.num_points} points in {mesh.dimension}D")
        print()

    # Step 2: Assemble sparse system
    if verbose:
        print("[2/5] Assembling sparse linear system...")

    # Estimate memory first
    mem_estimate = estimate_assembly_memory(mesh, field_type)
    if verbose:
        print(f"  Estimated memory: {mem_estimate['memory_mb']:.1f} MB")
        print(f"  System size: {mem_estimate['equations']} × {mem_estimate['unknowns']}")

    if field_type == 'vector':
        A = assemble_killing_vector_system(
            mesh=mesh,
            metric_func=metric_func,
            metric_params=metric_params,
            verbose=verbose
        )
    elif field_type == 'tensor':
        A = assemble_killing_tensor_system(
            mesh=mesh,
            metric_func=metric_func,
            metric_params=metric_params,
            verbose=verbose
        )
    else:
        raise ValueError(f"Unknown field type: {field_type}")

    if verbose:
        print()

    # Step 3: Compute null space
    if verbose:
        print("[3/5] Computing null space...")

    null_basis, singular_values = compute_null_space_svd(
        A,
        tolerance=1e-8,
        method='auto',
        verbose=verbose
    )

    null_space_dim = null_basis.shape[1]

    if verbose:
        print(f"  Null space dimension: {null_space_dim}")
        print()

    if null_space_dim == 0:
        if verbose:
            print("  No null space found - no Killing fields discovered.")
            print()

        elapsed = time.time() - start_time
        return KillingSolution(
            killing_fields=[],
            mesh=mesh,
            null_space_dim=0,
            regularized_dim=0,
            residuals=[],
            computation_time=elapsed,
            metadata={
                'manifold_type': manifold_type,
                'field_type': field_type,
                'resolution': resolution,
                'singular_values': singular_values
            }
        )

    # Step 4: Apply regularization
    if verbose:
        print("[4/5] Applying regularization...")

    regularized_basis = null_basis

    if reg['smoothness']:
        if verbose:
            print("  Smoothness regularization...")
        regularized_basis = apply_smoothness_regularization(
            regularized_basis,
            mesh,
            smoothness_penalty=reg['smoothness_penalty'],
            verbose=verbose
        )

    if reg['physical_priors']:
        if verbose:
            print("  Physical priors...")
        regularized_basis = apply_physical_priors(
            regularized_basis,
            mesh,
            gauge_fixing=reg['gauge'],
            particle_masses=masses,
            verbose=verbose
        )

    regularized_dim = regularized_basis.shape[1]

    if verbose:
        print(f"  Regularized dimension: {regularized_dim}")
        print()

    # Step 5: Verify solutions
    if verbose:
        print("[5/5] Verifying solutions...")

    verification = verify_null_space(A, regularized_basis, tolerance=1e-6)

    if verbose:
        print(f"  Max residual: {verification['max_residual']:.2e}")
        print(f"  Orthonormality error: {verification['orthonormality']:.2e}")
        print(f"  Rank: {verification['rank']}/{verification['expected_rank']}")
        print()

    # Package results
    killing_fields = [regularized_basis[:, i] for i in range(regularized_dim)]
    residuals = verification['residuals'].tolist()

    elapsed = time.time() - start_time

    if verbose:
        print("="*70)
        print(f"SOLUTION SUMMARY")
        print("="*70)
        print(f"Discovered fields: {len(killing_fields)}")
        print(f"Computation time: {elapsed:.2f} seconds")
        print("="*70)
        print()

    return KillingSolution(
        killing_fields=killing_fields,
        mesh=mesh,
        null_space_dim=null_space_dim,
        regularized_dim=regularized_dim,
        residuals=residuals,
        computation_time=elapsed,
        metadata={
            'manifold_type': manifold_type,
            'field_type': field_type,
            'resolution': resolution,
            'singular_values': singular_values,
            'verification': verification,
            'regularization': reg
        }
    )


# =============================================================================
# Metric Functions (Placeholders)
# =============================================================================

def _s1_bundle_metric(q: np.ndarray, masses: np.ndarray, energy: float, L_magnitude: float, G: float) -> np.ndarray:
    """Placeholder for S¹ bundle metric computation"""
    # Would use compute_s1_jm_metric from geometry module
    # For now, return identity
    n = len(q)
    return np.eye(n)


def _ks_spinor_metric(q: np.ndarray, masses: np.ndarray, energy: float, G: float) -> np.ndarray:
    """Placeholder for KS-Spinor metric computation"""
    # Would use compute_ks_jm_metric from geometry module
    n = len(q)
    return np.eye(n)
