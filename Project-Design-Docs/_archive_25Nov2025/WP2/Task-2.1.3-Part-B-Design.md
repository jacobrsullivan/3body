# Task 2.1.3 Part B: Riemann Curvature Analysis - Detailed Design

**Task**: WP 2.1.3 - Jacobi-Maupertuis Metric Analysis
**Part**: B - Riemann and Ricci Curvature Computation
**Status**: Design Phase
**Estimated Duration**: 2 days
**Dependencies**: Task 2.1.3 Part A Complete

---

## Overview

Part B implements the complete curvature tensor hierarchy: Riemann → Ricci → Scalar curvature. The scalar curvature $R$ is the key diagnostic for chaos: **negative curvature implies exponential divergence of nearby geodesics**, which manifests as sensitive dependence on initial conditions.

**Mathematical Goal**: Compute $R = g^{ij} R_{ij}$ where

$$
R_{ij} = \partial_k \Gamma^k_{ij} - \partial_j \Gamma^k_{ik} + \Gamma^k_{ij} \Gamma^l_{kl} - \Gamma^k_{il} \Gamma^l_{jk}
$$

---

## B1: Riemann Curvature Tensor

### Algorithm B1.1: Christoffel Derivatives

```python
def compute_christoffel_derivatives(
    christoffel_func: Callable[[ShapeSpaceState], ChristoffelSymbols],
    base_state: ShapeSpaceState,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute ∂Γ^k_{ij}/∂x^l using finite differences.

    Args:
        christoffel_func: Function computing Christoffel symbols
        base_state: Point where to compute
        epsilon: Step size

    Returns:
        4D array dGamma[l, k, i, j] = ∂Γ^k_{ij}/∂x^l
    """
    Gamma_base = christoffel_func(base_state)
    n = Gamma_base.symbols.shape[0]

    dGamma = np.zeros((n, n, n, n))

    for l in range(n):
        # Perturb l-th coordinate
        coords_plus = base_state.to_array().copy()
        coords_plus[l] += epsilon

        coords_minus = base_state.to_array().copy()
        coords_minus[l] -= epsilon

        state_plus = ShapeSpaceState.from_array(coords_plus)
        state_minus = ShapeSpaceState.from_array(coords_minus)

        Gamma_plus = christoffel_func(state_plus)
        Gamma_minus = christoffel_func(state_minus)

        # Finite difference
        dGamma[l, :, :, :] = (Gamma_plus.symbols - Gamma_minus.symbols) / (2 * epsilon)

    return dGamma
```

### Algorithm B1.2: Riemann Tensor (Full)

```python
def compute_riemann_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> np.ndarray:
    """
    Compute Riemann curvature tensor R^l_{ijk}.

    R^l_{ijk} = ∂_j Γ^l_{ik} - ∂_k Γ^l_{ij} + Γ^l_{jm} Γ^m_{ik} - Γ^l_{km} Γ^m_{ij}

    Args:
        christoffel: Γ^k_{ij}
        christoffel_derivatives: ∂Γ^k_{ij}/∂x^l

    Returns:
        4D array R[l, i, j, k] = R^l_{ijk}
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives

    n = Gamma.shape[0]
    riemann = np.zeros((n, n, n, n))

    for l in range(n):
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    # Derivative terms
                    riemann[l, i, j, k] += dGamma[j, l, i, k]  # ∂_j Γ^l_{ik}
                    riemann[l, i, j, k] -= dGamma[k, l, i, j]  # -∂_k Γ^l_{ij}

                    # Quadratic terms
                    for m in range(n):
                        riemann[l, i, j, k] += Gamma[l, j, m] * Gamma[m, i, k]
                        riemann[l, i, j, k] -= Gamma[l, k, m] * Gamma[m, i, j]

    return riemann
```

---

## B2: Ricci Curvature Tensor

### Algorithm B2.1: Contraction to Ricci

```python
def compute_ricci_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> np.ndarray:
    """
    Compute Ricci tensor R_{ij} by contracting Riemann.

    R_{ij} = R^k_{ikj} = ∂_k Γ^k_{ij} - ∂_j Γ^k_{ik} + Γ^k_{ij} Γ^l_{kl} - Γ^k_{il} Γ^l_{jk}

    This is more efficient than computing full Riemann then contracting.

    Args:
        christoffel: Γ^k_{ij}
        christoffel_derivatives: ∂Γ^k_{ij}/∂x^l

    Returns:
        2D array R_{ij} (symmetric)
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives

    n = Gamma.shape[0]
    ricci = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # Derivative terms
            for k in range(n):
                ricci[i, j] += dGamma[k, k, i, j]  # ∂_k Γ^k_{ij}
                ricci[i, j] -= dGamma[j, k, i, k]  # -∂_j Γ^k_{ik}

            # Quadratic terms
            for k in range(n):
                for l in range(n):
                    ricci[i, j] += Gamma[k, i, j] * Gamma[l, k, l]
                    ricci[i, j] -= Gamma[k, i, l] * Gamma[l, j, k]

    return ricci


def verify_ricci_symmetry(ricci: np.ndarray, tolerance: float = 1e-12) -> bool:
    """Verify Ricci tensor is symmetric."""
    return np.allclose(ricci, ricci.T, atol=tolerance)
```

---

## B3: Scalar Curvature

### Algorithm B3.1: Trace Contraction

```python
def compute_scalar_curvature(
    metric: RiemannianMetric,
    ricci: np.ndarray
) -> float:
    """
    Compute scalar curvature R = g^{ij} R_{ij}.

    Args:
        metric: Metric tensor g_{ij}
        ricci: Ricci tensor R_{ij}

    Returns:
        Scalar curvature R
    """
    g_inv = metric.inverse()

    # Trace: R = g^{ij} R_{ij}
    R = np.trace(g_inv @ ricci)

    return R


def classify_curvature_sign(R: float, threshold: float = 1e-14) -> str:
    """
    Classify scalar curvature by sign.

    R < 0: Negative curvature (hyperbolic) → chaos expected
    R = 0: Flat → integrable
    R > 0: Positive curvature (elliptic) → stable
    """
    if abs(R) < threshold:
        return "FLAT"
    elif R < 0:
        return "NEGATIVE (chaotic)"
    else:
        return "POSITIVE (stable)"
```

### Algorithm B3.2: Complete Curvature Pipeline

```python
def compute_curvature_tensors(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0
) -> CurvatureTensors:
    """
    Complete pipeline: state → scalar curvature.

    Args:
        shape_state: Point in shape space
        masses, energy, L_magnitude: System parameters

    Returns:
        CurvatureTensors with Ricci and scalar curvature
    """
    # 1. JM metric
    metric = compute_jm_metric(shape_state, masses, energy, L_magnitude)

    # 2. Metric derivatives
    metric_func = lambda s: compute_jm_metric(s, masses, energy, L_magnitude)
    dg = compute_metric_derivatives(metric_func, shape_state)

    # 3. Christoffel symbols
    christoffel = compute_christoffel_symbols(metric, dg)

    # 4. Christoffel derivatives
    christoffel_func = lambda s: compute_christoffel_symbols(
        metric_func(s),
        compute_metric_derivatives(metric_func, s)
    )
    dGamma = compute_christoffel_derivatives(christoffel_func, shape_state)

    # 5. Ricci tensor
    ricci = compute_ricci_tensor(christoffel, dGamma)

    # 6. Scalar curvature
    R = compute_scalar_curvature(metric, ricci)

    return CurvatureTensors(
        ricci=ricci,
        scalar=R,
        base_point=shape_state
    )


@dataclass(frozen=True)
class CurvatureTensors:
    """Complete curvature information."""
    ricci: np.ndarray  # R_{ij}
    scalar: float  # R
    base_point: ShapeSpaceState

    @property
    def is_positive(self) -> bool:
        return self.scalar > 0

    @property
    def is_negative(self) -> bool:
        return self.scalar < 0

    @property
    def is_flat(self, tolerance: float = 1e-14) -> bool:
        return abs(self.scalar) < tolerance
```

---

## B4: Chaos-Curvature Correlation

### Algorithm B4.1: Lyapunov Exponent

```python
def compute_lyapunov_exponent(
    cart_state: CartesianState,
    masses: Masses,
    integration_time: float = 100.0,
    dt: float = 0.01
) -> float:
    """
    Compute maximal Lyapunov exponent.

    Uses tangent space integration (variational equations).

    Returns:
        λ_max (positive for chaos)
    """
    # Integrate main trajectory + tangent vector
    # Standard method: QR decomposition at intervals

    state = cart_state
    tangent = np.random.randn(state.dimension * 2)  # Random initial tangent
    tangent /= np.linalg.norm(tangent)

    n_steps = int(integration_time / dt)
    lyapunov_sum = 0.0

    for step in range(n_steps):
        # Integrate both trajectory and tangent
        state, tangent = integrate_with_tangent(state, tangent, masses, dt)

        # Renormalize and accumulate
        norm = np.linalg.norm(tangent)
        lyapunov_sum += np.log(norm)
        tangent /= norm

    lambda_max = lyapunov_sum / integration_time

    return lambda_max
```

### Algorithm B4.2: Correlation Analysis

```python
def correlate_curvature_with_chaos(
    shape_states: list[ShapeSpaceState],
    masses: Masses,
    energy: float,
    integration_time: float = 100.0
) -> dict:
    """
    Compute R and λ at many points, analyze correlation.

    Returns:
        Dictionary with correlation statistics
    """
    n = len(shape_states)
    curvatures = np.zeros(n)
    lyapunov_exponents = np.zeros(n)

    for i, state in enumerate(shape_states):
        # Scalar curvature
        curv = compute_curvature_tensors(state, masses, energy)
        curvatures[i] = curv.scalar

        # Lyapunov exponent
        cart_state = shape_to_cartesian(state, masses)
        lyapunov_exponents[i] = compute_lyapunov_exponent(
            cart_state, masses, integration_time
        )

    # Correlation
    from scipy.stats import pearsonr
    r, p_value = pearsonr(curvatures, lyapunov_exponents)

    # Classification
    chaotic = lyapunov_exponents > 0.01
    negative_curv = curvatures < 0

    true_positive = np.sum(chaotic & negative_curv)
    false_positive = np.sum(~chaotic & negative_curv)
    true_negative = np.sum(~chaotic & ~negative_curv)
    false_negative = np.sum(chaotic & ~negative_curv)

    accuracy = (true_positive + true_negative) / n

    return {
        'curvatures': curvatures,
        'lyapunov_exponents': lyapunov_exponents,
        'correlation_coefficient': r,
        'p_value': p_value,
        'accuracy': accuracy,
        'confusion_matrix': {
            'TP': true_positive,
            'FP': false_positive,
            'TN': true_negative,
            'FN': false_negative
        }
    }
```

---

## Testing

```python
class TestScalarCurvature:
    def test_kepler_flat(self):
        """Kepler problem (m3 → 0) should have R → 0."""
        state = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)

        curvatures = []
        for m3 in [1.0, 0.1, 0.01, 0.001]:
            masses = Masses(1.0, 1.0, m3)
            curv = compute_curvature_tensors(state, masses, energy=-0.5)
            curvatures.append(abs(curv.scalar))

        # Should decrease
        assert curvatures[-1] < curvatures[0]
        assert curvatures[-1] < 1e-6  # Nearly flat

    def test_equal_mass_symmetry(self):
        """R should be symmetric under permutations."""
        masses = Masses(1.0, 1.0, 1.0)

        state1 = ShapeSpaceState(1.0, 1.2, 1.4, L=1.0)
        state2 = ShapeSpaceState(1.2, 1.4, 1.0, L=1.0)  # Permuted

        R1 = compute_curvature_tensors(state1, masses, -0.5).scalar
        R2 = compute_curvature_tensors(state2, masses, -0.5).scalar

        assert np.isclose(R1, R2, atol=1e-10)
```

---

**Status**: Complete | **Lines**: ~1,200
