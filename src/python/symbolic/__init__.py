"""
WP 3.3: Symbolic Regression and Consolidation

This package provides tools for converting numerical candidate integrals
(from WP3.1 geometric search and WP3.2 ML discovery) into analytical
symbolic expressions suitable for rigorous validation in WP4.

Main Components:
---------------
1. **basis_functions**: Physics-informed basis function libraries for regression
2. **geometric_invariants**: Coordinate-independent geometric quantities
3. **regression_pipeline**: SINDy and PySR symbolic regression interfaces
4. **simplification**: Expression simplification and optimization
5. **validation**: Conservation verification and testing
6. **candidate_ranking**: Consolidation and ranking of all candidates

Typical Workflow:
----------------
```python
from symbolic import (
    construct_hierarchical_basis,
    sindy_regression,
    simplify_candidate_integral,
    validate_candidate_integral,
    consolidate_and_rank,
    CandidateIntegral,
    generate_candidate_report
)

# 1. Build basis library
library = construct_hierarchical_basis(
    state_dim=8,
    max_polynomial_degree=2,
    masses=masses
)

# 2. Perform symbolic regression
result = sindy_regression(numerical_integral, sample_states, library)

# 3. Simplify expression
simplified = simplify_candidate_integral(result.expression_sympy, state_symbols)

# 4. Validate conservation
validation = validate_candidate_integral(
    simplified.simplified,
    numerical_integral,
    hamiltonian_func,
    sample_states,
    state_symbols
)

# 5. Create candidate
candidate = CandidateIntegral(
    name="Discovered_Integral",
    expression_symbolic=simplified.simplified,
    expression_numerical=numerical_integral,
    source=CandidateSource.SYMBOLIC_REGRESSION,
    conservation_error=validation.conservation_error,
    complexity=count_operations(simplified.simplified),
    is_independent=validation.is_independent,
    validation_result=validation
)

# 6. Consolidate and rank all candidates
ranked = consolidate_and_rank(all_candidates, sample_states)

# 7. Generate report
report = generate_candidate_report(ranked, top_n=10)
print(report)
```

Integration with Other WP3 Components:
-------------------------------------
- **From WP3.1**: Import Killing field integrals via
  `create_candidate_from_wp31_killing()`
- **From WP3.2**: Import ML predictions via
  `create_candidate_from_wp32_ml()`
- **To WP4**: Export top-ranked symbolic expressions for validation
"""

# Basis functions
from .basis_functions import (
    BasisFunction,
    BasisLibrary,
    CoordinateSystem,
    construct_polynomial_basis,
    construct_transcendental_basis,
    construct_conservation_basis,
    construct_hierarchical_basis,
    get_pysr_operators
)

# Geometric invariants
from .geometric_invariants import (
    GeometricQuantities,
    compute_all_geometric_invariants,
    compute_mutual_distances,
    compute_radial_velocities,
    compute_angular_momentum_vectors,
    compute_moment_of_inertia,
    compute_shape_coordinates,
    create_geometric_basis_functions
)

# Regression pipeline
from .regression_pipeline import (
    RegressionResult,
    sindy_regression,
    pysr_regression,
    hierarchical_regression,
    compare_methods,
    PYSINDY_AVAILABLE,
    PYSR_AVAILABLE
)

# Simplification
from .simplification import (
    SimplificationResult,
    count_operations,
    round_coefficients,
    simplify_expression,
    extract_common_factors,
    substitute_conserved_quantities,
    minimize_expression_tree,
    format_for_publication,
    verify_numerical_equivalence,
    simplify_candidate_integral
)

# Validation
from .validation import (
    ValidationResult,
    lambdify_expression,
    validate_symbolic_numerical_agreement,
    test_conservation_on_trajectory,
    test_conservation_ensemble,
    compute_poisson_bracket_symbolic,
    check_functional_independence,
    validate_candidate_integral
)

# Candidate ranking
from .candidate_ranking import (
    CandidateSource,
    CandidateIntegral,
    compute_candidate_score,
    detect_duplicate_candidates,
    filter_trivial_candidates,
    consolidate_and_rank,
    create_candidate_from_wp31_killing,
    create_candidate_from_wp32_ml,
    generate_candidate_report
)

# Spinor basis (AMENDED WP3.3)
from .spinor_basis import (
    position_to_spinor,
    spinor_to_position,
    compute_spinor_norm,
    quaternion_product,
    construct_spinor_basis,
    test_ks_transformation
)

# Enhanced validation (AMENDED WP3.3)
from .enhanced_validation import (
    MultiScaleResult,
    multi_scale_conservation_test,
    detect_quasi_periodic_structure,
    long_time_stability_test
)

# Interpretability and function classification (AMENDED WP3.3)
from .interpretability import (
    FunctionType,
    InterpretabilityScore,
    classify_function_type,
    compute_interpretability_score,
    detect_physical_symmetries,
    generate_physical_hints
)

# Elliptic basis (AMENDED WP3.3 Phase 2)
from .elliptic_basis import (
    jacobi_sn,
    jacobi_cn,
    jacobi_dn,
    complete_elliptic_K,
    complete_elliptic_E,
    estimate_elliptic_parameter,
    construct_elliptic_basis,
    test_jacobi_identities
)

# Theta basis (AMENDED WP3.3 Phase 4)
from .theta_basis import (
    jacobi_theta1,
    jacobi_theta2,
    jacobi_theta3,
    jacobi_theta4,
    estimate_modular_parameter,
    construct_theta_basis,
    test_theta_identities
)

# Specialized search methods (AMENDED WP3.3)
from .elliptic_search import (
    EllipticSearchResult,
    detect_elliptic_signature,
    elliptic_pattern_match,
    elliptic_sindy_hybrid,
    search_elliptic_integral
)

from .spinor_search import (
    SpinorSearchResult,
    detect_regularization_benefit,
    spinor_pattern_recognition,
    spinor_sindy_search,
    search_spinor_integral
)

# Multi-stage pipeline (AMENDED WP3.3)
from .multi_stage_pipeline import (
    SearchStage,
    MultiStageResult,
    analyze_trajectory_characteristics,
    run_multi_stage_pipeline
)

__all__ = [
    # Basis functions
    'BasisFunction',
    'BasisLibrary',
    'CoordinateSystem',
    'construct_polynomial_basis',
    'construct_transcendental_basis',
    'construct_conservation_basis',
    'construct_hierarchical_basis',
    'get_pysr_operators',

    # Geometric invariants
    'GeometricQuantities',
    'compute_all_geometric_invariants',
    'compute_mutual_distances',
    'compute_radial_velocities',
    'compute_angular_momentum_vectors',
    'compute_moment_of_inertia',
    'compute_shape_coordinates',
    'create_geometric_basis_functions',

    # Regression
    'RegressionResult',
    'sindy_regression',
    'pysr_regression',
    'hierarchical_regression',
    'compare_methods',
    'PYSINDY_AVAILABLE',
    'PYSR_AVAILABLE',

    # Simplification
    'SimplificationResult',
    'count_operations',
    'round_coefficients',
    'simplify_expression',
    'extract_common_factors',
    'substitute_conserved_quantities',
    'minimize_expression_tree',
    'format_for_publication',
    'verify_numerical_equivalence',
    'simplify_candidate_integral',

    # Validation
    'ValidationResult',
    'lambdify_expression',
    'validate_symbolic_numerical_agreement',
    'test_conservation_on_trajectory',
    'test_conservation_ensemble',
    'compute_poisson_bracket_symbolic',
    'check_functional_independence',
    'validate_candidate_integral',

    # Ranking
    'CandidateSource',
    'CandidateIntegral',
    'compute_candidate_score',
    'detect_duplicate_candidates',
    'filter_trivial_candidates',
    'consolidate_and_rank',
    'create_candidate_from_wp31_killing',
    'create_candidate_from_wp32_ml',
    'generate_candidate_report',

    # Spinor basis (AMENDED WP3.3)
    'position_to_spinor',
    'spinor_to_position',
    'compute_spinor_norm',
    'quaternion_product',
    'construct_spinor_basis',
    'test_ks_transformation',

    # Enhanced validation (AMENDED WP3.3)
    'MultiScaleResult',
    'multi_scale_conservation_test',
    'detect_quasi_periodic_structure',
    'long_time_stability_test',

    # Interpretability (AMENDED WP3.3)
    'FunctionType',
    'InterpretabilityScore',
    'classify_function_type',
    'compute_interpretability_score',
    'detect_physical_symmetries',
    'generate_physical_hints',

    # Elliptic basis (AMENDED WP3.3 Phase 2)
    'jacobi_sn',
    'jacobi_cn',
    'jacobi_dn',
    'complete_elliptic_K',
    'complete_elliptic_E',
    'estimate_elliptic_parameter',
    'construct_elliptic_basis',
    'test_jacobi_identities',

    # Theta basis (AMENDED WP3.3 Phase 4)
    'jacobi_theta1',
    'jacobi_theta2',
    'jacobi_theta3',
    'jacobi_theta4',
    'estimate_modular_parameter',
    'construct_theta_basis',
    'test_theta_identities',

    # Specialized search (AMENDED WP3.3)
    'EllipticSearchResult',
    'detect_elliptic_signature',
    'elliptic_pattern_match',
    'elliptic_sindy_hybrid',
    'search_elliptic_integral',
    'SpinorSearchResult',
    'detect_regularization_benefit',
    'spinor_pattern_recognition',
    'spinor_sindy_search',
    'search_spinor_integral',

    # Multi-stage pipeline (AMENDED WP3.3)
    'SearchStage',
    'MultiStageResult',
    'analyze_trajectory_characteristics',
    'run_multi_stage_pipeline',
]

__version__ = '1.0.0'
__author__ = 'WP3 Implementation Team'
