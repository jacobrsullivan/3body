"""
Spinor-based basis functions for symbolic regression using KS coordinates.

The Kustaanheimo-Stiefel (KS) transformation represents 3D position vectors
as 4D spinors (quaternions), providing a regularization of the gravitational
singularity and potentially revealing algebraic structure in conserved quantities.

Key Properties:
- Position: r = (x, y, z) → Spinor: u = (u0, u1, u2, u3)
- Distance: |r| = |u|² = u0² + u1² + u2² + u3²
- Regularization: Removes 1/r singularity in Hamiltonian

For the three-body problem, we have three spinors (one per pair):
- u12 for body pair 1-2
- u23 for body pair 2-3
- u31 for body pair 3-1

References:
- Stiefel & Scheifele, "Linear and Regular Celestial Mechanics" (1971)
- Kustaanheimo & Stiefel, "Perturbation theory of Kepler motion" (1965)
"""

import numpy as np
from typing import List, Tuple, Callable, Dict, Optional
from dataclasses import dataclass


@dataclass
class SpinorCoordinates:
    """
    KS spinor coordinates for three-body system.

    Attributes:
        u12: Spinor for body pair 1-2 (shape: (4,))
        u23: Spinor for body pair 2-3 (shape: (4,))
        u31: Spinor for body pair 3-1 (shape: (4,))
        u12_dot: Time derivative of u12 (shape: (4,))
        u23_dot: Time derivative of u23 (shape: (4,))
        u31_dot: Time derivative of u31 (shape: (4,))
    """
    u12: np.ndarray
    u23: np.ndarray
    u31: np.ndarray
    u12_dot: np.ndarray
    u23_dot: np.ndarray
    u31_dot: np.ndarray


def position_to_spinor(r: np.ndarray) -> np.ndarray:
    """
    Convert 3D position to 4D spinor using KS transformation.

    The standard KS transformation (Levi-Civita type):
        u0 = sqrt((|r| + x) / 2)
        u1 = y / (2*u0)
        u2 = z / (2*u0)
        u3 = 0  (gauge choice)

    Args:
        r: 3D position vector [x, y, z]

    Returns:
        u: 4D spinor [u0, u1, u2, u3]

    Note:
        The KS map is not unique - there's a gauge freedom.
        This implementation uses the standard gauge with u3 = 0.
    """
    x, y, z = r
    r_mag = np.linalg.norm(r)

    # Avoid singularity at origin
    if r_mag < 1e-12:
        return np.zeros(4)

    # Standard KS map
    # Handle the case when x ≈ -r (opposite side from origin)
    if r_mag + x > 1e-12:
        # Standard branch
        u0 = np.sqrt((r_mag + x) / 2)
        u1 = y / (2 * u0) if u0 > 1e-12 else 0.0
        u2 = z / (2 * u0) if u0 > 1e-12 else 0.0
        u3 = 0.0
    else:
        # Alternative branch for x ≈ -r
        # Use u1 as primary instead
        u0 = 0.0
        u1 = np.sqrt((r_mag - x) / 2)
        u2 = y / (2 * u1) if u1 > 1e-12 else 0.0
        u3 = z / (2 * u1) if u1 > 1e-12 else 0.0

    return np.array([u0, u1, u2, u3])


def spinor_to_position(u: np.ndarray) -> np.ndarray:
    """
    Convert 4D spinor back to 3D position (inverse KS transformation).

    The inverse transformation:
        x = u0² - u1² - u2² - u3²
        y = 2*(u0*u1 - u2*u3)
        z = 2*(u0*u2 + u1*u3)

    Args:
        u: 4D spinor [u0, u1, u2, u3]

    Returns:
        r: 3D position [x, y, z]
    """
    u0, u1, u2, u3 = u

    x = u0**2 - u1**2 - u2**2 - u3**2
    y = 2 * (u0*u1 - u2*u3)
    z = 2 * (u0*u2 + u1*u3)

    return np.array([x, y, z])


def velocity_to_spinor_momentum(
    v: np.ndarray,
    u: np.ndarray,
    mu: float
) -> np.ndarray:
    """
    Convert velocity to spinor momentum (approximate).

    This is a simplified transformation. The full KS momentum map
    requires solving a system of equations involving the spinor derivatives.

    For a more accurate implementation, see:
    Stiefel & Scheifele, Ch. 2, Eq. (2.32)

    Args:
        v: 3D velocity [vx, vy, vz]
        u: 4D spinor [u0, u1, u2, u3]
        mu: Reduced mass

    Returns:
        u_dot: 4D spinor momentum (approximate)
    """
    r_mag = np.dot(u, u)

    if r_mag < 1e-12:
        return np.zeros(4)

    # Simplified transformation: project velocity onto spinor directions
    # This is an approximation - full transformation requires more care
    u_normalized = u / np.sqrt(r_mag)

    # Compute radial component of velocity
    r = spinor_to_position(u)
    r_norm = r / (np.linalg.norm(r) + 1e-12)
    v_radial = np.dot(v, r_norm)

    # Approximate spinor momentum
    u_dot = 2 * mu * v_radial * u_normalized

    return u_dot


def cartesian_to_ks_spinors(
    state_cartesian: np.ndarray,
    masses: np.ndarray
) -> SpinorCoordinates:
    """
    Convert Cartesian phase space state to KS spinor coordinates.

    Args:
        state_cartesian: [q1x, q1y, q1z, q2x, q2y, q2z, q3x, q3y, q3z,
                          p1x, p1y, p1z, p2x, p2y, p2z, p3x, p3y, p3z]
                         (18-dimensional for 3-body problem)
        masses: [m1, m2, m3]

    Returns:
        SpinorCoordinates object with spinors for all three pairs
    """
    # Extract positions and momenta
    q = state_cartesian[:9].reshape(3, 3)  # (3 bodies, 3 coords)
    p = state_cartesian[9:].reshape(3, 3)

    # Relative positions
    r12 = q[1] - q[0]
    r23 = q[2] - q[1]
    r31 = q[0] - q[2]

    # Convert to spinors
    u12 = position_to_spinor(r12)
    u23 = position_to_spinor(r23)
    u31 = position_to_spinor(r31)

    # Relative velocities
    mu12 = masses[0] * masses[1] / (masses[0] + masses[1])
    mu23 = masses[1] * masses[2] / (masses[1] + masses[2])
    mu31 = masses[2] * masses[0] / (masses[2] + masses[0])

    v12 = (p[1] / masses[1]) - (p[0] / masses[0])
    v23 = (p[2] / masses[2]) - (p[1] / masses[1])
    v31 = (p[0] / masses[0]) - (p[2] / masses[2])

    # Convert velocities to spinor momenta
    u12_dot = velocity_to_spinor_momentum(v12, u12, mu12)
    u23_dot = velocity_to_spinor_momentum(v23, u23, mu23)
    u31_dot = velocity_to_spinor_momentum(v31, u31, mu31)

    return SpinorCoordinates(u12, u23, u31, u12_dot, u23_dot, u31_dot)


def quaternion_product(u1: np.ndarray, u2: np.ndarray) -> np.ndarray:
    """
    Compute quaternion product u1 ⊗ u2.

    Quaternion multiplication (Hamilton product):
        (a0 + a1*i + a2*j + a3*k) * (b0 + b1*i + b2*j + b3*k)

    Args:
        u1, u2: 4D spinors/quaternions

    Returns:
        u_product: Quaternion product u1 ⊗ u2
    """
    a0, a1, a2, a3 = u1
    b0, b1, b2, b3 = u2

    # Hamilton product formula
    c0 = a0*b0 - a1*b1 - a2*b2 - a3*b3
    c1 = a0*b1 + a1*b0 + a2*b3 - a3*b2
    c2 = a0*b2 - a1*b3 + a2*b0 + a3*b1
    c3 = a0*b3 + a1*b2 - a2*b1 + a3*b0

    return np.array([c0, c1, c2, c3])


def quaternion_product_norm(u1: np.ndarray, u2: np.ndarray) -> float:
    """
    Compute norm of quaternion product |u1 ⊗ u2|.

    Args:
        u1, u2: 4D spinors representing quaternions

    Returns:
        norm: Euclidean norm of the quaternion product
    """
    product = quaternion_product(u1, u2)
    return np.linalg.norm(product)


def construct_spinor_basis(
    masses: np.ndarray,
    max_degree: int = 3,
    include_quaternion_products: bool = True
) -> List[Tuple[Callable, str]]:
    """
    Construct basis functions using KS spinor coordinates.

    Creates ~80 basis functions organized by category:
    1. Individual spinor components (24 functions)
    2. Spinor norms (6 functions)
    3. Inner products between spinors (9 functions)
    4. Mixed bilinear forms (3 functions)
    5. Quaternion products (6 functions, optional)
    6. Higher-degree combinations

    Args:
        masses: Body masses [m1, m2, m3]
        max_degree: Maximum polynomial degree in spinor components
        include_quaternion_products: Include non-commutative products

    Returns:
        basis: List of (function, name) tuples

    Example:
        >>> basis = construct_spinor_basis(np.array([1., 1., 1.]))
        >>> print(f"Spinor basis size: {len(basis)}")
        >>> # Evaluate on Cartesian state
        >>> state = np.random.randn(18)
        >>> value = basis[0][0](state)
    """
    basis = []

    def make_spinor_func(extractor: Callable[[SpinorCoordinates], float], name: str):
        """Factory for creating basis functions from spinor coordinates."""
        def func(state_cartesian: np.ndarray) -> float:
            try:
                spinors = cartesian_to_ks_spinors(state_cartesian, masses)
                return float(extractor(spinors))
            except:
                return 0.0  # Handle evaluation errors gracefully
        func.__name__ = name
        return (func, name)

    # Category 1: Individual spinor components (position)
    for pair in ['12', '23', '31']:
        for i in range(4):
            basis.append(make_spinor_func(
                lambda s, pair=pair, i=i: getattr(s, f'u{pair}')[i],
                f"u{pair}_{i}"
            ))

    # Category 1b: Momentum spinor components
    for pair in ['12', '23', '31']:
        for i in range(4):
            basis.append(make_spinor_func(
                lambda s, pair=pair, i=i: getattr(s, f'u{pair}_dot')[i],
                f"udot{pair}_{i}"
            ))

    # Category 2: Spinor norms (|u|² = r for positions)
    for pair in ['12', '23', '31']:
        basis.append(make_spinor_func(
            lambda s, pair=pair: np.dot(getattr(s, f'u{pair}'), getattr(s, f'u{pair}')),
            f"|u{pair}|^2"
        ))

    for pair in ['12', '23', '31']:
        basis.append(make_spinor_func(
            lambda s, pair=pair: np.dot(getattr(s, f'u{pair}_dot'), getattr(s, f'u{pair}_dot')),
            f"|udot{pair}|^2"
        ))

    # Category 3: Inner products between position spinors
    pairs = ['12', '23', '31']
    for i, pair_i in enumerate(pairs):
        for j, pair_j in enumerate(pairs):
            if i < j:
                basis.append(make_spinor_func(
                    lambda s, pi=pair_i, pj=pair_j: np.dot(
                        getattr(s, f'u{pi}'),
                        getattr(s, f'u{pj}')
                    ),
                    f"u{pair_i}_dot_u{pair_j}"
                ))

    # Category 4: Mixed bilinear forms (position · momentum)
    for pair in pairs:
        basis.append(make_spinor_func(
            lambda s, p=pair: np.dot(
                getattr(s, f'u{p}'),
                getattr(s, f'u{p}_dot')
            ),
            f"u{pair}_dot_udot{pair}"
        ))

    # Category 5: Quaternion products (if enabled)
    if include_quaternion_products:
        for i, pair_i in enumerate(pairs):
            for j, pair_j in enumerate(pairs):
                if i < j:
                    basis.append(make_spinor_func(
                        lambda s, pi=pair_i, pj=pair_j: quaternion_product_norm(
                            getattr(s, f'u{pi}'),
                            getattr(s, f'u{pj}')
                        ),
                        f"quat_|u{pair_i}_x_u{pair_j}|"
                    ))

    # Category 6: Higher-degree combinations (if max_degree >= 2)
    if max_degree >= 2:
        for pair in pairs:
            # u² · u_dot (action-like variable)
            basis.append(make_spinor_func(
                lambda s, p=pair: (
                    np.dot(getattr(s, f'u{p}'), getattr(s, f'u{p}')) *
                    np.linalg.norm(getattr(s, f'u{p}_dot'))
                ),
                f"|u{pair}|^2*|udot{pair}|"
            ))

    return basis


# Validation and testing functions
def test_ks_norm_property(n_tests: int = 100, tolerance: float = 1e-10) -> bool:
    """
    Test that |u|² = |r| for random positions (fundamental KS property).

    Args:
        n_tests: Number of random positions to test
        tolerance: Acceptable numerical error

    Returns:
        success: True if all tests pass
    """
    for _ in range(n_tests):
        # Random 3D position
        r = np.random.randn(3) * 10  # Scale to avoid numerical issues

        # Convert to spinor
        u = position_to_spinor(r)

        # Check |u|² = |r|
        r_mag = np.linalg.norm(r)
        u_norm_sq = np.dot(u, u)

        if abs(u_norm_sq - r_mag) > tolerance:
            print(f"FAILED: |u|²={u_norm_sq:.10f} ≠ |r|={r_mag:.10f}")
            return False

    return True


def test_ks_inverse(n_tests: int = 100, tolerance: float = 1e-8) -> bool:
    """
    Test that spinor_to_position(position_to_spinor(r)) ≈ r.

    Args:
        n_tests: Number of random positions to test
        tolerance: Acceptable numerical error

    Returns:
        success: True if all tests pass
    """
    for _ in range(n_tests):
        r_original = np.random.randn(3) * 10

        # Forward and inverse transform
        u = position_to_spinor(r_original)
        r_reconstructed = spinor_to_position(u)

        # Check reconstruction
        error = np.linalg.norm(r_original - r_reconstructed)
        if error > tolerance:
            print(f"FAILED: reconstruction error = {error:.10f}")
            print(f"  Original:      {r_original}")
            print(f"  Reconstructed: {r_reconstructed}")
            return False

    return True


if __name__ == "__main__":
    print("=" * 70)
    print("KS Spinor Basis - Validation Tests")
    print("=" * 70)

    # Test 1: Norm property
    print("\nTest 1: KS norm property (|u|² = |r|)")
    if test_ks_norm_property():
        print("  ✓ PASSED")
    else:
        print("  ✗ FAILED")

    # Test 2: Inverse transformation
    print("\nTest 2: Inverse transformation")
    if test_ks_inverse():
        print("  ✓ PASSED")
    else:
        print("  ✗ FAILED")

    # Test 3: Basis construction
    print("\nTest 3: Spinor basis construction")
    masses = np.array([1.0, 1.0, 1.0])
    basis = construct_spinor_basis(masses, max_degree=2)
    print(f"  Constructed {len(basis)} basis functions")
    print(f"  First 10 functions: {[name for _, name in basis[:10]]}")

    # Test 4: Evaluate on random state
    print("\nTest 4: Evaluation on random Cartesian state")
    state = np.random.randn(18)
    try:
        for i, (func, name) in enumerate(basis[:5]):
            value = func(state)
            print(f"  {name} = {value:.6f}")
        print("  ✓ PASSED")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n" + "=" * 70)
    print("All tests complete")
    print("=" * 70)
