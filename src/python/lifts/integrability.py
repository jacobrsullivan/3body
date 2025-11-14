"""
Integrability analysis for S¹ bundle dynamics (WP 2.2, Part D).

Tests the lift-integrability hypothesis:
    Is the 3-body problem integrable on the S¹ bundle?

For integrability, we need:
    1. Three independent integrals in involution
    2. Functional independence
    3. {Fᵢ, Fⱼ} = 0 for all i, j

Candidate integrals:
    F₁ = H̃ (energy)
    F₂ = L (angular momentum)
    F₃ = p_θ (fiber momentum) <- NEW!
"""

from typing import Callable, List, Optional, Dict
import numpy as np
import itertools

from ..coordinates.base import Masses
from .s1_bundle import BundleState
from .lifted_hamiltonian import BundleTrajectory, LiftedHamiltonian
from .extended_symplectic import ExtendedSymplecticForm, poisson_bracket_on_bundle


def verify_basic_integrals(
    trajectory: BundleTrajectory,
    lifted_hamiltonian: LiftedHamiltonian,
    tolerance: float = 1e-10
) -> dict:
    """
    Verify conservation of the three candidate integrals.

    F₁ = H̃ (energy)
    F₂ = L (angular momentum)
    F₃ = p_θ (fiber momentum)

    Args:
        trajectory: Test trajectory
        lifted_hamiltonian: Hamiltonian
        tolerance: Conservation threshold

    Returns:
        Dictionary with conservation statistics
    """
    n = len(trajectory)

    F1 = np.zeros(n)  # Energy
    F2 = np.zeros(n)  # Angular momentum
    F3 = np.zeros(n)  # Fiber momentum

    for i, state in enumerate(trajectory.states):
        F1[i] = lifted_hamiltonian.evaluate(state)
        F2[i] = state.shape_state.L
        F3[i] = state.p_theta

    # Check conservation
    F1_drift = np.max(np.abs(F1 - F1[0])) if len(F1) > 1 else 0.0
    F2_drift = np.max(np.abs(F2 - F2[0])) if len(F2) > 1 else 0.0
    F3_drift = np.max(np.abs(F3 - F3[0])) if len(F3) > 1 else 0.0

    results = {
        'F1_conserved': F1_drift < tolerance,
        'F2_conserved': F2_drift < tolerance,
        'F3_conserved': F3_drift < tolerance,
        'F1_drift': F1_drift,
        'F2_drift': F2_drift,
        'F3_drift': F3_drift,
        'F1_relative_drift': F1_drift / abs(F1[0]) if abs(F1[0]) > 1e-14 else 0.0,
        'F1_values': F1,
        'F2_values': F2,
        'F3_values': F3,
        'all_conserved': (F1_drift < tolerance and
                         F2_drift < tolerance and
                         F3_drift < tolerance)
    }

    return results


def test_functional_independence(
    integrals: List[Callable[[BundleState], float]],
    state: BundleState,
    epsilon: float = 1e-7,
    tolerance: float = 1e-10
) -> dict:
    """
    Test if integrals are functionally independent.

    Criterion: Gradients dF₁, dF₂, dF₃ are linearly independent.

    Args:
        integrals: List of integral functions
        state: Point where to test
        epsilon: Finite difference step
        tolerance: Linear independence threshold

    Returns:
        Dictionary with independence test results
    """
    n = len(integrals)
    dim = state.phase_space_dimension

    # Compute gradients
    gradients = np.zeros((n, dim))

    for i, F in enumerate(integrals):
        gradients[i] = _compute_gradient(F, state, epsilon)

    # Check rank
    rank = np.linalg.matrix_rank(gradients, tol=tolerance)
    independent = (rank == n)

    # Compute condition number
    try:
        singular_values = np.linalg.svd(gradients, compute_uv=False)
        condition_number = singular_values[0] / singular_values[-1] if singular_values[-1] > 1e-14 else np.inf
    except:
        condition_number = np.inf

    return {
        'independent': independent,
        'rank': rank,
        'expected_rank': n,
        'condition_number': condition_number,
        'gradients': gradients,
        'singular_values': singular_values if 'singular_values' in locals() else None
    }


def _compute_gradient(
    f: Callable[[BundleState], float],
    state: BundleState,
    epsilon: float = 1e-7
) -> np.ndarray:
    """
    Compute gradient of function via finite differences.

    Args:
        f: Function on bundle
        state: Point where to compute gradient
        epsilon: Step size

    Returns:
        Gradient vector (length 8)
    """
    z0 = state.to_vector()
    f0 = f(state)

    grad = np.zeros(8)

    for i in range(8):
        z_plus = z0.copy()
        z_plus[i] += epsilon

        try:
            state_plus = BundleState.from_vector(z_plus, L=state.shape_state.L)
            f_plus = f(state_plus)

            # Central difference
            z_minus = z0.copy()
            z_minus[i] -= epsilon
            state_minus = BundleState.from_vector(z_minus, L=state.shape_state.L)
            f_minus = f(state_minus)

            grad[i] = (f_plus - f_minus) / (2 * epsilon)

        except (ValueError, ZeroDivisionError):
            # Fallback to forward difference
            try:
                grad[i] = (f_plus - f0) / epsilon
            except:
                grad[i] = 0.0

    return grad


def verify_involution(
    integrals: List[Callable[[BundleState], float]],
    state: BundleState,
    extended_form: ExtendedSymplecticForm,
    tolerance: float = 1e-8
) -> dict:
    """
    Verify {Fᵢ, Fⱼ} = 0 for all i, j.

    This is necessary for Liouville integrability.

    Args:
        integrals: List of integral functions [F₁, F₂, F₃]
        state: Point where to test
        extended_form: Extended symplectic form
        tolerance: Threshold for brackets

    Returns:
        Dictionary with Poisson brackets and involution status
    """
    n = len(integrals)
    brackets = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            try:
                brackets[i, j] = poisson_bracket_on_bundle(
                    integrals[i],
                    integrals[j],
                    state,
                    extended_form
                )
            except (ValueError, np.linalg.LinAlgError):
                brackets[i, j] = np.nan

    # Check antisymmetry
    antisymmetric = np.allclose(brackets, -brackets.T, atol=tolerance, equal_nan=True)

    # Check all brackets vanish
    # (Diagonal should be zero by antisymmetry)
    max_bracket = np.nanmax(np.abs(brackets))
    in_involution = max_bracket < tolerance

    # Extract upper triangle (unique pairs)
    pairs = {}
    for i in range(n):
        for j in range(i+1, n):
            pairs[f'{{F{i+1}, F{j+1}}}'] = brackets[i, j]

    return {
        'bracket_matrix': brackets,
        'antisymmetric': antisymmetric,
        'max_bracket': max_bracket,
        'in_involution': in_involution,
        'pairs': pairs,
        'integrable': in_involution and antisymmetric
    }


def classify_integrability(
    trajectory: BundleTrajectory,
    lifted_hamiltonian: LiftedHamiltonian,
    extended_form: ExtendedSymplecticForm,
    test_state: Optional[BundleState] = None
) -> dict:
    """
    Complete integrability analysis.

    Tests:
        1. Conservation of F₁, F₂, F₃
        2. Functional independence
        3. Involution {Fᵢ, Fⱼ} = 0

    Args:
        trajectory: Test trajectory
        lifted_hamiltonian: Hamiltonian
        extended_form: Symplectic form
        test_state: State for independence/involution tests (default: initial)

    Returns:
        Complete classification results
    """
    if test_state is None:
        test_state = trajectory.initial_state

    # Define the three integrals
    def F1(s: BundleState) -> float:
        """Energy"""
        return lifted_hamiltonian.evaluate(s)

    def F2(s: BundleState) -> float:
        """Angular momentum"""
        return s.shape_state.L

    def F3(s: BundleState) -> float:
        """Fiber momentum"""
        return s.p_theta

    integrals = [F1, F2, F3]

    # Test conservation
    conservation = verify_basic_integrals(trajectory, lifted_hamiltonian)

    # Test independence
    independence = test_functional_independence(integrals, test_state)

    # Test involution
    involution = verify_involution(integrals, test_state, extended_form)

    # Overall classification
    integrable = (
        conservation['all_conserved'] and
        independence['independent'] and
        involution['integrable']
    )

    return {
        'integrable': integrable,
        'conservation': conservation,
        'independence': independence,
        'involution': involution,
        'summary': {
            'conserved': conservation['all_conserved'],
            'independent': independence['independent'],
            'in_involution': involution['in_involution'],
            'conclusion': 'INTEGRABLE' if integrable else 'NON-INTEGRABLE'
        }
    }


def search_fourth_integral(
    trajectory: BundleTrajectory,
    candidate_functions: Optional[List[Callable]] = None,
    tolerance: float = 1e-10
) -> Optional[Callable]:
    """
    Search for additional integral beyond F₁, F₂, F₃.

    If found, system is super-integrable!

    Args:
        trajectory: Test trajectory
        candidate_functions: List of trial functions (default: generate automatically)
        tolerance: Conservation threshold

    Returns:
        Fourth integral (if found), else None
    """
    if candidate_functions is None:
        candidate_functions = generate_candidate_integrals()

    for candidate in candidate_functions:
        try:
            # Evaluate along trajectory
            values = np.array([candidate(state) for state in trajectory.states])

            # Check conservation
            drift = np.max(np.abs(values - values[0]))

            if drift < tolerance:
                # Potential fourth integral!
                # TODO: Verify functional independence with F₁, F₂, F₃
                return candidate

        except (ValueError, ZeroDivisionError):
            continue

    return None


def generate_candidate_integrals() -> List[Callable[[BundleState], float]]:
    """
    Generate candidate functions for fourth integral.

    Strategies:
        - Linear combinations of coordinates
        - Quadratic forms
        - Products of coordinates and momenta

    Returns:
        List of candidate functions
    """
    candidates = []

    # Linear combinations of shape coordinates
    for a, b, c in itertools.product([-1, 0, 1], repeat=3):
        if (a, b, c) != (0, 0, 0):
            def linear_combo(s: BundleState, a=a, b=b, c=c) -> float:
                return (
                    a * s.shape_state.r12 +
                    b * s.shape_state.r23 +
                    c * s.shape_state.r31
                )
            candidates.append(linear_combo)

    # Quadratic form in shape coordinates
    def quadratic_position(s: BundleState) -> float:
        r = np.array([s.shape_state.r12, s.shape_state.r23, s.shape_state.r31])
        return np.dot(r, r)

    candidates.append(quadratic_position)

    # Quadratic form in momenta
    def quadratic_momentum(s: BundleState) -> float:
        return np.dot(s.shape_momenta, s.shape_momenta)

    candidates.append(quadratic_momentum)

    # Mixed terms
    def mixed_rp(s: BundleState) -> float:
        r = np.array([s.shape_state.r12, s.shape_state.r23, s.shape_state.r31])
        return np.dot(r, s.shape_momenta)

    candidates.append(mixed_rp)

    return candidates


def compute_arnold_web_obstruction(
    results: dict
) -> Optional[str]:
    """
    Diagnose obstruction to integrability from results.

    Args:
        results: Output from classify_integrability

    Returns:
        Description of obstruction, or None if integrable
    """
    if results['integrable']:
        return None

    obstructions = []

    if not results['conservation']['all_conserved']:
        obstructions.append("Not all integrals are conserved")

    if not results['independence']['independent']:
        obstructions.append(
            f"Integrals are functionally dependent (rank={results['independence']['rank']}, expected=3)"
        )

    if not results['involution']['in_involution']:
        max_bracket = results['involution']['max_bracket']
        obstructions.append(
            f"Integrals not in involution (max bracket = {max_bracket:.6e})"
        )

    return "; ".join(obstructions)
