# Candidate Ranking Methodology

Scoring and ranking discovered candidate integrals for prioritization.

## Table of Contents

1. [Overview](#overview)
2. [Scoring Components](#scoring-components)
3. [Weight Selection](#weight-selection)
4. [Ranking Algorithm](#ranking-algorithm)
5. [Implementation](#implementation)
6. [Calibration](#calibration)

---

## Overview

### The Ranking Problem

After filtering, we typically have multiple candidate integrals. We need to:
1. **Score** each candidate on multiple criteria
2. **Rank** candidates for prioritized WP4 validation
3. **Select** top candidates within computational budget

### Multi-Criteria Decision

No single metric suffices. We balance:
- **Conservation quality**: How well is dI/dt = 0 satisfied?
- **Interpretability**: Is the expression physically meaningful?
- **Confidence**: How robust is the discovery?

---

## Scoring Components

### Component 1: Conservation Score

Measures how well the candidate is conserved along trajectories.

**Definition**:
```
conservation_score = 1 - log₁₀(conservation_error) / 10

where conservation_error = max|I(t) - I(0)| / |I(0)|
```

**Range**: [0, 1] where 1 = perfect conservation

**Implementation**:
```python
def conservation_score(I_values):
    """
    Score conservation quality.

    Perfect conservation (error = 0) → score = 1
    Poor conservation (error = 1) → score = 0
    """
    mean_I = np.mean(I_values)
    max_deviation = np.max(np.abs(I_values - mean_I))
    relative_error = max_deviation / (np.abs(mean_I) + 1e-15)

    # Clamp error to [1e-15, 1]
    error_clamped = np.clip(relative_error, 1e-15, 1.0)

    # Log scale: error=10^-10 → score≈0.67, error=10^-15 → score=1
    score = 1 - np.log10(error_clamped) / 15

    return np.clip(score, 0, 1)
```

### Component 2: Interpretability Score

Measures how physically meaningful and understandable the expression is.

**Factors**:
1. Function type (polynomial > elliptic > unknown)
2. Expression complexity (fewer terms better)
3. Known pattern match (recognizable forms better)

**Implementation**:
```python
# Base scores by function type
TYPE_SCORES = {
    'polynomial': 1.0,
    'rational': 0.9,
    'radical': 0.85,
    'trigonometric': 0.8,
    'spinor': 0.8,
    'elliptic': 0.7,
    'theta': 0.6,
    'exponential': 0.75,
    'mixed': 0.4,
    'unknown': 0.2,
}

# Known pattern bonuses
PATTERN_BONUSES = {
    'angular_momentum': 0.1,
    'energy_like': 0.1,
    'jacobi_constant': 0.1,
    'spinor_norm': 0.05,
    'bilinear': 0.05,
}

def interpretability_score(expression_str):
    """
    Score expression interpretability.
    """
    # Base score from function type
    func_type = classify_function(expression_str)
    base_score = TYPE_SCORES.get(func_type, 0.2)

    # Complexity penalty
    n_terms = expression_str.count('+') + expression_str.count('-') + 1
    n_operations = len(re.findall(r'[\+\-\*\/\^]', expression_str))
    complexity_penalty = min(0.3, 0.02 * n_terms + 0.01 * n_operations)

    # Nesting penalty
    max_depth = max_parenthesis_depth(expression_str)
    nesting_penalty = min(0.2, 0.03 * max_depth)

    # Pattern bonus
    bonus = 0
    for pattern, b in PATTERN_BONUSES.items():
        if pattern_matches(expression_str, pattern):
            bonus += b

    score = base_score - complexity_penalty - nesting_penalty + bonus
    return np.clip(score, 0.1, 1.0)

def max_parenthesis_depth(s):
    """Compute maximum nesting depth of parentheses."""
    max_depth = 0
    current_depth = 0
    for c in s:
        if c == '(':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif c == ')':
            current_depth -= 1
    return max_depth
```

### Component 3: Confidence Score

Measures robustness and reliability of the discovery.

**Factors**:
1. Consistency across timescales
2. Regression fit quality (R² or residual)
3. Sparsity of representation
4. Cross-validation performance

**Implementation**:
```python
def confidence_score(candidate, validation_results):
    """
    Score discovery confidence.
    """
    scores = []

    # Multi-scale consistency
    if 'multi_scale' in validation_results:
        scale_errors = list(validation_results['multi_scale'].values())
        consistency = 1 - np.std(scale_errors) / (np.mean(scale_errors) + 1e-15)
        scores.append(('consistency', np.clip(consistency, 0, 1)))

    # Regression quality
    if hasattr(candidate, 'r_squared'):
        scores.append(('r_squared', candidate.r_squared))

    # Sparsity (for SINDy results)
    if hasattr(candidate, 'n_terms') and hasattr(candidate, 'n_basis'):
        sparsity = 1 - candidate.n_terms / candidate.n_basis
        scores.append(('sparsity', sparsity))

    # Cross-validation (if available)
    if hasattr(candidate, 'cv_score'):
        scores.append(('cv_score', candidate.cv_score))

    # Weighted average
    if scores:
        return np.mean([s[1] for s in scores])
    else:
        return 0.5  # Default moderate confidence
```

---

## Weight Selection

### Default Weights

```python
DEFAULT_WEIGHTS = {
    'conservation': 0.4,
    'interpretability': 0.3,
    'confidence': 0.3,
}
```

### Use-Case Specific Weights

**For numerical validation focus**:
```python
VALIDATION_WEIGHTS = {
    'conservation': 0.6,
    'interpretability': 0.2,
    'confidence': 0.2,
}
```

**For physical insight focus**:
```python
INSIGHT_WEIGHTS = {
    'conservation': 0.3,
    'interpretability': 0.5,
    'confidence': 0.2,
}
```

**For publication focus**:
```python
PUBLICATION_WEIGHTS = {
    'conservation': 0.35,
    'interpretability': 0.35,
    'confidence': 0.3,
}
```

### Adaptive Weight Selection

```python
def select_weights(goal='balanced', conservation_errors=None):
    """
    Adaptively select weights based on goal and data.
    """
    if goal == 'validation':
        return VALIDATION_WEIGHTS
    elif goal == 'insight':
        return INSIGHT_WEIGHTS
    elif goal == 'publication':
        return PUBLICATION_WEIGHTS
    elif goal == 'adaptive' and conservation_errors is not None:
        # If many candidates have good conservation, emphasize interpretability
        good_conservation = np.mean(conservation_errors < 1e-10)
        if good_conservation > 0.5:
            return {'conservation': 0.3, 'interpretability': 0.5, 'confidence': 0.2}
        else:
            return {'conservation': 0.5, 'interpretability': 0.3, 'confidence': 0.2}
    else:
        return DEFAULT_WEIGHTS
```

---

## Ranking Algorithm

### Composite Score

```
Score(c) = w_cons × S_cons(c) + w_interp × S_interp(c) + w_conf × S_conf(c)
```

### Tie-Breaking

When scores are equal (within tolerance), use secondary criteria:
1. Lower complexity preferred
2. Earlier discovery time preferred
3. Lower conservation error preferred

### Implementation

```python
def rank_candidates(candidates, weights=None, validation_results=None):
    """
    Rank candidates by composite score.

    Args:
        candidates: List of candidate objects
        weights: Dict with 'conservation', 'interpretability', 'confidence' weights
        validation_results: Dict mapping candidate → validation results

    Returns:
        List of candidates sorted by score (descending)
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    if validation_results is None:
        validation_results = {}

    scored_candidates = []

    for cand in candidates:
        # Compute component scores
        s_cons = conservation_score(cand.values)
        s_interp = interpretability_score(cand.expression)
        s_conf = confidence_score(cand, validation_results.get(cand.id, {}))

        # Composite score
        score = (weights['conservation'] * s_cons +
                 weights['interpretability'] * s_interp +
                 weights['confidence'] * s_conf)

        # Store scores
        cand.conservation_score = s_cons
        cand.interpretability_score = s_interp
        cand.confidence_score = s_conf
        cand.total_score = score

        scored_candidates.append(cand)

    # Sort by score (descending), then by complexity (ascending) for ties
    scored_candidates.sort(
        key=lambda c: (-c.total_score, getattr(c, 'complexity', 0))
    )

    # Assign ranks
    for i, cand in enumerate(scored_candidates):
        cand.rank = i + 1

    return scored_candidates
```

---

## Implementation

### Complete CandidateRanker Class

```python
class CandidateRanker:
    """
    Rank candidate integrals by multi-criteria scoring.
    """

    def __init__(self, conservation_weight=0.4, interpretability_weight=0.3,
                 confidence_weight=0.3):
        """
        Initialize ranker with weights.

        Weights should sum to 1.0.
        """
        total = conservation_weight + interpretability_weight + confidence_weight
        self.weights = {
            'conservation': conservation_weight / total,
            'interpretability': interpretability_weight / total,
            'confidence': confidence_weight / total,
        }

    def score(self, candidate, validation_results=None):
        """
        Compute composite score for a single candidate.
        """
        s_cons = conservation_score(candidate.values)
        s_interp = interpretability_score(candidate.expression)
        s_conf = confidence_score(candidate, validation_results or {})

        total = (self.weights['conservation'] * s_cons +
                 self.weights['interpretability'] * s_interp +
                 self.weights['confidence'] * s_conf)

        return {
            'total': total,
            'conservation': s_cons,
            'interpretability': s_interp,
            'confidence': s_conf,
        }

    def rank(self, candidates, validation_results=None):
        """
        Rank all candidates.

        Returns:
            List sorted by score (best first)
        """
        if validation_results is None:
            validation_results = {}

        # Score all candidates
        for cand in candidates:
            scores = self.score(cand, validation_results.get(id(cand), {}))
            cand.total_score = scores['total']
            cand.conservation_score = scores['conservation']
            cand.interpretability_score = scores['interpretability']
            cand.confidence_score = scores['confidence']

        # Sort
        ranked = sorted(candidates, key=lambda c: -c.total_score)

        # Assign ranks
        for i, cand in enumerate(ranked):
            cand.rank = i + 1

        return ranked

    def top_k(self, candidates, k=5, validation_results=None):
        """Return top k candidates."""
        ranked = self.rank(candidates, validation_results)
        return ranked[:k]

    def report(self, candidates):
        """Generate ranking report."""
        lines = ["=" * 60]
        lines.append("CANDIDATE RANKING REPORT")
        lines.append("=" * 60)
        lines.append(f"Weights: cons={self.weights['conservation']:.2f}, "
                     f"interp={self.weights['interpretability']:.2f}, "
                     f"conf={self.weights['confidence']:.2f}")
        lines.append("-" * 60)

        for cand in candidates[:10]:
            lines.append(f"\nRank {cand.rank}: {cand.expression[:50]}...")
            lines.append(f"  Total Score: {cand.total_score:.4f}")
            lines.append(f"  Conservation: {cand.conservation_score:.4f}")
            lines.append(f"  Interpretability: {cand.interpretability_score:.4f}")
            lines.append(f"  Confidence: {cand.confidence_score:.4f}")

        return "\n".join(lines)
```

---

## Calibration

### Score Distribution Analysis

```python
def analyze_score_distribution(candidates):
    """Analyze distribution of scores for calibration."""
    scores = {
        'conservation': [c.conservation_score for c in candidates],
        'interpretability': [c.interpretability_score for c in candidates],
        'confidence': [c.confidence_score for c in candidates],
        'total': [c.total_score for c in candidates],
    }

    print("Score Distribution Summary:")
    for name, values in scores.items():
        print(f"  {name}:")
        print(f"    Mean: {np.mean(values):.3f}")
        print(f"    Std:  {np.std(values):.3f}")
        print(f"    Min:  {np.min(values):.3f}")
        print(f"    Max:  {np.max(values):.3f}")
```

### Validation on Known Cases

```python
def calibrate_on_known_cases():
    """
    Calibrate scoring on cases with known correct answer.

    E.g., Jacobi constant should rank highly for CR3BP.
    """
    # Generate CR3BP trajectory
    times, states = generate_cr3bp_trajectory(mu=0.012)

    # Run discovery
    search = MultiStageInvariantSearch(stages=['polynomial'])
    results = search.run(times, states, mu=0.012)

    # Rank
    ranker = CandidateRanker()
    ranked = ranker.rank(results.candidates)

    # Check if Jacobi constant is in top 3
    jacobi_rank = None
    for cand in ranked:
        if is_jacobi_constant_like(cand.expression):
            jacobi_rank = cand.rank
            break

    print(f"Jacobi constant ranked: {jacobi_rank}")
    if jacobi_rank and jacobi_rank <= 3:
        print("✓ Calibration PASSED")
    else:
        print("✗ Calibration FAILED - adjust weights")
```

---

## References

- Saaty, T.L. (1980). *The Analytic Hierarchy Process*
- Hwang, C.L. & Yoon, K. (1981). *Multiple Attribute Decision Making*
