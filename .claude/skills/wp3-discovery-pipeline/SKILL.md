---
name: wp3-discovery-pipeline
description: >
  Multi-stage coordinated pipeline for discovering conserved quantities in the three-body
  problem. Use when: (1) running comprehensive searches across all basis types,
  (2) coordinating spinor, elliptic, theta, and polynomial searches, (3) ranking candidates
  by confidence and interpretability, (4) filtering trivial integrals (E, L, C),
  (5) testing functional independence via Jacobian rank, (6) deduplicating candidates,
  (7) running end-to-end invariant discovery workflows, (8) validating against known
  integrable cases, (9) preparing candidates for WP4 validation, or (10) using Hamiltonian
  Neural Networks for ML-based discovery. Triggers on requests involving multi-stage
  search, candidate ranking, triviality checking, independence testing, functional
  independence, Jacobian rank, pipeline coordination, end-to-end discovery, HNN,
  Hamiltonian neural network, or comprehensive invariant search.
---

# WP3 Discovery Pipeline

Multi-stage coordinated pipeline for comprehensive invariant discovery.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MULTI-STAGE DISCOVERY PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   WP1 Trajectory Data          WP2 Lifted Spaces                            │
│         │                            │                                      │
│         └──────────┬─────────────────┘                                      │
│                    ▼                                                        │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 1: Trajectory Analysis                                        │   │
│   │ • Close encounters? → Spinor priority                              │   │
│   │ • Quasi-periodic? → Elliptic priority                              │   │
│   │ • Integrable signature? → Theta priority                           │   │
│   └─────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│   ┌─────────────────────────────▼──────────────────────────────────────┐   │
│   │ STAGE 2: Parallel Search (4 Tracks)                                │   │
│   │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │
│   │ │ Spinor   │ │ Elliptic │ │  Theta   │ │Polynomial│               │   │
│   │ │ ~80 funcs│ │ ~60 funcs│ │ ~40 funcs│ │ ~50 funcs│               │   │
│   │ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘               │   │
│   │      │            │            │            │                      │   │
│   │      └────────────┴────────────┴────────────┘                      │   │
│   │                        │                                            │   │
│   └────────────────────────┼────────────────────────────────────────────┘   │
│                            ▼                                                │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 3: Candidate Collection                                       │   │
│   │ • Merge results from all tracks                                    │   │
│   │ • Deduplicate equivalent expressions                               │   │
│   │ • Conservation validation (multi-scale)                            │   │
│   └─────────────────────────┬──────────────────────────────────────────┘   │
│                             ▼                                               │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 4: Triviality Filtering                                       │   │
│   │ • Remove known integrals: E, L, C                                  │   │
│   │ • Remove constants                                                  │   │
│   │ • Remove linear combinations of known integrals                    │   │
│   └─────────────────────────┬──────────────────────────────────────────┘   │
│                             ▼                                               │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 5: Independence Testing                                       │   │
│   │ • Jacobian rank test at 10⁴ sample points                          │   │
│   │ • rank([∇E, ∇L, ∇C, ∇Ĩ]) must increase by 1                       │   │
│   │ • Pass rate > 99%                                                   │   │
│   └─────────────────────────┬──────────────────────────────────────────┘   │
│                             ▼                                               │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 6: Ranking                                                    │   │
│   │ Score = w₁×confidence + w₂×interpretability + w₃×conservation     │   │
│   └─────────────────────────┬──────────────────────────────────────────┘   │
│                             ▼                                               │
│                    Ranked Candidate List → WP4                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Create coordinated pipeline
search = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=5,
    enable_ranking=True,
    enable_triviality_check=True,
    enable_independence_check=True
)

# Run comprehensive search
results = search.run(
    times=times,
    states=states,
    mu=mu,
    energy=E,
    angular_momentum=L
)

# Top candidates
print(f"Found {len(results.all_candidates)} total")
print(f"After filtering: {len(results.top_candidates)} candidates\n")

for i, cand in enumerate(results.top_candidates[:3]):
    print(f"Rank {i+1}: {cand.expression}")
    print(f"  Method: {cand.method}")
    print(f"  Confidence: {cand.confidence:.3f}")
    print(f"  Conservation: {cand.conservation_error:.2e}")
```

---

## Multi-Stage Search

**Location**: `src/python/symbolic/multi_stage_pipeline.py`

### Stage Configuration

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Full 4-stage search (comprehensive)
search = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=5
)

# Quick 2-stage search (fast)
quick_search = MultiStageInvariantSearch(
    stages=['polynomial', 'spinor'],
    max_candidates_per_stage=3
)

# Single specialized stage
spinor_only = MultiStageInvariantSearch(
    stages=['spinor'],
    max_candidates_per_stage=10
)

# Automatic stage selection based on trajectory
auto_search = MultiStageInvariantSearch(
    stages='auto',  # Auto-detect optimal order
    max_candidates_per_stage=5
)
```

### Stage Priority Logic

Stages execute based on trajectory characteristics:

```python
def determine_stage_order(times, states):
    """Determine optimal stage order based on trajectory."""
    from src.python.symbolic.spinor_search import detect_regularization_benefit
    from src.python.symbolic.elliptic_search import detect_elliptic_signature
    
    priority = []
    
    # Priority 1: Spinor if close encounters
    if detect_regularization_benefit(times, states):
        priority.append('spinor')
    
    # Priority 2: Elliptic if quasi-periodic
    qp = detect_elliptic_signature(times, states)
    if qp.is_quasi_periodic:
        priority.append('elliptic')
    
    # Priority 3: Theta if integrable signature
    # (Check for very regular motion, bounded, discrete spectrum)
    
    # Always include polynomial as fallback
    priority.append('polynomial')
    
    return priority
```

### Running Search

```python
results = search.run(
    times=times,
    states=states,
    mu=mu,
    energy=E,                    # For triviality filtering
    angular_momentum=L,          # For triviality filtering
    jacobi_constant=C            # For CR3BP triviality check
)

# Access results by stage
print("Results per stage:")
for stage, candidates in results.by_stage.items():
    print(f"  {stage}: {len(candidates)} candidates")

# Stage-specific parameters
print(f"\nStage parameters:")
print(f"  Elliptic m: {results.params.get('elliptic_m', 'N/A')}")
print(f"  Theta q: {results.params.get('theta_q', 'N/A')}")
```

---

## Candidate Ranking

**Location**: `src/python/symbolic/candidate_ranking.py`

### Ranking Formula

```
Score = w₁ × confidence + w₂ × interpretability + w₃ × (1 - log₁₀(conservation_error)/10)
```

Default weights: w₁=0.4, w₂=0.3, w₃=0.3

### Usage

```python
from src.python.symbolic.candidate_ranking import CandidateRanker

# Default ranking
ranker = CandidateRanker(
    confidence_weight=0.4,
    interpretability_weight=0.3,
    conservation_weight=0.3
)

ranked = ranker.rank(results.all_candidates)

for i, cand in enumerate(ranked[:5]):
    print(f"{i+1}. {cand.expression}")
    print(f"   Score: {cand.score:.3f}")
    print(f"   Breakdown: conf={cand.confidence:.2f}, "
          f"interp={cand.interpretability:.2f}, "
          f"cons={cand.conservation_score:.2f}")
```

### Custom Ranking Strategies

```python
# Prioritize interpretability (for physics insight)
interpretable_ranker = CandidateRanker(
    confidence_weight=0.2,
    interpretability_weight=0.6,
    conservation_weight=0.2
)

# Prioritize conservation (for numerical validation)
strict_ranker = CandidateRanker(
    confidence_weight=0.2,
    interpretability_weight=0.2,
    conservation_weight=0.6
)

# Equal weighting
balanced_ranker = CandidateRanker(
    confidence_weight=0.33,
    interpretability_weight=0.34,
    conservation_weight=0.33
)
```

---

## Triviality Filtering

**Location**: `src/python/symbolic/candidate_ranking.py`

### What is Trivial?

A candidate is **trivial** if it is:
1. **Constant**: variance < tolerance
2. **Known integral**: high correlation with E, L, or C
3. **Linear combination**: expressible as αE + βL + γC + δ

### Usage

```python
from src.python.symbolic.candidate_ranking import TrivialityChecker

checker = TrivialityChecker(
    known_integrals={
        'energy': E_values,
        'angular_momentum': L_values,
        'jacobi_constant': C_values  # Optional
    },
    constant_tolerance=1e-12,
    correlation_threshold=0.99
)

# Check single candidate
is_trivial, reason = checker.check(candidate, states)
if is_trivial:
    print(f"Trivial: {reason}")

# Filter list
non_trivial = checker.filter(candidates, states)
print(f"Removed {len(candidates) - len(non_trivial)} trivial candidates")
```

### Detailed Triviality Analysis

```python
result = checker.check_detailed(candidate, states)

print(f"Is constant: {result.is_constant}")
print(f"Variance: {result.variance:.2e}")
print(f"Correlation with E: {result.energy_correlation:.3f}")
print(f"Correlation with L: {result.L_correlation:.3f}")
print(f"Correlation with C: {result.C_correlation:.3f}")
print(f"Is linear combination: {result.is_linear_combination}")
if result.is_linear_combination:
    print(f"  Coefficients: α={result.alpha:.4f}, β={result.beta:.4f}, "
          f"γ={result.gamma:.4f}, δ={result.delta:.4f}")
```

**Reference**: See `references/triviality-independence.md` for theory.

---

## Independence Testing

**Location**: `src/python/ml/independence_test.py`

### Theory

Functions {I₁, I₂, ..., Iₙ} are **functionally independent** if their gradients are linearly independent almost everywhere:

```
rank([∇I₁, ∇I₂, ..., ∇Iₙ]) = n
```

For a new candidate Ĩ to be independent of known integrals {E, L, C}:
```
rank([∇E, ∇L, ∇C, ∇Ĩ]) = 4  (one more than before)
```

### Usage

```python
from src.python.ml.independence_test import IndependenceTest

test = IndependenceTest(tolerance=1e-8)

# Single candidate test
is_independent = test.is_independent(
    candidate_func=candidate.eval_func,
    known_funcs=[energy_func, L_func, C_func],
    states=states
)

if is_independent:
    print("✓ Candidate is functionally independent!")
else:
    print("✗ Candidate is dependent on known integrals")

# Find maximal independent set from multiple candidates
independent_set = test.find_independent_set(candidates, states)
print(f"Found {len(independent_set)} independent integrals")
```

### Jacobian Rank Test

```python
from src.python.ml.independence_test import compute_jacobian_rank

# Compute Jacobian at sample points
rank_results = compute_jacobian_rank(
    functions=[E_func, L_func, C_func, candidate_func],
    states=states,
    tolerance=1e-8
)

print(f"Mean Jacobian rank: {rank_results.mean_rank:.2f}")
print(f"Expected rank: {rank_results.expected_rank}")
print(f"Pass rate: {rank_results.pass_rate:.1%}")

if rank_results.pass_rate > 0.99:
    print("✓ Candidate adds new independent integral")
```

**Reference**: See `references/triviality-independence.md` for implementation.

---

## Complete Pipeline Workflow

```python
def discover_integrals_complete(times, states, mu, E, L, C=None):
    """
    Complete discovery pipeline with all stages.
    """
    from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch
    from src.python.symbolic.candidate_ranking import TrivialityChecker, CandidateRanker
    from src.python.ml.independence_test import IndependenceTest
    
    print("=== STAGE 1: Multi-Stage Search ===")
    search = MultiStageInvariantSearch(
        stages=['spinor', 'elliptic', 'polynomial'],
        max_candidates_per_stage=10
    )
    results = search.run(times, states, mu=mu)
    print(f"Found {len(results.all_candidates)} raw candidates")
    
    print("\n=== STAGE 2: Triviality Filtering ===")
    checker = TrivialityChecker(
        known_integrals={'energy': E, 'angular_momentum': L}
    )
    if C is not None:
        checker.known_integrals['jacobi_constant'] = C
    
    non_trivial = checker.filter(results.all_candidates, states)
    print(f"{len(non_trivial)} non-trivial candidates remain")
    
    print("\n=== STAGE 3: Independence Testing ===")
    test = IndependenceTest()
    independent = test.find_independent_set(non_trivial, states)
    print(f"{len(independent)} functionally independent candidates")
    
    print("\n=== STAGE 4: Ranking ===")
    ranker = CandidateRanker()
    ranked = ranker.rank(independent)
    
    print("\n=== FINAL RESULTS ===")
    for i, cand in enumerate(ranked[:5]):
        print(f"\n{i+1}. {cand.expression}")
        print(f"   Method: {cand.method}")
        print(f"   Score: {cand.score:.3f}")
        print(f"   Conservation error: {cand.conservation_error:.2e}")
        print(f"   Interpretability: {cand.interpretability:.2f}")
    
    return ranked
```

---

## Hamiltonian Neural Networks

**Location**: `src/python/ml/conservation_hnn.py`

### Theory

Hamiltonian Neural Networks (HNNs) learn dynamics while respecting symplectic structure:
- Network learns H̃(q, p) instead of (q̇, ṗ) directly
- Derivatives computed via autograd: q̇ = ∂H̃/∂p, ṗ = -∂H̃/∂q
- Auxiliary head can predict candidate integral Ĩ

### Architecture

```python
from src.python.ml.hnn_architecture import HamiltonianNN

# Create HNN with integral discovery head
hnn = HamiltonianNN(
    input_dim=12,           # Phase space dimension
    hidden_dims=[128, 128, 64],
    activation='softplus',
    learn_integral=True     # Add auxiliary head for Ĩ
)
```

### Training

```python
from src.python.ml.hnn_training import HNNTrainer

trainer = HNNTrainer(
    model=hnn,
    learning_rate=1e-3,
    conservation_weight=1.0,  # Weight on {Ĩ, H̃} = 0
    epochs=1000
)

# Train on trajectory data
history = trainer.fit(times, states)

# Extract learned integral
learned_integral = hnn.evaluate_integral(states)
```

### Integration with Pipeline

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Add HNN as a search stage
search = MultiStageInvariantSearch(
    stages=['hnn', 'spinor', 'elliptic', 'polynomial'],
    hnn_epochs=500,
    max_candidates_per_stage=5
)

results = search.run(times, states, mu=mu)

# HNN candidates appear in results.by_stage['hnn']
```

**Reference**: See `references/hnn-approach.md` for theory and implementation.

---

## Known Case Validation

Test pipeline on cases with known answers:

```python
def validate_on_known_cases():
    """Test pipeline recovers known integrals."""
    
    # Test 1: CR3BP should find Jacobi constant
    print("Test 1: CR3BP Jacobi Constant")
    times, states = generate_cr3bp_trajectory(mu=0.012)
    
    search = MultiStageInvariantSearch(stages=['polynomial'])
    results = search.run(times, states, mu=0.012)
    
    found_jacobi = any(
        'omega' in c.expression.lower() or 
        '2*omega' in c.expression.lower() or
        'jacobi' in c.expression.lower()
        for c in results.top_candidates
    )
    print(f"  Found Jacobi constant: {found_jacobi}")
    
    # Test 2: Lagrange points (L4/L5)
    print("\nTest 2: Lagrange L4 Point")
    times, states = generate_lagrange_trajectory('L4', mu=0.012)
    
    search = MultiStageInvariantSearch(stages=['polynomial', 'elliptic'])
    results = search.run(times, states, mu=0.012)
    
    print(f"  Found {len(results.top_candidates)} candidates")
    
    # Test 3: Figure-8 orbit (has known periodic structure)
    print("\nTest 3: Figure-8 Orbit")
    times, states = generate_figure8_trajectory()
    
    search = MultiStageInvariantSearch(stages=['polynomial', 'theta'])
    results = search.run(times, states, mu=None)
    
    print(f"  Found {len(results.top_candidates)} candidates")
```

---

## Pipeline Configuration

### Performance Tuning

```python
# Fast exploratory search
fast_config = MultiStageInvariantSearch(
    stages=['polynomial'],
    max_candidates_per_stage=3,
    sindy_threshold=0.2,
    enable_triviality_check=True,
    enable_independence_check=False  # Skip for speed
)

# Thorough production search
thorough_config = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=20,
    sindy_threshold=0.05,
    pysr_iterations=100,
    enable_hybrid=True,
    enable_triviality_check=True,
    enable_independence_check=True
)
```

### Parallel Execution

```python
# Run stages in parallel (if resources allow)
parallel_config = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'polynomial'],
    parallel=True,
    n_jobs=4
)
```

---

## Downstream: Preparing for WP4

```python
def prepare_for_wp4(candidates, times, states, mu):
    """
    Prepare validated candidates for WP4 Morales-Ramis test.
    """
    wp4_candidates = []
    
    for cand in candidates:
        wp4_cand = {
            'expression': cand.expression,
            'eval_func': cand.eval_func,
            'gradient_func': cand.gradient_func,  # For Poisson brackets
            'conservation_error': cand.conservation_error,
            'interpretability': cand.interpretability,
            'method': cand.method,
            
            # Additional data for WP4
            'sample_states': states[::10],  # Subsampled states
            'mu': mu,
            'validation_passed': True
        }
        wp4_candidates.append(wp4_cand)
    
    return wp4_candidates
```

---

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No candidates found | High thresholds | Lower SINDy threshold, increase max_candidates |
| All candidates trivial | Only finding E, L, C | Check triviality filtering parameters |
| Independence test fails | Dependent on known integrals | Expected if no new integrals exist |
| Too many candidates | Low thresholds | Increase thresholds, enable stricter filtering |
| Slow search | PySR enabled | Reduce pysr_iterations, use SINDy-only mode |

---

## Tests

```bash
# All pipeline tests
pytest tests/wp3/test_multi_stage_pipeline.py -v
pytest tests/wp3/test_triviality_and_independence.py -v
pytest tests/wp3/test_end_to_end_known_cases.py -v

# Specific tests
pytest tests/wp3/test_multi_stage_pipeline.py::test_stage_ordering -v
pytest tests/wp3/test_triviality_and_independence.py::test_jacobian_rank -v
```

---

## References

- `references/triviality-independence.md` - Filtering theory
- `references/candidate-ranking.md` - Ranking methodology
- `references/hnn-approach.md` - Hamiltonian neural networks
- `src/python/symbolic/multi_stage_pipeline.py` - Pipeline implementation
- `src/python/symbolic/candidate_ranking.py` - Ranking/filtering
- `src/python/ml/independence_test.py` - Independence testing
- `src/python/ml/conservation_hnn.py` - HNN implementation
