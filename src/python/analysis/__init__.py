"""
Analysis module for conserved quantity discovery and validation (WP 3.1, Task 3.1.4).

This module converts geometric objects (Killing fields/tensors) into conserved
quantities and rigorously filters them to identify genuinely new integrals:

- integral_from_killing.py: Killing fields → conserved quantities
- triviality_filter.py: Remove known integrals (E, L, coordinates)
- independence_test.py: Functional independence via Jacobian rank
- conservation_verification.py: Numerical time-evolution tests
- integral_pipeline.py: Complete end-to-end workflow

Task: WP 3.1, Task 3.1.4
"""

# Part A: Integral Conversion
from .integral_from_killing import (
    ConservedIntegral,
    State,
    killing_vector_to_integral,
    killing_tensor_to_integral,
    convert_killing_fields_batch,
)

# Part B: Triviality Filtering
from .triviality_filter import (
    KnownIntegrals,
    is_trivial_coordinate,
    is_trivial_known,
    is_constant_on_shell,
    filter_trivial_integrals,
    generate_test_states,
)

# Part C: Independence Testing
from .independence_test import (
    test_functional_independence,
    compute_poisson_bracket,
    test_involution,
    analyze_integral_structure,
)

# Part D: Conservation Verification
from .conservation_verification import (
    verify_conservation_along_trajectory,
    verify_conservation_ensemble,
    verify_integrals_batch,
    make_harmonic_hamiltonian,
    make_kepler_hamiltonian,
)

# Part F: Complete Pipeline
from .integral_pipeline import (
    IntegralDiscoveryResult,
    integral_discovery_pipeline,
    discover_integrals_from_killing_solution,
    rank_candidates,
    export_results,
)

__all__ = [
    # Core data structures
    "ConservedIntegral",
    "State",
    "IntegralDiscoveryResult",
    # Integral conversion
    "killing_vector_to_integral",
    "killing_tensor_to_integral",
    "convert_killing_fields_batch",
    # Triviality filtering
    "KnownIntegrals",
    "is_trivial_coordinate",
    "is_trivial_known",
    "is_constant_on_shell",
    "filter_trivial_integrals",
    "generate_test_states",
    # Independence testing
    "test_functional_independence",
    "compute_poisson_bracket",
    "test_involution",
    "analyze_integral_structure",
    # Conservation verification
    "verify_conservation_along_trajectory",
    "verify_conservation_ensemble",
    "verify_integrals_batch",
    "make_harmonic_hamiltonian",
    "make_kepler_hamiltonian",
    # Complete pipeline
    "integral_discovery_pipeline",
    "discover_integrals_from_killing_solution",
    "rank_candidates",
    "export_results",
]
