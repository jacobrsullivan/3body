"""
Triviality filtering for conserved quantities (WP 3.1, Task 3.1.4, Part B).

Filters out "trivial" integrals that don't represent new physics:
1. Coordinate functions (q_i, p_i)
2. Known conservation laws (E, L, p_θ)
3. Linear combinations of the above
4. Constants on the energy shell

Strategy: Generate test states, evaluate candidates and known integrals,
check for linear dependence via correlation/regression.
"""

from typing import List, Tuple, Optional, Dict
import numpy as np
from scipy import stats

from .integral_from_killing import ConservedIntegral, State


# =============================================================================
# Known Integrals Database
# =============================================================================

class KnownIntegrals:
    """Database of known conserved quantities for filtering"""

    @staticmethod
    def energy(
        masses: np.ndarray,
        potential_func: Optional[callable] = None,
        G: float = 1.0
    ) -> ConservedIntegral:
        """
        Total energy E = T + V.

        Args:
            masses: Particle masses
            potential_func: V(q) function (gravitational if None)
            G: Gravitational constant
        """
        def energy_expr(state: np.ndarray) -> float:
            if isinstance(state, State):
                q, p = state.q, state.p
            else:
                n = len(state) // 2
                q, p = state[:n], state[n:]

            # Kinetic energy (assuming p = m v for simplicity)
            T = 0.5 * np.sum(p**2)

            # Potential energy
            if potential_func is not None:
                V = potential_func(q)
            else:
                # Simple gravitational (placeholder)
                V = -np.sum(q**2)**(-0.5) if np.sum(q**2) > 1e-10 else 0.0

            return T + V

        def energy_grad(state: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
            """∂E/∂q = ∂V/∂q, ∂E/∂p = p (for standard kinetic energy)"""
            if isinstance(state, State):
                q, p = state.q, state.p
            else:
                n = len(state) // 2
                q, p = state[:n], state[n:]

            dE_dp = p.copy()

            # dV/dq via finite differences
            eps = 1e-6
            dE_dq = np.zeros_like(q)
            for i in range(len(q)):
                q_plus = q.copy()
                q_plus[i] += eps
                E_plus = energy_expr(np.concatenate([q_plus, p]))
                E_0 = energy_expr(np.concatenate([q, p]))
                dE_dq[i] = (E_plus - E_0) / eps

            return dE_dq, dE_dp

        return ConservedIntegral(
            name="Energy",
            expression=energy_expr,
            gradient=energy_grad,
            source='known',
            manifold_type='generic'
        )

    @staticmethod
    def angular_momentum_components(dimension: int = 3) -> List[ConservedIntegral]:
        """
        Angular momentum L_x, L_y, L_z (for 3D systems).

        For planar systems, only L_z is relevant.
        """
        # Placeholder - full implementation would depend on coordinate system
        integrals = []

        def Lz_expr(state: np.ndarray) -> float:
            """L_z = x p_y - y p_x (for 2D)"""
            if isinstance(state, State):
                q, p = state.q, state.p
            else:
                n = len(state) // 2
                q, p = state[:n], state[n:]

            if len(q) >= 2:
                return q[0] * p[1] - q[1] * p[0]
            return 0.0

        integrals.append(ConservedIntegral(
            name="AngularMomentum_z",
            expression=Lz_expr,
            source='known',
            manifold_type='generic'
        ))

        return integrals

    @staticmethod
    def s1_fiber_momentum() -> ConservedIntegral:
        """
        Momentum conjugate to S¹ fiber coordinate θ.

        For S¹ bundle (s, θ), p_θ is conserved.
        """
        def p_theta_expr(state: np.ndarray) -> float:
            if isinstance(state, State):
                p = state.p
            else:
                n = len(state) // 2
                p = state[n:]

            # Assume θ is last coordinate
            return p[-1]

        return ConservedIntegral(
            name="FiberMomentum_theta",
            expression=p_theta_expr,
            source='known',
            manifold_type='s1_bundle'
        )

    @staticmethod
    def center_of_mass_momentum() -> List[ConservedIntegral]:
        """Total linear momentum P_x, P_y, P_z"""
        integrals = []

        for i, axis in enumerate(['x', 'y', 'z']):
            def make_P_expr(idx):
                def P_expr(state: np.ndarray) -> float:
                    if isinstance(state, State):
                        p = state.p
                    else:
                        n = len(state) // 2
                        p = state[n:]
                    # Sum momenta (assuming particle indices are grouped)
                    return np.sum(p[idx::3]) if len(p) > idx else 0.0
                return P_expr

            integrals.append(ConservedIntegral(
                name=f"TotalMomentum_{axis}",
                expression=make_P_expr(i),
                source='known',
                manifold_type='generic'
            ))

        return integrals

    @staticmethod
    def get_all_known(
        manifold_type: str,
        masses: np.ndarray,
        *,
        include_com: bool = False
    ) -> List[ConservedIntegral]:
        """
        Get all known integrals for this manifold type.

        Args:
            manifold_type: 's1_bundle', 'ks_spinor', or 'generic'
            masses: Particle masses
            include_com: Include center of mass momentum (False for CM frame)

        Returns:
            List of known ConservedIntegral objects
        """
        known = [
            KnownIntegrals.energy(masses),
            *KnownIntegrals.angular_momentum_components(),
        ]

        if manifold_type == 's1_bundle':
            known.append(KnownIntegrals.s1_fiber_momentum())

        if include_com:
            known.extend(KnownIntegrals.center_of_mass_momentum())

        return known


# =============================================================================
# Triviality Tests
# =============================================================================

def is_trivial_coordinate(
    candidate: ConservedIntegral,
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> Tuple[bool, Optional[str]]:
    """
    Test if candidate is just a coordinate function q_i or p_i.

    Method:
        Evaluate candidate and each coordinate on test states.
        Compute correlation.
        If |corr| > 1 - tolerance, it's a coordinate function.

    Args:
        candidate: Integral to test
        test_states: Sample states for evaluation
        tolerance: Correlation threshold

    Returns:
        (is_trivial, coordinate_name)
    """
    if len(test_states) == 0:
        return False, None

    # Evaluate candidate
    candidate_values = np.array([candidate(s.to_array()) for s in test_states])

    # Test against each coordinate
    n = test_states[0].dimension

    # Test q coordinates
    for i in range(n):
        coord_values = np.array([s.q[i] for s in test_states])

        if np.std(coord_values) < 1e-10:
            continue  # Skip constant coordinates

        correlation = np.abs(np.corrcoef(candidate_values, coord_values)[0, 1])

        if correlation > 1 - tolerance:
            return True, f"q_{i}"

    # Test p coordinates
    for i in range(n):
        coord_values = np.array([s.p[i] for s in test_states])

        if np.std(coord_values) < 1e-10:
            continue

        correlation = np.abs(np.corrcoef(candidate_values, coord_values)[0, 1])

        if correlation > 1 - tolerance:
            return True, f"p_{i}"

    return False, None


def is_trivial_known(
    candidate: ConservedIntegral,
    known_integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> Tuple[bool, Optional[str]]:
    """
    Test if candidate is a known integral (or linear combination).

    Method:
        For each known integral I_k:
            Fit: candidate ≈ a·I_k + b
            If residual small, candidate is trivial.

    Args:
        candidate: Candidate to test
        known_integrals: List of known integrals
        test_states: Test states
        tolerance: Relative residual threshold

    Returns:
        (is_trivial, match_name)
    """
    if len(test_states) == 0:
        return False, None

    candidate_values = np.array([candidate(s.to_array()) for s in test_states])

    for known in known_integrals:
        known_values = np.array([known(s.to_array()) for s in test_states])

        # Skip if known integral is constant
        if np.std(known_values) < 1e-10:
            continue

        # Linear regression: candidate = a * known + b
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            known_values, candidate_values
        )

        # Compute residual
        predicted = slope * known_values + intercept
        residual_norm = np.linalg.norm(candidate_values - predicted)
        candidate_norm = np.linalg.norm(candidate_values)

        relative_residual = residual_norm / (candidate_norm + 1e-12)

        if relative_residual < tolerance or r_value**2 > (1 - tolerance):
            return True, known.name

    return False, None


def is_constant_on_shell(
    candidate: ConservedIntegral,
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> bool:
    """
    Test if candidate is approximately constant on energy shell.

    Method:
        Evaluate on many states with same energy.
        If std(values) / |mean(values)| < tolerance, it's constant.

    Args:
        candidate: Candidate integral
        test_states: Test states (should all have same energy)
        tolerance: Relative variation threshold

    Returns:
        True if approximately constant
    """
    if len(test_states) == 0:
        return False

    values = np.array([candidate(s.to_array()) for s in test_states])

    mean_val = np.mean(values)
    std_val = np.std(values)

    relative_std = std_val / (np.abs(mean_val) + 1e-12)

    return relative_std < tolerance


# =============================================================================
# Batch Filtering
# =============================================================================

def filter_trivial_integrals(
    candidates: List[ConservedIntegral],
    known_integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6,
    verbose: bool = True
) -> Tuple[List[ConservedIntegral], List[Dict]]:
    """
    Apply all triviality filters to candidate integrals.

    Args:
        candidates: List of candidate integrals
        known_integrals: List of known integrals
        test_states: Test states for evaluation
        tolerance: Threshold for all tests
        verbose: Print filtering results

    Returns:
        (non_trivial_candidates, rejection_reasons)
        rejection_reasons: List of dicts explaining rejections
    """
    non_trivial = []
    rejections = []

    if verbose:
        print(f"Filtering {len(candidates)} candidates:")
        print(f"  Test states: {len(test_states)}")
        print(f"  Known integrals: {len(known_integrals)}")
        print()

    for idx, candidate in enumerate(candidates):
        if verbose:
            print(f"  Candidate {idx}: {candidate.name}")

        # Test 1: Coordinate function
        is_coord, coord_name = is_trivial_coordinate(
            candidate, test_states, tolerance=tolerance
        )
        if is_coord:
            rejections.append({
                'candidate': candidate.name,
                'reason': f'coordinate_function: {coord_name}'
            })
            if verbose:
                print(f"    ✗ Rejected: coordinate {coord_name}")
            continue

        # Test 2: Known integral
        is_known, match = is_trivial_known(
            candidate, known_integrals, test_states, tolerance=tolerance
        )
        if is_known:
            rejections.append({
                'candidate': candidate.name,
                'reason': f'known_integral: {match}'
            })
            if verbose:
                print(f"    ✗ Rejected: matches {match}")
            continue

        # Test 3: Constant on shell
        is_const = is_constant_on_shell(
            candidate, test_states, tolerance=tolerance
        )
        if is_const:
            rejections.append({
                'candidate': candidate.name,
                'reason': 'constant_on_shell'
            })
            if verbose:
                print(f"    ✗ Rejected: constant")
            continue

        # Passed all tests
        non_trivial.append(candidate)
        if verbose:
            print(f"    ✓ Accepted")

    if verbose:
        print()
        print(f"Results: {len(non_trivial)}/{len(candidates)} non-trivial")

    return non_trivial, rejections


# =============================================================================
# Utility Functions
# =============================================================================

def generate_test_states(
    dimension: int,
    num_states: int,
    *,
    energy_range: Optional[Tuple[float, float]] = None,
    seed: int = 42
) -> List[State]:
    """
    Generate random test states for filtering.

    Args:
        dimension: Phase space dimension (n)
        num_states: Number of states to generate
        energy_range: Optional (E_min, E_max) constraint
        seed: Random seed

    Returns:
        List of State objects
    """
    rng = np.random.RandomState(seed)

    states = []
    for _ in range(num_states):
        q = rng.randn(dimension)
        p = rng.randn(dimension)

        # Optionally scale to match energy range
        # (simplified - would need actual Hamiltonian)

        states.append(State(q=q, p=p))

    return states
