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
from functools import lru_cache
from typing import List, Optional
import numpy as np
import logging
from scipy.integrate import solve_ivp
from scipy.optimize import root, root_scalar

logger = logging.getLogger(__name__)

_MAX_CORRECTED_LYAPUNOV_AMPLITUDE = 0.15


@lru_cache(maxsize=32)
def collinear_lagrange_point(mu: float, L_point: str) -> float:
    """Compute the collinear L1/L2 point for CR3BP mass parameter mu."""
    if L_point == "L1":
        bracket = (1e-12, 1.0 - mu - 1e-12)
    elif L_point == "L2":
        bracket = (1.0 - mu + 1e-12, 2.0)
    else:
        raise ValueError(f"L_point must be L1 or L2, got {L_point}")

    def force_balance(x: float) -> float:
        r1 = abs(x + mu)
        r2 = abs(x - 1.0 + mu)
        return (
            x
            - (1.0 - mu) * (x + mu) / r1**3
            - mu * (x - 1.0 + mu) / r2**3
        )

    result = root_scalar(force_balance, bracket=bracket, xtol=1e-14, rtol=1e-14)
    if not result.converged:
        raise RuntimeError(f"Could not solve {L_point} for mu={mu}")
    return float(result.root)


def _cr3bp_rhs(mu: float):
    """Return CR3BP first-order dynamics for scipy integrators."""
    from ..utils.dynamics import cr3bp_acceleration

    def rhs(_t: float, state: np.ndarray) -> np.ndarray:
        deriv = np.empty(6, dtype=float)
        deriv[:3] = state[3:]
        deriv[3:] = cr3bp_acceleration(state, mu)
        return deriv

    return rhs


def _planar_second_derivatives(mu: float, x: float) -> tuple[float, float]:
    """Planar CR3BP potential Hessian terms at y=z=0."""
    r1 = abs(x + mu)
    r2 = abs(x - 1.0 + mu)
    uxx = 1.0 + 2.0 * (1.0 - mu) / r1**3 + 2.0 * mu / r2**3
    uyy = 1.0 - (1.0 - mu) / r1**3 - mu / r2**3
    return uxx, uyy


def _planar_linear_frequency(mu: float, x_L: float) -> float:
    """Return the center-manifold planar frequency at a collinear point."""
    uxx, uyy = _planar_second_derivatives(mu, x_L)
    matrix = np.array(
        [
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [uxx, 0.0, 0.0, 2.0],
            [0.0, uyy, -2.0, 0.0],
        ]
    )
    eigenvalues = np.linalg.eigvals(matrix)
    imag_parts = sorted(
        abs(ev.imag)
        for ev in eigenvalues
        if abs(ev.real) < 1e-8 and abs(ev.imag) > 1e-8
    )
    if not imag_parts:
        raise RuntimeError("Could not identify planar center frequency")
    return float(imag_parts[0])


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

        if L_point == "L1":
            self.x_L = collinear_lagrange_point(mu, L_point)
        elif L_point == "L2":
            self.x_L = collinear_lagrange_point(mu, L_point)
        else:
            raise ValueError(f"L_point must be L1 or L2, got {L_point}")

    def generate_richardson_approximation(self, amplitude: float) -> PeriodicOrbitSpec:
        """
        Generate a planar Lyapunov orbit.

        Small-amplitude L1/L2 orbits are differentially corrected from a
        linearized seed. Larger amplitudes retain the historical Richardson
        approximation, because the simple two-variable corrector is not a
        global family continuation method.

        Args:
            amplitude: Orbit amplitude (Ay)

        Returns:
            PeriodicOrbitSpec
        """
        if 0.0 < amplitude <= _MAX_CORRECTED_LYAPUNOV_AMPLITUDE:
            try:
                return self._generate_differentially_corrected(amplitude)
            except Exception as exc:
                logger.warning(
                    "Differential correction failed for %s amplitude %.6g: %s",
                    self.L_point,
                    amplitude,
                    exc,
                )

        return self._generate_richardson_fallback(amplitude)

    def _generate_richardson_fallback(self, amplitude: float) -> PeriodicOrbitSpec:
        """Generate Lyapunov orbit using the historical simplified approximation."""
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
            amplitude=amplitude,
        )

        return orbit

    def _generate_differentially_corrected(self, amplitude: float) -> PeriodicOrbitSpec:
        """Generate a corrected planar Lyapunov orbit for bounded amplitudes."""
        direction = -1.0 if self.L_point == "L1" else 1.0
        x0 = self.x_L + direction * amplitude
        omega = _planar_linear_frequency(self.mu, self.x_L)
        uxx, _uyy = _planar_second_derivatives(self.mu, self.x_L)

        # Linear center-mode seed. The correction solves vy0 and half-period
        # so the orbit crosses y=0 with vx=0 at the opposite symmetry point.
        dx = x0 - self.x_L
        vy_guess = -((omega**2 + uxx) * dx) / 2.0
        half_period_guess = np.pi / omega
        initial_guess = np.array([vy_guess, half_period_guess], dtype=float)
        rhs = _cr3bp_rhs(self.mu)

        def propagate(vy0: float, half_period: float) -> np.ndarray:
            state0 = np.array([x0, 0.0, 0.0, 0.0, vy0, 0.0], dtype=float)
            solution = solve_ivp(
                rhs,
                (0.0, half_period),
                state0,
                method="DOP853",
                rtol=1e-12,
                atol=1e-14,
            )
            if not solution.success:
                raise RuntimeError(solution.message)
            return solution.y[:, -1]

        def residual(variables: np.ndarray) -> np.ndarray:
            vy0, half_period = variables
            if half_period <= 0.1 or not np.all(np.isfinite(variables)):
                return np.array([1e6, 1e6], dtype=float)
            final_state = propagate(vy0, half_period)
            return np.array([final_state[1], final_state[3]], dtype=float)

        corrected = root(residual, initial_guess, method="hybr", tol=1e-11)
        if not corrected.success or not np.all(np.isfinite(corrected.x)):
            raise RuntimeError(corrected.message)

        vy0, half_period = corrected.x
        if half_period <= 0.1:
            raise RuntimeError(f"invalid corrected half-period {half_period}")

        initial_state = np.array([x0, 0.0, 0.0, 0.0, vy0, 0.0], dtype=float)
        period = 2.0 * float(half_period)
        full_solution = solve_ivp(
            rhs,
            (0.0, period),
            initial_state,
            method="DOP853",
            rtol=1e-12,
            atol=1e-14,
        )
        if not full_solution.success:
            raise RuntimeError(full_solution.message)

        closure_error = float(np.linalg.norm(full_solution.y[:, -1] - initial_state))
        if closure_error > 1e-6:
            raise RuntimeError(f"closure error {closure_error:.3e} exceeds tolerance")

        C = self._compute_jacobi_constant(initial_state)

        return PeriodicOrbitSpec(
            name=f"{self.L_point}_Lyapunov_A{amplitude:.3f}",
            family="lyapunov",
            mu=self.mu,
            L_point=self.L_point,
            initial_state=initial_state,
            period=period,
            jacobi_constant=C,
            amplitude=amplitude,
        )

    def _compute_jacobi_constant(self, state: np.ndarray) -> float:
        """Compute Jacobi constant."""
        from ..utils.dynamics import calculate_jacobi_constant

        return calculate_jacobi_constant(state, self.mu)

    def generate_family(
        self, n_orbits: int = 10, amplitude_range: tuple = (0.01, 0.3)
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
            self.x_L = 1.0 - mu - (mu / 3.0) ** (1.0 / 3.0)
        elif L_point == "L2":
            self.x_L = 1.0 - mu + (mu / 3.0) ** (1.0 / 3.0)
        else:
            raise ValueError(f"L_point must be L1 or L2")

    def generate_richardson_halo(
        self, amplitude_z: float, branch: str = "northern"
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
            amplitude=amplitude_z,
        )

        return orbit

    def generate_family(
        self,
        n_orbits: int = 10,
        amplitude_range: tuple = (0.01, 0.3),
    ) -> List[PeriodicOrbitSpec]:
        """
        Generate family of Halo orbits.

        Args:
            n_orbits: Number of family members
            amplitude_range: (min, max) out-of-plane amplitude

        Returns:
            List of PeriodicOrbitSpec
        """
        amplitudes = np.linspace(amplitude_range[0], amplitude_range[1], n_orbits)
        family = []

        for amp in amplitudes:
            orbit = self.generate_richardson_halo(amp, branch="northern")
            family.append(orbit)

        logger.info(f"Generated {len(family)} Halo orbits around {self.L_point}")
        return family


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
