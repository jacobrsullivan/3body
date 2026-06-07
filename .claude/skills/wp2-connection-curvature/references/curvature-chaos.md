# Curvature-Chaos Correlation Analysis

Methodology for testing the relationship between scalar curvature and chaotic behavior.

## Table of Contents

1. [Hypothesis](#hypothesis)
2. [Theoretical Background](#theoretical-background)
3. [Testing Methodology](#testing-methodology)
4. [Statistical Analysis](#statistical-analysis)
5. [Visualization](#visualization)
6. [Interpretation](#interpretation)

---

## Hypothesis

**Conjecture**: Negative scalar curvature R < 0 of the Jacobi-Maupertuis metric correlates with chaotic motion in the three-body problem.

**Physical basis**:
- Negative curvature → geodesic instability (nearby geodesics diverge exponentially)
- Geodesic instability → sensitive dependence on initial conditions
- Sensitive dependence → chaos (positive Lyapunov exponent)

---

## Theoretical Background

### Geodesic Deviation

For the Jacobi-Maupertuis metric, trajectories are geodesics. The deviation equation:

```
D²J/dτ² = -R(·, γ̇)γ̇ · J
```

describes how nearby geodesics separate.

### Sectional Curvature and Stability

| Sectional Curvature K | Deviation Behavior | Trajectory Type |
|----------------------|--------------------| ----------------|
| K > 0 | Oscillating (bounded) | Stable, regular |
| K = 0 | Linear growth | Marginally stable |
| K < 0 | Exponential growth | Unstable, chaotic |

### Scalar Curvature as Average

The scalar curvature R is an average of sectional curvatures:

```
R = 2 Σ K_ij
```

So R < 0 indicates *on average* negative sectional curvature, suggesting instability.

### Known Results

**Geodesic flow on negatively curved manifolds**:
- Anosov (1967): Geodesic flow is hyperbolic (uniformly unstable)
- Klingenberg (1974): No conjugate points → Lyapunov instability

**Three-body problem**:
- Montgomery (1996): Studied curvature on shape sphere
- Knauf (2018): Negative curvature regions correlate with chaotic dynamics

---

## Testing Methodology

### Step 1: Generate Trajectory Ensemble

```python
def generate_test_ensemble(mu, n_trajectories=1000, n_periods=100):
    """
    Generate diverse trajectory ensemble for testing.

    Returns:
        List of trajectory dicts with 'state0', 'states', 'shape_states'
    """
    from src.python.integrators.ias15 import IAS15Integrator
    from src.python.ml.sobol_sampling import SobolSampler

    # Sample initial conditions using Sobol sequence
    sampler = SobolSampler(dimension=4)  # (x, y, vx, vy)
    samples = sampler.sample(n_trajectories)

    # Transform to physical initial conditions
    trajectories = []
    integrator = IAS15Integrator(mu=mu)

    for sample in samples:
        # Map sample to IC (implementation specific)
        state0 = map_to_initial_condition(sample, mu)

        # Integrate
        T = estimate_period(state0, mu)
        times, states = integrator.integrate(
            state0, (0, n_periods * T), dt=T/50
        )

        # Convert to shape space
        shape_states = [to_shape_space(s, mu) for s in states]

        trajectories.append({
            'state0': state0,
            'times': times,
            'states': states,
            'shape_states': shape_states
        })

    return trajectories
```

### Step 2: Compute Curvature Along Trajectories

```python
def compute_curvature_statistics(trajectory, jm_metric):
    """
    Compute curvature statistics along a trajectory.
    """
    R_values = []

    for shape_point in trajectory['shape_states']:
        try:
            R = jm_metric.scalar_curvature(shape_point)
            R_values.append(R)
        except:
            continue  # Skip invalid points

    if not R_values:
        return None

    return {
        'R_mean': np.mean(R_values),
        'R_min': np.min(R_values),
        'R_max': np.max(R_values),
        'R_std': np.std(R_values),
        'frac_negative': np.mean([r < 0 for r in R_values]),
        'R_values': R_values
    }
```

### Step 3: Compute Chaos Indicators

```python
def compute_chaos_indicators(trajectory, mu):
    """
    Compute MEGNO and FLI chaos indicators.
    """
    from src.python.validation.chaos_indicators import (
        MEGNOIndicator, FLIIndicator
    )

    megno = MEGNOIndicator(mu=mu)
    fli = FLIIndicator(mu=mu)

    megno_result = megno.compute(trajectory['state0'], t_max=100)
    fli_result = fli.compute(trajectory['state0'], t_max=50)

    return {
        'megno': megno_result['value'],
        'fli': fli_result['value'],
        'classification': megno_result['classification'],
        'is_chaotic': megno_result['classification'] == 'chaotic',
        'lyapunov_estimate': megno_result.get('lyapunov', None)
    }
```

### Step 4: Correlate

```python
def analyze_correlation(trajectories, masses, energy, mu):
    """
    Analyze curvature-chaos correlation.
    """
    jm = JacobiMaupertuisMetric(masses=masses, energy=energy)

    results = []
    for traj in trajectories:
        curv_stats = compute_curvature_statistics(traj, jm)
        chaos_stats = compute_chaos_indicators(traj, mu)

        if curv_stats is None:
            continue

        results.append({
            **curv_stats,
            **chaos_stats
        })

    return results
```

---

## Statistical Analysis

### Correlation Coefficients

```python
def compute_correlations(results):
    """
    Compute various correlation measures.
    """
    from scipy import stats

    R_means = [r['R_mean'] for r in results]
    R_mins = [r['R_min'] for r in results]
    fracs = [r['frac_negative'] for r in results]
    megnos = [r['megno'] for r in results]
    is_chaotic = [r['is_chaotic'] for r in results]

    # Pearson correlation (R_mean vs MEGNO)
    pearson_r, pearson_p = stats.pearsonr(R_means, megnos)

    # Spearman rank correlation (more robust)
    spearman_r, spearman_p = stats.spearmanr(R_means, megnos)

    # Point-biserial correlation (R_mean vs is_chaotic)
    pointbis_r, pointbis_p = stats.pointbiserialr(is_chaotic, R_means)

    # Agreement rate
    predictions = [r < 0 for r in R_means]
    n_agree = sum(p == c for p, c in zip(predictions, is_chaotic))
    agreement_rate = n_agree / len(results)

    return {
        'pearson': {'r': pearson_r, 'p': pearson_p},
        'spearman': {'r': spearman_r, 'p': spearman_p},
        'point_biserial': {'r': pointbis_r, 'p': pointbis_p},
        'agreement_rate': agreement_rate,
        'n_samples': len(results)
    }
```

### Confusion Matrix

```python
def compute_confusion_matrix(results):
    """
    Compute confusion matrix for R < 0 → chaotic prediction.
    """
    TP = sum(1 for r in results if r['R_mean'] < 0 and r['is_chaotic'])
    FP = sum(1 for r in results if r['R_mean'] < 0 and not r['is_chaotic'])
    TN = sum(1 for r in results if r['R_mean'] >= 0 and not r['is_chaotic'])
    FN = sum(1 for r in results if r['R_mean'] >= 0 and r['is_chaotic'])

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    accuracy = (TP + TN) / len(results)

    return {
        'confusion_matrix': [[TP, FP], [FN, TN]],
        'precision': precision,
        'recall': recall,
        'accuracy': accuracy,
        'f1': 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    }
```

---

## Visualization

### Scatter Plot

```python
def plot_curvature_vs_megno(results):
    """
    Scatter plot of mean curvature vs MEGNO.
    """
    import matplotlib.pyplot as plt

    R_means = [r['R_mean'] for r in results]
    megnos = [r['megno'] for r in results]
    is_chaotic = [r['is_chaotic'] for r in results]

    fig, ax = plt.subplots(figsize=(10, 8))

    # Color by classification
    colors = ['red' if c else 'blue' for c in is_chaotic]
    ax.scatter(R_means, megnos, c=colors, alpha=0.5, s=20)

    # Add reference lines
    ax.axvline(x=0, color='black', linestyle='--', label='R = 0')
    ax.axhline(y=2.0, color='gray', linestyle='--', label='MEGNO = 2 (regular)')

    # Labels
    ax.set_xlabel('Mean Scalar Curvature R', fontsize=12)
    ax.set_ylabel('MEGNO', fontsize=12)
    ax.set_title('Curvature-Chaos Correlation', fontsize=14)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='blue',
               label='Regular', markersize=10),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
               label='Chaotic', markersize=10),
    ]
    ax.legend(handles=legend_elements)

    return fig
```

### Curvature Landscape with Chaos Overlay

```python
def plot_curvature_landscape_with_trajectories(masses, energy, trajectories, n_points=50):
    """
    Plot curvature landscape with trajectory chaos classification overlaid.
    """
    import matplotlib.pyplot as plt

    jm = JacobiMaupertuisMetric(masses=masses, energy=energy)

    # Create grid
    r12_vals = np.linspace(0.5, 2.0, n_points)
    r23_vals = np.linspace(0.5, 2.0, n_points)
    R12, R23 = np.meshgrid(r12_vals, r23_vals)

    R_landscape = compute_curvature_landscape(R12, R23, jm)

    # Plot landscape
    fig, ax = plt.subplots(figsize=(12, 10))

    im = ax.contourf(R12, R23, R_landscape, levels=20, cmap='RdBu_r')
    plt.colorbar(im, ax=ax, label='Scalar Curvature R')

    # R = 0 contour
    ax.contour(R12, R23, R_landscape, levels=[0], colors='black', linewidths=2)

    # Overlay trajectory starting points
    for traj in trajectories[:100]:  # Limit for clarity
        shape = traj['shape_states'][0]
        color = 'red' if traj.get('is_chaotic', False) else 'blue'
        ax.scatter(shape[0], shape[1], c=color, s=30, alpha=0.7,
                   edgecolors='white', linewidths=0.5)

    ax.set_xlabel('r₁₂')
    ax.set_ylabel('r₂₃')
    ax.set_title('Curvature Landscape with Trajectory Classification')

    return fig
```

---

## Interpretation

### Expected Results

| Observation | Interpretation |
|-------------|----------------|
| Strong negative correlation (r < -0.5) | Curvature predicts chaos well |
| Weak correlation | Other factors dominate |
| High agreement rate (> 80%) | R < 0 is good chaos predictor |
| Asymmetric confusion matrix | May need different threshold |

### Caveats

1. **Local vs Global**: Curvature is local; chaos is global property
2. **Time scales**: Curvature measures instantaneous instability
3. **Mixed regions**: Trajectories can pass through both R > 0 and R < 0 regions
4. **Averaging effects**: Mean curvature may wash out important features

### Refined Hypothesis

Rather than strict R < 0 ↔ chaotic, consider:

1. **Time-weighted curvature**: Weight by residence time in each region
2. **Minimum curvature**: Track most negative curvature encountered
3. **Curvature integral**: ∫ R dt along trajectory
4. **Threshold dependence**: R < R_critical for some R_critical < 0

```python
def refined_curvature_predictor(trajectory, jm_metric, threshold=-0.1):
    """
    Refined chaos prediction based on curvature.
    """
    R_values = []
    for shape in trajectory['shape_states']:
        R = jm_metric.scalar_curvature(shape)
        R_values.append(R)

    # Multiple criteria
    criteria = {
        'mean_negative': np.mean(R_values) < 0,
        'min_below_threshold': np.min(R_values) < threshold,
        'frac_negative_high': np.mean([r < 0 for r in R_values]) > 0.5,
        'integral_negative': np.sum(R_values) < 0,
    }

    # Predict chaotic if any criterion satisfied
    predict_chaotic = any(criteria.values())

    return {
        'prediction': 'chaotic' if predict_chaotic else 'regular',
        'criteria': criteria,
        'confidence': sum(criteria.values()) / len(criteria)
    }
```

---

## References

- Anosov, D.V. (1967). "Geodesic flows on closed Riemannian manifolds of negative curvature"
- Montgomery, R. (1996). "The geometric phase of the three-body problem"
- Knauf, A. (2018). *Mathematical Physics: Classical Mechanics*
- `Science-Research-Docs/WP1 – Foundations.pdf`
