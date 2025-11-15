"""
Parameter space sampling for generating training data (Task 3.2.1, Part A).

This module implements Latin Hypercube Sampling (LHS) to generate diverse
initial conditions for the 3-body problem across the parameter space.

Key dimensions:
- Mass ratios: μ = m₂/m₁, m₃/(m₁+m₂)
- Energy: E (bound orbits)
- Angular momentum: L
- Eccentricity: e (orbital shape parameter)
"""

from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional
import numpy as np
from scipy.stats import qmc


@dataclass
class ParameterRanges:
    """
    Parameter space ranges for 3-body problem sampling.

    Attributes:
        mass_ratio: μ = m₂/m₁ ∈ [min, max]
        mass_3_ratio: m₃/(m₁+m₂) ∈ [min, max]
        energy: E ∈ [min, max] (negative for bound orbits)
        angular_momentum: L ∈ [min, max]
        eccentricity: e ∈ [min, max] (0 = circular, <1 = elliptical)
    """
    mass_ratio: Tuple[float, float] = (0.01, 0.5)
    mass_3_ratio: Tuple[float, float] = (0.01, 1.0)
    energy: Tuple[float, float] = (-2.0, -0.1)
    angular_momentum: Tuple[float, float] = (0.5, 3.0)
    eccentricity: Tuple[float, float] = (0.0, 0.9)

    def to_bounds(self) -> List[Tuple[float, float]]:
        """Return list of bounds for scipy LHS."""
        return [
            self.mass_ratio,
            self.mass_3_ratio,
            self.energy,
            self.angular_momentum,
            self.eccentricity
        ]


@dataclass
class InitialCondition:
    """
    Single initial condition for 3-body problem.

    Attributes:
        masses: (3,) array of body masses
        energy: Total energy
        angular_momentum: Total angular momentum magnitude
        position: (3, 3) positions in center-of-mass frame
        velocity: (3, 3) velocities
        metadata: Additional parameters (e.g., eccentricity)
    """
    masses: np.ndarray
    energy: float
    angular_momentum: float
    position: np.ndarray
    velocity: np.ndarray
    metadata: Dict

    def __post_init__(self):
        """Validate dimensions."""
        assert self.masses.shape == (3,), f"masses must be (3,), got {self.masses.shape}"
        assert self.position.shape == (3, 3), f"position must be (3,3), got {self.position.shape}"
        assert self.velocity.shape == (3, 3), f"velocity must be (3,3), got {self.velocity.shape}"

        # Ensure arrays are float64
        self.masses = np.asarray(self.masses, dtype=np.float64)
        self.position = np.asarray(self.position, dtype=np.float64)
        self.velocity = np.asarray(self.velocity, dtype=np.float64)


def generate_lhs_samples(
    param_ranges: ParameterRanges,
    num_samples: int,
    seed: int = 42,
    max_iterations: int = 100,
    energy_tolerance: float = 0.05,
    angular_momentum_tolerance: float = 0.05
) -> List[InitialCondition]:
    """
    Generate initial conditions via Latin Hypercube Sampling.

    This function samples the 5D parameter space (mass ratios, E, L, e)
    and constructs consistent initial conditions that satisfy:
    - Total energy ≈ E_target
    - Total angular momentum ≈ L_target
    - Center-of-mass frame (Σ m_i r_i = 0, Σ m_i v_i = 0)

    Args:
        param_ranges: Parameter space bounds
        num_samples: Number of samples to generate
        seed: Random seed for reproducibility
        max_iterations: Maximum attempts to satisfy constraints
        energy_tolerance: Relative tolerance for energy matching
        angular_momentum_tolerance: Relative tolerance for L matching

    Returns:
        List of validated initial conditions
    """
    # Create Latin Hypercube sampler
    sampler = qmc.LatinHypercube(d=5, seed=seed)

    # Generate samples in unit hypercube
    samples_unit = sampler.random(n=num_samples)

    # Scale to parameter ranges
    bounds = param_ranges.to_bounds()
    samples = qmc.scale(samples_unit, [b[0] for b in bounds], [b[1] for b in bounds])

    initial_conditions = []

    for i in range(num_samples):
        mu, m3_ratio, E, L, e = samples[i]

        # Construct masses (normalize so total mass M = 1)
        masses = _compute_masses(mu, m3_ratio)

        # Try to generate consistent initial condition
        for attempt in range(max_iterations):
            try:
                # Generate position/velocity via restricted problem + perturbation
                q, v = _sample_state_from_parameters(masses, E, L, e)

                # Apply center-of-mass corrections
                q, v = _apply_com_correction(q, v, masses)

                # Validate constraints
                E_actual = compute_energy(q, v, masses)
                L_actual = compute_angular_momentum_magnitude(q, v, masses)

                E_error = abs(E_actual - E) / abs(E)
                L_error = abs(L_actual - L) / L

                if E_error < energy_tolerance and L_error < angular_momentum_tolerance:
                    # Success - constraints satisfied
                    ic = InitialCondition(
                        masses=masses,
                        energy=E,
                        angular_momentum=L,
                        position=q,
                        velocity=v,
                        metadata={
                            'eccentricity': e,
                            'mass_ratio': mu,
                            'mass_3_ratio': m3_ratio,
                            'sample_id': i,
                            'actual_energy': E_actual,
                            'actual_angular_momentum': L_actual
                        }
                    )
                    initial_conditions.append(ic)
                    break

            except ValueError:
                # Configuration invalid (e.g., collision), try again
                continue

        # Log if we failed to generate valid IC
        if len(initial_conditions) <= i:
            print(f"Warning: Failed to generate valid IC for sample {i} after {max_iterations} attempts")

    print(f"Generated {len(initial_conditions)}/{num_samples} valid initial conditions")
    return initial_conditions


def _compute_masses(mu: float, m3_ratio: float) -> np.ndarray:
    """
    Compute individual masses from ratios.

    Given:
    - μ = m₂/m₁
    - r = m₃/(m₁+m₂)
    - M_total = 1 (normalization)

    Solve:
    - m₁ + m₂ + m₃ = 1
    - m₂ = μ·m₁
    - m₃ = r·(m₁ + m₂)

    Solution:
    - m₁ = 1 / (1 + μ + r·(1 + μ))
    - m₂ = μ·m₁
    - m₃ = r·(m₁ + m₂)

    Args:
        mu: Mass ratio m₂/m₁
        m3_ratio: Mass ratio m₃/(m₁+m₂)

    Returns:
        Array [m₁, m₂, m₃] with sum = 1
    """
    m1 = 1.0 / (1.0 + mu + m3_ratio * (1.0 + mu))
    m2 = mu * m1
    m3 = m3_ratio * (m1 + m2)

    masses = np.array([m1, m2, m3])

    # Verify normalization
    assert abs(masses.sum() - 1.0) < 1e-12, "Mass normalization failed"

    return masses


def _sample_state_from_parameters(
    masses: np.ndarray,
    E: float,
    L: float,
    e: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate position/velocity from energy, angular momentum, eccentricity.

    Strategy:
    1. Start with 2-body Keplerian orbit for m₁-m₂
    2. Place m₃ at random position consistent with E, L
    3. Perturb to satisfy exact constraints (iterative)

    This is a simplified version - for production, would use more
    sophisticated methods (e.g., variational approach).

    Args:
        masses: Body masses [m₁, m₂, m₃]
        E: Target energy
        L: Target angular momentum magnitude
        e: Target eccentricity

    Returns:
        q: Positions (3, 3)
        v: Velocities (3, 3)
    """
    m1, m2, m3 = masses

    # Simplified approach: Generate planar configuration
    # Place m1 at origin, m2 on ellipse, m3 perturbed

    # Semi-major axis from energy (2-body approximation)
    mu_12 = m1 * m2 / (m1 + m2)
    # E = -G m1 m2 / (2a) for 2-body
    # With G=1: a = -m1 m2 / (2E)
    a_12 = -m1 * m2 / (2 * E) if E < 0 else 1.0

    # Orbital parameters for m1-m2
    theta = np.random.uniform(0, 2 * np.pi)  # True anomaly
    r_12 = a_12 * (1 - e**2) / (1 + e * np.cos(theta))

    # Positions (planar, in orbital plane)
    r1_2d = np.array([-mu_12 * r_12 * np.cos(theta), -mu_12 * r_12 * np.sin(theta)])
    r2_2d = np.array([(m1 / (m1 + m2)) * r_12 * np.cos(theta),
                      (m1 / (m1 + m2)) * r_12 * np.sin(theta)])

    # Place m3 randomly (perturbed from plane)
    r3_mag = np.random.uniform(0.5 * a_12, 2.0 * a_12)
    phi = np.random.uniform(0, 2 * np.pi)
    z3 = np.random.uniform(-0.1 * a_12, 0.1 * a_12)  # Small out-of-plane
    r3_2d = np.array([r3_mag * np.cos(phi), r3_mag * np.sin(theta)])

    # 3D positions
    q = np.array([
        np.append(r1_2d, 0.0),
        np.append(r2_2d, 0.0),
        np.append(r3_2d, z3)
    ])

    # Velocities from L and E
    # Simplified: circular-like velocities + perturbations
    L_vec = np.array([0, 0, L])  # Angular momentum along z

    # Compute velocities to get approximately correct L and E
    # This is approximate - would need iterative refinement
    v1 = np.cross(L_vec, q[0]) / (m1 * np.linalg.norm(q[0])**2 + 1e-10)
    v2 = np.cross(L_vec, q[1]) / (m2 * np.linalg.norm(q[1])**2 + 1e-10)
    v3 = np.cross(L_vec, q[2]) / (m3 * np.linalg.norm(q[2])**2 + 1e-10)

    v = np.array([v1, v2, v3])

    # Add random perturbations
    v += np.random.normal(0, 0.01, (3, 3))

    return q, v


def _apply_com_correction(
    q: np.ndarray,
    v: np.ndarray,
    masses: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply center-of-mass corrections.

    Enforce:
    - Σ m_i r_i = 0 (center of mass at origin)
    - Σ m_i v_i = 0 (zero total momentum)

    Args:
        q: Positions (3, 3)
        v: Velocities (3, 3)
        masses: Body masses (3,)

    Returns:
        q_corrected, v_corrected
    """
    M_total = masses.sum()

    # Compute center of mass
    r_com = np.sum(masses[:, None] * q, axis=0) / M_total
    v_com = np.sum(masses[:, None] * v, axis=0) / M_total

    # Shift to center-of-mass frame
    q_corrected = q - r_com
    v_corrected = v - v_com

    return q_corrected, v_corrected


def compute_energy(
    q: np.ndarray,
    v: np.ndarray,
    masses: np.ndarray,
    G: float = 1.0
) -> float:
    """
    Compute total energy E = T + V.

    Args:
        q: Positions (3, 3)
        v: Velocities (3, 3)
        masses: Body masses (3,)
        G: Gravitational constant

    Returns:
        Total energy
    """
    # Kinetic energy
    T = 0.5 * np.sum(masses[:, None] * v**2)

    # Potential energy
    V = 0.0
    for i in range(3):
        for j in range(i + 1, 3):
            r_ij = np.linalg.norm(q[i] - q[j])
            if r_ij < 1e-10:
                raise ValueError(f"Collision between bodies {i} and {j}")
            V -= G * masses[i] * masses[j] / r_ij

    return T + V


def compute_angular_momentum_magnitude(
    q: np.ndarray,
    v: np.ndarray,
    masses: np.ndarray
) -> float:
    """
    Compute total angular momentum magnitude |L|.

    L = Σ m_i (r_i × v_i)

    Args:
        q: Positions (3, 3)
        v: Velocities (3, 3)
        masses: Body masses (3,)

    Returns:
        |L|
    """
    L_vec = np.zeros(3)
    for i in range(3):
        L_vec += masses[i] * np.cross(q[i], v[i])

    return np.linalg.norm(L_vec)


def generate_test_samples(num_samples: int = 10) -> List[InitialCondition]:
    """
    Generate small test dataset with default parameters.

    Useful for quick testing and validation.

    Args:
        num_samples: Number of samples to generate

    Returns:
        List of initial conditions
    """
    param_ranges = ParameterRanges()
    return generate_lhs_samples(param_ranges, num_samples, seed=42)


if __name__ == "__main__":
    # Quick test
    print("Testing parameter sampling...")

    test_ics = generate_test_samples(num_samples=5)

    print(f"\nGenerated {len(test_ics)} initial conditions")

    for i, ic in enumerate(test_ics):
        print(f"\nIC {i}:")
        print(f"  Masses: {ic.masses}")
        print(f"  Energy: {ic.energy:.4f} (actual: {ic.metadata['actual_energy']:.4f})")
        print(f"  L: {ic.angular_momentum:.4f} (actual: {ic.metadata['actual_angular_momentum']:.4f})")
        print(f"  Eccentricity: {ic.metadata['eccentricity']:.4f}")
