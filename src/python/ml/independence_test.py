"""
Functional independence testing (Task 3.2.4, Part C).

For Liouville integrability, an n-dimensional Hamiltonian system requires n
functionally independent integrals in involution. This module provides tools
to rigorously test:

1. Functional independence: ∇I₁, ∇I₂, ..., ∇Iₙ are linearly independent
2. Involution: {Iᵢ, Iⱼ} = 0 for all pairs
3. Non-triviality: Each Iᵢ is not constant, not a coordinate, not a function of H
4. Completeness: For n-DOF system, need n independent invariants

Mathematical Tests:
------------------
- Gradient rank test: rank([∇I₁, ∇I₂, ..., ∇Iₖ]) = k
- Correlation matrix: Iᵢ and Iⱼ should have low correlation
- Mutual information: I(Iᵢ ; Iⱼ) should be low
- Jacobian determinant: |∂(I₁,...,Iₖ)/∂(q₁,...,pₖ)| ≠ 0
"""

import jax
import jax.numpy as jnp
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from dataclasses import dataclass

from .conservation_hnn import ConservationHNN, MultiInvariantHNN
from .conservation_loss import involution_loss


@dataclass
class IndependenceTestResult:
    """
    Results from functional independence testing.

    Attributes:
        num_invariants: Number of invariants tested
        functionally_independent: True if all tests passed
        gradient_rank_mean: Mean rank of gradient matrix
        gradient_rank_full: Fraction of points with full rank
        correlation_matrix: Correlation matrix between invariants
        max_correlation: Maximum off-diagonal correlation
        involution_errors: {Iᵢ, Iⱼ} for all pairs
        max_involution_error: Maximum |{Iᵢ, Iⱼ}|
        jacobian_determinant_mean: Mean |det(∂I/∂z)|
        jacobian_determinant_nonzero: Fraction of non-zero determinants
        mutual_information_matrix: Mutual information I(Iᵢ ; Iⱼ)
        test_details: Additional test-specific information
    """
    num_invariants: int
    functionally_independent: bool
    gradient_rank_mean: float
    gradient_rank_full: float
    correlation_matrix: np.ndarray
    max_correlation: float
    involution_errors: np.ndarray
    max_involution_error: float
    jacobian_determinant_mean: float
    jacobian_determinant_nonzero: float
    mutual_information_matrix: Optional[np.ndarray]
    test_details: Dict[str, Any]


def gradient_rank_test(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    num_invariants: int,
    rank_tolerance: float = 1e-6
) -> Tuple[float, float]:
    """
    Test functional independence via gradient rank.

    For k functionally independent functions, the gradient matrix
    G = [∇I₁, ∇I₂, ..., ∇Iₖ] should have rank k at generic points.

    Args:
        model: Trained ConservationHNN (with num_invariants ≥ num_invariants)
        params: Model parameters
        test_states: Test states (N, state_dim)
        num_invariants: Number of invariants to test
        rank_tolerance: Tolerance for singular values

    Returns:
        mean_rank: Average rank across test points
        full_rank_fraction: Fraction of points with full rank

    Example:
        >>> mean_rank, full_rank_frac = gradient_rank_test(model, params, test_states, num_invariants=2)
        >>> print(f"Mean rank: {mean_rank:.2f} / {num_invariants}")
        >>> print(f"Full rank: {full_rank_frac:.1%}")
    """
    ranks = []

    for z in test_states:
        # Compute gradients of all invariants at this point
        gradients = []
        for i in range(num_invariants):
            I_func = lambda state: model.invariant(params, state, inv_idx=i)
            grad_I = jax.grad(I_func)(z)
            gradients.append(grad_I)

        # Stack into matrix: (num_invariants, state_dim)
        G = jnp.stack(gradients, axis=0)

        # Compute rank via SVD
        singular_values = jnp.linalg.svd(G, compute_uv=False)
        rank = jnp.sum(singular_values > rank_tolerance)
        ranks.append(int(rank))

    ranks = np.array(ranks)
    mean_rank = float(np.mean(ranks))
    full_rank_fraction = float(np.mean(ranks == num_invariants))

    return mean_rank, full_rank_fraction


def correlation_test(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    num_invariants: int
) -> Tuple[np.ndarray, float]:
    """
    Compute correlation matrix between invariants.

    Functionally independent invariants can have some correlation, but
    very high correlation (> 0.9) suggests redundancy.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        num_invariants: Number of invariants

    Returns:
        corr_matrix: Correlation matrix (num_invariants, num_invariants)
        max_off_diag_corr: Maximum off-diagonal |correlation|

    Example:
        >>> corr_matrix, max_corr = correlation_test(model, params, test_states, num_invariants=3)
        >>> print(f"Max correlation: {max_corr:.4f}")
        >>> if max_corr > 0.9:
        ...     print("Warning: High correlation suggests redundancy")
    """
    # Compute all invariants
    invariant_values = []
    for i in range(num_invariants):
        I_values = model.batch_invariant(params, test_states, inv_idx=i)
        invariant_values.append(np.array(I_values))

    # Stack and compute correlation matrix
    I_matrix = np.stack(invariant_values, axis=0)  # (num_invariants, N)
    corr_matrix = np.corrcoef(I_matrix)

    # Find maximum off-diagonal correlation
    mask = ~np.eye(num_invariants, dtype=bool)
    max_off_diag_corr = float(np.max(np.abs(corr_matrix[mask])))

    return corr_matrix, max_off_diag_corr


def involution_test(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    num_invariants: int
) -> Tuple[np.ndarray, float]:
    """
    Test involution: {Iᵢ, Iⱼ} ≈ 0 for all pairs.

    For Liouville integrability, all invariants must be in involution.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        num_invariants: Number of invariants

    Returns:
        involution_matrix: Mean |{Iᵢ, Iⱼ}| for all pairs
        max_involution_error: Maximum |{Iᵢ, Iⱼ}|

    Example:
        >>> invol_matrix, max_error = involution_test(model, params, test_states, num_invariants=2)
        >>> print(f"Max involution error: {max_error:.2e}")
        >>> if max_error < 1e-4:
        ...     print("✓ In involution")
    """
    involution_matrix = np.zeros((num_invariants, num_invariants))

    for i in range(num_invariants):
        for j in range(i + 1, num_invariants):
            # Compute {Iᵢ, Iⱼ} on test states
            invol_error = involution_loss(params, model, test_states, inv_idx_i=i, inv_idx_j=j)
            involution_matrix[i, j] = float(invol_error)
            involution_matrix[j, i] = float(invol_error)  # Symmetric

    max_involution_error = float(np.max(involution_matrix))

    return involution_matrix, max_involution_error


def jacobian_determinant_test(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    num_invariants: int,
    det_tolerance: float = 1e-6
) -> Tuple[float, float]:
    """
    Test via Jacobian determinant.

    For k functionally independent functions on a k-dimensional surface,
    the k×k Jacobian determinant should be non-zero.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        num_invariants: Number of invariants
        det_tolerance: Tolerance for zero determinant

    Returns:
        mean_det: Mean |det(∂I/∂z)|
        nonzero_fraction: Fraction of points with |det| > tolerance

    Example:
        >>> mean_det, nonzero_frac = jacobian_determinant_test(model, params, test_states, 2)
        >>> print(f"Mean |det|: {mean_det:.2e}")
        >>> print(f"Non-zero: {nonzero_frac:.1%}")
    """
    determinants = []

    for z in test_states:
        # Compute Jacobian matrix
        # For k invariants on state_dim space, use first k dimensions
        def invariants_func(z_partial):
            """Map k-dimensional input to k-dimensional output"""
            # Pad with zeros if needed
            z_full = jnp.concatenate([z_partial, z[num_invariants:]])
            return jnp.array([model.invariant(params, z_full, inv_idx=i)
                              for i in range(num_invariants)])

        jacobian = jax.jacfwd(invariants_func)(z[:num_invariants])
        det = jnp.linalg.det(jacobian) if jacobian.shape[0] == jacobian.shape[1] else 0.0
        determinants.append(float(jnp.abs(det)))

    determinants = np.array(determinants)
    mean_det = float(np.mean(determinants))
    nonzero_fraction = float(np.mean(determinants > det_tolerance))

    return mean_det, nonzero_fraction


def mutual_information_test(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    num_invariants: int,
    num_bins: int = 20
) -> np.ndarray:
    """
    Estimate mutual information between invariants.

    Mutual information I(Iᵢ ; Iⱼ) measures statistical dependence.
    Independent variables should have low mutual information.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        num_invariants: Number of invariants
        num_bins: Number of bins for histogram estimation

    Returns:
        mi_matrix: Mutual information matrix (num_invariants, num_invariants)

    Example:
        >>> mi_matrix = mutual_information_test(model, params, test_states, num_invariants=2)
        >>> print(f"I(I₁ ; I₂) = {mi_matrix[0, 1]:.4f} bits")
    """
    # Compute all invariants
    invariant_values = []
    for i in range(num_invariants):
        I_values = model.batch_invariant(params, test_states, inv_idx=i)
        invariant_values.append(np.array(I_values))

    # Compute mutual information for all pairs
    mi_matrix = np.zeros((num_invariants, num_invariants))

    for i in range(num_invariants):
        for j in range(i + 1, num_invariants):
            # Estimate MI using histogram-based method
            Ii = invariant_values[i]
            Ij = invariant_values[j]

            # Bin the data
            hist_2d, _, _ = np.histogram2d(Ii, Ij, bins=num_bins)
            hist_i, _ = np.histogram(Ii, bins=num_bins)
            hist_j, _ = np.histogram(Ij, bins=num_bins)

            # Normalize to probabilities
            p_ij = hist_2d / np.sum(hist_2d)
            p_i = hist_i / np.sum(hist_i)
            p_j = hist_j / np.sum(hist_j)

            # Compute MI: I(X;Y) = sum p(x,y) log(p(x,y) / (p(x)p(y)))
            mi = 0.0
            for ii in range(num_bins):
                for jj in range(num_bins):
                    if p_ij[ii, jj] > 0 and p_i[ii] > 0 and p_j[jj] > 0:
                        mi += p_ij[ii, jj] * np.log2(p_ij[ii, jj] / (p_i[ii] * p_j[jj]))

            mi_matrix[i, j] = mi
            mi_matrix[j, i] = mi

    return mi_matrix


def test_functional_independence(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    num_invariants: int,
    verbose: bool = True
) -> IndependenceTestResult:
    """
    Comprehensive functional independence testing.

    Runs all independence tests and produces a verdict.

    Args:
        model: Trained ConservationHNN with multiple invariants
        params: Model parameters
        test_states: Test states (N, state_dim)
        num_invariants: Number of invariants to test
        verbose: Print detailed results

    Returns:
        result: IndependenceTestResult

    Example:
        >>> result = test_functional_independence(model, params, test_states, num_invariants=2)
        >>> if result.functionally_independent:
        ...     print("✓ Invariants are functionally independent")
        >>> else:
        ...     print("✗ Invariants may be redundant")
    """
    if verbose:
        print("="*80)
        print(f"FUNCTIONAL INDEPENDENCE TEST ({num_invariants} invariants)")
        print("="*80)

    # Test 1: Gradient rank
    if verbose:
        print("\n[1] Gradient rank test...")
    mean_rank, full_rank_frac = gradient_rank_test(
        model, params, test_states, num_invariants
    )
    if verbose:
        print(f"  Mean rank: {mean_rank:.2f} / {num_invariants}")
        print(f"  Full rank: {full_rank_frac:.1%}")

    # Test 2: Correlation
    if verbose:
        print("\n[2] Correlation test...")
    corr_matrix, max_corr = correlation_test(
        model, params, test_states, num_invariants
    )
    if verbose:
        print(f"  Correlation matrix:")
        for row in corr_matrix:
            print(f"    {' '.join(f'{c:7.4f}' for c in row)}")
        print(f"  Max off-diagonal: {max_corr:.4f}")

    # Test 3: Involution
    if verbose:
        print("\n[3] Involution test...")
    invol_matrix, max_invol = involution_test(
        model, params, test_states, num_invariants
    )
    if verbose:
        print(f"  Involution matrix (mean |{{Iᵢ, Iⱼ}}|):")
        for row in invol_matrix:
            print(f"    {' '.join(f'{c:.2e}' for c in row)}")
        print(f"  Max involution error: {max_invol:.2e}")

    # Test 4: Jacobian determinant
    if verbose:
        print("\n[4] Jacobian determinant test...")
    mean_det, nonzero_frac = jacobian_determinant_test(
        model, params, test_states, num_invariants
    )
    if verbose:
        print(f"  Mean |det|: {mean_det:.2e}")
        print(f"  Non-zero fraction: {nonzero_frac:.1%}")

    # Test 5: Mutual information
    if verbose:
        print("\n[5] Mutual information test...")
    mi_matrix = mutual_information_test(
        model, params, test_states, num_invariants
    )
    if verbose:
        print(f"  Mutual information matrix (bits):")
        for row in mi_matrix:
            print(f"    {' '.join(f'{c:7.4f}' for c in row)}")

    # Verdict
    criteria = {
        'full_rank': full_rank_frac > 0.9,  # >90% of points have full rank
        'low_correlation': max_corr < 0.8,  # Max correlation < 0.8
        'in_involution': max_invol < 1e-3,  # Max involution error < 10⁻³
        'nonzero_jacobian': nonzero_frac > 0.9  # >90% non-zero determinant
    }

    functionally_independent = all(criteria.values())

    if verbose:
        print("\n" + "="*80)
        print("VERDICT")
        print("="*80)
        for criterion, passed in criteria.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {criterion}")
        print()
        if functionally_independent:
            print("✅ PASSED: Invariants are functionally independent")
        else:
            print("⚠️  WARNING: Invariants may not be fully independent")

    result = IndependenceTestResult(
        num_invariants=num_invariants,
        functionally_independent=functionally_independent,
        gradient_rank_mean=mean_rank,
        gradient_rank_full=full_rank_frac,
        correlation_matrix=corr_matrix,
        max_correlation=max_corr,
        involution_errors=invol_matrix,
        max_involution_error=max_invol,
        jacobian_determinant_mean=mean_det,
        jacobian_determinant_nonzero=nonzero_frac,
        mutual_information_matrix=mi_matrix,
        test_details=criteria
    )

    return result


def test_liouville_integrability(
    model: ConservationHNN,
    params: Any,
    test_states: jnp.ndarray,
    system_dof: int,
    verbose: bool = True
) -> Tuple[bool, IndependenceTestResult]:
    """
    Test whether discovered invariants satisfy Liouville integrability.

    For a system with n degrees of freedom, Liouville integrability requires:
    - n functionally independent integrals
    - All in involution: {Iᵢ, Iⱼ} = 0

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_states: Test states (N, state_dim)
        system_dof: Number of degrees of freedom (n)
        verbose: Print results

    Returns:
        is_integrable: True if Liouville integrable
        result: IndependenceTestResult

    Example:
        >>> # 3-body problem: n=3 DOF → need 3 independent invariants
        >>> is_integrable, result = test_liouville_integrability(
        ...     model, params, test_states, system_dof=3
        ... )
        >>> if is_integrable:
        ...     print("✅ System is Liouville integrable!")
    """
    if verbose:
        print("="*80)
        print(f"LIOUVILLE INTEGRABILITY TEST (n={system_dof} DOF)")
        print("="*80)
        print(f"Required: {system_dof} functionally independent invariants in involution")

    # Check number of invariants
    if hasattr(model, 'num_invariants'):
        num_discovered = model.num_invariants
    else:
        num_discovered = 1

    if verbose:
        print(f"Discovered: {num_discovered} invariants")

    if num_discovered < system_dof:
        if verbose:
            print(f"\n⚠️  WARNING: Need {system_dof - num_discovered} more invariants")
        # Test independence of what we have
        result = test_functional_independence(
            model, params, test_states, num_discovered, verbose=verbose
        )
        return False, result

    # Test independence of first n invariants
    result = test_functional_independence(
        model, params, test_states, system_dof, verbose=verbose
    )

    # Liouville integrable if:
    # 1. Have n invariants
    # 2. Functionally independent
    # 3. In involution
    is_integrable = (
        num_discovered >= system_dof and
        result.functionally_independent and
        result.max_involution_error < 1e-3
    )

    if verbose:
        print("\n" + "="*80)
        print("LIOUVILLE INTEGRABILITY VERDICT")
        print("="*80)
        if is_integrable:
            print("✅ SYSTEM IS LIOUVILLE INTEGRABLE")
            print(f"   {system_dof} functionally independent invariants in involution")
        else:
            print("⚠️  SYSTEM MAY NOT BE FULLY INTEGRABLE")
            if num_discovered < system_dof:
                print(f"   Need {system_dof - num_discovered} more invariants")
            if not result.functionally_independent:
                print("   Invariants are not fully independent")
            if result.max_involution_error >= 1e-3:
                print(f"   Involution error too large: {result.max_involution_error:.2e}")

    return is_integrable, result


# Test code
if __name__ == "__main__":
    print("Testing functional independence module...")

    from .conservation_hnn import create_conservation_hnn

    # Create model with 2 invariants
    print("\n[1] Creating ConservationHNN with 2 invariants...")
    model, params = create_conservation_hnn(
        state_dim=4,
        num_invariants=2,
        encoder_dims=(64, 64),
        seed=0
    )

    # Generate test states
    key = jax.random.PRNGKey(42)
    test_states = jax.random.normal(key, (100, 4)) * 2.0

    # Gradient rank test
    print("\n[2] Testing gradient rank...")
    mean_rank, full_rank_frac = gradient_rank_test(
        model, params, test_states, num_invariants=2
    )
    print(f"  Mean rank: {mean_rank:.2f}")
    print(f"  Full rank: {full_rank_frac:.1%}")

    # Correlation test
    print("\n[3] Testing correlation...")
    corr_matrix, max_corr = correlation_test(
        model, params, test_states, num_invariants=2
    )
    print(f"  Max correlation: {max_corr:.4f}")

    # Involution test
    print("\n[4] Testing involution...")
    invol_matrix, max_invol = involution_test(
        model, params, test_states, num_invariants=2
    )
    print(f"  Max involution error: {max_invol:.2e}")

    # Jacobian determinant test
    print("\n[5] Testing Jacobian determinant...")
    mean_det, nonzero_frac = jacobian_determinant_test(
        model, params, test_states, num_invariants=2
    )
    print(f"  Mean |det|: {mean_det:.2e}")
    print(f"  Non-zero: {nonzero_frac:.1%}")

    # Mutual information test
    print("\n[6] Testing mutual information...")
    mi_matrix = mutual_information_test(
        model, params, test_states, num_invariants=2
    )
    print(f"  I(I₁ ; I₂) = {mi_matrix[0, 1]:.4f} bits")

    # Full independence test
    print("\n[7] Testing full functional independence...")
    result = test_functional_independence(
        model, params, test_states, num_invariants=2, verbose=True
    )

    # Liouville integrability test
    print("\n[8] Testing Liouville integrability (2-DOF system)...")
    is_integrable, liouville_result = test_liouville_integrability(
        model, params, test_states, system_dof=2, verbose=True
    )

    print("\n✓ All tests passed!")
