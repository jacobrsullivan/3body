"""
Three-body time-regularized dynamics (Phase 3).

Extends Phase 2 (single-pair) to handle three-body problem with:
- Pairwise spinor states with unified time
- Global Sundman transformation
- Time-regularized Hamiltonian for three bodies
- Full (4+1)-dimensional KS lift for three pairs

Mathematical Framework:
    State space: (u12, u23, u31, p12, p23, p31, s, K, t, E)
    where each uᵢⱼ ∈ ℝ⁴ (spinor), pᵢⱼ ∈ ℝ⁴ (conjugate momentum)
    Total: 3×4 + 3×4 + 1 + 1 + 1 + 1 = 28 variables (s is independent → 27D state vector)

    Time transformation: dt/ds = Ω(r12, r23, r31)
    Energy relation: K = E · Ω

    Equations of motion:
        duᵢⱼ/ds = pᵢⱼ
        dpᵢⱼ/ds = ∂H/∂uᵢⱼ
        dt/ds = Ω
        dK/ds = E · dΩ/ds
        dE/ds = 0
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Callable
import numpy as np
from scipy.integrate import solve_ivp

from .spinor_vector import SpinorVector
from .ks_pairwise import PairwiseSpinorState
from .sundman import (
    compute_time_dilation_threebody,
    TimeTransformationStrategy,
    SundmanTransformation
)

# Type alias for convenience
SundmanStrategy = str  # Will convert to TimeTransformationStrategy
from .levi_civita import levi_civita_map
from ..coordinates.base import Masses


@dataclass(frozen=True)
class PairwiseSpinorStateWithTime:
    """
    Extended pairwise spinor state with time regularization.

    This combines:
    - Pairwise spinor coordinates (Phase 0: three-body KS)
    - Dual-time tracking (Phase 1: extended phase space)
    - Energy tracking (Phase 1: K and E)

    Attributes:
        u12, u23, u31: Spinor coordinates for each pair (∈ ℝ⁴)
        p_u12, p_u23, p_u31: Conjugate momenta (∈ ℝ⁴)
        s: Fictitious time (independent variable)
        K: Regularized energy = E · Ω
        t: Physical time
        E: Physical energy (conserved)

    Dimension: 28 total variables
        - 12 spinor coordinates (3 pairs × 4 components)
        - 12 conjugate momenta
        - 1 fictitious time s
        - 1 regularized energy K
        - 1 physical time t
        - 1 physical energy E
        - s is independent variable during integration → state vector is 27D
    """
    u12: SpinorVector
    u23: SpinorVector
    u31: SpinorVector
    p_u12: SpinorVector
    p_u23: SpinorVector
    p_u31: SpinorVector
    s: float
    K: float
    t: float
    E: float

    @property
    def spinor_coordinates(self) -> np.ndarray:
        """Stack all spinor coordinates: shape (12,)"""
        return np.concatenate([
            self.u12.to_array(),
            self.u23.to_array(),
            self.u31.to_array()
        ])

    @property
    def conjugate_momenta(self) -> np.ndarray:
        """Stack all conjugate momenta: shape (12,)"""
        return np.concatenate([
            self.p_u12.to_array(),
            self.p_u23.to_array(),
            self.p_u31.to_array()
        ])

    def get_pairwise_radii(self) -> Tuple[float, float, float]:
        """Get pairwise separation distances."""
        r12 = np.linalg.norm(self.u12.to_array())**2
        r23 = np.linalg.norm(self.u23.to_array())**2
        r31 = np.linalg.norm(self.u31.to_array())**2
        return r12, r23, r31

    def compute_time_dilation(self, strategy: SundmanStrategy = "sum") -> float:
        """
        Compute time dilation factor Ω for this state.

        Args:
            strategy: Sundman combination strategy

        Returns:
            Ω(r12, r23, r31)
        """
        r12, r23, r31 = self.get_pairwise_radii()

        # Convert string strategy to enum
        if isinstance(strategy, str):
            strategy_enum = getattr(TimeTransformationStrategy, strategy.upper())
        else:
            strategy_enum = strategy

        result = compute_time_dilation_threebody(
            r12=r12, r23=r23, r31=r31,
            strategy=strategy_enum
        )
        return result.Omega

    def validate_time_relation(self, tolerance: float = 1e-6) -> bool:
        """Validate K = E · Ω(u)"""
        Omega = self.compute_time_dilation()
        expected_K = self.E * Omega
        error = abs(self.K - expected_K)
        return error < tolerance

    def to_vector(self) -> np.ndarray:
        """
        Convert to state vector for integration.

        Excludes s (independent variable), includes K, t, E.

        Returns:
            State vector [u12, u23, u31, p12, p23, p31, t, K, E] ∈ ℝ²⁷
        """
        return np.concatenate([
            self.spinor_coordinates,  # 12
            self.conjugate_momenta,   # 12
            [self.t],                 # 1
            [self.K],                 # 1
            [self.E]                  # 1
        ])  # Total: 27

    @classmethod
    def from_vector(
        cls,
        vec: np.ndarray,
        s: float
    ) -> "PairwiseSpinorStateWithTime":
        """
        Reconstruct from state vector.

        Args:
            vec: State vector [u12, u23, u31, p12, p23, p31, t, K, E] ∈ ℝ²⁷
            s: Fictitious time

        Returns:
            PairwiseSpinorStateWithTime
        """
        if len(vec) != 27:
            raise ValueError(f"Expected vector of length 27, got {len(vec)}")

        # Extract components
        u12 = SpinorVector(vec[0:4])
        u23 = SpinorVector(vec[4:8])
        u31 = SpinorVector(vec[8:12])

        p_u12 = SpinorVector(vec[12:16])
        p_u23 = SpinorVector(vec[16:20])
        p_u31 = SpinorVector(vec[20:24])

        t = vec[24]
        K = vec[25]
        E = vec[26]

        return cls(
            u12=u12, u23=u23, u31=u31,
            p_u12=p_u12, p_u23=p_u23, p_u31=p_u31,
            s=s, K=K, t=t, E=E
        )


@dataclass
class ThreeBodyTimeRegularizedHamiltonian:
    """
    Time-regularized Hamiltonian for three-body problem.

    H_reg(u, p_u, K) = (1/2)‖p_u‖² - K/Ω + V_reg(u)

    where:
    - V_reg includes gravitational potential in regularized coordinates
    - Ω = Ω(r12, r23, r31) is the global time dilation

    Attributes:
        masses: Mass parameters (m1, m2, m3, G)
        strategy: Sundman combination strategy
    """
    masses: Masses
    strategy: SundmanStrategy = "sum"
    G: float = 1.0  # Gravitational constant

    def evaluate(self, state: PairwiseSpinorStateWithTime) -> float:
        """
        Evaluate Hamiltonian at given state.

        Args:
            state: Current state

        Returns:
            H_reg value
        """
        # Kinetic energy: (1/2)‖p_u‖²
        p = state.conjugate_momenta
        T = 0.5 * np.dot(p, p)

        # Time dilation factor
        Omega = state.compute_time_dilation(self.strategy)

        # Regularized energy term
        energy_term = -state.K / Omega if Omega > 1e-10 else 0.0

        # Gravitational potential (in spinor coordinates)
        V = self._compute_potential(state)

        return T + energy_term + V

    def _compute_potential(self, state: PairwiseSpinorStateWithTime) -> float:
        """
        Compute gravitational potential in spinor coordinates.

        V = -G(m1m2/r12 + m2m3/r23 + m3m1/r31)

        where rᵢⱼ = ‖uᵢⱼ‖² in KS coordinates.
        """
        r12, r23, r31 = state.get_pairwise_radii()

        m1, m2, m3 = self.masses.m1, self.masses.m2, self.masses.m3

        # Prevent division by zero
        eps = 1e-10
        V = -self.G * (
            m1 * m2 / max(r12, eps) +
            m2 * m3 / max(r23, eps) +
            m3 * m1 / max(r31, eps)
        )

        return V

    def compute_forces(self, state: PairwiseSpinorStateWithTime) -> dict:
        """
        Compute forces (∂H/∂u) for each pair.

        Returns:
            Dictionary with force components for each pair
        """
        # Use finite differences for gradient
        eps = 1e-8
        forces = {}

        for pair_name in ['u12', 'u23', 'u31']:
            u = getattr(state, pair_name).to_array()
            grad = np.zeros(4)

            for i in range(4):
                # Perturb component i
                u_plus = u.copy()
                u_plus[i] += eps

                # Create perturbed state
                state_plus = self._replace_spinor(state, pair_name, u_plus)
                H_plus = self.evaluate(state_plus)

                u_minus = u.copy()
                u_minus[i] -= eps
                state_minus = self._replace_spinor(state, pair_name, u_minus)
                H_minus = self.evaluate(state_minus)

                grad[i] = (H_plus - H_minus) / (2 * eps)

            forces[pair_name] = grad

        return forces

    def _replace_spinor(
        self,
        state: PairwiseSpinorStateWithTime,
        pair_name: str,
        new_u: np.ndarray
    ) -> PairwiseSpinorStateWithTime:
        """Helper to create state with one spinor replaced."""
        kwargs = {
            'u12': state.u12,
            'u23': state.u23,
            'u31': state.u31,
            'p_u12': state.p_u12,
            'p_u23': state.p_u23,
            'p_u31': state.p_u31,
            's': state.s,
            'K': state.K,
            't': state.t,
            'E': state.E
        }
        kwargs[pair_name] = SpinorVector(new_u)
        return PairwiseSpinorStateWithTime(**kwargs)


def integrate_threebody_time_regularized(
    initial_state: PairwiseSpinorStateWithTime,
    hamiltonian: ThreeBodyTimeRegularizedHamiltonian,
    s_span: Tuple[float, float],
    n_points: int = 1000,
    rtol: float = 1e-10,
    atol: float = 1e-12
) -> "ThreeBodyTrajectory":
    """
    Integrate three-body problem with time regularization.

    Integrates the equations:
        duᵢⱼ/ds = pᵢⱼ
        dpᵢⱼ/ds = -∂H/∂uᵢⱼ
        dt/ds = Ω(r12, r23, r31)
        dK/ds = E · dΩ/ds
        dE/ds = 0

    Args:
        initial_state: Initial condition
        hamiltonian: Three-body Hamiltonian
        s_span: Integration interval in fictitious time
        n_points: Number of output points
        rtol, atol: Integration tolerances

    Returns:
        ThreeBodyTrajectory with solution
    """
    def rhs(s: float, z: np.ndarray) -> np.ndarray:
        """Right-hand side of differential equations."""
        # Reconstruct state
        state = PairwiseSpinorStateWithTime.from_vector(z, s)

        # Get components
        u12, u23, u31 = state.u12.to_array(), state.u23.to_array(), state.u31.to_array()
        p12, p23, p31 = state.p_u12.to_array(), state.p_u23.to_array(), state.p_u31.to_array()
        K, E = state.K, state.E

        # Equations of motion: du/ds = p_u
        du12_ds = p12
        du23_ds = p23
        du31_ds = p31

        # Forces: dp/ds = -∂H/∂u
        forces = hamiltonian.compute_forces(state)
        dp12_ds = -forces['u12']
        dp23_ds = -forces['u23']
        dp31_ds = -forces['u31']

        # Time evolution: dt/ds = Ω
        Omega = state.compute_time_dilation(hamiltonian.strategy)
        dt_ds = Omega

        # K evolution: dK/ds = E · dΩ/ds
        # dΩ/ds = (∂Ω/∂r12)(dr12/ds) + (∂Ω/∂r23)(dr23/ds) + (∂Ω/∂r31)(dr31/ds)
        # where rᵢⱼ = ‖uᵢⱼ‖², so drᵢⱼ/ds = 2uᵢⱼ·(duᵢⱼ/ds) = 2uᵢⱼ·pᵢⱼ
        r12, r23, r31 = state.get_pairwise_radii()

        # Get strategy enum
        if isinstance(hamiltonian.strategy, str):
            strategy_enum = getattr(TimeTransformationStrategy, hamiltonian.strategy.upper())
        else:
            strategy_enum = hamiltonian.strategy

        # Create Sundman transformation and compute gradient
        sundman = SundmanTransformation(strategy_enum)
        dOmega_dr = sundman.compute_derivative(r12, r23, r31)  # ∂Ω/∂rᵢⱼ

        # Compute dr/ds
        dr12_ds = 2.0 * np.dot(u12, p12)
        dr23_ds = 2.0 * np.dot(u23, p23)
        dr31_ds = 2.0 * np.dot(u31, p31)

        # Chain rule: dΩ/ds = ∂Ω/∂r · dr/ds
        dOmega_ds = dOmega_dr[0] * dr12_ds + dOmega_dr[1] * dr23_ds + dOmega_dr[2] * dr31_ds

        dK_ds = E * dOmega_ds

        # Energy conservation: dE/ds = 0
        dE_ds = 0.0

        # Assemble derivative vector
        dz_ds = np.concatenate([
            du12_ds, du23_ds, du31_ds,  # 12 components
            dp12_ds, dp23_ds, dp31_ds,  # 12 components
            [dt_ds],                      # 1 component
            [dK_ds],                      # 1 component
            [dE_ds]                       # 1 component
        ])  # Total: 27

        return dz_ds

    # Initial condition
    z0 = initial_state.to_vector()

    # Solve
    s_eval = np.linspace(s_span[0], s_span[1], n_points)
    sol = solve_ivp(
        rhs,
        s_span,
        z0,
        t_eval=s_eval,
        rtol=rtol,
        atol=atol,
        method='DOP853'
    )

    if not sol.success:
        raise RuntimeError(f"Integration failed: {sol.message}")

    # Package results
    return ThreeBodyTrajectory(
        s_values=sol.t,
        states=[PairwiseSpinorStateWithTime.from_vector(sol.y[:, i], sol.t[i])
                for i in range(len(sol.t))],
        hamiltonian=hamiltonian
    )


@dataclass
class ThreeBodyTrajectory:
    """
    Solution trajectory for three-body time-regularized integration.

    Attributes:
        s_values: Fictitious time values
        states: List of PairwiseSpinorStateWithTime
        hamiltonian: Hamiltonian used for integration
    """
    s_values: np.ndarray
    states: list[PairwiseSpinorStateWithTime]
    hamiltonian: ThreeBodyTimeRegularizedHamiltonian

    @property
    def t_values(self) -> np.ndarray:
        """Extract physical time values."""
        return np.array([state.t for state in self.states])

    def get_energies(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract energy values along trajectory.

        Returns:
            (E_values, K_values): Physical and regularized energies
        """
        E_vals = np.array([state.E for state in self.states])
        K_vals = np.array([state.K for state in self.states])
        return E_vals, K_vals

    def get_time_dilations(self) -> np.ndarray:
        """Extract time dilation factors."""
        return np.array([state.compute_time_dilation(self.hamiltonian.strategy)
                        for state in self.states])

    def get_pairwise_separations(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract pairwise separation distances.

        Returns:
            (r12_values, r23_values, r31_values)
        """
        r12_vals = []
        r23_vals = []
        r31_vals = []

        for state in self.states:
            r12, r23, r31 = state.get_pairwise_radii()
            r12_vals.append(r12)
            r23_vals.append(r23)
            r31_vals.append(r31)

        return np.array(r12_vals), np.array(r23_vals), np.array(r31_vals)

    def validate_conservation(self) -> dict:
        """
        Validate conservation laws along trajectory.

        Returns:
            Dictionary with conservation metrics
        """
        E_vals, K_vals = self.get_energies()
        Omega_vals = self.get_time_dilations()

        # E should be conserved
        E_drift = np.std(E_vals)
        E_conserved = E_drift < 1e-6

        # K = E·Ω should be maintained
        K_expected = E_vals * Omega_vals
        time_relation_error = np.max(np.abs(K_vals - K_expected))
        time_relation_satisfied = time_relation_error < 1e-4

        return {
            'E_conserved': E_conserved,
            'E_drift': E_drift,
            'E_mean': np.mean(E_vals),
            'time_relation_satisfied': time_relation_satisfied,
            'time_relation_error': time_relation_error,
            'K_mean': np.mean(K_vals),
            'Omega_min': np.min(Omega_vals),
            'Omega_max': np.max(Omega_vals)
        }
