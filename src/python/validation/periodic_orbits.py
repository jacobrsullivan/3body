"""
Periodic orbit library for Morales-Ramis test (WP 4.2, Task 4.2.1).

Provides initial conditions and periods for known periodic solutions:
- Lagrange equilateral configurations (L4, L5)
- Euler collinear configurations
- Figure-8 choreography (Moore 1993, Chenciner-Montgomery 2000)

These orbits are used as reference solutions for computing Normal Variational
Equations and testing the Morales-Ramis criterion.

References:
- Meyer & Schmidt, "Periodic orbits near L4 for mass ratios near critical value" (1971)
- Moore, "Braids in classical dynamics" (1993)
- Chenciner & Montgomery, "A remarkable periodic solution of the three-body problem" (2000)
- Maciejewski & Przybylska, "Non-integrability of planar three-body problem" (2011)
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Callable
import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class PeriodicOrbit:
    """
    Specification of a periodic orbit for Morales-Ramis analysis.

    Attributes:
        name: Human-readable name
        initial_condition: State at t=0 (phase space coordinates)
        period: Fundamental period T
        mass_ratios: (m1, m2, m3) or (μ, 1-μ) for CR3BP
        energy: Total energy (if applicable)
        angular_momentum: Total angular momentum
        description: Brief description of orbit
        reference: Literature citation
        stability_type: 'stable', 'unstable', or 'neutral'
    """
    name: str
    initial_condition: np.ndarray
    period: float
    mass_ratios: Tuple[float, ...]
    energy: Optional[float] = None
    angular_momentum: Optional[float] = None
    description: str = ""
    reference: str = ""
    stability_type: str = "unknown"

    def __post_init__(self):
        """Validate orbit specification."""
        if self.period <= 0:
            raise ValueError(f"Period must be positive, got {self.period}")
        if len(self.initial_condition) % 2 != 0:
            raise ValueError(
                f"Initial condition must have even dimension (q, p), "
                f"got {len(self.initial_condition)}"
            )


# =============================================================================
# Lagrange Equilateral Configurations (L4, L5)
# =============================================================================

def lagrange_l4_circular_restricted_3bp(mu: float = 0.012) -> PeriodicOrbit:
    """
    Lagrange L4 equilibrium point in circular restricted 3-body problem.

    The L4 point is one of the equilateral Lagrange points, forming an
    equilateral triangle with the two primaries. It's stable for μ < μ_critical ≈ 0.0385.

    Args:
        mu: Mass parameter μ = m2/(m1+m2). Default is Earth-Moon (0.012).

    Returns:
        PeriodicOrbit for L4 point

    Note:
        This is an equilibrium in rotating frame, so period is 2π (one rotation).
        In inertial frame, it's a periodic orbit.
    """
    # L4 position in rotating frame: equilateral triangle
    x_L4 = 0.5 - mu
    y_L4 = np.sqrt(3) / 2

    # Equilibrium → zero velocity in rotating frame
    vx_L4 = 0.0
    vy_L4 = 0.0

    # Initial condition: [x, y, vx, vy] in rotating frame
    ic = np.array([x_L4, y_L4, vx_L4, vy_L4])

    # Energy at L4 (effective potential in CR3BP)
    # V_eff = -(1-μ)/r1 - μ/r2 - (x² + y²)/2
    r1 = np.sqrt((x_L4 + mu)**2 + y_L4**2)
    r2 = np.sqrt((x_L4 - 1 + mu)**2 + y_L4**2)
    V_eff = -(1 - mu)/r1 - mu/r2 - 0.5*(x_L4**2 + y_L4**2)
    E_L4 = V_eff  # Kinetic energy is zero at equilibrium

    return PeriodicOrbit(
        name="Lagrange_L4",
        initial_condition=ic,
        period=2*np.pi,  # Period in rotating frame
        mass_ratios=(mu, 1-mu),
        energy=E_L4,
        angular_momentum=None,  # Depends on reduction
        description=(
            f"L4 Lagrange point (equilateral) for μ={mu:.4f}. "
            "Stable for μ < 0.0385 (Routh 1875)."
        ),
        reference="Meyer & Schmidt (1971), Szebehely (1967)",
        stability_type="stable" if mu < 0.0385 else "unstable"
    )


def lagrange_l4_equal_masses() -> PeriodicOrbit:
    """
    Lagrange equilateral configuration for equal masses.

    Three bodies of equal mass forming rotating equilateral triangle.
    This is a relative equilibrium (constant shape, rotating).

    Returns:
        PeriodicOrbit for equal-mass equilateral

    Reference:
        Lagrange (1772), "Essay on the three-body problem"
    """
    # Place bodies at vertices of equilateral triangle
    # in rotating frame centered at barycenter

    # Side length of triangle (arbitrary, set to 1)
    a = 1.0

    # Vertices of equilateral triangle centered at origin
    # Body 1: (a/√3, 0)
    # Body 2: (-a/(2√3), a/2)
    # Body 3: (-a/(2√3), -a/2)

    sqrt3 = np.sqrt(3)
    x1, y1 = a/sqrt3, 0.0
    x2, y2 = -a/(2*sqrt3), a/2
    x3, y3 = -a/(2*sqrt3), -a/2

    # Positions in Cartesian coordinates (planar)
    q = np.array([x1, y1, x2, y2, x3, y3])

    # For rotating equilibrium, velocities are perpendicular to position
    # v = ω × r where ω is angular velocity
    # For equal masses and equilateral triangle: ω² = 3m/a³ (with G=1, m=1)
    omega = np.sqrt(3.0 / a**3)

    # Velocities: v = ω(-y, x) for each body
    vx1, vy1 = -omega * y1, omega * x1
    vx2, vy2 = -omega * y2, omega * x2
    vx3, vy3 = -omega * y3, omega * x3

    p = np.array([vx1, vy1, vx2, vy2, vx3, vy3])

    # Period: T = 2π/ω
    period = 2*np.pi / omega

    # Energy (kinetic + potential)
    # T = (1/2)Σ m_i v_i² = (1/2)(3m)·(ωa/√3)²
    # V = -Σ_i<j m_i m_j / r_ij = -3m²/a (three pairs, each distance a)
    T = 0.5 * 3 * (omega * a / sqrt3)**2
    V = -3.0 / a
    E = T + V

    # Angular momentum: L = Σ m_i (r_i × v_i)·z
    # For rotating equilibrium: L = I·ω where I is moment of inertia
    # I = Σ m_i r_i² = 3m·(a/√3)² = m·a²
    L = 3 * (a/sqrt3)**2 * omega

    return PeriodicOrbit(
        name="Lagrange_Equilateral_EqualMass",
        initial_condition=np.concatenate([q, p]),
        period=period,
        mass_ratios=(1.0, 1.0, 1.0),
        energy=E,
        angular_momentum=L,
        description=(
            "Lagrange equilateral configuration for three equal masses. "
            "Rotating relative equilibrium discovered by Lagrange (1772)."
        ),
        reference="Lagrange (1772), Marchal (1990)",
        stability_type="neutral"  # Linearly stable but nonlinearly bounded
    )


# =============================================================================
# Euler Collinear Configurations
# =============================================================================

def euler_collinear_equal_masses() -> PeriodicOrbit:
    """
    Euler collinear configuration for equal masses.

    Three bodies on a line, with central body between the other two.
    This is a homothetic solution (shape preserved, scales with time).

    Returns:
        PeriodicOrbit for collinear configuration

    Reference:
        Euler (1767), Combot (2012) "Non-integrability of collinear 3BP"
    """
    # Place bodies on x-axis: body 2 at origin, bodies 1 and 3 symmetric
    # For equal masses and zero angular momentum: x1 = -x3

    # Initial separation (arbitrary)
    d = 1.0

    # Positions (planar, on x-axis)
    x1, y1 = -d, 0.0
    x2, y2 = 0.0, 0.0
    x3, y3 = d, 0.0

    q = np.array([x1, y1, x2, y2, x3, y3])

    # For homothetic collapse with E=0:
    # Initial velocities are radial (toward center of mass)
    # v_i ∝ r_i (homothetic scaling)

    # Rate of collapse: determined by energy and virial theorem
    # For E=0: v² = -2V/m, where V = -m²(1/d + 1/2d) = -3m²/(2d)
    # v = √(3m/(2d)) for m=1

    v_mag = np.sqrt(3.0 / (2*d))

    # Velocities toward center
    vx1, vy1 = v_mag, 0.0  # Moving right (toward center)
    vx2, vy2 = 0.0, 0.0    # At center, stationary initially
    vx3, vy3 = -v_mag, 0.0 # Moving left (toward center)

    p = np.array([vx1, vy1, vx2, vy2, vx3, vy3])

    # This is not periodic - it collapses to triple collision!
    # For Morales-Ramis test, we need to regularize or use short time interval

    # Collision time (approximate): t_c ≈ d/v
    t_collision = d / v_mag

    # "Period" for analysis purposes (before collision)
    period = 0.5 * t_collision  # Analyze before collision

    # Energy (should be ~ 0 for homothetic E=0 solution)
    T = 0.5 * (2 * v_mag**2 + 0)  # Two moving bodies
    V = -1.0/d - 1.0/(2*d) - 1.0/d  # Three pairs: 1-2, 2-3, 1-3 (1-3 at 2d)
    E = T + V

    return PeriodicOrbit(
        name="Euler_Collinear_EqualMass",
        initial_condition=np.concatenate([q, p]),
        period=period,  # Time before collision
        mass_ratios=(1.0, 1.0, 1.0),
        energy=E,
        angular_momentum=0.0,  # Zero angular momentum
        description=(
            "Euler collinear configuration (equal masses, zero L). "
            "Homothetic collapse solution. Not truly periodic (ends in collision)."
        ),
        reference="Euler (1767), Combot (2012)",
        stability_type="unstable"
    )


# =============================================================================
# Figure-8 Choreography
# =============================================================================

def figure_8_choreography_approximate() -> PeriodicOrbit:
    """
    Approximate Figure-8 choreography (Moore 1993, Chenciner-Montgomery 2000).

    Three equal masses chasing each other along a figure-8 curve.

    Note:
        This is an approximate initial condition. For high-precision,
        use homotopy continuation from literature values.

    Returns:
        PeriodicOrbit for Figure-8

    Reference:
        Moore (1993), Chenciner & Montgomery (2000), Simó (2002)
    """
    # Approximate initial condition from Simó (2002)
    # Body 1 starts on right lobe, bodies 2 and 3 symmetric

    # These are approximate - for real calculations, use high-precision from literature
    x1 = 0.97000436  # Body 1 position
    y1 = -0.24308753

    # Bodies 2 and 3 at symmetric positions
    # Using 120-degree rotational symmetry
    theta = 2*np.pi/3
    cos_theta, sin_theta = np.cos(theta), np.sin(theta)

    x2 = x1 * cos_theta - y1 * sin_theta
    y2 = x1 * sin_theta + y1 * cos_theta

    x3 = x1 * cos_theta - y1 * (-sin_theta)  # Other direction
    y3 = x1 * (-sin_theta) + y1 * cos_theta

    q = np.array([x1, y1, x2, y2, x3, y3])

    # Velocities (also from Simó, approximate)
    vx1 = -0.93240737 / 2  # Divided by 2 for units
    vy1 = -0.86473146 / 2

    vx2 = vx1 * cos_theta - vy1 * sin_theta
    vy2 = vx1 * sin_theta + vy1 * cos_theta

    vx3 = vx1 * cos_theta - vy1 * (-sin_theta)
    vy3 = vx1 * (-sin_theta) + vy1 * cos_theta

    p = np.array([vx1, vy1, vx2, vy2, vx3, vy3])

    # Period from Chenciner-Montgomery: T ≈ 6.3259
    period = 6.32591398  # High-precision value from literature

    # Energy and angular momentum
    # For choreographic solution with equal masses at unit separation
    E_approx = -1.0  # Approximate
    L_approx = 0.0   # Zero angular momentum for figure-8

    return PeriodicOrbit(
        name="Figure8_Choreography",
        initial_condition=np.concatenate([q, p]),
        period=period,
        mass_ratios=(1.0, 1.0, 1.0),
        energy=E_approx,
        angular_momentum=L_approx,
        description=(
            "Figure-8 choreography discovered by Moore (1993), "
            "proven to exist by Chenciner & Montgomery (2000). "
            "Three equal masses chase each other on figure-8 curve."
        ),
        reference="Moore (1993), Chenciner & Montgomery (2000), Simó (2002)",
        stability_type="unstable"
    )


# =============================================================================
# Orbit Integration and Validation
# =============================================================================

def integrate_orbit(
    orbit: PeriodicOrbit,
    hamiltonian: Callable[[np.ndarray], float],
    n_periods: float = 1.0,
    n_points: int = 1000,
    **integrator_kwargs
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Integrate periodic orbit for validation.

    Args:
        orbit: Periodic orbit specification
        hamiltonian: Hamiltonian function H(q, p) → scalar
        n_periods: Number of periods to integrate
        n_points: Number of output points
        **integrator_kwargs: Additional arguments for solve_ivp

    Returns:
        times: Time array
        states: State array (n_points, 2n)
    """
    def hamilton_rhs(t, y):
        """Hamilton's equations: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q"""
        n = len(y) // 2

        # Numerical gradients
        eps = 1e-8
        dH_dq = np.zeros(n)
        dH_dp = np.zeros(n)

        H_0 = hamiltonian(y)

        for i in range(n):
            # ∂H/∂q_i
            y_plus = y.copy()
            y_plus[i] += eps
            dH_dq[i] = (hamiltonian(y_plus) - H_0) / eps

            # ∂H/∂p_i
            y_plus = y.copy()
            y_plus[n + i] += eps
            dH_dp[i] = (hamiltonian(y_plus) - H_0) / eps

        dq_dt = dH_dp   # ∂H/∂p
        dp_dt = -dH_dq  # -∂H/∂q

        return np.concatenate([dq_dt, dp_dt])

    # Time span
    t_final = orbit.period * n_periods
    t_eval = np.linspace(0, t_final, n_points)

    # Default integrator settings
    default_kwargs = {
        'method': 'DOP853',
        'rtol': 1e-10,
        'atol': 1e-12
    }
    default_kwargs.update(integrator_kwargs)

    # Integrate
    sol = solve_ivp(
        hamilton_rhs,
        (0, t_final),
        orbit.initial_condition,
        t_eval=t_eval,
        **default_kwargs
    )

    if not sol.success:
        raise RuntimeError(f"Integration failed: {sol.message}")

    return sol.t, sol.y.T


def validate_periodicity(
    orbit: PeriodicOrbit,
    hamiltonian: Callable,
    tolerance: float = 1e-4
) -> dict:
    """
    Validate that orbit is approximately periodic.

    Args:
        orbit: Orbit to validate
        hamiltonian: Hamiltonian function
        tolerance: Maximum error in closing condition

    Returns:
        Validation report dictionary
    """
    # Integrate for one period
    times, states = integrate_orbit(orbit, hamiltonian, n_periods=1.0, n_points=500)

    # Check closure
    initial_state = states[0]
    final_state = states[-1]
    closure_error = np.linalg.norm(final_state - initial_state)
    relative_error = closure_error / np.linalg.norm(initial_state)

    # Check energy conservation
    energies = np.array([hamiltonian(s) for s in states])
    energy_drift = np.abs(energies - energies[0])
    max_energy_drift = np.max(energy_drift)

    is_periodic = relative_error < tolerance
    energy_conserved = max_energy_drift < tolerance

    return {
        'is_periodic': is_periodic,
        'closure_error': closure_error,
        'relative_closure_error': relative_error,
        'max_energy_drift': max_energy_drift,
        'energy_conserved': energy_conserved,
        'validation_passed': is_periodic and energy_conserved
    }


# =============================================================================
# Orbit Catalog
# =============================================================================

def get_orbit_catalog() -> dict[str, PeriodicOrbit]:
    """
    Get catalog of all available periodic orbits.

    Returns:
        Dictionary mapping orbit names to PeriodicOrbit objects
    """
    catalog = {}

    # Lagrange configurations
    catalog['lagrange_l4_cr3bp'] = lagrange_l4_circular_restricted_3bp()
    catalog['lagrange_l4_cr3bp_earthmoon'] = lagrange_l4_circular_restricted_3bp(mu=0.012)
    catalog['lagrange_equilateral_equal'] = lagrange_l4_equal_masses()

    # Euler configurations
    catalog['euler_collinear_equal'] = euler_collinear_equal_masses()

    # Choreographies
    catalog['figure8'] = figure_8_choreography_approximate()

    return catalog


def get_orbit_by_name(name: str) -> Optional[PeriodicOrbit]:
    """
    Retrieve orbit by name from catalog.

    Args:
        name: Orbit name (key in catalog)

    Returns:
        PeriodicOrbit if found, None otherwise
    """
    catalog = get_orbit_catalog()
    return catalog.get(name)


def list_available_orbits() -> list[str]:
    """
    List names of all available orbits.

    Returns:
        List of orbit names
    """
    return list(get_orbit_catalog().keys())
