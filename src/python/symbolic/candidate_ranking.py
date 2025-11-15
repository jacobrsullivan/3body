"""
Candidate integral consolidation and ranking (Task 3.3.3).

This module consolidates candidate integrals from all WP3 tracks:
- WP 3.1: Geometric search (Killing fields)
- WP 3.2: ML discovery (HNN predictions)
- WP 3.3: Symbolic regression outputs

It ranks candidates by:
1. Conservation accuracy
2. Simplicity (expression complexity)
3. Functional independence
4. Novelty (not trivially related to known integrals)

The output is a ranked list of the most promising candidates for WP4 validation.

References:
- WP3-Complete-Overview.md
- Task 3.3.3 Implementation Plan
"""

import numpy as np
import sympy as sp
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import warnings

from .simplification import simplify_candidate_integral, count_operations
from .validation import validate_candidate_integral, ValidationResult


class CandidateSource(Enum):
    """Source of candidate integral."""
    KILLING_FIELD = "wp3.1_killing_field"
    KILLING_TENSOR = "wp3.1_killing_tensor"
    ML_HNN = "wp3.2_hnn"
    ML_SYMPNET = "wp3.2_sympnet"
    SYMBOLIC_REGRESSION = "wp3.3_symbolic"
    MANUAL = "manual"
    UNKNOWN = "unknown"


@dataclass
class CandidateIntegral:
    """
    A candidate conserved quantity.

    Attributes:
        name: Descriptive name
        expression_symbolic: SymPy expression
        expression_numerical: Numerical evaluation function
        source: Where the candidate came from
        conservation_error: Drift |ΔI/I| on test trajectories
        complexity: Expression complexity (operation count)
        is_independent: Functionally independent of known integrals
        validation_result: Full ValidationResult object
        simplification_factor: How much simpler than original (1.0 = no change)
        metadata: Additional information
        score: Overall quality score (lower is better)
    """
    name: str
    expression_symbolic: sp.Expr
    expression_numerical: Callable[[np.ndarray], float]
    source: CandidateSource
    conservation_error: float
    complexity: int
    is_independent: bool
    validation_result: Optional[ValidationResult] = None
    simplification_factor: float = 1.0
    metadata: Dict = field(default_factory=dict)
    score: float = np.inf

    def __lt__(self, other):
        """For sorting by score."""
        return self.score < other.score


def compute_candidate_score(
    candidate: CandidateIntegral,
    weights: Dict[str, float] = None
) -> float:
    """
    Compute overall quality score for candidate.

    Lower score = better candidate.

    Score components:
    - Conservation error (primary)
    - Complexity (secondary)
    - Independence bonus (if independent)
    - Novelty bonus (if from rare source)

    Args:
        candidate: CandidateIntegral object
        weights: Dictionary of weight parameters

    Returns:
        score: Overall quality score

    Default weights:
        - conservation: 1000.0 (most important)
        - complexity: 1.0
        - independence_bonus: -100.0 (negative = reward)
        - novelty_bonus: -50.0
    """
    if weights is None:
        weights = {
            'conservation': 1000.0,
            'complexity': 1.0,
            'independence_bonus': -100.0,
            'not_independent_penalty': 200.0,
            'novelty_bonus': -50.0,
            'simplification_bonus': -20.0
        }

    score = 0.0

    # Conservation error (log scale, higher error = worse score)
    if candidate.conservation_error > 0:
        score += weights['conservation'] * np.log10(candidate.conservation_error + 1e-16)
    else:
        score -= 1000  # Perfect conservation

    # Complexity
    score += weights['complexity'] * candidate.complexity

    # Independence
    if candidate.is_independent:
        score += weights['independence_bonus']
    else:
        score += weights['not_independent_penalty']

    # Novelty (bonus for non-standard sources)
    if candidate.source in [CandidateSource.KILLING_TENSOR, CandidateSource.ML_SYMPNET]:
        score += weights['novelty_bonus']

    # Simplification (reward for significant simplification)
    if candidate.simplification_factor < 0.8:
        score += weights['simplification_bonus'] * (1.0 - candidate.simplification_factor)

    return score


def detect_duplicate_candidates(
    candidates: List[CandidateIntegral],
    sample_states: np.ndarray,
    numerical_tolerance: float = 1e-8
) -> List[Tuple[int, int]]:
    """
    Detect duplicate candidates (same integral, different form).

    Two candidates are duplicates if their numerical values match
    on a large set of test states.

    Args:
        candidates: List of candidates
        sample_states: Test states (N, dim)
        numerical_tolerance: Tolerance for considering values equal

    Returns:
        duplicate_pairs: List of (i, j) index pairs that are duplicates
    """
    n_candidates = len(candidates)
    duplicate_pairs = []

    # Evaluate all candidates on sample states
    values = np.zeros((n_candidates, len(sample_states)))

    for i, cand in enumerate(candidates):
        for j, state in enumerate(sample_states):
            try:
                values[i, j] = cand.expression_numerical(state)
            except:
                values[i, j] = np.nan

    # Compare pairwise
    for i in range(n_candidates):
        for j in range(i + 1, n_candidates):
            # Check if values are nearly identical
            diff = np.abs(values[i] - values[j])
            valid_mask = ~(np.isnan(diff))

            if np.sum(valid_mask) > 0:
                mean_diff = np.mean(diff[valid_mask])
                if mean_diff < numerical_tolerance:
                    duplicate_pairs.append((i, j))

    return duplicate_pairs


def filter_trivial_candidates(
    candidates: List[CandidateIntegral],
    known_trivial: List[Callable[[np.ndarray], float]],
    sample_states: np.ndarray,
    tolerance: float = 1e-8
) -> List[CandidateIntegral]:
    """
    Filter out trivial candidates (constants, known integrals).

    Args:
        candidates: List of candidates
        known_trivial: List of known trivial integrals (E, L, etc.)
        sample_states: Test states
        tolerance: Numerical tolerance

    Returns:
        filtered: List of non-trivial candidates
    """
    filtered = []

    for cand in candidates:
        is_trivial = False

        # Check if constant
        try:
            values = [cand.expression_numerical(state) for state in sample_states[:10]]
            if np.std(values) < tolerance:
                print(f"Filtering {cand.name}: constant")
                is_trivial = True
        except:
            pass

        # Check against known trivial integrals
        if not is_trivial:
            for trivial_func in known_trivial:
                try:
                    diffs = [
                        abs(cand.expression_numerical(state) - trivial_func(state))
                        for state in sample_states[:100]
                    ]
                    if np.mean(diffs) < tolerance:
                        print(f"Filtering {cand.name}: matches known integral")
                        is_trivial = True
                        break
                except:
                    pass

        if not is_trivial:
            filtered.append(cand)

    return filtered


def consolidate_and_rank(
    candidates: List[CandidateIntegral],
    sample_states: np.ndarray,
    known_trivial: Optional[List[Callable]] = None,
    remove_duplicates: bool = True,
    weights: Optional[Dict[str, float]] = None
) -> List[CandidateIntegral]:
    """
    Consolidate candidates from all sources and rank by quality.

    Pipeline:
    1. Filter trivial candidates
    2. Remove duplicates
    3. Compute scores
    4. Sort by score (best first)

    Args:
        candidates: All candidate integrals
        sample_states: Test states for numerical comparisons
        known_trivial: Known trivial integrals to filter
        remove_duplicates: Remove duplicate candidates
        weights: Scoring weights

    Returns:
        ranked_candidates: Sorted list (best first)

    Example:
        >>> candidates = [...]  # From WP3.1, WP3.2, WP3.3
        >>> samples = np.random.randn(1000, 8)
        >>> ranked = consolidate_and_rank(candidates, samples)
        >>> print(f"Best candidate: {ranked[0].name}")
        >>> print(f"Score: {ranked[0].score:.2f}")
    """
    print(f"Consolidating {len(candidates)} candidates...")

    # Step 1: Filter trivial
    if known_trivial is not None:
        candidates = filter_trivial_candidates(
            candidates,
            known_trivial,
            sample_states
        )
        print(f"  After filtering trivial: {len(candidates)}")

    # Step 2: Detect duplicates
    if remove_duplicates and len(candidates) > 1:
        duplicate_pairs = detect_duplicate_candidates(candidates, sample_states)

        # Remove second of each duplicate pair
        to_remove = set([j for i, j in duplicate_pairs])
        candidates = [cand for idx, cand in enumerate(candidates) if idx not in to_remove]
        print(f"  After removing duplicates: {len(candidates)}")

    # Step 3: Compute scores
    for cand in candidates:
        cand.score = compute_candidate_score(cand, weights)

    # Step 4: Sort by score
    ranked = sorted(candidates, key=lambda c: c.score)

    print(f"  Ranking complete. Best score: {ranked[0].score:.2f}")

    return ranked


def create_candidate_from_wp31_killing(
    killing_field_name: str,
    integral_expr: sp.Expr,
    integral_func: Callable,
    validation: ValidationResult,
    is_tensor: bool = False
) -> CandidateIntegral:
    """
    Create CandidateIntegral from WP3.1 Killing field result.

    Args:
        killing_field_name: Name of Killing field
        integral_expr: SymPy expression for integral
        integral_func: Numerical evaluation function
        validation: ValidationResult from testing
        is_tensor: True if from Killing tensor (else Killing vector)

    Returns:
        candidate: CandidateIntegral object
    """
    source = CandidateSource.KILLING_TENSOR if is_tensor else CandidateSource.KILLING_FIELD

    return CandidateIntegral(
        name=f"I_{killing_field_name}",
        expression_symbolic=integral_expr,
        expression_numerical=integral_func,
        source=source,
        conservation_error=validation.conservation_error,
        complexity=count_operations(integral_expr),
        is_independent=validation.is_independent if validation.is_independent is not None else False,
        validation_result=validation,
        metadata={'killing_field': killing_field_name}
    )


def create_candidate_from_wp32_ml(
    model_name: str,
    integral_expr: sp.Expr,
    integral_func: Callable,
    validation: ValidationResult,
    is_sympnet: bool = False
) -> CandidateIntegral:
    """
    Create CandidateIntegral from WP3.2 ML result.

    Args:
        model_name: Name of trained model
        integral_expr: Symbolic expression (from regression)
        integral_func: Numerical function (from network)
        validation: ValidationResult
        is_sympnet: True if SympNet (else HNN)

    Returns:
        candidate: CandidateIntegral object
    """
    source = CandidateSource.ML_SYMPNET if is_sympnet else CandidateSource.ML_HNN

    return CandidateIntegral(
        name=f"I_ML_{model_name}",
        expression_symbolic=integral_expr,
        expression_numerical=integral_func,
        source=source,
        conservation_error=validation.conservation_error,
        complexity=count_operations(integral_expr),
        is_independent=validation.is_independent if validation.is_independent is not None else False,
        validation_result=validation,
        metadata={'model': model_name}
    )


def generate_candidate_report(
    ranked_candidates: List[CandidateIntegral],
    top_n: int = 10,
    output_format: str = 'markdown'
) -> str:
    """
    Generate report of top candidate integrals.

    Args:
        ranked_candidates: Sorted list of candidates
        top_n: Number of top candidates to include
        output_format: 'markdown', 'latex', or 'plain'

    Returns:
        report: Formatted report string

    Example:
        >>> report = generate_candidate_report(ranked[:10])
        >>> print(report)
        >>> # Save to file
        >>> with open('candidates.md', 'w') as f:
        ...     f.write(report)
    """
    if output_format == 'markdown':
        return _generate_markdown_report(ranked_candidates, top_n)
    elif output_format == 'latex':
        return _generate_latex_report(ranked_candidates, top_n)
    else:
        return _generate_plain_report(ranked_candidates, top_n)


def _generate_markdown_report(candidates: List[CandidateIntegral], top_n: int) -> str:
    """Generate Markdown formatted report."""
    lines = []
    lines.append("# Top Candidate Conserved Integrals")
    lines.append("")
    lines.append(f"Total candidates analyzed: {len(candidates)}")
    lines.append(f"Showing top {min(top_n, len(candidates))} candidates")
    lines.append("")

    # Table header
    lines.append("| Rank | Name | Expression | Source | Conservation Error | Complexity | Independent | Score |")
    lines.append("|------|------|------------|--------|-------------------|------------|-------------|-------|")

    # Table rows
    for rank, cand in enumerate(candidates[:top_n], 1):
        expr_str = str(cand.expression_symbolic)
        if len(expr_str) > 40:
            expr_str = expr_str[:37] + "..."

        independent_str = "✓" if cand.is_independent else "✗"

        lines.append(
            f"| {rank} | {cand.name} | `{expr_str}` | {cand.source.value} | "
            f"{cand.conservation_error:.2e} | {cand.complexity} | {independent_str} | {cand.score:.2f} |"
        )

    lines.append("")
    lines.append("## Detailed Information")
    lines.append("")

    # Detailed entries
    for rank, cand in enumerate(candidates[:min(5, top_n)], 1):
        lines.append(f"### {rank}. {cand.name}")
        lines.append("")
        lines.append(f"**Expression**: `{cand.expression_symbolic}`")
        lines.append("")
        lines.append(f"**LaTeX**: ${sp.latex(cand.expression_symbolic)}$")
        lines.append("")
        lines.append(f"- **Source**: {cand.source.value}")
        lines.append(f"- **Conservation error**: {cand.conservation_error:.2e}")
        lines.append(f"- **Complexity**: {cand.complexity} operations")
        lines.append(f"- **Functionally independent**: {'Yes' if cand.is_independent else 'No'}")
        lines.append(f"- **Score**: {cand.score:.2f}")

        if cand.validation_result and cand.validation_result.poisson_bracket_with_H:
            pb = cand.validation_result.poisson_bracket_with_H
            lines.append(f"- **Poisson bracket {{I, H}}**: `{pb}`")

        lines.append("")

    return "\n".join(lines)


def _generate_latex_report(candidates: List[CandidateIntegral], top_n: int) -> str:
    """Generate LaTeX formatted report."""
    # TODO: Implement LaTeX formatting
    return _generate_plain_report(candidates, top_n)


def _generate_plain_report(candidates: List[CandidateIntegral], top_n: int) -> str:
    """Generate plain text report."""
    lines = []
    lines.append("=" * 80)
    lines.append("TOP CANDIDATE CONSERVED INTEGRALS")
    lines.append("=" * 80)
    lines.append("")

    for rank, cand in enumerate(candidates[:top_n], 1):
        lines.append(f"Rank {rank}: {cand.name}")
        lines.append(f"  Expression:  {cand.expression_symbolic}")
        lines.append(f"  Source:      {cand.source.value}")
        lines.append(f"  Cons. Error: {cand.conservation_error:.2e}")
        lines.append(f"  Complexity:  {cand.complexity}")
        lines.append(f"  Independent: {'Yes' if cand.is_independent else 'No'}")
        lines.append(f"  Score:       {cand.score:.2f}")
        lines.append("")

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    print("Candidate Ranking - Example\n")

    # Create mock candidates
    q0, q1, p0, p1 = sp.symbols('q0 q1 p0 p1')

    candidates = [
        CandidateIntegral(
            name="Energy",
            expression_symbolic=p0**2 + p1**2 + q0**2 + q1**2,
            expression_numerical=lambda z: z[2]**2 + z[3]**2 + z[0]**2 + z[1]**2,
            source=CandidateSource.KILLING_FIELD,
            conservation_error=1e-12,
            complexity=6,
            is_independent=True
        ),
        CandidateIntegral(
            name="Angular_Momentum",
            expression_symbolic=q0*p1 - q1*p0,
            expression_numerical=lambda z: z[0]*z[3] - z[1]*z[2],
            source=CandidateSource.KILLING_FIELD,
            conservation_error=1e-11,
            complexity=3,
            is_independent=True
        ),
        CandidateIntegral(
            name="ML_Candidate",
            expression_symbolic=p0**2 + q1**2,
            expression_numerical=lambda z: z[2]**2 + z[1]**2,
            source=CandidateSource.ML_HNN,
            conservation_error=1e-5,
            complexity=2,
            is_independent=False
        ),
    ]

    # Rank candidates
    samples = np.random.randn(100, 4)
    ranked = consolidate_and_rank(candidates, samples, remove_duplicates=False)

    # Generate report
    report = generate_candidate_report(ranked, top_n=10)
    print(report)
