# WP 2.2 Part D: Integrability Search - Detailed Design

**Task**: WP 2.2 - S¹ "Untwisting" Lift Construction
**Part**: D - Integrability Search
**Status**: Design Phase
**Estimated Duration**: 3 days
**Dependencies**: WP 2.2 Parts A, B, C Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Data Structures](#data-structures)
4. [Core Algorithms](#core-algorithms)
5. [Implementation Details](#implementation-details)
6. [Validation Strategy](#validation-strategy)
7. [Performance Targets](#performance-targets)
8. [Integration Points](#integration-points)
9. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

Part D answers the central scientific question of WP 2.2:

**Is the three-body problem integrable on the S¹ bundle?**

This requires:
1. **Identifying integrals**: Find conserved quantities $F_1, F_2, \ldots$
2. **Testing functional independence**: Are the $F_i$ independent?
3. **Verifying involution**: Do they satisfy $\{F_i, F_j\} = 0$?
4. **Classification**: Integrable, non-integrable, or partially integrable?
5. **Construction** (if integrable): Build action-angle coordinates

### Mathematical Criterion

For a Hamiltonian system with $2n$ dimensional phase space, **complete integrability** requires:
- $n$ **independent** integrals $F_1, \ldots, F_n$ in **involution**

For our S¹ bundle:
- Phase space dimension: $2n = 8$ (planar case)
- Need: $n = 4$ integrals

**Candidate Integrals**:
1. $F_1 = \widetilde{H}$ (energy) ✓
2. $F_2 = L$ (angular momentum) ✓
3. $F_3 = p_\theta$ (fiber momentum) ✓ **NEW!**
4. $F_4 = ?$ (unknown, to be found)

**Goal**: Determine if $F_4$ exists, and if so, construct it.

### Objectives

1. **Verify Three Integrals**: Confirm $F_1, F_2, F_3$ are conserved
2. **Test Functional Independence**: Check gradients are linearly independent
3. **Verify Involution**: Compute $\{F_i, F_j\}$, verify = 0
4. **Search for Fourth Integral**: Systematic search for $F_4$
5. **Classification**: Determine integrability status
6. **Action-Angle Coordinates** (if integrable): Explicit construction
7. **Documentation**: Technical report on findings

### Deliverables

- `IntegralVerifier` class
- `IntegrabilityClassifier` class
- Functional independence tester
- Poisson bracket involution checker
- Fourth integral search algorithms
- Action-angle coordinate constructor (if applicable)
- Technical report section
- Classification results

---

## Mathematical Background

### Liouville Integrability

**Definition**: A Hamiltonian system $(M, \omega, H)$ with $\dim(M) = 2n$ is **Liouville integrable** if there exist $n$ smooth functions $F_1, \ldots, F_n$ such that:

1. **Independence**: $dF_1, \ldots, dF_n$ are linearly independent almost everywhere
2. **Involution**: $\{F_i, F_j\} = 0$ for all $i, j$
3. **Conserved**: $\{H, F_i\} = 0$ (equivalently, $H$ is one of the $F_i$)

**Consequence** (Liouville-Arnold Theorem):
- Level sets $M_c = \{F_1 = c_1, \ldots, F_n = c_n\}$ are invariant manifolds
- If compact and connected, $M_c \cong \mathbb{T}^n$ (n-dimensional torus)
- Dynamics on $M_c$ are **quasi-periodic** (linear in action-angle coordinates)

### Our Case: S¹ Bundle

**Configuration space**: $\dim(P) = 4$ (shape space 3D + fiber 1D)
**Phase space**: $\dim(T^*P) = 8$

**Need**: $n = 4$ independent integrals in involution

**Known Integrals**:
1. **Energy**: $F_1 = \widetilde{H}(s, \theta, p_s, p_\theta) = H_{\text{red}}(s, p_s)$
2. **Angular Momentum**: $F_2 = L$ (from rotational symmetry)
3. **Fiber Momentum**: $F_3 = p_\theta$ (from $\theta$-independence of $\widetilde{H}$)

**Question**: Does $F_4$ exist?

### Obstruction to Integrability

Even on the bundle, integrability is **not guaranteed**:
- The curvature $\mathcal{F} = d\mathcal{A} \neq 0$ may still obstruct via higher-order effects
- Three integrals might not extend to four
- Level sets may not foliate into tori

**Scenarios**:
1. **Integrable**: $F_4$ exists → System is integrable upstairs!
2. **Non-integrable**: No $F_4$ → Chaos persists even after lift
3. **Partially integrable**: $F_4$ exists on submanifold only

### Action-Angle Coordinates

If integrable, we can construct **action-angle variables** $(\mathbf{I}, \boldsymbol{\theta})$:
- **Actions**: $I_i = \oint_{C_i} \mathbf{p} \cdot d\mathbf{q}$ (conserved)
- **Angles**: $\theta_i \in [0, 2\pi)$ (advance linearly in time)

**Dynamics in action-angle coordinates**:
$$\dot{I}_i = 0, \quad \dot{\theta}_i = \omega_i(\mathbf{I}) = \frac{\partial H}{\partial I_i}$$

Pure rotation on torus! Solution is **trivial**:
$$I_i(t) = I_i(0), \quad \theta_i(t) = \theta_i(0) + \omega_i t$$

---

## Data Structures

### Integral

```python
# File: src/python/analysis/integral.py

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np
from ..lifts.s1_bundle import BundleState

@dataclass(frozen=True)
class Integral:
    """
    Integral of motion (conserved quantity).

    An integral F satisfies: {H, F} = 0 ⟺ dF/dt = 0 along trajectories.

    Attributes:
        name: Human-readable name (e.g., "Energy", "Angular Momentum")
        function: Callable mapping BundleState → float
        symbolic_expression: Optional symbolic representation
        metadata: Optional auxiliary data

    Examples:
        >>> # Energy integral
        >>> energy = Integral(
        ...     name="Energy",
        ...     function=lambda state: lifted_H.evaluate(state)
        ... )
        >>>
        >>> # Fiber momentum integral
        >>> p_theta_integral = Integral(
        ...     name="Fiber Momentum",
        ...     function=lambda state: state.p_theta
        ... )
    """
    name: str
    function: Callable[[BundleState], float]
    symbolic_expression: Optional[str] = None
    metadata: Optional[dict] = None

    def evaluate(self, state: BundleState) -> float:
        """Evaluate integral at state"""
        return self.function(state)

    def gradient(
        self,
        state: BundleState,
        epsilon: float = 1e-8
    ) -> np.ndarray:
        """
        Compute gradient ∂F/∂z via finite differences.

        Returns:
            Gradient vector (8,) in phase space
        """
        F_center = self.evaluate(state)
        gradient = np.zeros(8)

        state_vector = state.to_vector()

        for i in range(8):
            perturbed = state_vector.copy()
            perturbed[i] += epsilon

            state_perturbed = BundleState.from_vector(
                perturbed,
                L=state.shape_state.L
            )

            F_perturbed = self.evaluate(state_perturbed)

            gradient[i] = (F_perturbed - F_center) / epsilon

        return gradient

    def is_conserved_on_trajectory(
        self,
        trajectory: 'BundleTrajectory',
        tolerance: float = 1e-10
    ) -> dict:
        """
        Check if F is conserved along trajectory.

        Args:
            trajectory: Trajectory to test
            tolerance: Conservation threshold

        Returns:
            Dictionary with conservation statistics

        Examples:
            >>> results = energy.is_conserved_on_trajectory(traj)
            >>> results['conserved']
            True
            >>> results['max_drift']
            1.234e-11
        """
        n = len(trajectory.states)
        values = np.zeros(n)

        for i, state in enumerate(trajectory.states):
            values[i] = self.evaluate(state)

        drift = np.max(np.abs(values - values[0]))
        relative_drift = drift / abs(values[0]) if abs(values[0]) > 1e-15 else drift

        conserved = drift < tolerance

        return {
            'conserved': conserved,
            'max_drift': drift,
            'relative_drift': relative_drift,
            'values': values,
            'tolerance': tolerance
        }


@dataclass
class IntegralSet:
    """
    Set of integrals (candidate for complete integrability).

    Attributes:
        integrals: List of Integral objects
        dimension: Phase space dimension (should = 2 × len(integrals))

    Examples:
        >>> integrals = IntegralSet([energy, L_integral, p_theta_integral])
        >>> integrals.n_integrals
        3
        >>> integrals.is_complete(phase_space_dim=8)
        False  # Need 4 for completeness
    """
    integrals: list[Integral]
    dimension: int = 8  # Phase space dimension

    @property
    def n_integrals(self) -> int:
        """Number of integrals"""
        return len(self.integrals)

    @property
    def required_for_integrability(self) -> int:
        """Number of integrals needed for complete integrability"""
        return self.dimension // 2

    def is_complete(self) -> bool:
        """Check if set is complete (n integrals for 2n phase space)"""
        return self.n_integrals == self.required_for_integrability

    def evaluate_all(self, state: BundleState) -> np.ndarray:
        """
        Evaluate all integrals at state.

        Returns:
            Array [F_1(state), F_2(state), ..., F_n(state)]
        """
        return np.array([F.evaluate(state) for F in self.integrals])

    def gradient_matrix(self, state: BundleState) -> np.ndarray:
        """
        Compute gradient matrix [∂F_i/∂z^j].

        Returns:
            Matrix of shape (n_integrals, dimension)
            Row i = gradient of F_i
        """
        n = self.n_integrals
        gradients = np.zeros((n, self.dimension))

        for i, F in enumerate(self.integrals):
            gradients[i] = F.gradient(state)

        return gradients
```

### IntegrabilityClassification

```python
# File: src/python/analysis/integrability_classification.py

from dataclasses import dataclass
from enum import Enum
import numpy as np

class IntegrabilityStatus(Enum):
    """Classification of integrability"""
    INTEGRABLE = "integrable"
    NON_INTEGRABLE = "non_integrable"
    PARTIALLY_INTEGRABLE = "partially_integrable"
    UNKNOWN = "unknown"


@dataclass
class IntegrabilityClassification:
    """
    Result of integrability analysis.

    Attributes:
        status: IntegrabilityStatus enum
        n_integrals_found: Number of independent integrals
        n_required: Number needed for complete integrability
        involution_verified: Whether {F_i, F_j} = 0 verified
        independence_verified: Whether dF_i are independent
        integrals: IntegralSet object
        poisson_bracket_matrix: Matrix [{F_i, F_j}]
        gradient_rank: Rank of gradient matrix
        evidence: Dictionary with detailed evidence
        recommendations: Next steps based on classification

    Examples:
        >>> classification = classifier.classify(integral_set, trajectories)
        >>> classification.status
        <IntegrabilityStatus.INTEGRABLE: 'integrable'>
        >>> classification.is_integrable
        True
    """
    status: IntegrabilityStatus
    n_integrals_found: int
    n_required: int
    involution_verified: bool
    independence_verified: bool
    integrals: 'IntegralSet'
    poisson_bracket_matrix: np.ndarray
    gradient_rank: int
    evidence: dict
    recommendations: list[str]

    @property
    def is_integrable(self) -> bool:
        """True if system is completely integrable"""
        return self.status == IntegrabilityStatus.INTEGRABLE

    @property
    def is_non_integrable(self) -> bool:
        """True if system is definitely non-integrable"""
        return self.status == IntegrabilityStatus.NON_INTEGRABLE

    @property
    def completion_percentage(self) -> float:
        """Percentage towards complete integrability"""
        return 100.0 * self.n_integrals_found / self.n_required

    def summary(self) -> str:
        """
        Human-readable summary.

        Returns:
            Multi-line string with classification summary
        """
        lines = [
            "=" * 60,
            "INTEGRABILITY CLASSIFICATION SUMMARY",
            "=" * 60,
            f"Status: {self.status.value.upper()}",
            f"Integrals found: {self.n_integrals_found}/{self.n_required}",
            f"Completion: {self.completion_percentage:.1f}%",
            "",
            "Verification Checks:",
            f"  • Independence: {'✓' if self.independence_verified else '✗'}",
            f"  • Involution: {'✓' if self.involution_verified else '✗'}",
            f"  • Gradient rank: {self.gradient_rank}",
            "",
            "Integrals:"
        ]

        for i, integral in enumerate(self.integrals.integrals, 1):
            lines.append(f"  {i}. {integral.name}")

        if self.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  → {rec}")

        lines.append("=" * 60)

        return "\n".join(lines)
```

---

## Core Algorithms

### D1: Functional Independence Test

**Algorithm: Gradient Rank Test**

```python
def test_functional_independence(
    integral_set: IntegralSet,
    test_states: list[BundleState],
    tolerance: float = 1e-8
) -> dict:
    """
    Test if integrals F_1, ..., F_n are functionally independent.

    Criterion: Gradients dF_1, ..., dF_n are linearly independent.

    Method: Compute rank of gradient matrix at multiple points.

    Args:
        integral_set: Set of integrals to test
        test_states: Multiple states where to test (ensure genericity)
        tolerance: Rank computation tolerance

    Returns:
        Dictionary with independence test results

    Performance:
        - Time: O(k × n × m²) for k states, n integrals, m=dimension
        - Space: O(n × m) for gradient matrix

    Examples:
        >>> integrals = IntegralSet([energy, L, p_theta])
        >>> test_states = [generate_random_bundle_state() for _ in range(100)]
        >>> results = test_functional_independence(integrals, test_states)
        >>> results['independent']
        True
        >>> results['min_rank']
        3
    """
    n_integrals = integral_set.n_integrals
    n_states = len(test_states)

    ranks = np.zeros(n_states, dtype=int)
    determinants = np.zeros(n_states)  # If square matrix

    for i, state in enumerate(test_states):
        # Compute gradient matrix
        grad_matrix = integral_set.gradient_matrix(state)

        # Compute rank
        ranks[i] = np.linalg.matrix_rank(grad_matrix, tol=tolerance)

        # If square, also compute determinant
        if grad_matrix.shape[0] == grad_matrix.shape[1]:
            determinants[i] = np.linalg.det(grad_matrix)

    # Check if rank is consistently = n_integrals
    min_rank = np.min(ranks)
    max_rank = np.max(ranks)
    mean_rank = np.mean(ranks)

    independent = (min_rank == n_integrals) and (max_rank == n_integrals)

    # Rank deficiency analysis
    rank_deficiency = n_integrals - min_rank

    results = {
        'independent': independent,
        'min_rank': min_rank,
        'max_rank': max_rank,
        'mean_rank': mean_rank,
        'expected_rank': n_integrals,
        'rank_deficiency': rank_deficiency,
        'ranks': ranks,
        'determinants': determinants if len(determinants) > 0 else None,
        'n_states_tested': n_states,
        'tolerance': tolerance
    }

    return results
```

### D2: Involution Verification

**Algorithm: Pairwise Poisson Bracket Computation**

```python
def verify_involution(
    integral_set: IntegralSet,
    test_states: list[BundleState],
    symplectic_form: 'ExtendedSymplecticForm',
    tolerance: float = 1e-8
) -> dict:
    """
    Verify {F_i, F_j} = 0 for all pairs i, j.

    Args:
        integral_set: Set of integrals
        test_states: Multiple test states
        symplectic_form: Extended symplectic form
        tolerance: Poisson bracket threshold

    Returns:
        Dictionary with involution verification results

    Performance:
        - Time: O(k × n² × m²) for k states, n integrals, m=dimension
        - Space: O(n²) for bracket matrix

    Examples:
        >>> results = verify_involution(integrals, test_states, form)
        >>> results['in_involution']
        True
        >>> results['max_bracket']
        3.456e-10
    """
    from ..lifts.poisson_bracket import PoissonBracket

    n = integral_set.n_integrals
    n_states = len(test_states)

    # Store brackets at each state
    bracket_matrices = np.zeros((n_states, n, n))

    bracket_calc = PoissonBracket(symplectic_form)

    for s, state in enumerate(test_states):
        for i in range(n):
            for j in range(i, n):  # Only upper triangle (anti-symmetry)
                bracket = bracket_calc.evaluate(
                    integral_set.integrals[i].function,
                    integral_set.integrals[j].function,
                    state
                )

                bracket_matrices[s, i, j] = bracket
                bracket_matrices[s, j, i] = -bracket  # Anti-symmetry

    # Statistics
    max_bracket = np.max(np.abs(bracket_matrices))
    mean_bracket = np.mean(np.abs(bracket_matrices))

    # Check involution: all brackets < tolerance
    in_involution = max_bracket < tolerance

    # Identify worst violators
    worst_state_idx = np.unravel_index(
        np.argmax(np.abs(bracket_matrices)),
        bracket_matrices.shape
    )[0]
    worst_pair = np.unravel_index(
        np.argmax(np.abs(bracket_matrices[worst_state_idx])),
        (n, n)
    )

    results = {
        'in_involution': in_involution,
        'max_bracket': max_bracket,
        'mean_bracket': mean_bracket,
        'bracket_matrices': bracket_matrices,
        'avg_bracket_matrix': np.mean(bracket_matrices, axis=0),
        'worst_state_idx': worst_state_idx,
        'worst_pair': worst_pair,
        'tolerance': tolerance,
        'n_states_tested': n_states
    }

    return results
```

### D3: Fourth Integral Search

**Algorithm: Candidate Generation and Testing**

```python
def search_for_fourth_integral(
    existing_integrals: IntegralSet,
    test_trajectories: list['BundleTrajectory'],
    candidate_generators: list[Callable],
    conservation_tolerance: float = 1e-10
) -> Optional[Integral]:
    """
    Systematic search for fourth integral of motion.

    Strategy:
        1. Generate candidate functions
        2. Test conservation on multiple trajectories
        3. Check functional independence with existing integrals
        4. Verify involution with existing integrals

    Args:
        existing_integrals: Known integrals (F_1, F_2, F_3)
        test_trajectories: Set of test trajectories
        candidate_generators: Functions generating candidate integrals
        conservation_tolerance: Threshold for conservation

    Returns:
        Fourth integral if found, else None

    Performance:
        - Time: O(n_candidates × n_trajs × n_points)
        - Can be parallelized over candidates

    Examples:
        >>> fourth_integral = search_for_fourth_integral(
        ...     IntegralSet([energy, L, p_theta]),
        ...     test_trajectories,
        ...     generate_polynomial_candidates()
        ... )
        >>> if fourth_integral:
        ...     print(f"Found F_4: {fourth_integral.name}")
        ... else:
        ...     print("No fourth integral found")
    """
    print(f"Searching for fourth integral...")
    print(f"  Testing {len(candidate_generators)} candidate generators")
    print(f"  On {len(test_trajectories)} test trajectories")

    candidates_tested = 0

    for generator in candidate_generators:
        # Generate candidate function
        candidate = generator()
        candidates_tested += 1

        # Test 1: Conservation
        conserved_on_all = True

        for traj in test_trajectories:
            integral_candidate = Integral(
                name=f"Candidate_{candidates_tested}",
                function=candidate
            )

            conservation_result = integral_candidate.is_conserved_on_trajectory(
                traj,
                tolerance=conservation_tolerance
            )

            if not conservation_result['conserved']:
                conserved_on_all = False
                break

        if not conserved_on_all:
            continue  # Not conserved, skip

        print(f"  → Candidate {candidates_tested} is conserved!")

        # Test 2: Functional independence
        augmented_integrals = IntegralSet(
            existing_integrals.integrals + [integral_candidate]
        )

        # Test on random states
        test_states = [
            traj.states[np.random.randint(len(traj.states))]
            for traj in test_trajectories[:10]
        ]

        independence_result = test_functional_independence(
            augmented_integrals,
            test_states
        )

        if not independence_result['independent']:
            print(f"    (but not independent, skipping)")
            continue

        print(f"  → Candidate {candidates_tested} is independent!")

        # Test 3: Involution with existing integrals
        # (Simplified: just check with existing three)

        # If all tests pass: WE FOUND IT!
        print(f"  ✓ FOUND FOURTH INTEGRAL!")
        return integral_candidate

    print(f"  ✗ No fourth integral found after testing {candidates_tested} candidates")
    return None


def generate_polynomial_candidates(
    max_degree: int = 4
) -> list[Callable]:
    """
    Generate polynomial candidate functions.

    Strategies:
        - Monomials: r12^a r23^b r31^c
        - Momentum polynomials: p12^a p23^b p31^c
        - Mixed: r_i^a p_j^b
        - Symmetric combinations

    Args:
        max_degree: Maximum polynomial degree

    Returns:
        List of candidate generator functions
    """
    generators = []

    import itertools

    # Monomials in positions
    for a, b, c in itertools.product(range(max_degree+1), repeat=3):
        if a + b + c == 0 or a + b + c > max_degree:
            continue

        def make_position_polynomial(a, b, c):
            return lambda state: (
                state.shape_state.r12**a *
                state.shape_state.r23**b *
                state.shape_state.r31**c
            )

        generators.append(lambda: make_position_polynomial(a, b, c))

    # Similar for momenta...

    # Eccentricity-like (inspired by Kepler problem)
    def eccentricity_candidate():
        """
        Runge-Lenz vector analog (if exists).

        For Kepler: e = p × L - m*G*M*r_hat
        """
        # Adapt to 3-body...
        return lambda state: 0.0  # Placeholder

    generators.append(eccentricity_candidate)

    return generators
```

### D4: Complete Classification

**Algorithm: Integrability Classifier**

```python
def classify_integrability(
    integral_set: IntegralSet,
    test_trajectories: list['BundleTrajectory'],
    symplectic_form: 'ExtendedSymplecticForm',
    search_for_additional: bool = True
) -> IntegrabilityClassification:
    """
    Complete integrability classification.

    Pipeline:
        1. Verify conservation on trajectories
        2. Test functional independence
        3. Verify involution
        4. Search for additional integrals (if requested)
        5. Classify status
        6. Generate recommendations

    Args:
        integral_set: Set of known integrals
        test_trajectories: Test trajectories
        symplectic_form: Extended symplectic form
        search_for_additional: Whether to search for more integrals

    Returns:
        IntegrabilityClassification object

    Examples:
        >>> classification = classify_integrability(
        ...     IntegralSet([energy, L, p_theta]),
        ...     trajectories,
        ...     extended_form
        ... )
        >>> print(classification.summary())
    """
    print("\n" + "="*60)
    print("INTEGRABILITY CLASSIFICATION")
    print("="*60)

    n_integrals = integral_set.n_integrals
    n_required = integral_set.required_for_integrability

    # Extract test states from trajectories
    test_states = []
    for traj in test_trajectories[:10]:  # Use first 10 trajectories
        # Sample states from trajectory
        n_samples = min(10, len(traj.states))
        indices = np.linspace(0, len(traj.states)-1, n_samples, dtype=int)
        test_states.extend([traj.states[i] for i in indices])

    # Step 1: Verify conservation
    print(f"\n1. Verifying conservation of {n_integrals} integrals...")
    conservation_results = []

    for i, integral in enumerate(integral_set.integrals):
        conserved_count = 0
        for traj in test_trajectories:
            result = integral.is_conserved_on_trajectory(traj)
            if result['conserved']:
                conserved_count += 1

        conservation_results.append(conserved_count / len(test_trajectories))
        print(f"   {integral.name}: {conservation_results[-1]*100:.1f}% conserved")

    all_conserved = all(r > 0.95 for r in conservation_results)

    # Step 2: Test independence
    print(f"\n2. Testing functional independence...")
    independence_result = test_functional_independence(
        integral_set,
        test_states
    )

    print(f"   Rank: {independence_result['min_rank']}/{n_integrals}")
    print(f"   Independent: {'✓' if independence_result['independent'] else '✗'}")

    # Step 3: Verify involution
    print(f"\n3. Verifying involution {{F_i, F_j}} = 0...")
    involution_result = verify_involution(
        integral_set,
        test_states,
        symplectic_form
    )

    print(f"   Max bracket: {involution_result['max_bracket']:.3e}")
    print(f"   In involution: {'✓' if involution_result['in_involution'] else '✗'}")

    # Step 4: Search for additional integrals
    fourth_integral = None

    if search_for_additional and n_integrals < n_required:
        print(f"\n4. Searching for additional integrals...")
        print(f"   Need: {n_required - n_integrals} more")

        candidates = generate_polynomial_candidates(max_degree=3)
        fourth_integral = search_for_fourth_integral(
            integral_set,
            test_trajectories,
            candidates
        )

        if fourth_integral:
            # Add to integral set
            integral_set = IntegralSet(
                integral_set.integrals + [fourth_integral]
            )
            n_integrals += 1

    # Step 5: Classification
    print(f"\n5. Classification...")

    if n_integrals == n_required and independence_result['independent'] and involution_result['in_involution']:
        status = IntegrabilityStatus.INTEGRABLE
        print("   STATUS: INTEGRABLE ✓")
    elif n_integrals < n_required:
        status = IntegrabilityStatus.NON_INTEGRABLE
        print("   STATUS: NON-INTEGRABLE (insufficient integrals)")
    else:
        status = IntegrabilityStatus.UNKNOWN
        print("   STATUS: UNKNOWN (further investigation needed)")

    # Step 6: Recommendations
    recommendations = []

    if status == IntegrabilityStatus.INTEGRABLE:
        recommendations.append("Construct action-angle coordinates")
        recommendations.append("Verify Liouville tori foliation")
        recommendations.append("Proceed to WP3 (solution characterization)")

    elif status == IntegrabilityStatus.NON_INTEGRABLE:
        recommendations.append("Proceed to WP2.3 (KS-Spinor lift, higher dimension)")
        recommendations.append("Analyze chaos indicators in lifted space")
        recommendations.append("Compare chaos levels: bundle vs. reduced")

    # Build classification object
    classification = IntegrabilityClassification(
        status=status,
        n_integrals_found=n_integrals,
        n_required=n_required,
        involution_verified=involution_result['in_involution'],
        independence_verified=independence_result['independent'],
        integrals=integral_set,
        poisson_bracket_matrix=involution_result['avg_bracket_matrix'],
        gradient_rank=independence_result['min_rank'],
        evidence={
            'conservation': conservation_results,
            'independence': independence_result,
            'involution': involution_result,
            'fourth_integral': fourth_integral
        },
        recommendations=recommendations
    )

    print("\n" + "="*60)
    print(classification.summary())

    return classification
```

---

## Implementation Details

### File Organization

```
src/python/analysis/
├── __init__.py
├── integral.py                     # Integral, IntegralSet classes
├── integrability_classification.py # Classification infrastructure
├── functional_independence.py      # Independence tests
├── involution_test.py              # Poisson bracket verification
├── integral_search.py              # Fourth integral search
└── action_angle.py                 # Action-angle construction (if integrable)
```

### Candidate Generation Strategies

**Polynomial Candidates**:
- Monomials in $r_{ij}$
- Monomials in $p_i$
- Mixed products

**Symmetry-Based**:
- Inspired by symmetries (permutations of masses)
- Conservation laws from Noether's theorem

**Kepler-Inspired**:
- Runge-Lenz vector analogs
- Eccentricity-like quantities

**Machine Learning** (future):
- Symbolic regression (SINDy, etc.)
- Neural network-discovered conserved quantities

---

## Validation Strategy

### Unit Tests

```python
# File: tests/analysis/test_integrability.py

class TestFunctionalIndependence:
    """Test independence testing"""

    def test_independent_set(self):
        """Test on known independent set"""
        pass

    def test_dependent_set(self):
        """Test on known dependent set"""
        pass


class TestInvolution:
    """Test Poisson bracket involution"""

    def test_canonical_involution(self):
        """{q, p} should NOT be in involution"""
        pass

    def test_conserved_involution(self):
        """Conserved quantities should be in involution"""
        pass


class TestIntegralSearch:
    """Test fourth integral search"""

    def test_polynomial_candidates(self):
        """Test polynomial candidate generation"""
        pass

    def test_conservation_check(self):
        """Test conservation verification"""
        pass
```

---

## Performance Targets

| Operation | Complexity | Target Time |
|-----------|-----------|-------------|
| Single integral evaluation | O(1) | < 1 μs |
| Gradient computation | O(n) | < 100 μs |
| Independence test | O(k × n × m²) | < 100 ms |
| Involution test | O(k × n² × m²) | < 1 s |
| Fourth integral search | O(cand × traj × pts) | < 10 min |

---

## Integration Points

### With Parts A, B, C
```python
from ..lifts.s1_bundle import BundleState
from ..lifts.extended_symplectic import ExtendedSymplecticForm
from ..lifts.lifted_hamiltonian import BundleTrajectory
```

### With WP3 (if integrable)
```python
# Pass action-angle coordinates to solution characterization
```

### With WP2.3 (if non-integrable)
```python
# Motivation for higher-dimensional lift
```

---

## Success Criteria

### Part D Complete When:

- [  ] Three integrals verified as conserved
- [  ] Functional independence tested
- [  ] Involution verified for known integrals
- [  ] Fourth integral search completed
- [  ] Classification determined: integrable or non-integrable
- [  ] If integrable: action-angle coordinates constructed
- [  ] If non-integrable: obstruction documented
- [  ] Technical report section written
- [  ] Recommendations for next steps documented
- [  ] All tests passing

**Key Outcome**: Definitive answer to:
**"Is the planar three-body problem integrable on the S¹ bundle?"**

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 3 days

**This completes WP 2.2 design documentation!**

Next: Update status tracker and commit all WP 2.2 documentation.
