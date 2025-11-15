"""
Functional independence testing (WP 3.1, Task 3.1.4, Part C).

Tests if conserved integrals are functionally independent via:
1. Jacobian rank: rank(∂I_i/∂(q,p)) = k
2. Poisson brackets: {I_i, I_j} for involution checking

For Liouville integrability, we need n functionally independent integrals
in involution on a 2n-dimensional phase space.
"""

from typing import List, Tuple, Dict, Optional
import numpy as np
from scipy.linalg import svd, qr

from .integral_from_killing import ConservedIntegral, State


# =============================================================================
# Part C1: Functional Independence via Jacobian
# =============================================================================

def test_functional_independence(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6,
    verbose: bool = False
) -> Dict:
    """
    Test functional independence via Jacobian rank.

    Method:
        For integrals I_1, ..., I_k, compute Jacobian at test points:
            J_ij = ∂I_i / ∂x_j  where x = (q, p)

        If rank(J) = k at all points, integrals are independent.

    Args:
        integrals: List of k integrals to test
        test_states: Sample states for evaluation
        tolerance: Rank tolerance (singular value threshold)
        verbose: Print diagnostic info

    Returns:
        {
            'independent': bool,
            'rank': int,  # Minimum rank found
            'expected_rank': int,  # Should equal len(integrals)
            'condition_number': float,
            'independent_subset': List[int],  # Maximal independent subset
            'singular_values_avg': np.ndarray
        }
    """
    k = len(integrals)

    if k == 0:
        return {
            'independent': True,
            'rank': 0,
            'expected_rank': 0,
            'condition_number': 1.0,
            'independent_subset': [],
            'singular_values_avg': np.array([])
        }

    if len(test_states) == 0:
        raise ValueError("Need at least one test state")

    n = test_states[0].dimension  # Phase space dimension 2n

    if verbose:
        print(f"Testing functional independence:")
        print(f"  Number of integrals: {k}")
        print(f"  Phase space dimension: {2*n}")
        print(f"  Test states: {len(test_states)}")

    # Evaluate Jacobian at each test state
    jacobians = []
    singular_values_list = []

    for state_idx, state in enumerate(test_states):
        J = np.zeros((k, 2*n))

        for i, integral in enumerate(integrals):
            if integral.gradient is not None:
                # Use analytical gradient
                dI_dq, dI_dp = integral.gradient(state.to_array())
                J[i, :n] = dI_dq
                J[i, n:] = dI_dp
            else:
                # Numerical gradient via finite differences
                eps = 1e-6
                state_arr = state.to_array()
                I_0 = integral(state_arr)

                for j in range(2*n):
                    state_plus = state_arr.copy()
                    state_plus[j] += eps
                    I_plus = integral(state_plus)
                    J[i, j] = (I_plus - I_0) / eps

        jacobians.append(J)

        # Compute singular values
        U, sigma, Vt = svd(J, full_matrices=False)
        singular_values_list.append(sigma)

    # Analyze ranks
    ranks = []
    for J in jacobians:
        rank = np.linalg.matrix_rank(J, tol=tolerance)
        ranks.append(rank)

    min_rank = min(ranks)
    avg_rank = np.mean(ranks)

    # Average singular values
    singular_values_avg = np.mean(singular_values_list, axis=0)

    # Find maximal independent subset
    if min_rank < k:
        # Use QR decomposition with column pivoting on stacked Jacobian
        J_stacked = np.vstack(jacobians)
        Q, R, P = qr(J_stacked.T, pivoting=True, mode='economic')

        # P contains column permutation - first min_rank columns are independent
        independent_subset = P[:min_rank].tolist()
    else:
        independent_subset = list(range(k))

    # Condition number (average)
    condition_numbers = []
    for sigma in singular_values_list:
        if len(sigma) > 0 and sigma[-1] > 1e-15:
            cond = sigma[0] / sigma[-1]
            condition_numbers.append(cond)

    avg_condition = np.mean(condition_numbers) if condition_numbers else np.inf

    if verbose:
        print(f"  Minimum rank: {min_rank}/{k}")
        print(f"  Average rank: {avg_rank:.2f}")
        print(f"  Condition number: {avg_condition:.2e}")
        print(f"  Singular values (avg): {singular_values_avg}")

    return {
        'independent': (min_rank == k),
        'rank': min_rank,
        'expected_rank': k,
        'condition_number': avg_condition,
        'independent_subset': independent_subset,
        'singular_values_avg': singular_values_avg,
        'ranks_per_state': ranks
    }


# =============================================================================
# Part C2: Poisson Bracket Relations
# =============================================================================

def compute_poisson_bracket(
    I1: ConservedIntegral,
    I2: ConservedIntegral,
    state: State,
    *,
    epsilon: float = 1e-6
) -> float:
    """
    Compute Poisson bracket {I1, I2} at a state.

    For canonical coordinates (q, p):
        {I1, I2} = sum_i (∂I1/∂q_i ∂I2/∂p_i - ∂I1/∂p_i ∂I2/∂q_i)

    Args:
        I1, I2: Two integrals
        state: Phase space state
        epsilon: Finite difference step (if gradients not available)

    Returns:
        Poisson bracket value (scalar)
    """
    n = state.dimension

    # Get gradients
    if I1.gradient is not None:
        dI1_dq, dI1_dp = I1.gradient(state.to_array())
    else:
        # Numerical gradient
        dI1_dq, dI1_dp = _numerical_gradient(I1, state, epsilon)

    if I2.gradient is not None:
        dI2_dq, dI2_dp = I2.gradient(state.to_array())
    else:
        dI2_dq, dI2_dp = _numerical_gradient(I2, state, epsilon)

    # {I1, I2} = dI1/dq · dI2/dp - dI1/dp · dI2/dq
    bracket = np.dot(dI1_dq, dI2_dp) - np.dot(dI1_dp, dI2_dq)

    return bracket


def _numerical_gradient(
    integral: ConservedIntegral,
    state: State,
    epsilon: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute gradient numerically via finite differences"""
    n = state.dimension
    state_arr = state.to_array()
    I_0 = integral(state_arr)

    dI_dq = np.zeros(n)
    dI_dp = np.zeros(n)

    # ∂I/∂q
    for i in range(n):
        q_plus = state.q.copy()
        q_plus[i] += epsilon
        state_plus = State(q=q_plus, p=state.p)
        I_plus = integral(state_plus.to_array())
        dI_dq[i] = (I_plus - I_0) / epsilon

    # ∂I/∂p
    for i in range(n):
        p_plus = state.p.copy()
        p_plus[i] += epsilon
        state_plus = State(q=state.q, p=p_plus)
        I_plus = integral(state_plus.to_array())
        dI_dp[i] = (I_plus - I_0) / epsilon

    return dI_dq, dI_dp


def test_involution(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6,
    verbose: bool = False
) -> Dict:
    """
    Test if integrals are in involution (Poisson brackets vanish).

    For Liouville integrability: need n integrals in involution.

    Method:
        Compute {I_i, I_j} for all pairs at test states.
        Average over states.
        Check if all |{I_i, I_j}| < tolerance.

    Args:
        integrals: List of integrals
        test_states: Test states
        tolerance: Threshold for {I_i, I_j} ≈ 0
        verbose: Print results

    Returns:
        {
            'in_involution': bool,
            'poisson_brackets': np.ndarray,  # (k × k) averaged
            'max_bracket': float,
            'violations': List[Tuple[int, int, float]]  # (i, j, value)
        }
    """
    k = len(integrals)

    if k <= 1:
        # Single integral is trivially in involution with itself
        return {
            'in_involution': True,
            'poisson_brackets': np.zeros((k, k)),
            'max_bracket': 0.0,
            'violations': []
        }

    if verbose:
        print(f"Testing involution:")
        print(f"  Integrals: {k}")
        print(f"  Test states: {len(test_states)}")

    # Compute brackets for all pairs, averaged over states
    brackets_avg = np.zeros((k, k))

    for state in test_states:
        for i in range(k):
            for j in range(i+1, k):  # Antisymmetric, so only compute upper triangle
                bracket = compute_poisson_bracket(
                    integrals[i], integrals[j], state
                )
                brackets_avg[i, j] += bracket / len(test_states)

    # Fill in lower triangle (antisymmetry: {I,J} = -{J,I})
    for i in range(k):
        for j in range(i):
            brackets_avg[i, j] = -brackets_avg[j, i]

    # Check for violations
    max_bracket = 0.0
    violations = []

    for i in range(k):
        for j in range(i+1, k):
            bracket_val = abs(brackets_avg[i, j])
            if bracket_val > max_bracket:
                max_bracket = bracket_val

            if bracket_val > tolerance:
                violations.append((i, j, bracket_val))

    in_involution = (max_bracket < tolerance)

    if verbose:
        print(f"  Max |{{I_i, I_j}}|: {max_bracket:.2e}")
        print(f"  In involution: {in_involution}")
        if violations:
            print(f"  Violations: {len(violations)}")
            for i, j, val in violations[:5]:  # Show first 5
                print(f"    {{I_{i}, I_{j}}} = {val:.2e}")

    return {
        'in_involution': in_involution,
        'poisson_brackets': brackets_avg,
        'max_bracket': max_bracket,
        'violations': violations
    }


# =============================================================================
# Combined Analysis
# =============================================================================

def analyze_integral_structure(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6,
    verbose: bool = True
) -> Dict:
    """
    Complete analysis of integral structure:
    - Functional independence
    - Involution
    - Integrability assessment

    Args:
        integrals: List of conserved integrals
        test_states: Test states
        tolerance: Numerical threshold
        verbose: Print detailed results

    Returns:
        Complete analysis dictionary
    """
    if verbose:
        print("="*70)
        print("INTEGRAL STRUCTURE ANALYSIS")
        print("="*70)
        print()

    # Test independence
    independence_result = test_functional_independence(
        integrals, test_states, tolerance=tolerance, verbose=verbose
    )

    print()

    # Test involution (only on independent subset)
    if independence_result['independent']:
        integrals_to_test = integrals
    else:
        # Use maximal independent subset
        subset_indices = independence_result['independent_subset']
        integrals_to_test = [integrals[i] for i in subset_indices]

        if verbose:
            print(f"Using independent subset: {subset_indices}")
            print()

    involution_result = test_involution(
        integrals_to_test, test_states, tolerance=tolerance, verbose=verbose
    )

    # Assess integrability
    n = test_states[0].dimension
    num_independent = independence_result['rank']
    in_involution = involution_result['in_involution']

    is_integrable = (num_independent == n) and in_involution
    integrability_status = _assess_integrability(n, num_independent, in_involution)

    if verbose:
        print()
        print("="*70)
        print("INTEGRABILITY ASSESSMENT")
        print("="*70)
        print(f"  Phase space dimension: 2n = {2*n}")
        print(f"  Independent integrals: {num_independent}")
        print(f"  Required for integrability: n = {n}")
        print(f"  In involution: {in_involution}")
        print(f"  Status: {integrability_status}")
        print("="*70)

    return {
        'independence': independence_result,
        'involution': involution_result,
        'is_integrable': is_integrable,
        'integrability_status': integrability_status,
        'phase_space_dim': 2*n,
        'num_independent': num_independent,
        'required_for_integrability': n
    }


def _assess_integrability(
    n: int,
    num_independent: int,
    in_involution: bool
) -> str:
    """Assess integrability status based on counts"""
    if num_independent == n and in_involution:
        return "LIOUVILLE INTEGRABLE (n independent integrals in involution)"
    elif num_independent == n and not in_involution:
        return "INDEPENDENT BUT NOT IN INVOLUTION (not integrable)"
    elif num_independent == n - 1:
        return "NEARLY INTEGRABLE (n-1 independent integrals)"
    elif num_independent > 0 and num_independent < n:
        return f"PARTIALLY INTEGRABLE ({num_independent}/{n} integrals)"
    elif num_independent == 0:
        return "NON-INTEGRABLE (no integrals found)"
    elif num_independent > n:
        return f"SUPERINTEGRABLE ({num_independent} > n integrals)"
    else:
        return "UNKNOWN STATUS"
