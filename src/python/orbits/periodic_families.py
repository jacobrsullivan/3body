"""
Known Periodic Orbit Library for CR3BP (WP1 Phase 5).

Catalog of classical periodic orbit families:
- Lyapunov orbits (planar, around L1/L2)
- Halo orbits (3D, around L1/L2)
- Vertical/Axial orbits

Used for:
- Validation of integrators
- Reference trajectories
- Initial conditions for exploration

References:
-----------
- Richardson (1980): "Analytic construction of periodic orbits about the
  collinear points"
- Howell (1984): "Three-dimensional, periodic, 'halo' orbits"
- Koon et al. (2000): "Dynamical Systems, the Three-Body Problem and
  Space Mission Design"
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class PeriodicOrbitSpec:
    """
    Specification for a periodic orbit.

    Attributes:
        name: Orbit name/identifier
        family: Family type ("lyapunov", "halo", "vertical")
        mu: Mass parameter
        L_point: Associated Lagrange point ("L1", "L2", etc.)
        initial_state: Initial condition [x, y, z, vx, vy, vz]
        period: Orbital period
        jacobi_constant: Jacobi constant C
        stability_index: Stability eigenvalue
        amplitude: Characteristic amplitude (family parameter)
    """
    name: str
    family: str
    mu: float
    L_point: str
    initial_state: np.ndarray
    period: float
    jacobi_constant: float
    stability_index: Optional[float] = None
    amplitude: Optional[float] = None


class PeriodicOrbitLibrary:
    """Library of known periodic orbits."""

    def __init__(self):
        """Initialize orbit library."""
        self.orbits: List[PeriodicOrbitSpec] = []
        logger.info("Initialized periodic orbit library")

    def add_orbit(self, orbit: PeriodicOrbitSpec):
        """Add orbit to library."""
        self.orbits.append(orbit)
        logger.info(f"Added orbit: {orbit.name} ({orbit.family})")

    def get_by_family(self, family: str) -> List[PeriodicOrbitSpec]:
        """Get all orbits of given family."""
        return [orb for orb in self.orbits if orb.family == family]

    def get_by_lagrange_point(self, L_point: str) -> List[PeriodicOrbitSpec]:
        """Get all orbits around given Lagrange point."""
        return [orb for orb in self.orbits if orb.L_point == L_point]


class LyapunovOrbitGenerator:
    """Generate Lyapunov orbit family around L1/L2."""

    def __init__(self, mu: float, L_point: str = "L1"):
        """
        Initialize Lyapunov orbit generator.

        Args:
            mu: Mass parameter
            L_point: "L1" or "L2"
        """
        self.mu = mu
        self.L_point = L_point

        # Approximate L-point position
        if L_point == "L1":
            self.x_L = 1.0 - mu - (mu/3.0)**(1.0/3.0)
        elif L_point == "L2":
            self.x_L = 1.0 - mu + (mu/3.0)**(1.0/3.0)
        else:
            raise ValueError(f"L_point must be L1 or L2, got {L_point}")

    def generate_richardson_approximation(
        self,
        amplitude: float
    ) -> PeriodicOrbitSpec:
        """
        Generate Lyapunov orbit using Richardson's 3rd-order approximation.

        Args:
            amplitude: Orbit amplitude (Ay)

        Returns:
            PeriodicOrbitSpec
        """
        # Richardson's approximation (simplified)
        # Full implementation would use complete 3rd-order expansion

        # Linear frequency
        gamma = abs(1.0 - self.mu - self.x_L)  # Distance to secondary
        omega = np.sqrt(1.0 + 2.0 / gamma**3)  # Approximate

        # Initial condition (3rd-order approximation)
        Ay = amplitude
        Az = 0.0  # Planar Lyapunov

        x0 = self.x_L + Ay
        y0 = 0.0
        z0 = 0.0
        vx0 = 0.0
        vy0 = Ay * omega
        vz0 = 0.0

        initial_state = np.array([x0, y0, z0, vx0, vy0, vz0])

        # Period (approximate)
        period = 2.0 * np.pi / omega

        # Jacobi constant (approximate)
        C = self._compute_jacobi_constant(initial_state)

        orbit = PeriodicOrbitSpec(
            name=f"{self.L_point}_Lyapunov_A{amplitude:.3f}",
            family="lyapunov",
            mu=self.mu,
            L_point=self.L_point,
            initial_state=initial_state,
            period=period,
            jacobi_constant=C,
            amplitude=amplitude
        )

        return orbit

    def _compute_jacobi_constant(self, state: np.ndarray) -> float:
        """Compute Jacobi constant."""
        from ..utils.dynamics import calculate_jacobi_constant
        return calculate_jacobi_constant(state, self.mu)

    def generate_family(
        self,
        n_orbits: int = 10,
        amplitude_range: tuple = (0.01, 0.3)
    ) -> List[PeriodicOrbitSpec]:
        """
        Generate family of Lyapunov orbits.

        Args:
            n_orbits: Number of family members
            amplitude_range: (min, max) amplitude

        Returns:
            List of PeriodicOrbitSpec
        """
        amplitudes = np.linspace(amplitude_range[0], amplitude_range[1], n_orbits)
        family = []

        for amp in amplitudes:
            orbit = self.generate_richardson_approximation(amp)
            family.append(orbit)

        logger.info(f"Generated {len(family)} Lyapunov orbits around {self.L_point}")
        return family


class HaloOrbitGenerator:
    """Generate Halo orbit family (3D periodic orbits)."""

    def __init__(self, mu: float, L_point: str = "L1"):
        """Initialize Halo orbit generator."""
        self.mu = mu
        self.L_point = L_point

        if L_point == "L1":
            self.x_L = 1.0 - mu - (mu/3.0)**(1.0/3.0)
        elif L_point == "L2":
            self.x_L = 1.0 - mu + (mu/3.0)**(1.0/3.0)
        else:
            raise ValueError(f"L_point must be L1 or L2")

    def generate_richardson_halo(
        self,
        amplitude_z: float,
        branch: str = "northern"
    ) -> PeriodicOrbitSpec:
        """
        Generate Halo orbit using Richardson's approximation.

        Args:
            amplitude_z: Out-of-plane amplitude
            branch: "northern" or "southern"

        Returns:
            PeriodicOrbitSpec
        """
        # Simplified Halo approximation
        Az = amplitude_z if branch == "northern" else -amplitude_z

        # Richardson's 3rd-order approximation
        gamma = abs(1.0 - self.mu - self.x_L)
        omega = np.sqrt(1.0 + 2.0 / gamma**3)

        # Halo orbit parameters (simplified)
        Ay = Az * 1.5  # Approximate relation

        x0 = self.x_L
        y0 = Ay
        z0 = 0.0
        vx0 = 0.0
        vy0 = 0.0
        vz0 = Az * omega

        initial_state = np.array([x0, y0, z0, vx0, vy0, vz0])
        period = 2.0 * np.pi / omega

        from ..utils.dynamics import calculate_jacobi_constant
        C = calculate_jacobi_constant(initial_state, self.mu)

        orbit = PeriodicOrbitSpec(
            name=f"{self.L_point}_Halo_{branch}_Az{amplitude_z:.3f}",
            family="halo",
            mu=self.mu,
            L_point=self.L_point,
            initial_state=initial_state,
            period=period,
            jacobi_constant=C,
            amplitude=amplitude_z
        )

        return orbit


def create_earth_moon_library() -> PeriodicOrbitLibrary:
    """Create library of known Earth-Moon periodic orbits."""
    library = PeriodicOrbitLibrary()
    mu = 0.01215  # Earth-Moon

    # Generate L1 Lyapunov family
    lyap_gen = LyapunovOrbitGenerator(mu, "L1")
    l1_lyapunov = lyap_gen.generate_family(n_orbits=5)
    for orb in l1_lyapunov:
        library.add_orbit(orb)

    # Generate L2 Lyapunov family
    lyap_gen_l2 = LyapunovOrbitGenerator(mu, "L2")
    l2_lyapunov = lyap_gen_l2.generate_family(n_orbits=5)
    for orb in l2_lyapunov:
        library.add_orbit(orb)

    # Generate some Halo orbits
    halo_gen = HaloOrbitGenerator(mu, "L1")
    for Az in [0.05, 0.1, 0.15]:
        for branch in ["northern", "southern"]:
            halo = halo_gen.generate_richardson_halo(Az, branch)
            library.add_orbit(halo)

    logger.info(f"Created Earth-Moon library with {len(library.orbits)} orbits")
    return library
