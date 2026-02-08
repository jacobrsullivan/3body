# Statistical Testing for Integral Validation

Statistical methods for validating conservation of candidate integrals.

## Overview

Statistical testing provides rigorous quantification of conservation quality. Rather than relying on single trajectories, we use ensemble methods and hypothesis testing to establish confidence in integral validity.

## Hypothesis Testing Framework

### Null and Alternative Hypotheses

**Standard approach** (difficult to prove conservation):
- H₀: Integral is conserved (drift = 0)
- H₁: Integral is NOT conserved (drift ≠ 0)
- Problem: Can only reject H₀, never confirm it

**Equivalence testing** (TOST - Two One-Sided Tests):
- H₀: |drift| ≥ ε (NOT equivalent to zero)
- H₁: |drift| < ε (equivalent to zero)
- Advantage: Can positively conclude conservation

### TOST Implementation

```python
import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import List

@dataclass
class TOSTResult:
    """Results from Two One-Sided Tests for equivalence."""
    p_value: float
    reject_null: bool
    equivalence_bound: float
    sample_mean: float
    sample_std: float
    n_samples: int
    confidence_interval: tuple
    conclusion: str

def tost_conservation_test(
    drift_rates: np.ndarray,
    equivalence_bound: float = 1e-12,
    alpha: float = 0.05
) -> TOSTResult:
    """
    Two One-Sided Tests for equivalence to zero.
    
    Parameters:
        drift_rates: Array of measured drift rates
        equivalence_bound: ε such that |drift| < ε means "conserved"
        alpha: Significance level
        
    Returns:
        TOSTResult with test outcomes
    """
    n = len(drift_rates)
    mean = np.mean(drift_rates)
    std = np.std(drift_rates, ddof=1)
    se = std / np.sqrt(n)
    
    # Two one-sided t-tests
    # Test 1: H₀: μ ≥ ε vs H₁: μ < ε
    t_upper = (mean - equivalence_bound) / se
    p_upper = stats.t.cdf(t_upper, df=n-1)
    
    # Test 2: H₀: μ ≤ -ε vs H₁: μ > -ε  
    t_lower = (mean + equivalence_bound) / se
    p_lower = 1 - stats.t.cdf(t_lower, df=n-1)
    
    # TOST p-value is max of the two
    p_tost = max(p_upper, p_lower)
    
    # Reject null (conclude equivalence) if p < α
    reject_null = p_tost < alpha
    
    # Confidence interval
    t_crit = stats.t.ppf(1 - alpha, df=n-1)
    ci = (mean - t_crit * se, mean + t_crit * se)
    
    if reject_null:
        conclusion = f"CONSERVED: Drift equivalent to zero (|drift| < {equivalence_bound:.0e})"
    else:
        conclusion = f"NOT CONSERVED: Cannot establish equivalence"
    
    return TOSTResult(
        p_value=p_tost,
        reject_null=reject_null,
        equivalence_bound=equivalence_bound,
        sample_mean=mean,
        sample_std=std,
        n_samples=n,
        confidence_interval=ci,
        conclusion=conclusion
    )
```

### Sample Size Determination

```python
def required_sample_size(
    effect_size: float,
    equivalence_bound: float,
    power: float = 0.80,
    alpha: float = 0.05
) -> int:
    """
    Compute required sample size for TOST with given power.
    
    Parameters:
        effect_size: Expected std of drift rates
        equivalence_bound: ε for equivalence
        power: Desired power (1 - Type II error)
        alpha: Significance level
        
    Returns:
        Required sample size
    """
    from scipy.optimize import brentq
    
    def power_function(n):
        """Compute power for given n."""
        n = int(n)
        se = effect_size / np.sqrt(n)
        
        # Non-centrality parameters (assuming true mean = 0)
        t_crit = stats.t.ppf(1 - alpha, df=n-1)
        
        # Power is probability of rejecting both one-sided nulls
        # When true mean = 0, both tests have same power
        ncp = equivalence_bound / se
        power_one = stats.nct.cdf(-t_crit + ncp, df=n-1, nc=ncp)
        
        return power_one - power
    
    # Find n that achieves desired power
    try:
        n_required = int(brentq(power_function, 10, 100000))
    except ValueError:
        n_required = 100000  # Very large if not found
    
    return n_required
```

## Monte Carlo Methods

### Bootstrap Confidence Intervals

```python
def bootstrap_confidence_interval(
    data: np.ndarray,
    statistic: callable = np.mean,
    n_bootstrap: int = 10000,
    confidence: float = 0.95,
    seed: int = 42
) -> dict:
    """
    Compute bootstrap confidence interval for any statistic.
    
    Parameters:
        data: Sample data
        statistic: Function to compute (default: mean)
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level
        
    Returns:
        Dict with point estimate and confidence interval
    """
    np.random.seed(seed)
    n = len(data)
    
    # Bootstrap resampling
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        resample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats.append(statistic(resample))
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # Percentile method
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
    
    # BCa adjustment (bias-corrected and accelerated)
    point_estimate = statistic(data)
    
    # Bias correction
    z0 = stats.norm.ppf(np.mean(bootstrap_stats < point_estimate))
    
    # Acceleration (jackknife estimate)
    jackknife_stats = []
    for i in range(n):
        jack_sample = np.delete(data, i)
        jackknife_stats.append(statistic(jack_sample))
    jackknife_stats = np.array(jackknife_stats)
    
    jack_mean = np.mean(jackknife_stats)
    a = np.sum((jack_mean - jackknife_stats)**3) / (6 * np.sum((jack_mean - jackknife_stats)**2)**1.5)
    
    # BCa intervals
    z_alpha = stats.norm.ppf(alpha / 2)
    z_1_alpha = stats.norm.ppf(1 - alpha / 2)
    
    alpha1 = stats.norm.cdf(z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha)))
    alpha2 = stats.norm.cdf(z0 + (z0 + z_1_alpha) / (1 - a * (z0 + z_1_alpha)))
    
    bca_lower = np.percentile(bootstrap_stats, 100 * alpha1)
    bca_upper = np.percentile(bootstrap_stats, 100 * alpha2)
    
    return {
        'point_estimate': point_estimate,
        'percentile_ci': (lower, upper),
        'bca_ci': (bca_lower, bca_upper),
        'bootstrap_std': np.std(bootstrap_stats),
        'bootstrap_distribution': bootstrap_stats
    }
```

### Permutation Tests

```python
def permutation_test_drift(
    candidate_drifts: np.ndarray,
    jacobi_drifts: np.ndarray,
    n_permutations: int = 10000,
    seed: int = 42
) -> dict:
    """
    Permutation test comparing candidate drift to Jacobi drift.
    
    Tests if candidate conserves as well as Jacobi constant.
    H₀: Candidate drift = Jacobi drift (in distribution)
    """
    np.random.seed(seed)
    
    # Observed test statistic: difference in mean absolute drift
    observed_diff = np.mean(np.abs(candidate_drifts)) - np.mean(np.abs(jacobi_drifts))
    
    # Pool the data
    combined = np.concatenate([candidate_drifts, jacobi_drifts])
    n_candidate = len(candidate_drifts)
    
    # Permutation distribution
    perm_diffs = []
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_candidate = combined[:n_candidate]
        perm_jacobi = combined[n_candidate:]
        
        perm_diff = np.mean(np.abs(perm_candidate)) - np.mean(np.abs(perm_jacobi))
        perm_diffs.append(perm_diff)
    
    perm_diffs = np.array(perm_diffs)
    
    # Two-sided p-value
    p_value = np.mean(np.abs(perm_diffs) >= np.abs(observed_diff))
    
    return {
        'observed_difference': observed_diff,
        'p_value': p_value,
        'candidate_as_good': p_value > 0.05,  # Fail to reject → similar
        'permutation_distribution': perm_diffs
    }
```

## Multiple Testing Corrections

### Bonferroni Correction

```python
def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> dict:
    """
    Bonferroni correction for multiple comparisons.
    
    Very conservative: controls family-wise error rate.
    """
    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests
    
    rejections = [p < adjusted_alpha for p in p_values]
    
    return {
        'original_alpha': alpha,
        'adjusted_alpha': adjusted_alpha,
        'n_tests': n_tests,
        'rejections': rejections,
        'n_significant': sum(rejections)
    }
```

### Benjamini-Hochberg (FDR Control)

```python
def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> dict:
    """
    Benjamini-Hochberg procedure for FDR control.
    
    Less conservative than Bonferroni, controls false discovery rate.
    """
    n = len(p_values)
    
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # BH critical values
    critical = alpha * np.arange(1, n+1) / n
    
    # Find largest k where p_(k) ≤ critical
    reject = sorted_p <= critical
    
    if np.any(reject):
        k_max = np.max(np.where(reject)[0])
        rejections = np.zeros(n, dtype=bool)
        rejections[sorted_indices[:k_max+1]] = True
    else:
        rejections = np.zeros(n, dtype=bool)
    
    return {
        'alpha': alpha,
        'rejections': rejections.tolist(),
        'n_significant': int(np.sum(rejections)),
        'adjusted_p_values': np.minimum(1, sorted_p * n / np.arange(1, n+1))
    }
```

## Distribution Analysis

### Testing for Normality

```python
def test_drift_normality(drift_rates: np.ndarray) -> dict:
    """
    Test if drift rates follow normal distribution.
    
    Important for validity of t-tests and confidence intervals.
    """
    # Shapiro-Wilk test
    if len(drift_rates) <= 5000:
        sw_stat, sw_p = stats.shapiro(drift_rates)
    else:
        # Use subsample for large n
        subsample = np.random.choice(drift_rates, size=5000, replace=False)
        sw_stat, sw_p = stats.shapiro(subsample)
    
    # Anderson-Darling test
    ad_result = stats.anderson(drift_rates, dist='norm')
    
    # Kolmogorov-Smirnov test
    ks_stat, ks_p = stats.kstest(
        drift_rates, 
        'norm', 
        args=(np.mean(drift_rates), np.std(drift_rates))
    )
    
    # Skewness and kurtosis
    skewness = stats.skew(drift_rates)
    kurtosis = stats.kurtosis(drift_rates)
    
    is_normal = sw_p > 0.05 and ks_p > 0.05
    
    return {
        'shapiro_wilk': {'statistic': sw_stat, 'p_value': sw_p},
        'anderson_darling': {
            'statistic': ad_result.statistic,
            'critical_values': dict(zip(ad_result.significance_level, ad_result.critical_values))
        },
        'kolmogorov_smirnov': {'statistic': ks_stat, 'p_value': ks_p},
        'skewness': skewness,
        'kurtosis': kurtosis,
        'is_normal': is_normal
    }
```

### Outlier Detection

```python
def detect_outliers(data: np.ndarray, method: str = 'iqr') -> dict:
    """
    Detect outliers in conservation errors.
    
    Outliers may indicate:
    - Numerical instabilities
    - Close approaches to singularities
    - Breakdown of integral near resonances
    """
    if method == 'iqr':
        # Interquartile range method
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = (data < lower) | (data > upper)
        
    elif method == 'zscore':
        # Z-score method
        z = np.abs(stats.zscore(data))
        outliers = z > 3
        lower = np.mean(data) - 3 * np.std(data)
        upper = np.mean(data) + 3 * np.std(data)
        
    elif method == 'mad':
        # Median Absolute Deviation (robust)
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        modified_z = 0.6745 * (data - median) / mad
        outliers = np.abs(modified_z) > 3.5
        lower = median - 3.5 * mad / 0.6745
        upper = median + 3.5 * mad / 0.6745
    
    return {
        'outlier_indices': np.where(outliers)[0],
        'n_outliers': np.sum(outliers),
        'outlier_fraction': np.mean(outliers),
        'bounds': (lower, upper),
        'outlier_values': data[outliers]
    }
```

## Comparing Multiple Candidates

### ANOVA for Drift Comparison

```python
def compare_candidate_drifts(
    candidates: dict,
    n_samples_per: int = 100
) -> dict:
    """
    Compare drift rates across multiple candidates using ANOVA.
    
    Parameters:
        candidates: Dict of {name: drift_rates array}
        
    Returns:
        ANOVA results and pairwise comparisons
    """
    names = list(candidates.keys())
    groups = [candidates[name][:n_samples_per] for name in names]
    
    # One-way ANOVA
    f_stat, p_value = stats.f_oneway(*groups)
    
    # Effect size (eta-squared)
    all_data = np.concatenate(groups)
    grand_mean = np.mean(all_data)
    
    ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups)
    ss_total = np.sum((all_data - grand_mean)**2)
    eta_squared = ss_between / ss_total
    
    # Pairwise comparisons (Tukey HSD)
    from scipy.stats import tukey_hsd
    tukey = tukey_hsd(*groups)
    
    return {
        'f_statistic': f_stat,
        'p_value': p_value,
        'eta_squared': eta_squared,
        'significant_difference': p_value < 0.05,
        'tukey_results': {
            'statistic': tukey.statistic,
            'pvalue': tukey.pvalue
        },
        'group_means': {name: np.mean(candidates[name]) for name in names},
        'group_stds': {name: np.std(candidates[name]) for name in names}
    }
```

### Ranking Candidates

```python
def rank_candidates_by_conservation(
    candidates: dict,
    criterion: str = 'median_error'
) -> List[tuple]:
    """
    Rank candidates by conservation quality.
    
    Parameters:
        candidates: Dict of {name: error_array}
        criterion: 'mean_error', 'median_error', 'max_error', 'pass_rate'
        
    Returns:
        Sorted list of (name, score) tuples
    """
    rankings = []
    
    for name, errors in candidates.items():
        if criterion == 'mean_error':
            score = np.mean(errors)
        elif criterion == 'median_error':
            score = np.median(errors)
        elif criterion == 'max_error':
            score = np.max(errors)
        elif criterion == 'pass_rate':
            score = -np.mean(errors < 1e-10)  # Negative for descending order
        else:
            raise ValueError(f"Unknown criterion: {criterion}")
        
        rankings.append((name, score))
    
    # Sort by score (lower is better)
    rankings.sort(key=lambda x: x[1])
    
    return rankings
```

## Visualization

```python
import matplotlib.pyplot as plt

def plot_statistical_summary(results: dict, save_path: str = None):
    """
    Create comprehensive statistical visualization.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Distribution of errors
    ax1 = axes[0, 0]
    errors = results.get('errors', [])
    ax1.hist(np.log10(np.array(errors) + 1e-16), bins=50, density=True, alpha=0.7)
    ax1.axvline(x=np.log10(1e-10), color='r', linestyle='--', label='Threshold')
    ax1.set_xlabel('log₁₀(Error)')
    ax1.set_ylabel('Density')
    ax1.set_title('Error Distribution')
    ax1.legend()
    
    # 2. Q-Q plot for normality
    ax2 = axes[0, 1]
    stats.probplot(errors, dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot (Normality Check)')
    
    # 3. Cumulative distribution
    ax3 = axes[1, 0]
    sorted_errors = np.sort(errors)
    cdf = np.arange(1, len(sorted_errors)+1) / len(sorted_errors)
    ax3.semilogx(sorted_errors, cdf * 100)
    ax3.axvline(x=1e-10, color='r', linestyle='--')
    ax3.axhline(y=99.9, color='g', linestyle=':')
    ax3.set_xlabel('Error')
    ax3.set_ylabel('Cumulative %')
    ax3.set_title('Cumulative Distribution')
    
    # 4. Box plot comparison (if multiple candidates)
    ax4 = axes[1, 1]
    if 'candidate_errors' in results:
        data = [results['candidate_errors'][name] for name in results['candidate_errors']]
        ax4.boxplot(data, labels=list(results['candidate_errors'].keys()))
        ax4.set_ylabel('Error')
        ax4.set_title('Candidate Comparison')
        ax4.set_yscale('log')
    else:
        ax4.text(0.5, 0.5, 'No comparison data', ha='center', va='center')
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    plt.show()
```

## Complete Statistical Validation

```python
@dataclass
class StatisticalValidationResult:
    """Complete statistical validation results."""
    passed: bool
    tost_result: TOSTResult
    bootstrap_ci: dict
    normality_test: dict
    outlier_analysis: dict
    summary: str

def complete_statistical_validation(
    drift_rates: np.ndarray,
    equivalence_bound: float = 1e-12,
    alpha: float = 0.05,
    jacobi_comparison: np.ndarray = None
) -> StatisticalValidationResult:
    """
    Run complete statistical validation suite.
    """
    # TOST equivalence test
    tost = tost_conservation_test(drift_rates, equivalence_bound, alpha)
    
    # Bootstrap confidence interval
    bootstrap = bootstrap_confidence_interval(drift_rates, np.mean)
    
    # Normality test
    normality = test_drift_normality(drift_rates)
    
    # Outlier detection
    outliers = detect_outliers(np.abs(drift_rates), method='mad')
    
    # Compare to Jacobi if available
    jacobi_comparison_result = None
    if jacobi_comparison is not None:
        jacobi_comparison_result = permutation_test_drift(drift_rates, jacobi_comparison)
    
    # Overall verdict
    passed = (
        tost.reject_null and
        outliers['outlier_fraction'] < 0.01 and
        (jacobi_comparison_result is None or jacobi_comparison_result['candidate_as_good'])
    )
    
    summary = f"""Statistical Validation Summary:
    TOST p-value: {tost.p_value:.4f} ({'PASS' if tost.reject_null else 'FAIL'})
    Mean drift: {tost.sample_mean:.2e} ± {tost.sample_std:.2e}
    95% CI: ({bootstrap['bca_ci'][0]:.2e}, {bootstrap['bca_ci'][1]:.2e})
    Normal distribution: {'Yes' if normality['is_normal'] else 'No'}
    Outlier fraction: {outliers['outlier_fraction']:.2%}
    Overall: {'PASSED' if passed else 'FAILED'}"""
    
    return StatisticalValidationResult(
        passed=passed,
        tost_result=tost,
        bootstrap_ci=bootstrap,
        normality_test=normality,
        outlier_analysis=outliers,
        summary=summary
    )
```

## References

- Wellek, S. (2010). *Testing Statistical Hypotheses of Equivalence and Noninferiority*
- Efron, B. & Tibshirani, R.J. (1994). *An Introduction to the Bootstrap*
- Benjamini, Y. & Hochberg, Y. (1995). "Controlling the False Discovery Rate"
- Good, P.I. (2005). *Permutation, Parametric and Bootstrap Tests of Hypotheses*
