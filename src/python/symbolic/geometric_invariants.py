"""
Geometric invariant quantities for three-body problem (Task 3.3.2 support).

This module computes coordinate-independent geometric quantities that
serve as natural building blocks for conserved integrals:

- Mutual distances: r_ij
- Relative velocities: v_ij
- Radial velocities: r_ij · v_ij / |r_ij|
- Angular momenta: r_ij × v_ij
- Shape-space coordinates
- Moments of inertia

These quantities are invariant under:
- Translations (center of mass)
- Rotations (orientation)
- Time reversal (for appropriate combinations)

Using geometric invariants ensures discovered integrals are physically meaningful.

References:
- Montgomery, "The N-body problem" (2001)
- Albouy & Chenciner, "Le problème des n corps" (1998)
"""

import numpy as np
from typing import Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class GeometricQuantities:
    """
    Container for geometric invariant quantities of 3-body system.

    Attributes:
        distances: Mutual distances [r12, r23, r31]
        velocities_rel: Relative velocities (3, 3) - v_ij vectors
        radial_velocities: Radial components of relative velocities (3,)
        angular_momenta: Angular momentum vectors per pair (3, 3)
        total_angular_momentum: Total L vector (3,)
        moment_of_inertia: Scalar moment of inertia
        shape_coords: Shape space coordinates (if applicable)
    """
    distances: np.ndarray
    velocities_rel: np.ndarray
    radial_velocities: np.ndarray
    angular_momenta: np.ndarray
    total_angular_momentum: np.ndarray
    moment_of_inertia: float
    shape_coords: Optional[np.ndarray] = None


def extract_positions_velocities_3body(
    state: np.ndarray,
    masses: np.ndarray,
    coordinate_type: str = "jacobi"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract 3D positions and velocities from phase space state.

    Args:
        state: Phase space state vector
        masses: Three body masses [m1, m2, m3]
        coordinate_type: Type of coordinates ('jacobi', 'cartesian', 'relative')

    Returns:
        positions: (3, 3) array of positions [r1, r2, r3]
        velocities: (3, 3) array of velocities [v1, v2, v3]

    Note:
        For Jacobi coordinates, this performs inverse transformation.
        For relative coordinates, reconstructs absolute positions.
    """
    n = len(state) // 2
    q = state[:n]
    v = state[n:]

    if coordinate_type == "cartesian":
        # Direct extraction for 3D: [x1,y1,z1, x2,y2,z2, x3,y3,z3]
        if n == 9:
            positions = q.reshape(3, 3)
            velocities = v.reshape(3, 3)
        elif n == 6:  # Planar
            positions = np.zeros((3, 3))
            positions[:, :2] = q.reshape(3, 2)
            velocities = np.zeros((3, 3))
            velocities[:, :2] = v.reshape(3, 2)
        else:
            raise ValueError(f"Unexpected dimension for cartesian: {n}")

    elif coordinate_type == "jacobi":
        # Jacobi coordinates: Transform to Cartesian
        # Standard definition:
        #   rho1 = r2 - r1 (relative position of body 2 w.r.t. body 1)
        #   rho2 = r3 - R_12 (position of body 3 w.r.t. CoM of 1,2)
        #   R_CM = (m1*r1 + m2*r2 + m3*r3) / M_total

        m1, m2, m3 = masses
        M_total = m1 + m2 + m3
        M12 = m1 + m2

        if n == 9:  # 3D Jacobi
            rho1 = q[:3]  # r2 - r1
            rho2 = q[3:6]  # r3 - CoM(1,2)
            R_CM = q[6:9]  # Center of mass

            v_rho1 = v[:3]
            v_rho2 = v[3:6]
            v_CM = v[6:9]

        elif n == 6:  # Planar Jacobi
            rho1 = np.append(q[:2], 0)
            rho2 = np.append(q[2:4], 0)
            R_CM = np.append(q[4:6], 0)

            v_rho1 = np.append(v[:2], 0)
            v_rho2 = np.append(v[2:4], 0)
            v_CM = np.append(v[4:6], 0)
        else:
            raise ValueError(f"Unexpected dimension for jacobi: {n}")

        # Inverse transformation:
        # r1 = R_CM - (m2/M12) * rho1 - (m3/M_total) * rho2
        # r2 = R_CM + (m1/M12) * rho1 - (m3/M_total) * rho2
        # r3 = R_CM + (M12/M_total) * rho2

        r1 = R_CM - (m2/M12) * rho1 - (m3/M_total) * rho2
        r2 = R_CM + (m1/M12) * rho1 - (m3/M_total) * rho2
        r3 = R_CM + (M12/M_total) * rho2

        positions = np.array([r1, r2, r3])

        # Same transformation for velocities
        v1 = v_CM - (m2/M12) * v_rho1 - (m3/M_total) * v_rho2
        v2 = v_CM + (m1/M12) * v_rho1 - (m3/M_total) * v_rho2
        v3 = v_CM + (M12/M_total) * v_rho2

        velocities = np.array([v1, v2, v3])

    elif coordinate_type == "relative":
        # Relative coordinates: r1 at origin (COM frame), r2, r3 given
        # This assumes center of mass frame: m1*r1 + m2*r2 + m3*r3 = 0

        m1, m2, m3 = masses
        M_total = m1 + m2 + m3

        if n == 6:  # 3D relative (r2, r3 as 3-vectors)
            r2 = q[:3]
            r3 = q[3:6]
            # Solve for r1 from COM constraint
            r1 = -(m2*r2 + m3*r3) / m1

            v2 = v[:3]
            v3 = v[3:6]
            v1 = -(m2*v2 + m3*v3) / m1

            positions = np.array([r1, r2, r3])
            velocities = np.array([v1, v2, v3])

        elif n == 4:  # Planar relative
            r2 = np.append(q[:2], 0)
            r3 = np.append(q[2:4], 0)
            r1 = -(m2*r2 + m3*r3) / m1

            v2 = np.append(v[:2], 0)
            v3 = np.append(v[2:4], 0)
            v1 = -(m2*v2 + m3*v3) / m1

            positions = np.array([r1, r2, r3])
            velocities = np.array([v1, v2, v3])
        else:
            raise ValueError(f"Unexpected dimension for relative: {n}")

    else:
        raise ValueError(f"Unknown coordinate type: {coordinate_type}")

    return positions, velocities


def compute_mutual_distances(positions: np.ndarray) -> np.ndarray:
    """
    Compute mutual distances r_ij.

    Args:
        positions: (3, 3) array of positions [r1, r2, r3]

    Returns:
        distances: [r12, r23, r31] where r_ij = |r_i - r_j|
    """
    r1, r2, r3 = positions

    r12 = np.linalg.norm(r2 - r1)
    r23 = np.linalg.norm(r3 - r2)
    r31 = np.linalg.norm(r1 - r3)

    return np.array([r12, r23, r31])


def compute_relative_velocities(
    positions: np.ndarray,
    velocities: np.ndarray
) -> np.ndarray:
    """
    Compute relative velocity vectors v_ij = v_j - v_i.

    Args:
        positions: (3, 3) positions (not used here, but kept for consistency)
        velocities: (3, 3) velocities

    Returns:
        v_rel: (3, 3) array [v12, v23, v31]
    """
    v1, v2, v3 = velocities

    v12 = v2 - v1
    v23 = v3 - v2
    v31 = v1 - v3

    return np.array([v12, v23, v31])


def compute_radial_velocities(
    positions: np.ndarray,
    velocities: np.ndarray
) -> np.ndarray:
    """
    Compute radial velocity components: (r_ij · v_ij) / |r_ij|.

    Args:
        positions: (3, 3) positions
        velocities: (3, 3) velocities

    Returns:
        vr: [vr_12, vr_23, vr_31] radial velocities
    """
    r1, r2, r3 = positions
    v1, v2, v3 = velocities

    # r_ij vectors
    r12_vec = r2 - r1
    r23_vec = r3 - r2
    r31_vec = r1 - r3

    # v_ij vectors
    v12_vec = v2 - v1
    v23_vec = v3 - v2
    v31_vec = v1 - v3

    # Radial components
    r12 = np.linalg.norm(r12_vec)
    r23 = np.linalg.norm(r23_vec)
    r31 = np.linalg.norm(r31_vec)

    vr_12 = np.dot(r12_vec, v12_vec) / r12 if r12 > 1e-10 else 0.0
    vr_23 = np.dot(r23_vec, v23_vec) / r23 if r23 > 1e-10 else 0.0
    vr_31 = np.dot(r31_vec, v31_vec) / r31 if r31 > 1e-10 else 0.0

    return np.array([vr_12, vr_23, vr_31])


def compute_angular_momentum_vectors(
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute angular momentum vectors.

    Args:
        positions: (3, 3) positions
        velocities: (3, 3) velocities
        masses: (3,) masses

    Returns:
        L_pairs: (3, 3) angular momenta for each pair [L12, L23, L31]
        L_total: (3,) total angular momentum vector
    """
    r1, r2, r3 = positions
    v1, v2, v3 = velocities
    m1, m2, m3 = masses

    # Relative angular momenta (reduced mass formulation)
    mu12 = m1 * m2 / (m1 + m2)
    mu23 = m2 * m3 / (m2 + m3)
    mu31 = m3 * m1 / (m3 + m1)

    L12 = mu12 * np.cross(r2 - r1, v2 - v1)
    L23 = mu23 * np.cross(r3 - r2, v3 - v2)
    L31 = mu31 * np.cross(r1 - r3, v1 - v3)

    # Total angular momentum
    L_total = m1 * np.cross(r1, v1) + m2 * np.cross(r2, v2) + m3 * np.cross(r3, v3)

    L_pairs = np.array([L12, L23, L31])

    return L_pairs, L_total


def compute_moment_of_inertia(
    positions: np.ndarray,
    masses: np.ndarray,
    center_of_mass: bool = True
) -> float:
    """
    Compute scalar moment of inertia I = sum_i m_i |r_i|^2.

    Args:
        positions: (3, 3) positions
        masses: (3,) masses
        center_of_mass: If True, use COM frame

    Returns:
        I: Scalar moment of inertia
    """
    r1, r2, r3 = positions
    m1, m2, m3 = masses

    if center_of_mass:
        # Shift to center of mass
        r_com = (m1 * r1 + m2 * r2 + m3 * r3) / (m1 + m2 + m3)
        r1 = r1 - r_com
        r2 = r2 - r_com
        r3 = r3 - r_com

    I = m1 * np.dot(r1, r1) + m2 * np.dot(r2, r2) + m3 * np.dot(r3, r3)

    return I


def compute_shape_coordinates(positions: np.ndarray) -> np.ndarray:
    """
    Compute shape space coordinates (triangle shape parameters).

    For planar 3-body, the shape can be described by:
    - s1, s2, s3: Normalized side lengths or similar
    - θ: Orientation angle (removed in shape space)

    This is a simplified version. Full implementation depends on
    specific shape space definition.

    Args:
        positions: (3, 3) positions

    Returns:
        shape_coords: Shape space coordinates (dimension depends on definition)
    """
    # Compute mutual distances
    distances = compute_mutual_distances(positions)
    r12, r23, r31 = distances

    # Normalize by total perimeter (scale-invariant)
    perimeter = r12 + r23 + r31
    if perimeter < 1e-10:
        return np.zeros(3)

    s1 = r12 / perimeter
    s2 = r23 / perimeter
    s3 = r31 / perimeter

    return np.array([s1, s2, s3])


def compute_all_geometric_invariants(
    state: np.ndarray,
    masses: np.ndarray,
    coordinate_type: str = "cartesian"
) -> GeometricQuantities:
    """
    Compute all geometric invariant quantities from phase space state.

    This is the main entry point for extracting geometric features
    for symbolic regression.

    Args:
        state: Phase space state vector
        masses: Three body masses
        coordinate_type: Type of coordinates in state

    Returns:
        quantities: GeometricQuantities dataclass with all invariants

    Example:
        >>> masses = np.array([1.0, 1.0, 1.0])
        >>> state = np.random.randn(18)  # 3D Cartesian
        >>> geom = compute_all_geometric_invariants(state, masses, 'cartesian')
        >>> print(f"Distances: {geom.distances}")
        >>> print(f"Total L: {geom.total_angular_momentum}")
    """
    # Extract positions and velocities
    positions, velocities = extract_positions_velocities_3body(
        state, masses, coordinate_type
    )

    # Compute all invariants
    distances = compute_mutual_distances(positions)
    velocities_rel = compute_relative_velocities(positions, velocities)
    radial_velocities = compute_radial_velocities(positions, velocities)
    L_pairs, L_total = compute_angular_momentum_vectors(positions, velocities, masses)
    I = compute_moment_of_inertia(positions, masses)
    shape_coords = compute_shape_coordinates(positions)

    return GeometricQuantities(
        distances=distances,
        velocities_rel=velocities_rel,
        radial_velocities=radial_velocities,
        angular_momenta=L_pairs,
        total_angular_momentum=L_total,
        moment_of_inertia=I,
        shape_coords=shape_coords
    )


def create_geometric_basis_functions(masses: np.ndarray) -> Dict[str, callable]:
    """
    Create dictionary of geometric basis functions for symbolic regression.

    Returns functions that can be directly evaluated on phase space states.

    Args:
        masses: Three body masses

    Returns:
        basis_dict: Dictionary mapping names to evaluation functions

    Example:
        >>> masses = np.array([1.0, 1.0, 1.0])
        >>> basis = create_geometric_basis_functions(masses)
        >>> state = np.random.randn(18)
        >>> r12 = basis['r12'](state)
        >>> L_mag = basis['L_magnitude'](state)
    """
    def make_geometric_func(invariant_name: str):
        """Factory to create geometric invariant evaluation function."""
        def eval_func(state: np.ndarray) -> float:
            geom = compute_all_geometric_invariants(state, masses, 'cartesian')

            if invariant_name == 'r12':
                return geom.distances[0]
            elif invariant_name == 'r23':
                return geom.distances[1]
            elif invariant_name == 'r31':
                return geom.distances[2]
            elif invariant_name == 'vr_12':
                return geom.radial_velocities[0]
            elif invariant_name == 'vr_23':
                return geom.radial_velocities[1]
            elif invariant_name == 'vr_31':
                return geom.radial_velocities[2]
            elif invariant_name == 'L_magnitude':
                return np.linalg.norm(geom.total_angular_momentum)
            elif invariant_name == 'Lx':
                return geom.total_angular_momentum[0]
            elif invariant_name == 'Ly':
                return geom.total_angular_momentum[1]
            elif invariant_name == 'Lz':
                return geom.total_angular_momentum[2]
            elif invariant_name == 'I':
                return geom.moment_of_inertia
            elif invariant_name == 's1':
                return geom.shape_coords[0] if geom.shape_coords is not None else 0.0
            elif invariant_name == 's2':
                return geom.shape_coords[1] if geom.shape_coords is not None else 0.0
            elif invariant_name == 's3':
                return geom.shape_coords[2] if geom.shape_coords is not None else 0.0
            else:
                raise ValueError(f"Unknown invariant: {invariant_name}")

        return eval_func

    # Create dictionary of all geometric invariants
    invariant_names = [
        'r12', 'r23', 'r31',  # Distances
        'vr_12', 'vr_23', 'vr_31',  # Radial velocities
        'L_magnitude', 'Lx', 'Ly', 'Lz',  # Angular momentum
        'I',  # Moment of inertia
        's1', 's2', 's3'  # Shape coordinates
    ]

    basis_dict = {name: make_geometric_func(name) for name in invariant_names}

    # Add compound terms
    basis_dict['r12_squared'] = lambda state: basis_dict['r12'](state)**2
    basis_dict['r23_squared'] = lambda state: basis_dict['r23'](state)**2
    basis_dict['r31_squared'] = lambda state: basis_dict['r31'](state)**2
    basis_dict['L_squared'] = lambda state: basis_dict['L_magnitude'](state)**2

    return basis_dict


# Testing
if __name__ == "__main__":
    # Test with random 3-body configuration
    masses = np.array([1.0, 1.0, 1.0])

    # Generate random Cartesian state (planar, 6D config + 6D momentum)
    state = np.random.randn(12)

    # Compute geometric invariants
    geom = compute_all_geometric_invariants(state, masses, 'cartesian')

    print("Geometric Invariants:")
    print(f"  Distances (r12, r23, r31): {geom.distances}")
    print(f"  Radial velocities: {geom.radial_velocities}")
    print(f"  Total angular momentum: {geom.total_angular_momentum}")
    print(f"  |L|: {np.linalg.norm(geom.total_angular_momentum):.4f}")
    print(f"  Moment of inertia: {geom.moment_of_inertia:.4f}")
    print(f"  Shape coordinates: {geom.shape_coords}")

    # Test basis functions
    basis = create_geometric_basis_functions(masses)
    print(f"\nAvailable basis functions: {len(basis)}")
    print(f"  r12 = {basis['r12'](state):.4f}")
    print(f"  L_magnitude = {basis['L_magnitude'](state):.4f}")
    print(f"  r12_squared = {basis['r12_squared'](state):.4f}")
