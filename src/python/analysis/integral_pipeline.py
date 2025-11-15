"""
Complete integral discovery pipeline (WP 3.1, Task 3.1.4, Part F).

Orchestrates the complete workflow from Killing fields to verified conserved quantities:
1. Convert Killing fields → integrals
2. Filter trivial integrals
3. Test functional independence
4. Verify conservation on trajectories
5. Rank and export results

This is the main entry point for Task 3.1.4.
"""

from typing import List, Dict, Callable, Optional, Tuple
import numpy as np
from dataclasses import dataclass, asdict
import json
import pickle

from ..pde.mesh_generation import Mesh
from ..pde.killing_solver import KillingSolution
from .integral_from_killing import (
    ConservedIntegral,
    State,
    killing_vector_to_integral,
    convert_killing_fields_batch
)
from .triviality_filter import (
    KnownIntegrals,
    filter_trivial_integrals,
    generate_test_states
)
from .independence_test import (
    analyze_integral_structure
)
from .conservation_verification import (
    verify_integrals_batch
)


# =============================================================================
# Results Dataclass
# =============================================================================

@dataclass
class IntegralDiscoveryResult:
    """
    Complete results from integral discovery pipeline.

    Attributes:
        raw_candidates: All integrals from Killing fields
        non_trivial: After triviality filtering
        independent: Functionally independent subset
        conserved: Verified via trajectory integration
        ranked: Final ranked list with quality metrics
        statistics: Summary statistics
        manifold_type: Type of manifold
        field_type: 'vector' or 'tensor'
    """
    raw_candidates: List[ConservedIntegral]
    non_trivial: List[ConservedIntegral]
    independent: List[ConservedIntegral]
    conserved: List[ConservedIntegral]
    ranked: List[Tuple[ConservedIntegral, Dict]]
    statistics: Dict
    manifold_type: str
    field_type: str


# =============================================================================
# Main Pipeline
# =============================================================================

def integral_discovery_pipeline(
    killing_solution: KillingSolution,
    metric_func: Callable[[np.ndarray], np.ndarray],
    hamiltonian: Callable[[np.ndarray], float],
    masses: np.ndarray,
    *,
    test_trajectory_count: int = 10,
    test_state_count: int = 100,
    time_span: Tuple[float, float] = (0, 100),
    conservation_tolerance: float = 1e-6,
    independence_tolerance: float = 1e-6,
    triviality_tolerance: float = 1e-6,
    success_threshold: float = 0.9,
    verbose: bool = True
) -> IntegralDiscoveryResult:
    """
    Complete pipeline from Killing fields to verified integrals.

    Steps:
    1. Convert Killing fields → conserved integrals
    2. Filter trivial integrals (coordinates, known integrals)
    3. Test functional independence
    4. Verify conservation along trajectories
    5. Rank by quality metrics
    6. Package results

    Args:
        killing_solution: Output from solve_killing_fields()
        metric_func: Metric tensor function g(q)
        hamiltonian: System Hamiltonian H(q, p)
        masses: Particle masses
        test_trajectory_count: Number of trajectories for verification
        test_state_count: Number of states for other tests
        time_span: Integration time for verification
        conservation_tolerance: Max drift for conservation
        independence_tolerance: Tolerance for Jacobian rank
        triviality_tolerance: Tolerance for triviality tests
        success_threshold: Minimum success rate (e.g., 0.9 = 90%)
        verbose: Print detailed progress

    Returns:
        IntegralDiscoveryResult with all candidates and filtering steps
    """
    if verbose:
        print("="*70)
        print("INTEGRAL DISCOVERY PIPELINE")
        print("="*70)
        print()

    manifold_type = killing_solution.metadata.get('manifold_type', 'generic')
    field_type = killing_solution.metadata.get('field_type', 'vector')

    # Generate test states
    n = killing_solution.mesh.dimension
    test_states = generate_test_states(
        dimension=n,
        num_states=test_state_count
    )

    test_trajectories = test_states[:test_trajectory_count]

    # =========================================================================
    # Step 1: Convert Killing fields to integrals
    # =========================================================================

    if verbose:
        print("[1/5] Converting Killing fields to integrals...")
        print(f"  Killing fields found: {len(killing_solution.killing_fields)}")

    if len(killing_solution.killing_fields) == 0:
        if verbose:
            print("  No Killing fields to convert.")
            print()

        return IntegralDiscoveryResult(
            raw_candidates=[],
            non_trivial=[],
            independent=[],
            conserved=[],
            ranked=[],
            statistics={
                'raw_count': 0,
                'non_trivial_count': 0,
                'independent_count': 0,
                'conserved_count': 0
            },
            manifold_type=manifold_type,
            field_type=field_type
        )

    raw_candidates = convert_killing_fields_batch(
        killing_solution.killing_fields,
        killing_solution.mesh,
        metric_func,
        field_type=field_type,
        verbose=verbose
    )

    if verbose:
        print(f"  Converted {len(raw_candidates)} integrals")
        print()

    # =========================================================================
    # Step 2: Filter trivial integrals
    # =========================================================================

    if verbose:
        print("[2/5] Filtering trivial integrals...")

    known_integrals = KnownIntegrals.get_all_known(
        manifold_type,
        masses,
        include_com=False  # Assume CM frame
    )

    if verbose:
        print(f"  Known integrals: {[k.name for k in known_integrals]}")

    non_trivial, rejections = filter_trivial_integrals(
        raw_candidates,
        known_integrals,
        test_states,
        tolerance=triviality_tolerance,
        verbose=verbose
    )

    if verbose:
        print()

    # =========================================================================
    # Step 3: Test functional independence
    # =========================================================================

    if verbose:
        print("[3/5] Testing functional independence...")

    if len(non_trivial) == 0:
        if verbose:
            print("  No non-trivial integrals to test.")
            print()

        independent = []
        structure_analysis = {}

    else:
        structure_analysis = analyze_integral_structure(
            non_trivial,
            test_states,
            tolerance=independence_tolerance,
            verbose=verbose
        )

        # Extract independent subset
        independent_indices = structure_analysis['independence']['independent_subset']
        independent = [non_trivial[i] for i in independent_indices]

        if verbose:
            print()

    # =========================================================================
    # Step 4: Verify conservation on trajectories
    # =========================================================================

    if verbose:
        print("[4/5] Verifying conservation on trajectories...")

    if len(independent) == 0:
        if verbose:
            print("  No independent integrals to verify.")
            print()

        conserved = []
        verification_report = {}

    else:
        conserved, verification_report = verify_integrals_batch(
            independent,
            test_trajectories,
            hamiltonian,
            time_span=time_span,
            tolerance=conservation_tolerance,
            success_threshold=success_threshold,
            verbose=verbose
        )

        if verbose:
            print()

    # =========================================================================
    # Step 5: Rank by quality metrics
    # =========================================================================

    if verbose:
        print("[5/5] Ranking candidates...")

    if len(conserved) > 0:
        ranked = rank_candidates(
            conserved,
            test_states,
            verbose=verbose
        )
    else:
        ranked = []

    if verbose:
        print()

    # =========================================================================
    # Compile statistics
    # =========================================================================

    statistics = {
        'raw_count': len(raw_candidates),
        'non_trivial_count': len(non_trivial),
        'independent_count': len(independent),
        'conserved_count': len(conserved),
        'rejection_reasons': rejections,
        'structure_analysis': structure_analysis,
        'verification_report': verification_report
    }

    if verbose:
        print("="*70)
        print("PIPELINE SUMMARY")
        print("="*70)
        print(f"  Raw candidates: {statistics['raw_count']}")
        print(f"  Non-trivial: {statistics['non_trivial_count']}")
        print(f"  Independent: {statistics['independent_count']}")
        print(f"  Conserved: {statistics['conserved_count']}")
        print("="*70)
        print()

    return IntegralDiscoveryResult(
        raw_candidates=raw_candidates,
        non_trivial=non_trivial,
        independent=independent,
        conserved=conserved,
        ranked=ranked,
        statistics=statistics,
        manifold_type=manifold_type,
        field_type=field_type
    )


# =============================================================================
# Ranking and Export
# =============================================================================

def rank_candidates(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    verbose: bool = False
) -> List[Tuple[ConservedIntegral, Dict]]:
    """
    Rank candidates by quality metrics.

    Metrics:
    1. Conservation quality: Residual (lower is better)
    2. Simplicity: Placeholder (would need symbolic form)
    3. Generality: Variance across states (higher is better)

    Args:
        integrals: List of verified integrals
        test_states: Test states for evaluation
        verbose: Print rankings

    Returns:
        List of (integral, metrics_dict) sorted by composite score
    """
    ranked = []

    for integral in integrals:
        # Metric 1: Conservation quality (residual)
        conservation_score = 1.0 / (1.0 + integral.residual)

        # Metric 2: Simplicity (placeholder - would extract from symbolic form)
        simplicity_score = 0.5

        # Metric 3: Generality (variance across states)
        values = [integral(s.to_array()) for s in test_states]
        variance = np.var(values)
        generality_score = variance / (1.0 + variance)  # Normalize

        # Composite score
        composite = (
            0.5 * conservation_score +
            0.2 * simplicity_score +
            0.3 * generality_score
        )

        metrics = {
            'conservation_score': conservation_score,
            'simplicity_score': simplicity_score,
            'generality_score': generality_score,
            'composite_score': composite,
            'residual': integral.residual
        }

        ranked.append((integral, metrics))

    # Sort by composite score (descending)
    ranked.sort(key=lambda x: x[1]['composite_score'], reverse=True)

    if verbose:
        print("Ranking:")
        for idx, (integral, metrics) in enumerate(ranked):
            print(f"  {idx+1}. {integral.name}")
            print(f"      Composite: {metrics['composite_score']:.3f}")
            print(f"      Residual: {metrics['residual']:.2e}")

    return ranked


def export_results(
    result: IntegralDiscoveryResult,
    output_path: str,
    *,
    format: str = 'pickle'
) -> None:
    """
    Export discovery results.

    Formats:
    - 'pickle': Full Python objects
    - 'json': Metadata only (no callables)

    Args:
        result: IntegralDiscoveryResult to export
        output_path: Output file path
        format: Export format
    """
    if format == 'pickle':
        with open(output_path, 'wb') as f:
            pickle.dump(result, f)

    elif format == 'json':
        # Export metadata only
        metadata = {
            'manifold_type': result.manifold_type,
            'field_type': result.field_type,
            'statistics': {
                'raw_count': result.statistics['raw_count'],
                'non_trivial_count': result.statistics['non_trivial_count'],
                'independent_count': result.statistics['independent_count'],
                'conserved_count': result.statistics['conserved_count']
            },
            'conserved_integrals': [
                {
                    'name': I.name,
                    'source': I.source,
                    'residual': float(I.residual),
                    'manifold_type': I.manifold_type
                }
                for I in result.conserved
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    else:
        raise ValueError(f"Unknown format: {format}")


# =============================================================================
# Convenience Function
# =============================================================================

def discover_integrals_from_killing_solution(
    killing_solution: KillingSolution,
    metric_func: Callable,
    hamiltonian: Callable,
    masses: np.ndarray,
    **kwargs
) -> IntegralDiscoveryResult:
    """
    Convenience wrapper for the complete pipeline.

    This is the main entry point for Task 3.1.4.

    Example:
        >>> from pde import solve_killing_fields
        >>> from analysis import discover_integrals_from_killing_solution
        >>>
        >>> # Solve for Killing fields
        >>> killing_sol = solve_killing_fields(...)
        >>>
        >>> # Discover conserved integrals
        >>> result = discover_integrals_from_killing_solution(
        ...     killing_sol,
        ...     metric_func=my_metric,
        ...     hamiltonian=my_hamiltonian,
        ...     masses=np.array([1, 1, 1])
        ... )
        >>>
        >>> print(f"Found {len(result.conserved)} conserved integrals!")
    """
    return integral_discovery_pipeline(
        killing_solution,
        metric_func,
        hamiltonian,
        masses,
        **kwargs
    )
