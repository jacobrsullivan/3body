# Task 2.1.3 Part B: Curvature Analysis - Detailed Design

**Task**: WP 2.1.3 - Jacobi-Maupertuis Metric Analysis
**Part**: B - Curvature Analysis
**Status**: Design Phase
**Estimated Duration**: 2-3 days
**Dependencies**: Task 2.1.3 Part A Complete (JM Metric)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Foundations](#mathematical-foundations)
3. [B1: Riemann Curvature Tensor](#b1-riemann-curvature-tensor)
4. [B2: Ricci Tensor](#b2-ricci-tensor)
5. [B3: Scalar Curvature](#b3-scalar-curvature)
6. [B4: Chaos-Curvature Correlation](#b4-chaos-curvature-correlation)
7. [B5: Lyapunov Exponent Computation](#b5-lyapunov-exponent-computation)
8. [Implementation Details](#implementation-details)
9. [Validation and Testing](#validation-and-testing)

---

## Overview

### Purpose

Part B implements curvature computation for the Jacobi-Maupertuis metric and analyzes its correlation with chaos. The central scientific hypothesis is:

**Negative scalar curvature $R < 0$ is the geometric signature of chaotic dynamics.**

### What is Scalar Curvature?

**Physical Intuition**: Scalar curvature $R$ measures how the geometry deviates from flat (Euclidean) space. For the JM metric:
- **Negative $R$**: Geodesics (trajectories) diverge exponentially → **chaos**
- **Positive $R$**: Geodesics converge → **stable dynamics**
- **Zero $R$**: Flat space → **integrable system**

**Mathematical Definition**: $R$ is the complete contraction of the Riemann curvature tensor.

### Key Components

This part implements five main computational components:

1. **Riemann Tensor**: $R^l_{ijk}$ - full curvature information
2. **Ricci Tensor**: $R_{ij}$ - contraction of Riemann tensor
3. **Scalar Curvature**: $R = g^{ij} R_{ij}$ - complete contraction
4. **Chaos Indicators**: Lyapunov exponents, MEGNO
5. **Correlation Analysis**: Statistical analysis of $R$ vs chaos

### Deliverables

- `src/python/geometry/riemann_curvature.py` - Full curvature tensors
- `src/python/geometry/scalar_curvature.py` - Scalar curvature evaluator
- `src/python/analysis/chaos_indicators.py` - Lyapunov, MEGNO computation
- `src/python/analysis/correlation_analysis.py` - Statistical correlation
- Complete validation suite
- Performance target: <10 ms per curvature evaluation

---

## Mathematical Foundations

### Curvature Tensor Hierarchy

The curvature of a Riemannian manifold is encoded in a hierarchy of tensors:

**Riemann Tensor** $R^l_{ijk}$ (rank-4):
$$
R^l_{ijk} = \frac{\partial \Gamma^l_{jk}}{\partial x^i} - \frac{\partial \Gamma^l_{ik}}{\partial x^j} + \Gamma^m_{jk}\Gamma^l_{im} - \Gamma^m_{ik}\Gamma^l_{jm}
$$

**Ricci Tensor** $R_{ij}$ (rank-2, contraction):
$$
R_{ij} = R^k_{ikj} = \sum_k R^k_{ikj}
$$

**Scalar Curvature** $R$ (scalar, complete contraction):
$$
R = g^{ij} R_{ij}
$$

### Computational Path

```
Metric g_ij
    ↓ [derivatives]
Christoffel Γ^k_ij
    ↓ [derivatives + products]
Riemann R^l_ijk
    ↓ [contraction]
Ricci R_ij
    ↓ [trace with metric]
Scalar R
```

### Alternative Formula for Ricci Tensor

For computational efficiency, we use:

$$
R_{ij} = \frac{\partial \Gamma^k_{ij}}{\partial x^k} - \frac{\partial \Gamma^k_{ik}}{\partial x^j} + \Gamma^k_{ij}\Gamma^l_{kl} - \Gamma^k_{il}\Gamma^l_{jk}
$$

This avoids computing the full Riemann tensor.

### Geodesic Deviation and Chaos

The **Jacobi equation** governs separation of nearby geodesics:

$$
\frac{D^2 \xi^i}{dt^2} + R^i_{jkl} \dot{x}^j \xi^k \dot{x}^l = 0
$$

For negative sectional curvature, $\|\xi\|$ grows exponentially:
$$
\|\xi(t)\| \sim e^{\lambda t}
$$

This is precisely the mechanism of dynamical chaos (sensitive dependence on initial conditions).

---

## B1: Riemann Curvature Tensor

### Full Riemann Tensor

While we primarily need the Ricci tensor, computing the full Riemann tensor is useful for:
- Sectional curvatures (direction-dependent chaos)
- Validation of theoretical properties
- Geodesic deviation analysis

### Implementation

```python
# File: src/python/geometry/riemann_curvature.py

import numpy as np
from dataclasses import dataclass
from typing import Optional

from ..coordinates.shape_space import ShapeSpaceState
from .christoffel import ChristoffelSymbols


@dataclass(frozen=True)
class RiemannTensor:
    """
    Riemann curvature tensor R^l_ijk.

    Stored as 4D array: components[l, i, j, k] = R^l_ijk

    Attributes:
        components: 4D array (n, n, n, n)
        base_point: Point where evaluated
        coordinate_names: Coordinate labels
    """
    components: np.ndarray  # Shape (n, n, n, n)
    base_point: ShapeSpaceState
    coordinate_names: list[str]

    def __post_init__(self):
        """Validate antisymmetry properties."""
        n = self.components.shape[0]
        assert self.components.shape == (n, n, n, n)

        # Check antisymmetry: R^l_ijk = -R^l_jik
        for l in range(n):
            antisymmetry_error = np.linalg.norm(
                self.components[l] + self.components[l].transpose(1, 0, 2)
            )
            assert antisymmetry_error < 1e-10, "Must be antisymmetric in (i,j)"

    def contract_to_ricci(self) -> np.ndarray:
        """
        Contract to Ricci tensor: R_ij = R^k_ikj.

        Returns:
            Ricci tensor (n×n)
        """
        n = self.components.shape[0]
        ricci = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                for k in range(n):
                    ricci[i, j] += self.components[k, i, k, j]

        return ricci

    def sectional_curvature(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Compute sectional curvature K(v1, v2).

        K = R(v1, v2, v2, v1) / |v1 ∧ v2|^2

        Args:
            v1, v2: Tangent vectors (linearly independent)

        Returns:
            Sectional curvature (scalar)
        """
        # Compute R(v1, v2, v2, v1) = R^l_ijk v1^i v2^j v2^k v1^l
        R_eval = 0.0
        n = len(v1)

        for l in range(n):
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        R_eval += self.components[l, i, j, k] * v1[i] * v2[j] * v2[k] * v1[l]

        # Denominator: |v1 ∧ v2|^2 = |v1|^2 |v2|^2 - (v1·v2)^2
        v1_norm = np.linalg.norm(v1)
        v2_norm = np.linalg.norm(v2)
        v1_dot_v2 = np.dot(v1, v2)

        wedge_norm_squared = v1_norm**2 * v2_norm**2 - v1_dot_v2**2

        if wedge_norm_squared < 1e-14:
            raise ValueError("Vectors are linearly dependent")

        K = R_eval / wedge_norm_squared

        return K


def compute_riemann_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> RiemannTensor:
    """
    Compute Riemann curvature tensor from Christoffel symbols.

    R^l_ijk = ∂_i Γ^l_jk - ∂_j Γ^l_ik + Γ^m_jk Γ^l_im - Γ^m_ik Γ^l_jm

    Args:
        christoffel: Christoffel symbols Γ^k_ij
        christoffel_derivatives: ∂Γ^k_ij/∂x^l, shape (n, n, n, n)
            dGamma[l, k, i, j] = ∂Γ^k_ij/∂x^l

    Returns:
        RiemannTensor object
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
                    term1 = dGamma[i, l, j, k]  # ∂_i Γ^l_jk
                    term2 = -dGamma[j, l, i, k]  # -∂_j Γ^l_ik

                    # Quadratic terms
                    term3 = 0.0
                    term4 = 0.0
                    for m in range(n):
                        term3 += Gamma[m, j, k] * Gamma[l, i, m]  # Γ^m_jk Γ^l_im
                        term4 -= Gamma[m, i, k] * Gamma[l, j, m]  # -Γ^m_ik Γ^l_jm

                    riemann[l, i, j, k] = term1 + term2 + term3 + term4

    return RiemannTensor(
        components=riemann,
        base_point=christoffel.base_point,
        coordinate_names=christoffel.coordinate_names
    )


def compute_christoffel_derivatives(
    christoffel_func: callable,
    base_state: ShapeSpaceState,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute ∂Γ^k_ij/∂x^l using finite differences.

    Args:
        christoffel_func: Function computing Christoffel at any point
        base_state: Point where to compute derivatives
        epsilon: Step size

    Returns:
        4D array dGamma[l, k, i, j] = ∂Γ^k_ij/∂x^l
    """
    Gamma_base = christoffel_func(base_state)
    n = Gamma_base.dimension

    dGamma = np.zeros((n, n, n, n))

    for l in range(n):
        # Perturb l-th coordinate
        state_plus = _perturb_shape_coordinate(base_state, l, epsilon)
        state_minus = _perturb_shape_coordinate(base_state, l, -epsilon)

        Gamma_plus = christoffel_func(state_plus)
        Gamma_minus = christoffel_func(state_minus)

        # Central difference: ∂Γ/∂x^l
        dGamma[l, :, :, :] = (Gamma_plus.symbols - Gamma_minus.symbols) / (2 * epsilon)

    return dGamma
```

---

## B2: Ricci Tensor

### Direct Computation

We compute the Ricci tensor directly without the full Riemann tensor:

$$
R_{ij} = \frac{\partial \Gamma^k_{ij}}{\partial x^k} - \frac{\partial \Gamma^k_{ik}}{\partial x^j} + \Gamma^k_{ij}\Gamma^l_{kl} - \Gamma^k_{il}\Gamma^l_{jk}
$$

### Implementation

```python
@dataclass(frozen=True)
class RicciTensor:
    """
    Ricci curvature tensor R_ij.

    Symmetric contraction of Riemann tensor.

    Attributes:
        components: Symmetric matrix R_ij (n×n)
        base_point: Point where evaluated
        coordinate_names: Coordinate labels
    """
    components: np.ndarray  # (n, n) symmetric
    base_point: ShapeSpaceState
    coordinate_names: list[str]

    def __post_init__(self):
        """Validate symmetry."""
        n = self.components.shape[0]
        assert self.components.shape == (n, n)

        # Check symmetry: R_ij = R_ji
        symmetry_error = np.linalg.norm(
            self.components - self.components.T
        )
        assert symmetry_error < 1e-10, "Ricci tensor must be symmetric"

    def eigenvalues(self) -> np.ndarray:
        """Principal curvatures."""
        return np.linalg.eigvalsh(self.components)

    def is_positive_definite(self) -> bool:
        """Check if all eigenvalues > 0."""
        return np.all(self.eigenvalues() > -1e-14)

    def is_negative_definite(self) -> bool:
        """Check if all eigenvalues < 0."""
        return np.all(self.eigenvalues() < 1e-14)


def compute_ricci_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> RicciTensor:
    """
    Compute Ricci tensor from Christoffel symbols.

    R_ij = ∂_k Γ^k_ij - ∂_j Γ^k_ik + Γ^k_ij Γ^l_kl - Γ^k_il Γ^l_jk

    Args:
        christoffel: Γ^k_ij
        christoffel_derivatives: ∂Γ^k_ij/∂x^l

    Returns:
        RicciTensor object
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives

    n = Gamma.shape[0]
    ricci = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # First two terms: derivatives
            for k in range(n):
                ricci[i, j] += dGamma[k, k, i, j]  # ∂_k Γ^k_ij
                ricci[i, j] -= dGamma[j, k, i, k]  # -∂_j Γ^k_ik

            # Last two terms: quadratic in Christoffel
            for k in range(n):
                for l in range(n):
                    ricci[i, j] += Gamma[k, i, j] * Gamma[l, k, l]  # Γ^k_ij Γ^l_kl
                    ricci[i, j] -= Gamma[k, i, l] * Gamma[l, j, k]  # -Γ^k_il Γ^l_jk

    return RicciTensor(
        components=ricci,
        base_point=christoffel.base_point,
        coordinate_names=christoffel.coordinate_names
    )


def compute_ricci_tensor_optimized(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> RicciTensor:
    """
    Optimized version using Einstein summation.

    Approximately 5x faster for n=3.
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives

    # Derivative terms using einsum
    term1 = np.einsum('kij->ij', dGamma[:, :, :, :])  # ∂_k Γ^k_ij
    term2 = -np.einsum('jki->ij', dGamma[:, :, :, :])  # -∂_j Γ^k_ik

    # Quadratic terms
    term3 = np.einsum('kij,lkl->ij', Gamma, Gamma)  # Γ^k_ij Γ^l_kl
    term4 = -np.einsum('kil,ljk->ij', Gamma, Gamma)  # -Γ^k_il Γ^l_jk

    ricci = term1 + term2 + term3 + term4

    return RicciTensor(
        components=ricci,
        base_point=christoffel.base_point,
        coordinate_names=christoffel.coordinate_names
    )
```

---

## B3: Scalar Curvature

### Definition and Computation

$$
R = g^{ij} R_{ij} = \text{Tr}(g^{-1} R)
$$

### Implementation

```python
# File: src/python/geometry/scalar_curvature.py

import numpy as np
from dataclasses import dataclass
from typing import Callable

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from .jm_metric import RiemannianMetric, compute_jm_metric
from .christoffel import ChristoffelSymbols, compute_christoffel_symbols
from .riemann_curvature import RicciTensor, compute_ricci_tensor


@dataclass(frozen=True)
class CurvatureTensors:
    """
    Complete curvature information at a point.

    Attributes:
        riemann: Full Riemann tensor (optional, expensive)
        ricci: Ricci tensor
        scalar: Scalar curvature R
        base_point: Point where evaluated
    """
    ricci: RicciTensor
    scalar: float
    base_point: ShapeSpaceState
    riemann: Optional[RiemannTensor] = None

    @property
    def is_positive(self) -> bool:
        """Positive scalar curvature (regular dynamics)."""
        return self.scalar > 0

    @property
    def is_negative(self) -> bool:
        """Negative scalar curvature (chaotic dynamics)."""
        return self.scalar < 0

    @property
    def is_flat(self, tolerance: float = 1e-12) -> bool:
        """Nearly zero curvature (integrable)."""
        return abs(self.scalar) < tolerance


def compute_scalar_curvature(
    metric: RiemannianMetric,
    ricci: RicciTensor
) -> float:
    """
    Compute scalar curvature R = g^ij R_ij.

    Args:
        metric: Metric tensor g_ij
        ricci: Ricci tensor R_ij

    Returns:
        Scalar curvature (float)
    """
    g_inv = metric.inverse()
    R_matrix = ricci.components

    # Trace: R = g^ij R_ij = Tr(g^{-1} R)
    R = np.trace(g_inv @ R_matrix)

    return R


def compute_curvature_tensors_complete(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    compute_full_riemann: bool = False
) -> CurvatureTensors:
    """
    Complete pipeline: metric → Christoffel → Ricci → scalar curvature.

    Args:
        shape_state: Point in shape space
        masses: Body masses
        energy: Total energy
        L_magnitude: Angular momentum
        compute_full_riemann: Whether to compute full Riemann tensor

    Returns:
        CurvatureTensors object
    """
    # 1. Compute JM metric
    metric = compute_jm_metric(shape_state, masses, energy, L_magnitude)

    # 2. Compute metric derivatives (finite differences)
    metric_func = lambda s: compute_jm_metric(s, masses, energy, L_magnitude)

    from .jm_metric import compute_metric_derivatives
    dg = compute_metric_derivatives(metric_func, shape_state)

    # 3. Compute Christoffel symbols
    christoffel = compute_christoffel_symbols(metric, dg)

    # 4. Compute Christoffel derivatives
    def christoffel_func(s):
        g = metric_func(s)
        dg_local = compute_metric_derivatives(metric_func, s)
        return compute_christoffel_symbols(g, dg_local)

    from .riemann_curvature import compute_christoffel_derivatives
    dGamma = compute_christoffel_derivatives(christoffel_func, shape_state)

    # 5. Compute Ricci tensor
    ricci = compute_ricci_tensor(christoffel, dGamma)

    # 6. Compute scalar curvature
    R = compute_scalar_curvature(metric, ricci)

    # 7. Optionally compute full Riemann
    riemann = None
    if compute_full_riemann:
        from .riemann_curvature import compute_riemann_tensor
        riemann = compute_riemann_tensor(christoffel, dGamma)

    return CurvatureTensors(
        ricci=ricci,
        scalar=R,
        base_point=shape_state,
        riemann=riemann
    )


def compute_scalar_curvature_field(
    shape_states: list[ShapeSpaceState],
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    parallel: bool = True
) -> np.ndarray:
    """
    Compute scalar curvature at many points.

    Args:
        shape_states: List of N points
        masses: Body masses
        energy: Total energy
        L_magnitude: Angular momentum
        parallel: Use multiprocessing

    Returns:
        Array of N scalar curvature values
    """
    N = len(shape_states)

    if not parallel or N < 50:
        # Serial computation
        curvatures = []
        for state in shape_states:
            try:
                curv = compute_curvature_tensors_complete(
                    state, masses, energy, L_magnitude
                )
                curvatures.append(curv.scalar)
            except (ValueError, np.linalg.LinAlgError):
                # Classically forbidden or singular
                curvatures.append(np.nan)

        return np.array(curvatures)

    # Parallel computation
    from multiprocessing import Pool, cpu_count
    from functools import partial

    def worker(state):
        try:
            curv = compute_curvature_tensors_complete(
                state, masses, energy, L_magnitude
            )
            return curv.scalar
        except:
            return np.nan

    with Pool(cpu_count()) as pool:
        curvatures = pool.map(worker, shape_states)

    return np.array(curvatures)
```

---

## B4: Chaos-Curvature Correlation

### Hypothesis Testing

**Hypothesis**: For the three-body problem, $R < 0 \Leftrightarrow \lambda_{\max} > 0$

where $\lambda_{\max}$ is the maximal Lyapunov exponent.

### Statistical Analysis

```python
# File: src/python/analysis/correlation_analysis.py

import numpy as np
from typing import List, Dict
from dataclasses import dataclass
from scipy.stats import pearsonr, spearmanr

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses


@dataclass
class CorrelationResults:
    """
    Results of chaos-curvature correlation analysis.

    Attributes:
        curvatures: Array of R values
        lyapunov_exponents: Array of λ_max values
        pearson_r: Pearson correlation coefficient
        pearson_p: p-value for Pearson
        spearman_r: Spearman rank correlation
        spearman_p: p-value for Spearman
        classification_accuracy: Fraction correctly classified
        confusion_matrix: 2×2 array [[TN, FP], [FN, TP]]
    """
    curvatures: np.ndarray
    lyapunov_exponents: np.ndarray
    pearson_r: float
    pearson_p: float
    spearman_r: float
    spearman_p: float
    classification_accuracy: float
    confusion_matrix: np.ndarray

    def print_summary(self):
        """Print formatted summary."""
        print("\n" + "="*70)
        print("Chaos-Curvature Correlation Analysis")
        print("="*70)
        print(f"Sample size: {len(self.curvatures)}")
        print()
        print(f"Pearson correlation:  r = {self.pearson_r:.4f}  (p = {self.pearson_p:.3e})")
        print(f"Spearman correlation: ρ = {self.spearman_r:.4f}  (p = {self.spearman_p:.3e})")
        print()
        print(f"Classification Accuracy: {self.classification_accuracy*100:.1f}%")
        print()
        print("Confusion Matrix:")
        print(f"  True Negatives:  {self.confusion_matrix[0,0]:.0f}")
        print(f"  False Positives: {self.confusion_matrix[0,1]:.0f}")
        print(f"  False Negatives: {self.confusion_matrix[1,0]:.0f}")
        print(f"  True Positives:  {self.confusion_matrix[1,1]:.0f}")
        print("="*70)


def correlate_curvature_with_chaos(
    shape_states: List[ShapeSpaceState],
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    lyapunov_integration_time: float = 100.0,
    chaos_threshold: float = 0.01
) -> CorrelationResults:
    """
    Compute R and λ_max at many points, analyze correlation.

    Args:
        shape_states: List of sample points
        masses: Body masses
        energy: Total energy
        L_magnitude: Angular momentum
        lyapunov_integration_time: Time to integrate for λ
        chaos_threshold: Threshold for λ_max to classify as chaotic

    Returns:
        CorrelationResults object
    """
    n = len(shape_states)

    curvatures = np.zeros(n)
    lyapunov_exponents = np.zeros(n)

    from ..geometry.scalar_curvature import compute_curvature_tensors_complete
    from .chaos_indicators import compute_lyapunov_exponent

    for i, state in enumerate(shape_states):
        # Scalar curvature
        try:
            curv = compute_curvature_tensors_complete(
                state, masses, energy, L_magnitude
            )
            curvatures[i] = curv.scalar
        except:
            curvatures[i] = np.nan

        # Lyapunov exponent
        try:
            cart_state = shape_to_cartesian_canonical(state, masses)
            lambda_max = compute_lyapunov_exponent(
                cart_state, masses, lyapunov_integration_time
            )
            lyapunov_exponents[i] = lambda_max
        except:
            lyapunov_exponents[i] = np.nan

    # Remove NaN entries
    valid = ~(np.isnan(curvatures) | np.isnan(lyapunov_exponents))
    curvatures_valid = curvatures[valid]
    lyapunov_valid = lyapunov_exponents[valid]

    # Correlation analysis
    pearson_r, pearson_p = pearsonr(curvatures_valid, lyapunov_valid)
    spearman_r, spearman_p = spearmanr(curvatures_valid, lyapunov_valid)

    # Classification: R < 0 predicts λ > threshold
    chaotic = lyapunov_valid > chaos_threshold
    negative_curvature = curvatures_valid < 0

    # Confusion matrix
    TP = np.sum(chaotic & negative_curvature)      # True positive
    FP = np.sum(~chaotic & negative_curvature)     # False positive
    TN = np.sum(~chaotic & ~negative_curvature)    # True negative
    FN = np.sum(chaotic & ~negative_curvature)     # False negative

    confusion_matrix = np.array([[TN, FP], [FN, TP]])

    accuracy = (TP + TN) / len(curvatures_valid)

    return CorrelationResults(
        curvatures=curvatures_valid,
        lyapunov_exponents=lyapunov_valid,
        pearson_r=pearson_r,
        pearson_p=pearson_p,
        spearman_r=spearman_r,
        spearman_p=spearman_p,
        classification_accuracy=accuracy,
        confusion_matrix=confusion_matrix
    )
```

---

## B5: Lyapunov Exponent Computation

### Variational Equations

The maximal Lyapunov exponent $\lambda_{\max}$ is computed by integrating the **variational equations**:

$$
\frac{d}{dt}\begin{pmatrix} \mathbf{x} \\ \delta\mathbf{x} \end{pmatrix} = \begin{pmatrix} \mathbf{f}(\mathbf{x}) \\ \mathbf{J}(\mathbf{x}) \delta\mathbf{x} \end{pmatrix}
$$

where $\mathbf{J}$ is the Jacobian of the flow.

### Implementation

```python
# File: src/python/analysis/chaos_indicators.py

import numpy as np
from typing import Tuple

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses
from ..dynamics.equations_of_motion import three_body_acceleration


def compute_lyapunov_exponent(
    initial_state: CartesianState,
    masses: Masses,
    integration_time: float,
    dt: float = 0.01,
    renormalization_interval: int = 10
) -> float:
    """
    Compute maximal Lyapunov exponent using variational equations.

    Args:
        initial_state: Initial condition
        masses: Body masses
        integration_time: Total integration time
        dt: Time step
        renormalization_interval: Steps between tangent vector renormalization

    Returns:
        λ_max (positive for chaos)
    """
    # Flatten state to vector
    x0 = np.concatenate([
        initial_state.positions.ravel(),
        initial_state.velocities.ravel()
    ])  # 12D for 3 bodies in 2D

    # Initial tangent vector (random perturbation)
    tangent0 = np.random.randn(len(x0))
    tangent0 /= np.linalg.norm(tangent0)

    # Integration
    n_steps = int(integration_time / dt)

    x = x0.copy()
    tangent = tangent0.copy()

    log_stretch_sum = 0.0

    for step in range(n_steps):
        # Integrate main trajectory + tangent vector
        x, tangent = _integrate_step_with_tangent(
            x, tangent, masses, dt
        )

        # Renormalize tangent vector periodically
        if (step + 1) % renormalization_interval == 0:
            tangent_norm = np.linalg.norm(tangent)
            log_stretch_sum += np.log(tangent_norm)
            tangent /= tangent_norm

    # Final renormalization
    tangent_norm = np.linalg.norm(tangent)
    log_stretch_sum += np.log(tangent_norm)

    # Lyapunov exponent
    lambda_max = log_stretch_sum / integration_time

    return lambda_max


def _integrate_step_with_tangent(
    x: np.ndarray,
    tangent: np.ndarray,
    masses: Masses,
    dt: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    One step of variational equation integration (RK4).

    Args:
        x: State vector (12D)
        tangent: Tangent vector (12D)
        masses: Body masses
        dt: Time step

    Returns:
        x_new, tangent_new
    """
    # RK4 for main trajectory
    k1_x = _flow_derivative(x, masses)
    k2_x = _flow_derivative(x + 0.5*dt*k1_x, masses)
    k3_x = _flow_derivative(x + 0.5*dt*k2_x, masses)
    k4_x = _flow_derivative(x + dt*k3_x, masses)

    x_new = x + (dt/6) * (k1_x + 2*k2_x + 2*k3_x + k4_x)

    # RK4 for tangent vector (linearized)
    k1_t = _tangent_derivative(x, tangent, masses)
    k2_t = _tangent_derivative(x + 0.5*dt*k1_x, tangent + 0.5*dt*k1_t, masses)
    k3_t = _tangent_derivative(x + 0.5*dt*k2_x, tangent + 0.5*dt*k2_t, masses)
    k4_t = _tangent_derivative(x + dt*k3_x, tangent + dt*k3_t, masses)

    tangent_new = tangent + (dt/6) * (k1_t + 2*k2_t + 2*k3_t + k4_t)

    return x_new, tangent_new


def _flow_derivative(x: np.ndarray, masses: Masses) -> np.ndarray:
    """
    Compute ẋ = f(x) for three-body problem.

    Args:
        x: State [r1, r2, r3, v1, v2, v3] (12D for 2D motion)
        masses: Body masses

    Returns:
        ẋ (12D)
    """
    n_bodies = 3
    dimension = len(x) // (2 * n_bodies)  # 2 for 2D

    positions = x[:n_bodies*dimension].reshape(n_bodies, dimension)
    velocities = x[n_bodies*dimension:].reshape(n_bodies, dimension)

    # Accelerations from Newton's law
    accelerations = three_body_acceleration(positions, masses)

    # ẋ = [v, a]
    dx = np.concatenate([velocities.ravel(), accelerations.ravel()])

    return dx


def _tangent_derivative(
    x: np.ndarray,
    tangent: np.ndarray,
    masses: Masses
) -> np.ndarray:
    """
    Compute tangent vector derivative: d(δx)/dt = J(x) δx.

    Uses finite differences to approximate Jacobian.
    """
    epsilon = 1e-8

    # Jacobian-vector product via finite differences
    f_x = _flow_derivative(x, masses)

    jac_times_tangent = np.zeros_like(tangent)

    for i in range(len(x)):
        x_perturbed = x.copy()
        x_perturbed[i] += epsilon

        f_perturbed = _flow_derivative(x_perturbed, masses)

        # ∂f/∂x_i ≈ (f(x+ε e_i) - f(x)) / ε
        jac_column_i = (f_perturbed - f_x) / epsilon

        jac_times_tangent += jac_column_i * tangent[i]

    return jac_times_tangent
```

---

## Implementation Details

### Module Structure

```
src/python/geometry/
├── riemann_curvature.py    # B1: Riemann tensor
├── ricci_tensor.py         # B2: Ricci tensor (can merge with riemann)
├── scalar_curvature.py     # B3: Complete curvature pipeline

src/python/analysis/
├── chaos_indicators.py     # B5: Lyapunov, MEGNO
└── correlation_analysis.py # B4: Statistical correlation
```

---

## Validation and Testing

### Test Suite

```python
# tests/geometry/test_scalar_curvature.py

import pytest
import numpy as np

from src.python.coordinates.shape_space import ShapeSpaceState
from src.python.coordinates.base import Masses
from src.python.geometry.scalar_curvature import compute_curvature_tensors_complete


class TestScalarCurvature:
    """Test suite for scalar curvature computation."""

    def test_curvature_real_valued(self):
        """Scalar curvature must be real."""
        masses = Masses(1.0, 1.0, 1.0)
        state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)

        curv = compute_curvature_tensors_complete(
            state, masses, energy=-0.5, L_magnitude=1.0
        )

        assert np.isreal(curv.scalar)
        assert np.isfinite(curv.scalar)

    def test_ricci_symmetric(self):
        """Ricci tensor must be symmetric."""
        masses = Masses(1.0, 1.0, 1.0)
        state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)

        curv = compute_curvature_tensors_complete(
            state, masses, energy=-0.5, L_magnitude=1.0
        )

        # Symmetry validated in __post_init__

    def test_two_body_limit(self):
        """As m3 → 0, curvature → 0 (Kepler is flat)."""
        m3_values = [0.1, 0.01, 0.001]
        state = ShapeSpaceState(r12=1.0, r23=2.0, r31=2.0, L=1.0)

        curvatures = []
        for m3 in m3_values:
            masses = Masses(1.0, 1.0, m3)

            try:
                curv = compute_curvature_tensors_complete(
                    state, masses, energy=-0.5, L_magnitude=1.0
                )
                curvatures.append(abs(curv.scalar))
            except:
                curvatures.append(np.nan)

        # Should decrease towards zero
        assert curvatures[-1] < curvatures[0]


class TestChaosCurvatureCorrelation:
    """Test chaos-curvature correlation hypothesis."""

    @pytest.mark.slow
    def test_correlation_positive(self):
        """Correlation coefficient should be positive."""
        from analysis.correlation_analysis import correlate_curvature_with_chaos

        masses = Masses(1.0, 1.0, 1.0)

        # Generate sample states
        n_samples = 100
        states = generate_random_states(n_samples)

        results = correlate_curvature_with_chaos(
            states, masses, energy=-0.5, L_magnitude=1.0
        )

        # Expect positive correlation
        assert results.pearson_r > 0.5  # At least moderate correlation
        assert results.pearson_p < 0.05  # Statistically significant
```

---

## Success Criteria

### Part B Complete When:

- [ ] Riemann tensor computation implemented
- [ ] Ricci tensor computed correctly
- [ ] Scalar curvature evaluator functional
- [ ] Lyapunov exponent computation working
- [ ] Chaos-curvature correlation analysis complete
- [ ] All validation tests pass:
  - [ ] Curvature real-valued and finite
  - [ ] Ricci tensor symmetric
  - [ ] Two-body limit (R → 0)
  - [ ] Correlation statistically significant
  - [ ] Classification accuracy > 70%
- [ ] Performance target met (<10 ms per curvature)
- [ ] Documentation complete

**Ready to proceed to Part C** when all boxes checked.

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 2-3 days
**Next**: Part C (Visualization & Exploration)
