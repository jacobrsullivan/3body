"""
Symbolic conservation verification for candidate integrals (Task 3.3.2, 3.3.3 support).

This module validates symbolic expressions by:
1. Numerical conservation testing (integrate trajectories)
2. Symbolic-numerical agreement testing
3. Functional independence verification
4. Poisson bracket computation (preliminary WP4 preparation)

Validation ensures discovered integrals are genuine conserved quantities
before passing them to WP4 for rigorous mathematical verification.

References:
- Arnold, "Mathematical Methods of Classical Mechanics" (1989)
- Goldstein et al., "Classical Mechanics" (2002)
"""

import numpy as np
import sympy as sp
from typing import Callable, List, Tuple, Dict, Optional
from dataclasses import dataclass
from scipy.integrate import solve_ivp


@dataclass
class ValidationResult:
    """
    Result of conservation validation.

    Attributes:
        is_conserved: Whether quantity is conserved within tolerance
        conservation_error: Max relative drift |ΔI/I| over trajectories
        symbolic_numerical_residual: RMS difference between symbolic and numerical
        is_independent: Whether functionally independent of known integrals
        poisson_bracket_with_H: Symbolic Poisson bracket {I, H} (if computable)
        test_statistics: Additional statistics from testing
    """
    is_conserved: bool
    conservation_error: float
    symbolic_numerical_residual: float
    is_independent: Optional[bool] = None
    poisson_bracket_with_H: Optional[sp.Expr] = None
    test_statistics: Dict = None

    def __post_init__(self):
        if self.test_statistics is None:
            self.test_statistics = {}


def lambdify_expression(
    expr: sp.Expr,
    state_symbols: List[sp.Symbol]
) -> Callable[[np.ndarray], float]:
    """
    Convert SymPy expression to numerical evaluation function.

    Args:
        expr: SymPy expression
        state_symbols: List of symbols in order matching state vector

    Returns:
        eval_func: Function that takes state vector and returns scalar

    Example:
        >>> x, y = sp.symbols('x y')
        >>> expr = x**2 + y**2
        >>> f = lambdify_expression(expr, [x, y])
        >>> f(np.array([3, 4]))  # Returns 25.0
    """
    # Create lambdified function
    f_lambda = sp.lambdify(state_symbols, expr, 'numpy')

    def eval_func(state: np.ndarray) -> float:
        """Evaluate expression on state vector."""
        try:
            return float(f_lambda(*state))
        except:
            # Evaluation failed (singularity, etc.)
            return np.nan

    return eval_func


def validate_symbolic_numerical_agreement(
    expr_symbolic: sp.Expr,
    expr_numerical: Callable[[np.ndarray], float],
    sample_states: np.ndarray,
    state_symbols: List[sp.Symbol],
    tolerance: float = 1e-10
) -> Tuple[bool, float]:
    """
    Verify symbolic expression matches numerical function.

    Args:
        expr_symbolic: SymPy expression
        expr_numerical: Numerical evaluation function
        sample_states: Test states (N, dim)
        state_symbols: List of symbols
        tolerance: Acceptance tolerance

    Returns:
        agrees: True if expressions match within tolerance
        rms_residual: RMS difference over test states
    """
    # Convert symbolic to numerical
    f_symbolic = lambdify_expression(expr_symbolic, state_symbols)

    # Evaluate both on test states
    residuals = []
    for state in sample_states:
        val_sym = f_symbolic(state)
        val_num = expr_numerical(state)

        if not (np.isnan(val_sym) or np.isnan(val_num)):
            residuals.append(abs(val_sym - val_num))

    if len(residuals) == 0:
        return False, np.inf

    rms_residual = np.sqrt(np.mean(np.array(residuals)**2))
    agrees = rms_residual < tolerance

    return agrees, rms_residual


def test_conservation_on_trajectory(
    integral_func: Callable[[np.ndarray], float],
    hamiltonian_func: Callable[[np.ndarray], Tuple[np.ndarray, float]],
    initial_state: np.ndarray,
    t_span: float = 100.0,
    n_eval: int = 1000,
    tolerance: float = 1e-5
) -> Tuple[bool, float, np.ndarray]:
    """
    Test conservation by integrating a trajectory.

    Args:
        integral_func: Function to test for conservation
        hamiltonian_func: Function returning (dz/dt, H) for Hamilton's equations
        initial_state: Initial condition
        t_span: Integration time
        n_eval: Number of evaluation points
        tolerance: Relative conservation tolerance

    Returns:
        is_conserved: True if |ΔI/I| < tolerance
        max_drift: Maximum relative drift
        I_values: Time series of integral values

    Example:
        >>> def my_integral(z): return z[0]**2 + z[1]**2
        >>> def hamiltonian(z): return np.array([z[2], z[3], -z[0], -z[1]]), 0.5*sum(z**2)
        >>> conserved, drift, I_t = test_conservation_on_trajectory(my_integral, hamiltonian, np.ones(4))
    """
    # Define ODE system
    def dynamics(t, z):
        dz_dt, H = hamiltonian_func(z)
        return dz_dt

    # Integrate
    t_eval = np.linspace(0, t_span, n_eval)
    sol = solve_ivp(
        dynamics,
        [0, t_span],
        initial_state,
        t_eval=t_eval,
        method='DOP853',
        rtol=1e-10,
        atol=1e-12
    )

    if not sol.success:
        return False, np.inf, np.array([])

    # Evaluate integral along trajectory
    I_values = np.array([integral_func(sol.y[:, i]) for i in range(len(t_eval))])

    # Compute drift
    I_0 = I_values[0]
    if abs(I_0) < 1e-14:
        # Integral is zero - check absolute drift instead
        max_drift = np.max(np.abs(I_values))
    else:
        max_drift = np.max(np.abs((I_values - I_0) / I_0))

    is_conserved = max_drift < tolerance

    return is_conserved, max_drift, I_values


def test_conservation_ensemble(
    integral_func: Callable[[np.ndarray], float],
    hamiltonian_func: Callable[[np.ndarray], Tuple[np.ndarray, float]],
    initial_states: np.ndarray,
    t_span: float = 100.0,
    success_threshold: float = 0.9,
    tolerance: float = 1e-5
) -> Tuple[bool, float, List[float]]:
    """
    Test conservation on ensemble of trajectories.

    Args:
        integral_func: Integral to test
        hamiltonian_func: Hamiltonian dynamics
        initial_states: Array of initial conditions (N, dim)
        t_span: Integration time per trajectory
        success_threshold: Fraction of trajectories that must conserve (e.g., 0.9 = 90%)
        tolerance: Per-trajectory tolerance

    Returns:
        is_conserved: True if success_threshold fraction conserve
        mean_drift: Mean drift across all trajectories
        drift_list: List of drift values per trajectory
    """
    drift_list = []
    n_success = 0

    for initial_state in initial_states:
        conserved, drift, _ = test_conservation_on_trajectory(
            integral_func,
            hamiltonian_func,
            initial_state,
            t_span=t_span,
            tolerance=tolerance
        )

        drift_list.append(drift)
        if conserved:
            n_success += 1

    success_rate = n_success / len(initial_states)
    mean_drift = np.mean(drift_list)

    is_conserved = success_rate >= success_threshold

    return is_conserved, mean_drift, drift_list


def compute_poisson_bracket_symbolic(
    I: sp.Expr,
    H: sp.Expr,
    q_symbols: List[sp.Symbol],
    p_symbols: List[sp.Symbol]
) -> sp.Expr:
    """
    Compute Poisson bracket {I, H} symbolically.

    {I, H} = sum_i (∂I/∂q_i ∂H/∂p_i - ∂I/∂p_i ∂H/∂q_i)

    Args:
        I: Integral expression
        H: Hamiltonian expression
        q_symbols: Configuration variables
        p_symbols: Momentum variables

    Returns:
        poisson_bracket: Symbolic expression for {I, H}

    Example:
        >>> q, p = sp.symbols('q p')
        >>> I = q**2
        >>> H = p**2/2 + q**2/2
        >>> pb = compute_poisson_bracket_symbolic(I, [q], [p])
        >>> # Returns: 2*q*p
    """
    if len(q_symbols) != len(p_symbols):
        raise ValueError("Must have equal number of q and p symbols")

    poisson = sp.S.Zero

    for q, p in zip(q_symbols, p_symbols):
        dI_dq = sp.diff(I, q)
        dI_dp = sp.diff(I, p)
        dH_dq = sp.diff(H, q)
        dH_dp = sp.diff(H, p)

        poisson += dI_dq * dH_dp - dI_dp * dH_dq

    return sp.simplify(poisson)


def check_functional_independence(
    candidate_func: Callable[[np.ndarray], float],
    known_funcs: List[Callable[[np.ndarray], float]],
    sample_states: np.ndarray,
    tolerance: float = 1e-6
) -> bool:
    """
    Check if candidate is functionally independent of known integrals.

    Uses Jacobian rank test: if candidate is independent, the Jacobian
    matrix of [I_1, ..., I_k, I_candidate] should have rank k+1.

    Args:
        candidate_func: Candidate integral function
        known_funcs: List of known integral functions (E, L, etc.)
        sample_states: Sample points for testing (N, dim)
        tolerance: Numerical tolerance for rank determination

    Returns:
        is_independent: True if functionally independent

    Example:
        >>> # E = p^2, L = q*p, candidate = q^2 (independent)
        >>> states = np.random.randn(100, 2)
        >>> is_independent = check_functional_independence(
        ...     lambda z: z[0]**2,  # q^2
        ...     [lambda z: z[1]**2, lambda z: z[0]*z[1]],  # E, L
        ...     states
        ... )
    """
    n_known = len(known_funcs)
    n_states, state_dim = sample_states.shape

    # Compute Jacobian numerically
    epsilon = 1e-8

    # Evaluate all integrals on sample
    I_all = np.zeros((n_states, n_known + 1))

    for i in range(n_states):
        state = sample_states[i]

        # Known integrals
        for j, func in enumerate(known_funcs):
            I_all[i, j] = func(state)

        # Candidate integral
        I_all[i, n_known] = candidate_func(state)

    # Compute numerical Jacobian at representative points
    ranks = []

    for i in range(min(10, n_states)):  # Test at multiple points
        state = sample_states[i]
        jacobian = np.zeros((n_known + 1, state_dim))

        # Numerical derivatives
        for j, func in enumerate(known_funcs + [candidate_func]):
            for k in range(state_dim):
                state_plus = state.copy()
                state_plus[k] += epsilon
                state_minus = state.copy()
                state_minus[k] -= epsilon

                grad = (func(state_plus) - func(state_minus)) / (2 * epsilon)
                jacobian[j, k] = grad

        # Compute rank
        U, s, Vt = np.linalg.svd(jacobian, full_matrices=False)
        rank = np.sum(s > tolerance)
        ranks.append(rank)

    # If rank consistently increases by 1, candidate is independent
    expected_rank = n_known + 1
    mean_rank = np.mean(ranks)

    is_independent = abs(mean_rank - expected_rank) < 0.5  # Allow some numerical error

    return is_independent


def validate_candidate_integral(
    expr_symbolic: sp.Expr,
    expr_numerical: Callable[[np.ndarray], float],
    hamiltonian_func: Callable[[np.ndarray], Tuple[np.ndarray, float]],
    sample_states: np.ndarray,
    state_symbols: List[sp.Symbol],
    known_integrals: Optional[List[Callable]] = None,
    test_trajectories: Optional[np.ndarray] = None,
    hamiltonian_symbolic: Optional[sp.Expr] = None
) -> ValidationResult:
    """
    Comprehensive validation of candidate integral.

    This is the main validation entry point combining all tests.

    Args:
        expr_symbolic: SymPy expression
        expr_numerical: Numerical evaluation function
        hamiltonian_func: Hamiltonian dynamics function
        sample_states: Sample states for testing
        state_symbols: List of SymPy symbols
        known_integrals: Known conserved integrals for independence test
        test_trajectories: Initial conditions for trajectory tests
        hamiltonian_symbolic: Symbolic Hamiltonian (for Poisson bracket)

    Returns:
        result: ValidationResult with all test outcomes

    Example:
        >>> # Validate energy conservation
        >>> q, p = sp.symbols('q p')
        >>> E_sym = p**2/2 + q**2/2
        >>> E_num = lambda z: z[1]**2/2 + z[0]**2/2
        >>> def H_func(z): return np.array([z[1], -z[0]]), E_num(z)
        >>> samples = np.random.randn(100, 2)
        >>> result = validate_candidate_integral(E_sym, E_num, H_func, samples, [q, p])
    """
    # Test 1: Symbolic-numerical agreement
    agrees, residual = validate_symbolic_numerical_agreement(
        expr_symbolic,
        expr_numerical,
        sample_states,
        state_symbols,
        tolerance=1e-10
    )

    # Test 2: Conservation on trajectories
    if test_trajectories is None:
        test_trajectories = sample_states[:min(10, len(sample_states))]

    is_conserved, mean_drift, drift_list = test_conservation_ensemble(
        expr_numerical,
        hamiltonian_func,
        test_trajectories,
        t_span=50.0,
        success_threshold=0.8,
        tolerance=1e-5
    )

    conservation_error = mean_drift

    # Test 3: Functional independence
    is_independent = None
    if known_integrals is not None:
        is_independent = check_functional_independence(
            expr_numerical,
            known_integrals,
            sample_states,
            tolerance=1e-6
        )

    # Test 4: Poisson bracket (if symbolic Hamiltonian available)
    poisson_bracket = None
    if hamiltonian_symbolic is not None:
        n = len(state_symbols) // 2
        q_syms = state_symbols[:n]
        p_syms = state_symbols[n:]

        try:
            poisson_bracket = compute_poisson_bracket_symbolic(
                expr_symbolic,
                hamiltonian_symbolic,
                q_syms,
                p_syms
            )
        except:
            poisson_bracket = None

    # Compile statistics
    test_statistics = {
        'symbolic_numerical_agrees': agrees,
        'n_test_trajectories': len(test_trajectories),
        'drift_values': drift_list,
        'mean_drift': mean_drift,
        'max_drift': max(drift_list) if len(drift_list) > 0 else np.inf
    }

    return ValidationResult(
        is_conserved=is_conserved and agrees,
        conservation_error=conservation_error,
        symbolic_numerical_residual=residual,
        is_independent=is_independent,
        poisson_bracket_with_H=poisson_bracket,
        test_statistics=test_statistics
    )


# Example usage
if __name__ == "__main__":
    print("Symbolic Validation - Example: Harmonic Oscillator\n")

    # Harmonic oscillator: H = (p^2 + q^2) / 2
    q, p = sp.symbols('q p')
    H_sym = (p**2 + q**2) / 2
    I_sym = H_sym  # Energy is conserved

    # Numerical functions
    def H_func(z):
        """Hamiltonian dynamics."""
        q_val, p_val = z
        dq_dt = p_val
        dp_dt = -q_val
        return np.array([dq_dt, dp_dt]), (p_val**2 + q_val**2) / 2

    def I_func(z):
        """Integral (energy)."""
        return (z[1]**2 + z[0]**2) / 2

    # Generate test data
    samples = np.random.randn(100, 2)
    initial_conditions = np.random.randn(5, 2)

    # Validate
    result = validate_candidate_integral(
        I_sym,
        I_func,
        H_func,
        samples,
        [q, p],
        hamiltonian_symbolic=H_sym,
        test_trajectories=initial_conditions
    )

    print("Validation Results:")
    print(f"  Is conserved: {result.is_conserved}")
    print(f"  Conservation error: {result.conservation_error:.2e}")
    print(f"  Symbolic-numerical residual: {result.symbolic_numerical_residual:.2e}")
    print(f"  Poisson bracket {{I, H}}: {result.poisson_bracket_with_H}")
    print(f"  Mean drift: {result.test_statistics['mean_drift']:.2e}")
    print(f"  Max drift: {result.test_statistics['max_drift']:.2e}")
