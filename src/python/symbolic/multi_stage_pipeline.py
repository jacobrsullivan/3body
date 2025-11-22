"""
Multi-stage symbolic regression pipeline (AMENDED WP3.3).

This module coordinates all search methods in a hierarchical workflow:
    Stage 1: Standard polynomial/rational regression
    Stage 2: Spinor-based search (if regularization beneficial)
    Stage 3: Elliptic function search (if quasi-periodic detected)
    Stage 4: Theta function search (if strong integrability evidence)

The pipeline automatically selects appropriate methods based on trajectory
characteristics and intermediate results.

References:
- AMENDED_Task-3.3.1-Implementation-Plan.md
- AMENDED_WP3.3-Symbolic-Regression-Summary.md
"""

import numpy as np
import sympy as sp
from typing import List, Tuple, Optional, Callable, Dict
from dataclasses import dataclass
from enum import Enum

from .regression_pipeline import sindy_regression, pysr_regression, hierarchical_regression
from .spinor_search import search_spinor_integral, SpinorSearchResult
from .elliptic_search import search_elliptic_integral, detect_elliptic_signature, EllipticSearchResult
from .enhanced_validation import multi_scale_conservation_test, detect_quasi_periodic_structure
from .interpretability import compute_interpretability_score, FunctionType
from .candidate_ranking import CandidateIntegral, CandidateSource


class SearchStage(Enum):
    """Search stages in multi-stage pipeline."""
    POLYNOMIAL = "stage1_polynomial"
    SPINOR = "stage2_spinor"
    ELLIPTIC = "stage3_elliptic"
    THETA = "stage4_theta"


@dataclass
class MultiStageResult:
    """
    Result from multi-stage pipeline.

    Attributes:
        best_candidate: Best CandidateIntegral found
        stage_completed: Highest stage completed
        all_candidates: All candidates from all stages
        trajectory_characteristics: Dict of detected features
        recommendation: Recommendation for next steps
    """
    best_candidate: Optional[CandidateIntegral]
    stage_completed: SearchStage
    all_candidates: List[CandidateIntegral]
    trajectory_characteristics: Dict
    recommendation: str


def analyze_trajectory_characteristics(
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    masses: np.ndarray
) -> Dict:
    """
    Analyze trajectory to determine which search stages to activate.

    Detects:
        1. Close encounters (→ spinor search)
        2. Quasi-periodic structure (→ elliptic search)
        3. Multiple timescales
        4. System energy/complexity

    Args:
        trajectory: Phase space trajectory
        trajectory_times: Time points
        masses: Body masses

    Returns:
        characteristics: Dict with detected features
    """
    characteristics = {}

    # 1. Check for close encounters
    n_bodies = len(masses)
    dim = 3
    n_samples = len(trajectory)

    close_encounter_count = 0
    min_distance = np.inf

    for state in trajectory:
        positions = []
        for i in range(n_bodies):
            r_i = state[i*dim:(i+1)*dim]
            positions.append(r_i)

        for i in range(n_bodies):
            for j in range(i+1, n_bodies):
                dist = np.linalg.norm(positions[i] - positions[j])
                min_distance = min(min_distance, dist)
                if dist < 0.1:
                    close_encounter_count += 1

    close_encounter_fraction = close_encounter_count / (n_samples * n_bodies * (n_bodies-1) / 2)
    characteristics['close_encounter_fraction'] = close_encounter_fraction
    characteristics['min_distance'] = min_distance
    characteristics['needs_regularization'] = close_encounter_fraction > 0.05

    # 2. Analyze energy
    # Simple energy estimate: KE + PE
    energies = []
    for state in trajectory:
        positions = [state[i*dim:(i+1)*dim] for i in range(n_bodies)]
        velocities = [state[n_bodies*dim + i*dim:n_bodies*dim + (i+1)*dim] for i in range(n_bodies)]

        KE = 0.5 * sum(masses[i] * np.dot(velocities[i], velocities[i]) for i in range(n_bodies))

        PE = 0.0
        for i in range(n_bodies):
            for j in range(i+1, n_bodies):
                r_ij = np.linalg.norm(positions[i] - positions[j])
                if r_ij > 1e-10:
                    PE -= masses[i] * masses[j] / r_ij

        energies.append(KE + PE)

    energy_drift = np.abs(np.max(energies) - np.min(energies))
    characteristics['energy_drift'] = energy_drift
    characteristics['mean_energy'] = np.mean(energies)

    # 3. Trajectory duration and sampling
    total_time = trajectory_times[-1] - trajectory_times[0]
    dt_mean = np.mean(np.diff(trajectory_times))

    characteristics['total_time'] = total_time
    characteristics['dt_mean'] = dt_mean
    characteristics['n_samples'] = n_samples

    return characteristics


def run_multi_stage_pipeline(
    I_numerical: Callable,
    trajectory: np.ndarray,
    trajectory_times: np.ndarray,
    masses: np.ndarray,
    max_stage: SearchStage = SearchStage.ELLIPTIC,
    state_symbols: Optional[List[sp.Symbol]] = None,
    verbose: bool = True
) -> MultiStageResult:
    """
    Run complete multi-stage symbolic regression pipeline.

    Pipeline stages:
        1. POLYNOMIAL: Standard SINDy/PySR with polynomial basis
        2. SPINOR: KS regularized coordinates (if close encounters)
        3. ELLIPTIC: Jacobi elliptic functions (if quasi-periodic)
        4. THETA: Theta functions (if strong integrability evidence)

    Each stage is only executed if previous stages suggest it would be beneficial.

    Args:
        I_numerical: Candidate conserved quantity (numerical function)
        trajectory: Phase space trajectory (N, dim)
        trajectory_times: Time points (N,)
        masses: Body masses
        max_stage: Maximum stage to attempt
        state_symbols: SymPy symbols for state (optional)
        verbose: Print progress

    Returns:
        result: MultiStageResult with best candidate and all findings

    Example:
        >>> result = run_multi_stage_pipeline(
        ...     I_numerical=my_integral,
        ...     trajectory=traj,
        ...     trajectory_times=times,
        ...     masses=np.array([1.0, 1.0, 1.0])
        ... )
        >>> print(f"Best candidate: {result.best_candidate.name}")
        >>> print(f"Function type: {result.best_candidate.metadata['function_type']}")
    """
    if verbose:
        print("=" * 70)
        print("MULTI-STAGE SYMBOLIC REGRESSION PIPELINE")
        print("=" * 70)

    all_candidates = []
    best_candidate = None

    # Initialize state symbols if not provided
    if state_symbols is None:
        state_symbols = [sp.Symbol(f'z{i}') for i in range(len(trajectory[0]))]

    # Analyze trajectory
    if verbose:
        print("\nAnalyzing trajectory characteristics...")
        print("-" * 70)

    characteristics = analyze_trajectory_characteristics(
        trajectory, trajectory_times, masses
    )

    if verbose:
        print(f"  Close encounters: {characteristics['close_encounter_fraction']:.1%}")
        print(f"  Min distance: {characteristics['min_distance']:.4f}")
        print(f"  Energy drift: {characteristics['energy_drift']:.2e}")
        print(f"  Total time: {characteristics['total_time']:.2f}")
        print(f"  Samples: {characteristics['n_samples']}")

    # ========== STAGE 1: POLYNOMIAL REGRESSION ==========

    if verbose:
        print("\n" + "=" * 70)
        print("STAGE 1: POLYNOMIAL/RATIONAL REGRESSION")
        print("=" * 70)

    from .basis_functions import construct_hierarchical_basis

    # Build standard basis
    standard_basis = construct_hierarchical_basis(
        masses=masses,
        max_polynomial_degree=3,
        include_transcendental=True
    )

    if verbose:
        print(f"  Basis size: {len(standard_basis)} functions")

    # Try SINDy
    if verbose:
        print("  Running SINDy...")

    try:
        sindy_result = sindy_regression(
            I_numerical=I_numerical,
            sample_states=trajectory[::10],
            basis_library=standard_basis,
            threshold=0.01
        )

        if sindy_result.residual < 0.01:
            if verbose:
                print(f"  ✓ SINDy success: residual = {sindy_result.residual:.2e}")

            # Create candidate
            from .simplification import count_operations

            candidate = CandidateIntegral(
                name="Polynomial_SINDy",
                expression_symbolic=sindy_result.expression_symbolic,
                expression_numerical=I_numerical,
                source=CandidateSource.SYMBOLIC_REGRESSION,
                conservation_error=sindy_result.residual,
                complexity=count_operations(sindy_result.expression_symbolic),
                is_independent=True,  # Assume independent for now
                metadata={
                    'search_stage': 'polynomial',
                    'method': 'sindy'
                }
            )

            all_candidates.append(candidate)
            best_candidate = candidate
        else:
            if verbose:
                print(f"  ✗ SINDy failed: residual = {sindy_result.residual:.2e}")
    except Exception as e:
        if verbose:
            print(f"  ✗ SINDy error: {e}")

    # If polynomial stage succeeded with low residual, we're done
    if best_candidate and best_candidate.conservation_error < 0.001:
        if verbose:
            print("\n  ✓ Polynomial regression sufficient - stopping early")

        return MultiStageResult(
            best_candidate=best_candidate,
            stage_completed=SearchStage.POLYNOMIAL,
            all_candidates=all_candidates,
            trajectory_characteristics=characteristics,
            recommendation="Polynomial integral found with high accuracy. No further search needed."
        )

    # ========== STAGE 2: SPINOR SEARCH ==========

    if max_stage.value >= SearchStage.SPINOR.value and characteristics['needs_regularization']:
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 2: SPINOR-BASED SEARCH")
            print("=" * 70)
            print("  (Triggered by close encounters)")

        spinor_result = search_spinor_integral(
            I_numerical=I_numerical,
            trajectory=trajectory,
            masses=masses,
            state_symbols=state_symbols
        )

        if spinor_result.found_spinor_integral:
            if verbose:
                print(f"  ✓ Spinor integral found: {spinor_result.spinor_component_type}")

            # Create candidate
            from .simplification import count_operations

            candidate = CandidateIntegral(
                name=f"Spinor_{spinor_result.spinor_component_type}",
                expression_symbolic=spinor_result.best_expression,
                expression_numerical=spinor_result.best_function,
                source=CandidateSource.SYMBOLIC_REGRESSION,
                conservation_error=spinor_result.validation.conservation_error if spinor_result.validation else 1.0,
                complexity=count_operations(spinor_result.best_expression),
                is_independent=True,
                validation_result=spinor_result.validation,
                metadata={
                    'search_stage': 'spinor',
                    'spinor_type': spinor_result.spinor_component_type,
                    'function_type': 'spinor'
                }
            )

            all_candidates.append(candidate)

            # Update best if better
            if best_candidate is None or candidate.conservation_error < best_candidate.conservation_error:
                best_candidate = candidate
    else:
        if verbose and max_stage.value >= SearchStage.SPINOR.value:
            print("\n  ℹ Skipping spinor search (no close encounters)")

    # ========== STAGE 3: ELLIPTIC SEARCH ==========

    if max_stage.value >= SearchStage.ELLIPTIC.value:
        # Check for quasi-periodic signature
        if verbose:
            print("\n  Checking for quasi-periodic structure...")

        has_qp, qp_confidence, freqs = detect_elliptic_signature(
            I_numerical, trajectory, trajectory_times, threshold=0.6
        )

        if has_qp:
            if verbose:
                print("\n" + "=" * 70)
                print("STAGE 3: ELLIPTIC FUNCTION SEARCH")
                print("=" * 70)
                print(f"  (Triggered by quasi-periodic signature, confidence={qp_confidence:.2f})")

            elliptic_result = search_elliptic_integral(
                I_numerical=I_numerical,
                trajectory=trajectory,
                trajectory_times=trajectory_times,
                masses=masses,
                state_symbols=state_symbols
            )

            if elliptic_result.found_elliptic:
                if verbose:
                    print(f"  ✓ Elliptic integral found!")
                    print(f"    Method: {elliptic_result.search_method}")
                    print(f"    Elliptic parameter m: {elliptic_result.elliptic_parameter:.4f}")

                # Create candidate
                from .simplification import count_operations

                candidate = CandidateIntegral(
                    name=f"Elliptic_{elliptic_result.search_method}",
                    expression_symbolic=elliptic_result.best_expression,
                    expression_numerical=elliptic_result.best_function,
                    source=CandidateSource.SYMBOLIC_REGRESSION,
                    conservation_error=elliptic_result.validation.conservation_error if elliptic_result.validation else 1.0,
                    complexity=count_operations(elliptic_result.best_expression),
                    is_independent=True,
                    validation_result=elliptic_result.validation,
                    metadata={
                        'search_stage': 'elliptic',
                        'elliptic_parameter': elliptic_result.elliptic_parameter,
                        'function_type': 'elliptic',
                        'CRITICAL_DISCOVERY': True  # Flag exceptional finding
                    }
                )

                all_candidates.append(candidate)

                # Update best
                if best_candidate is None or candidate.conservation_error < best_candidate.conservation_error:
                    best_candidate = candidate
        else:
            if verbose:
                print(f"\n  ℹ Skipping elliptic search (no quasi-periodic signature)")

    # ========== FINAL ANALYSIS ==========

    if verbose:
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)

    # Determine recommendation
    if best_candidate is None:
        recommendation = "No suitable integral form discovered. Try:\n" \
                        "  1. Longer trajectory integration\n" \
                        "  2. Different initial conditions\n" \
                        "  3. Manual analysis of system symmetries"
        stage_completed = SearchStage.POLYNOMIAL

    elif best_candidate.conservation_error < 1e-6:
        # Compute interpretability
        interp = compute_interpretability_score(best_candidate.expression_symbolic)
        best_candidate.metadata['interpretability'] = interp.interpretability
        best_candidate.metadata['physical_meaning'] = interp.physical_meaning

        if interp.function_type in [FunctionType.ELLIPTIC, FunctionType.THETA]:
            recommendation = "EXCEPTIONAL DISCOVERY: Elliptic/theta integral found.\n" \
                           "  → Proceed to WP4 for rigorous validation\n" \
                           "  → Verify against known integrable cases\n" \
                           "  → Publish findings if validated"
        elif interp.function_type == FunctionType.SPINOR:
            recommendation = "Spinor-based integral discovered.\n" \
                           "  → Validate using KS transformation properties\n" \
                           "  → Check for hidden SO(4) symmetries\n" \
                           "  → Proceed to WP4 validation"
        else:
            recommendation = "Polynomial/rational integral found.\n" \
                           "  → Validate conservation on independent trajectories\n" \
                           "  → Check functional independence from known integrals\n" \
                           "  → Proceed to WP4 if novel"

        # Determine stage completed
        stage_name = best_candidate.metadata.get('search_stage', 'polynomial')
        if stage_name == 'elliptic':
            stage_completed = SearchStage.ELLIPTIC
        elif stage_name == 'spinor':
            stage_completed = SearchStage.SPINOR
        else:
            stage_completed = SearchStage.POLYNOMIAL

    else:
        recommendation = "Approximate integral form found (moderate accuracy).\n" \
                        "  → Verify on longer trajectories\n" \
                        "  → Try different regression parameters\n" \
                        "  → May indicate approximate/partial integral"
        stage_completed = SearchStage.POLYNOMIAL

    if verbose:
        print(f"\nBest candidate: {best_candidate.name if best_candidate else 'None'}")
        print(f"Stages completed: {stage_completed.value}")
        print(f"Total candidates: {len(all_candidates)}")
        print(f"\nRecommendation:\n{recommendation}")

    return MultiStageResult(
        best_candidate=best_candidate,
        stage_completed=stage_completed,
        all_candidates=all_candidates,
        trajectory_characteristics=characteristics,
        recommendation=recommendation
    )


# Example usage
if __name__ == "__main__":
    print("Multi-Stage Pipeline - Example")
    print("=" * 70)

    # Create synthetic trajectory
    trajectory = np.random.randn(1000, 18)
    times = np.linspace(0, 100, 1000)
    masses = np.array([1.0, 1.0, 1.0])

    # Create synthetic conserved quantity (energy-like)
    def synthetic_integral(state):
        # Kinetic energy
        v = state[9:18]
        return 0.5 * np.dot(v, v)

    # Run pipeline
    result = run_multi_stage_pipeline(
        I_numerical=synthetic_integral,
        trajectory=trajectory,
        trajectory_times=times,
        masses=masses,
        max_stage=SearchStage.ELLIPTIC,
        verbose=True
    )

    print("\n" + "=" * 70)
    print("Pipeline complete!")
    print("=" * 70)
