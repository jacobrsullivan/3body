"""
Levi-Civita matrix and bilinear map for KS transformation.

The Levi-Civita matrix L(u) defines the bilinear map from 4D spinors to 3D vectors:
    r = L(u) · u

where u = (u₀, u₁, u₂, u₃) ∈ ℝ⁴ and r = (x, y, z) ∈ ℝ³.

Matrix Structure:
    L(u) = ⎡ u₀  -u₁  -u₂   u₃ ⎤
           ⎢ u₁   u₀   u₃   u₂ ⎥
           ⎣ u₂  -u₃   u₀  -u₁ ⎦

Key Property: |L(u)·u|² = |u|⁴
"""

import numpy as np
from typing import Union


def levi_civita_matrix(u: np.ndarray) -> np.ndarray:
    """
    Construct the 3×4 Levi-Civita matrix L(u).

    Args:
        u: 4D spinor vector (u₀, u₁, u₂, u₃)

    Returns:
        L(u): 3×4 matrix

    Example:
        >>> u = np.array([1.0, 0.0, 0.0, 0.0])
        >>> L = levi_civita_matrix(u)
        >>> r = L @ u
        >>> # r = (1, 0, 0)
    """
    if len(u) != 4:
        raise ValueError(f"Spinor must be 4D, got {len(u)}")

    u0, u1, u2, u3 = u

    L = np.array([
        [ u0, -u1, -u2,  u3],
        [ u1,  u0,  u3,  u2],
        [ u2, -u3,  u0, -u1]
    ])

    return L


def levi_civita_map(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """
    Bilinear map: r = L(u) · v.

    For KS transform, typically v = u, giving r = L(u) · u.

    Args:
        u: First 4D spinor
        v: Second 4D spinor

    Returns:
        r: 3D vector

    Key Property:
        When v = u: |r|² = |u|⁴ ⟹ |r| = |u|²
    """
    L = levi_civita_matrix(u)
    r = L @ v
    return r


def inverse_levi_civita_map(
    r: np.ndarray,
    sign: int = 1,
    method: str = "geometric"
) -> np.ndarray:
    """
    Inverse KS transform: find u such that L(u)·u = r.

    Note: Inverse is NOT unique! Given r, there are infinitely many u.
    This function returns one particular choice.

    Args:
        r: 3D position vector (x, y, z)
        sign: ±1 determines branch (default: +1)
        method: Inversion method ('geometric' or 'algebraic')

    Returns:
        u: 4D spinor (one of infinitely many solutions)

    Algorithm (geometric method):
        Choose u₀ = √(|r| + x) / √2 (one branch)
        Then solve for u₁, u₂, u₃ from bilinear equations

    Reference:
        Stiefel & Scheifele, "Linear and Regular Celestial Mechanics" (1971)
    """
    x, y, z = r
    r_mag = np.linalg.norm(r)

    if r_mag < 1e-14:
        # At origin, choose u = 0
        return np.zeros(4)

    if method == "geometric":
        # Geometric construction (Stiefel-Scheifele)
        # Choose u₀ based on first component
        if x >= 0:
            u0 = np.sqrt((r_mag + x) / 2)
            u1 = sign * y / (2 * u0) if abs(u0) > 1e-14 else 0
            u2 = sign * z / (2 * u0) if abs(u0) > 1e-14 else 0
            u3 = 0.0
        else:
            # Use different parametrization when x < 0
            u1 = np.sqrt((r_mag - x) / 2)
            u0 = sign * y / (2 * u1) if abs(u1) > 1e-14 else 0
            u2 = 0.0
            u3 = sign * z / (2 * u1) if abs(u1) > 1e-14 else 0

        u = np.array([u0, u1, u2, u3])

    elif method == "algebraic":
        # Alternative: use quaternion square root
        # This is more robust but requires quaternion algebra
        raise NotImplementedError("Algebraic method not yet implemented")

    else:
        raise ValueError(f"Unknown method: {method}")

    return u


def validate_bilinear_relation(
    u: np.ndarray,
    r: np.ndarray,
    tolerance: float = 1e-12
) -> bool:
    """
    Verify r = L(u) · u and |r|² = |u|⁴.

    Args:
        u: 4D spinor
        r: 3D position
        tolerance: Numerical tolerance

    Returns:
        True if bilinear relation holds
    """
    # Compute r from u
    r_computed = levi_civita_map(u, u)

    # Check r = L(u)·u
    error_position = np.linalg.norm(r - r_computed)

    # Check |r|² = |u|⁴
    r_mag_squared = np.dot(r, r)
    u_mag_squared = np.dot(u, u)
    u_mag_fourth = u_mag_squared ** 2

    error_norm = abs(r_mag_squared - u_mag_fourth)

    return (error_position < tolerance and error_norm < tolerance)


def levi_civita_matrix_transpose(u: np.ndarray) -> np.ndarray:
    """
    Transpose of Levi-Civita matrix: L^T(u).

    Used in velocity transformation: v = 2 L^T(u) · u'.

    Args:
        u: 4D spinor

    Returns:
        L^T(u): 4×3 matrix
    """
    return levi_civita_matrix(u).T


def spinor_product(u: np.ndarray, v: np.ndarray) -> float:
    """
    Spinor inner product: ⟨u, v⟩ = u · v (Euclidean).

    Args:
        u, v: 4D spinors

    Returns:
        Inner product
    """
    return np.dot(u, v)


def spinor_norm(u: np.ndarray) -> float:
    """
    Spinor norm: ‖u‖ = √(u·u).

    Physical meaning: r = ‖u‖²

    Args:
        u: 4D spinor

    Returns:
        Norm
    """
    return np.sqrt(spinor_product(u, u))
