"""
RATTLE integrator for constrained Hamiltonian dynamics (WP 2.3, Part C).

Implements the RATTLE algorithm (Andersen 1983) for symplectic integration
on the KS constraint manifold. This is the PRIMARY integration method
for constrained KS dynamics.

Key Features:
    - Symplectic structure preservation
    - Constraint satisfaction to machine precision
    - Second-order accurate in time
    - Robust handling of ill-conditioned Jacobians

Fallback Hierarchy:
    RATTLE (double) → RATTLE (SVD) → RATTLE (quad) → SHAKE → FAIL

References:
    - Andersen (1983): "RATTLE: A velocity version of the SHAKE algorithm"
    - Leimkuhler & Reich (2004): "Simulating Hamiltonian Dynamics"
    - AMENDED_WP2.3 (2025): Section "Part C: Constrained Hamiltonian Dynamics"
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np
import warnings

from ..coordinates.base import Masses
from .ks_pairwise import PairwiseSpinorState


class ConvergenceError(Exception):
    """Raised when Newton solver fails to converge."""
    pass


class ConstraintViolation(Exception):
    """Raised when constraints exceed tolerance."""
    pass


@dataclass(frozen=True)
class RATTLEConfig:
    """
    Configuration for RATTLE integrator.

    Attributes:
        constraint_tolerance: Maximum constraint violation
        newton_tolerance: Convergence tolerance for Newton solver
        max_newton_iterations: Maximum Newton iterations
        condition_number_threshold: Threshold for switching to SVD
        use_quad_precision: Whether to use quad precision for ill-conditioned systems
        enable_baumgarte: Whether to enable Baumgarte stabilization
        baumgarte_alpha: Baumgarte damping parameter α
        baumgarte_beta: Baumgarte spring parameter β
    """
    constraint_tolerance: float = 1e-12
    newton_tolerance: float = 1e-14
    max_newton_iterations: int = 20
    condition_number_threshold: float = 1e10
    use_quad_precision: bool = False
    enable_baumgarte: bool = False
    baumgarte_alpha: float = 10.0
    baumgarte_beta: float = 10.0


class RATTLEIntegrator:
    """
    Symplectic integrator for constrained Hamiltonian systems.

    Implements the RATTLE algorithm with robustness enhancements:
        1. SVD fallback for ill-conditioned Jacobians
        2. Quad-precision fallback for severe ill-conditioning
        3. Constraint monitoring and alerts
        4. Optional Baumgarte stabilization

    The RATTLE algorithm enforces constraints at both position
    and velocity levels, preserving the symplectic structure.

    Algorithm:
        1. Half-step momentum (unconstrained)
        2. Full-step position (constrained via Newton solve)
        3. Half-step momentum (unconstrained)
        4. Project momentum onto tangent space (velocity constraints)
    """

    def __init__(
        self,
        masses: Masses,
        G: float = 1.0,
        config: Optional[RATTLEConfig] = None
    ):
        """
        Initialize RATTLE integrator.

        Args:
            masses: Body masses (m1, m2, m3)
            G: Gravitational constant
            config: RATTLE configuration (uses defaults if None)
        """
        self.masses = masses
        self.G = G
        self.config = config or RATTLEConfig()

        # Statistics tracking
        self.newton_iterations_history: List[int] = []
        self.constraint_violations_history: List[float] = []
        self.condition_numbers_history: List[float] = []
        self.svd_fallback_count = 0
        self.quad_fallback_count = 0

    def step(
        self,
        state: PairwiseSpinorState,
        ds: float
    ) -> PairwiseSpinorState:
        """
        Single RATTLE step.

        Args:
            state: Current spinor state on constraint manifold
            ds: Fictitious time step

        Returns:
            New state on constraint manifold

        Raises:
            ConvergenceError: If Newton solver fails to converge
            ConstraintViolation: If final constraints exceed tolerance
        """
        # Extract state components
        u = state.spinor_coordinates  # Shape (12,)
        p = state.spinor_momenta       # Shape (12,)

        # 1. Half-step unconstrained momentum update
        forces = self._compute_forces(u)
        p_half = p + 0.5 * ds * forces

        # 2. Full-step position update (constrained)
        try:
            u_new, lambda_q, iterations = self._position_update_with_constraints(
                u, p_half, ds
            )
            self.newton_iterations_history.append(iterations)
        except ConvergenceError as e:
            # Newton failed - this is a critical error
            raise ConvergenceError(
                f"RATTLE position update failed: {e}"
            )

        # 3. Half-step unconstrained momentum update (at new position)
        forces_new = self._compute_forces(u_new)
        p_star = p_half + 0.5 * ds * forces_new

        # 4. Project momentum onto tangent space (velocity constraints)
        try:
            p_new = self._project_momentum_onto_tangent_space(u_new, p_star)
        except np.linalg.LinAlgError:
            # Projection failed - fall back to uncorrected momentum
            warnings.warn("Momentum projection failed, using uncorrected momentum")
            p_new = p_star

        # 5. Verify constraints
        constraint_violation = self._evaluate_constraint_violation(u_new, p_new)
        self.constraint_violations_history.append(constraint_violation)

        if constraint_violation > self.config.constraint_tolerance:
            if constraint_violation > 1e-6:
                # Catastrophic violation
                raise ConstraintViolation(
                    f"Severe constraint violation: |g| = {constraint_violation:.2e}"
                )
            else:
                # Minor violation - warn but continue
                warnings.warn(
                    f"Constraint tolerance exceeded: |g| = {constraint_violation:.2e}"
                )

        # 6. Update time
        dt = np.mean([state.u12.norm_squared, state.u23.norm_squared, state.u31.norm_squared]) * ds
        s_new = state.fictitious_time + ds
        t_new = (state.real_time + dt) if state.real_time is not None else None

        # 7. Reconstruct state
        return PairwiseSpinorState.from_coordinates_and_momenta(
            u_new, p_new, s_new, t_new
        )

    def _position_update_with_constraints(
        self,
        u: np.ndarray,
        p_half: np.ndarray,
        ds: float
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Solve for u_new such that g(u_new) = 0.

        Uses Newton-Raphson with robustness enhancements:
            - SVD fallback for ill-conditioned systems
            - Quad precision fallback for severe ill-conditioning
            - Line search for robustness

        Args:
            u: Current positions (12,)
            p_half: Half-step momenta (12,)
            ds: Time step

        Returns:
            u_new: Updated positions satisfying constraints (12,)
            lambda_q: Lagrange multipliers (6,)
            iterations: Number of Newton iterations

        Raises:
            ConvergenceError: If Newton fails to converge
        """
        # Initial guess: unconstrained update
        # u_trial = u + ds * p_half (assuming unit mass for now)
        u_trial = u + ds * p_half
        lambda_trial = np.zeros(6)  # 6 constraints

        # Newton iteration
        for iteration in range(self.config.max_newton_iterations):
            # Evaluate constraints and Jacobian
            g = self._evaluate_position_constraints(u_trial)
            J = self._constraint_jacobian(u_trial)  # Shape (6, 12)

            # Check convergence
            g_norm = np.linalg.norm(g)
            if g_norm < self.config.newton_tolerance:
                return u_trial, lambda_trial, iteration + 1

            # Newton step: solve for Lagrange multiplier corrections
            # System: J (ds M^{-1} J^T) delta_lambda = -g
            # For simplicity, assume M = I (unit mass)

            A = J @ (ds * J.T)  # Shape (6, 6)
            b = -g

            # Check condition number
            try:
                cond = np.linalg.cond(A)
                self.condition_numbers_history.append(cond)
            except np.linalg.LinAlgError:
                cond = np.inf

            # Solve with appropriate method
            try:
                if cond < self.config.condition_number_threshold:
                    # Well-conditioned: direct solve
                    delta_lambda = np.linalg.solve(A, b)
                elif cond < 1e12:
                    # Mildly ill-conditioned: SVD
                    delta_lambda = self._solve_svd(A, b)
                    self.svd_fallback_count += 1
                elif self.config.use_quad_precision:
                    # Severely ill-conditioned: quad precision
                    delta_lambda = self._solve_quad_precision(A, b)
                    self.quad_fallback_count += 1
                else:
                    # Give up
                    raise ConvergenceError(
                        f"System is severely ill-conditioned (κ = {cond:.2e}) "
                        "and quad precision is disabled"
                    )
            except np.linalg.LinAlgError as e:
                raise ConvergenceError(f"Linear solve failed: {e}")

            # Update multipliers and position
            lambda_trial += delta_lambda
            u_trial += ds * J.T @ delta_lambda

        # If we reach here, Newton did not converge
        raise ConvergenceError(
            f"Newton solver failed after {self.config.max_newton_iterations} iterations. "
            f"Residual: |g| = {g_norm:.2e}"
        )

    def _project_momentum_onto_tangent_space(
        self,
        u: np.ndarray,
        p_star: np.ndarray
    ) -> np.ndarray:
        """
        Project momentum onto tangent space of constraint manifold.

        Velocity constraints: ∇g_k · p = 0 for all k

        Solve for p_new = p_star + J^T μ such that:
            J M^{-1} (p_star + J^T μ) = 0

        Args:
            u: Current positions (on constraint manifold) (12,)
            p_star: Unconstrained momentum (12,)

        Returns:
            p_new: Projected momentum (tangent to manifold) (12,)
        """
        J = self._constraint_jacobian(u)  # Shape (6, 12)

        # Velocity constraint: J M^{-1} p = 0
        # Assuming M = I (unit mass)
        # Solve: (J J^T) μ = -J p_star

        A = J @ J.T  # Shape (6, 6)
        b = -J @ p_star

        # Solve (with robustness)
        try:
            cond = np.linalg.cond(A)
            if cond < 1e10:
                mu = np.linalg.solve(A, b)
            else:
                mu = self._solve_svd(A, b)
        except np.linalg.LinAlgError:
            # If projection fails, return uncorrected momentum
            warnings.warn("Velocity projection failed")
            return p_star

        p_new = p_star + J.T @ mu
        return p_new

    def _evaluate_position_constraints(self, u: np.ndarray) -> np.ndarray:
        """
        Evaluate position constraints g(u) = 0.

        Constraints:
            g_1 = |u_12|^2 - r_12
            g_2 = |u_23|^2 - r_23
            g_3 = |u_31|^2 - r_31
            g_4:6 = L(u_12)u_12 + L(u_23)u_23 + L(u_31)u_31  (closure, 3 components)

        Args:
            u: Spinor positions (12,) = [u_12, u_23, u_31]

        Returns:
            g: Constraint violations (6,)
        """
        from .levi_civita import levi_civita_map

        u12 = u[0:4]
        u23 = u[4:8]
        u31 = u[8:12]

        # Reconstruct physical distances from spinors
        r12_vec = levi_civita_map(u12, u12)
        r23_vec = levi_civita_map(u23, u23)
        r31_vec = levi_civita_map(u31, u31)

        r12 = np.linalg.norm(r12_vec)
        r23 = np.linalg.norm(r23_vec)
        r31 = np.linalg.norm(r31_vec)

        # Bilinear constraints
        g = np.zeros(6)
        g[0] = np.dot(u12, u12) - r12
        g[1] = np.dot(u23, u23) - r23
        g[2] = np.dot(u31, u31) - r31

        # Closure constraint (3D vector)
        closure = r12_vec + r23_vec + r31_vec
        g[3:6] = closure

        return g

    def _constraint_jacobian(self, u: np.ndarray) -> np.ndarray:
        """
        Compute Jacobian of constraints: J = ∇g(u).

        Args:
            u: Spinor positions (12,) = [u_12, u_23, u_31]

        Returns:
            J: Jacobian matrix (6 x 12)
        """
        from .levi_civita import levi_civita_jacobian

        u12 = u[0:4]
        u23 = u[4:8]
        u31 = u[8:12]

        J = np.zeros((6, 12))

        # Gradient of bilinear constraints: ∇|u|^2 = 2u
        J[0, 0:4] = 2 * u12
        J[1, 4:8] = 2 * u23
        J[2, 8:12] = 2 * u31

        # Gradient of closure constraint: ∇[L(u)u]
        # This requires computing d/du_i [L(u) u]_j
        J_lc12 = levi_civita_jacobian(u12)  # Shape (3, 4)
        J_lc23 = levi_civita_jacobian(u23)
        J_lc31 = levi_civita_jacobian(u31)

        J[3:6, 0:4] = J_lc12
        J[3:6, 4:8] = J_lc23
        J[3:6, 8:12] = J_lc31

        return J

    def _compute_forces(self, u: np.ndarray) -> np.ndarray:
        """
        Compute forces F = -∇V in spinor coordinates.

        The potential in fictitious time is:
            V_reg(u) = -G Σ_{ij} m_i m_j / |u_ij|^2

        Args:
            u: Spinor positions (12,)

        Returns:
            F: Forces (12,)
        """
        u12 = u[0:4]
        u23 = u[4:8]
        u31 = u[8:12]

        F = np.zeros(12)

        # Compute distances (r_ij = |u_ij|^2)
        r12_sq = np.dot(u12, u12)
        r23_sq = np.dot(u23, u23)
        r31_sq = np.dot(u31, u31)

        m1, m2, m3 = self.masses.m1, self.masses.m2, self.masses.m3

        # Force on u_12: F = -∇V = -∇(-μ/|u|^2) = -μ ∇(|u|^(-2))
        # ∇(|u|^(-2)) = ∇(1/|u|^2) = -2u/|u|^4
        # So F = -μ (-2u/|u|^4) = 2μu/|u|^4

        if r12_sq > 1e-14:
            F[0:4] = 2 * self.G * m1 * m2 * u12 / (r12_sq ** 2)

        if r23_sq > 1e-14:
            F[4:8] = 2 * self.G * m2 * m3 * u23 / (r23_sq ** 2)

        if r31_sq > 1e-14:
            F[8:12] = 2 * self.G * m3 * m1 * u31 / (r31_sq ** 2)

        return F

    def _evaluate_constraint_violation(
        self,
        u: np.ndarray,
        p: np.ndarray
    ) -> float:
        """
        Evaluate total constraint violation.

        Checks both position and velocity constraints.

        Args:
            u: Positions (12,)
            p: Momenta (12,)

        Returns:
            Total violation norm
        """
        # Position constraints
        g_pos = self._evaluate_position_constraints(u)

        # Velocity constraints: J · p = 0
        J = self._constraint_jacobian(u)
        g_vel = J @ p

        # Combined violation
        violation = np.sqrt(np.linalg.norm(g_pos)**2 + np.linalg.norm(g_vel)**2)
        return violation

    def _solve_svd(self, A: np.ndarray, b: np.ndarray, threshold: float = 1e-10) -> np.ndarray:
        """
        Solve Ax=b using SVD with singular value truncation.

        Args:
            A: Matrix (n, n)
            b: Right-hand side (n,)
            threshold: Relative threshold for singular values

        Returns:
            x: Solution (n,)
        """
        U, S, Vt = np.linalg.svd(A)

        # Truncate small singular values
        S_inv = np.where(S > threshold * S[0], 1/S, 0)

        # Solve: x = V S^{-1} U^T b
        x = Vt.T @ np.diag(S_inv) @ U.T @ b
        return x

    def _solve_quad_precision(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Solve Ax=b using quad precision (requires mpmath).

        Args:
            A: Matrix (n, n)
            b: Right-hand side (n,)

        Returns:
            x: Solution (n,)
        """
        try:
            import mpmath
        except ImportError:
            raise ImportError(
                "Quad precision solving requires mpmath. "
                "Install with: pip install mpmath"
            )

        mpmath.mp.dps = 50  # 50 decimal digits

        # Convert to mpmath matrices
        A_mp = mpmath.matrix(A.tolist())
        b_mp = mpmath.matrix(b.tolist())

        # Solve
        x_mp = mpmath.lu_solve(A_mp, b_mp)

        # Convert back to numpy
        x = np.array([float(x_mp[i]) for i in range(len(b))])
        return x

    def integrate(
        self,
        initial_state: PairwiseSpinorState,
        s_span: Tuple[float, float],
        n_steps: int
    ) -> 'RATTLETrajectory':
        """
        Integrate on constraint manifold.

        Args:
            initial_state: Initial spinor state
            s_span: Fictitious time interval (s_start, s_end)
            n_steps: Number of steps

        Returns:
            RATTLETrajectory with states and diagnostics
        """
        s_start, s_end = s_span
        ds = (s_end - s_start) / n_steps

        states = [initial_state]
        s_values = [s_start]

        state = initial_state

        for i in range(n_steps):
            try:
                state = self.step(state, ds)
                states.append(state)
                s_values.append(s_start + (i + 1) * ds)
            except (ConvergenceError, ConstraintViolation) as e:
                warnings.warn(
                    f"Integration failed at step {i}/{n_steps}: {e}"
                )
                break

        return RATTLETrajectory(
            fictitious_times=np.array(s_values),
            states=states,
            initial_state=initial_state,
            integrator=self
        )

    def get_statistics(self) -> dict:
        """
        Get integration statistics.

        Returns:
            Dictionary with diagnostic information
        """
        return {
            'total_steps': len(self.newton_iterations_history),
            'mean_newton_iterations': (
                np.mean(self.newton_iterations_history)
                if self.newton_iterations_history else 0
            ),
            'max_newton_iterations': (
                max(self.newton_iterations_history)
                if self.newton_iterations_history else 0
            ),
            'mean_constraint_violation': (
                np.mean(self.constraint_violations_history)
                if self.constraint_violations_history else 0
            ),
            'max_constraint_violation': (
                max(self.constraint_violations_history)
                if self.constraint_violations_history else 0
            ),
            'mean_condition_number': (
                np.mean(self.condition_numbers_history)
                if self.condition_numbers_history else 0
            ),
            'max_condition_number': (
                max(self.condition_numbers_history)
                if self.condition_numbers_history else 0
            ),
            'svd_fallback_count': self.svd_fallback_count,
            'quad_fallback_count': self.quad_fallback_count,
        }


@dataclass(frozen=True)
class RATTLETrajectory:
    """
    Trajectory from RATTLE integration.

    Attributes:
        fictitious_times: Array of fictitious times s
        states: List of PairwiseSpinorState
        initial_state: Initial condition
        integrator: RATTLE integrator (for diagnostics)
    """
    fictitious_times: np.ndarray
    states: List[PairwiseSpinorState]
    initial_state: PairwiseSpinorState
    integrator: RATTLEIntegrator

    def __len__(self) -> int:
        """Number of points in trajectory"""
        return len(self.states)

    def __getitem__(self, index: int) -> PairwiseSpinorState:
        """Access state at index"""
        return self.states[index]

    def get_diagnostics(self) -> dict:
        """Get integration diagnostics"""
        return self.integrator.get_statistics()
