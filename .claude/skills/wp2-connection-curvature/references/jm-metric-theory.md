# Jacobi-Maupertuis Metric Theory

Mathematical foundations for the Jacobi-Maupertuis metric on shape space.

## Table of Contents

1. [Jacobi's Principle](#jacobis-principle)
2. [JM Metric Definition](#jm-metric-definition)
3. [Christoffel Symbols](#christoffel-symbols)
4. [Riemann Curvature](#riemann-curvature)
5. [Geodesic Equation](#geodesic-equation)
6. [Curvature and Stability](#curvature-and-stability)
7. [Implementation](#implementation)

---

## Jacobi's Principle

### Maupertuis' Principle

For a conservative system with Hamiltonian H = T + V and fixed energy E:

```
δ∫ p · dq = 0
```

Trajectories extremize the action ∫ p·dq at fixed energy.

### Jacobi's Reformulation

Jacobi showed that this is equivalent to:

```
δ∫ √(2(E-V)) ds = 0
```

where ds is the arc length in the kinetic metric g_kin = Σ mᵢ drᵢ².

This means trajectories are **geodesics** of the Jacobi-Maupertuis metric.

---

## JM Metric Definition

### Formula

The Jacobi-Maupertuis metric is a conformal rescaling of the kinetic metric:

```
g_JM = 2(E - V(s)) · g_kin
```

where:
- E = total energy (fixed constant)
- V(s) = potential energy on shape space
- g_kin = kinetic energy metric (mass-weighted Euclidean)

### Explicit Form

For shape space with coordinates s = (r₁₂, r₂₃, r₃₁):

```python
def jm_metric_tensor(shape_point, masses, energy):
    """
    Compute the Jacobi-Maupertuis metric tensor.

    g_JM_ij = 2(E - V(s)) · g_kin_ij

    Returns:
        3×3 symmetric positive-definite matrix (if E > V)
    """
    # Kinetic metric in shape space
    g_kin = compute_kinetic_metric(shape_point, masses)

    # Potential
    V = compute_potential(shape_point, masses)

    # Conformal factor
    Omega = 2 * (energy - V)

    if Omega <= 0:
        raise ValueError(f"E ≤ V: forbidden region (Ω = {Omega})")

    return Omega * g_kin
```

### Kinetic Metric on Shape Space

The kinetic metric induced on shape space from the mass-weighted metric:

```python
def compute_kinetic_metric(shape_point, masses):
    """
    Kinetic metric g_kin on shape space.

    For pairwise distance coordinates (r₁₂, r₂₃, r₃₁), this is
    derived from T = ½ Σ mᵢ |ṙᵢ|² expressed in shape variables.
    """
    r12, r23, r31 = shape_point
    m1, m2, m3 = masses
    M = sum(masses)

    # Reduced masses
    mu12 = m1 * m2 / M
    mu23 = m2 * m3 / M
    mu31 = m3 * m1 / M

    # Metric components (symmetric)
    g = np.zeros((3, 3))
    g[0, 0] = mu12
    g[1, 1] = mu23
    g[2, 2] = mu31

    # Off-diagonal terms from constraint coupling
    # (depends on specific embedding)

    return g
```

### Allowed Region

The JM metric is only defined where E > V(s):

```
Hill region: {s : V(s) < E}
```

At the boundary V(s) = E, the metric degenerates (conformal factor → 0).

---

## Christoffel Symbols

### Definition

The Christoffel symbols (Levi-Civita connection) of the JM metric:

```
Γ^k_ij = ½ g^{kl} (∂_i g_{lj} + ∂_j g_{il} - ∂_l g_{ij})
```

### Conformal Transformation

For a conformal metric g̃ = Ω · g, the Christoffel symbols transform as:

```
Γ̃^k_ij = Γ^k_ij + (1/2Ω)(δ^k_i ∂_j Ω + δ^k_j ∂_i Ω - g_ij g^{kl} ∂_l Ω)
```

### Implementation

```python
def compute_christoffel(shape_point, masses, energy, delta=1e-6):
    """
    Compute Christoffel symbols Γ^k_ij for JM metric.

    Returns:
        (3, 3, 3) array where result[k,i,j] = Γ^k_ij
    """
    g = jm_metric_tensor(shape_point, masses, energy)
    g_inv = np.linalg.inv(g)

    # Compute metric derivatives
    dg = np.zeros((3, 3, 3))  # dg[i,j,k] = ∂g_ij/∂s_k

    for k in range(3):
        sp = shape_point.copy()
        sp[k] += delta
        g_plus = jm_metric_tensor(sp, masses, energy)

        sp[k] -= 2*delta
        g_minus = jm_metric_tensor(sp, masses, energy)

        dg[:, :, k] = (g_plus - g_minus) / (2*delta)

    # Christoffel formula
    Gamma = np.zeros((3, 3, 3))
    for k in range(3):
        for i in range(3):
            for j in range(3):
                for l in range(3):
                    Gamma[k, i, j] += 0.5 * g_inv[k, l] * (
                        dg[l, j, i] + dg[i, l, j] - dg[i, j, l]
                    )

    return Gamma
```

---

## Riemann Curvature

### Riemann Tensor

The Riemann curvature tensor measures the failure of parallel transport to commute:

```
R^l_ijk = ∂_j Γ^l_ik - ∂_k Γ^l_ij + Γ^l_jm Γ^m_ik - Γ^l_km Γ^m_ij
```

### Implementation

```python
def compute_riemann_tensor(shape_point, masses, energy, delta=1e-6):
    """
    Compute Riemann curvature tensor R^l_ijk.

    Returns:
        (3, 3, 3, 3) array
    """
    Gamma = compute_christoffel(shape_point, masses, energy)

    # Compute Γ derivatives
    dGamma = np.zeros((3, 3, 3, 3))  # dGamma[l,i,k,j] = ∂Γ^l_ik/∂s_j

    for j in range(3):
        sp = shape_point.copy()
        sp[j] += delta
        Gamma_plus = compute_christoffel(sp, masses, energy)

        sp[j] -= 2*delta
        Gamma_minus = compute_christoffel(sp, masses, energy)

        dGamma[:, :, :, j] = (Gamma_plus - Gamma_minus) / (2*delta)

    # Riemann formula
    R = np.zeros((3, 3, 3, 3))
    for l in range(3):
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    R[l, i, j, k] = dGamma[l, i, k, j] - dGamma[l, i, j, k]
                    for m in range(3):
                        R[l, i, j, k] += (
                            Gamma[l, j, m] * Gamma[m, i, k] -
                            Gamma[l, k, m] * Gamma[m, i, j]
                        )

    return R
```

### Ricci Tensor

Contraction of Riemann tensor:

```
R_ij = R^k_ikj
```

```python
def compute_ricci_tensor(shape_point, masses, energy):
    """Compute Ricci tensor by contracting Riemann."""
    R_riemann = compute_riemann_tensor(shape_point, masses, energy)

    Ricci = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                Ricci[i, j] += R_riemann[k, i, k, j]

    return Ricci
```

### Scalar Curvature

The scalar curvature is the trace of the Ricci tensor:

```
R = g^ij R_ij
```

```python
def compute_scalar_curvature(shape_point, masses, energy):
    """Compute scalar curvature."""
    g = jm_metric_tensor(shape_point, masses, energy)
    g_inv = np.linalg.inv(g)
    Ricci = compute_ricci_tensor(shape_point, masses, energy)

    R = np.einsum('ij,ij->', g_inv, Ricci)
    return R
```

---

## Geodesic Equation

### Equation

Trajectories are geodesics of the JM metric:

```
d²s^k/dτ² + Γ^k_ij (ds^i/dτ)(ds^j/dτ) = 0
```

where τ is the affine parameter (related to arc length).

### Physical Time

The relationship between affine parameter τ and physical time t:

```
dt/dτ = √(g_ij ṡ^i ṡ^j) / √(2(E-V))
```

### Geodesic Deviation

The Jacobi equation governs the evolution of nearby geodesics:

```
D²J^i/dτ² + R^i_jkl (ds^j/dτ) J^k (ds^l/dτ) = 0
```

where J is the deviation vector.

**Key result**: Negative sectional curvature implies geodesic instability (exponential divergence).

---

## Curvature and Stability

### Sectional Curvature

For a 2-plane spanned by vectors u, v:

```
K(u,v) = R_ijkl u^i v^j u^k v^l / (g_ik g_jl - g_il g_jk) u^i v^j u^k v^l
```

### Stability Criterion

| Curvature | Geodesic Behavior | Dynamics |
|-----------|-------------------|----------|
| K > 0 (positive) | Oscillating deviation | Stable, regular |
| K = 0 (flat) | Linear deviation | Marginally stable |
| K < 0 (negative) | Exponential divergence | Unstable, chaotic |

### Scalar Curvature as Indicator

For 3D manifolds, scalar curvature R gives an average over all sectional curvatures:

```
R = 2(K₁₂ + K₂₃ + K₃₁)
```

**Hypothesis**: R < 0 indicates prevalence of unstable directions → chaos expected.

---

## Implementation

### Complete JM Metric Class

```python
class JacobiMaupertuisMetric:
    """Complete Jacobi-Maupertuis metric implementation."""

    def __init__(self, masses, energy):
        self.masses = masses
        self.energy = energy

    def metric_tensor(self, shape_point):
        """Compute g_JM at shape point."""
        g_kin = self._kinetic_metric(shape_point)
        V = self._potential(shape_point)
        Omega = 2 * (self.energy - V)

        if Omega <= 0:
            return None  # Forbidden region

        return Omega * g_kin

    def inverse_metric(self, shape_point):
        """Compute g^{-1}_JM."""
        g = self.metric_tensor(shape_point)
        return np.linalg.inv(g) if g is not None else None

    def christoffel_symbols(self, shape_point):
        """Compute Γ^k_ij."""
        # Implementation as above
        pass

    def riemann_tensor(self, shape_point):
        """Compute R^l_ijk."""
        # Implementation as above
        pass

    def ricci_tensor(self, shape_point):
        """Compute R_ij."""
        R = self.riemann_tensor(shape_point)
        return np.einsum('kikj->ij', R)

    def scalar_curvature(self, shape_point):
        """Compute scalar curvature R."""
        g_inv = self.inverse_metric(shape_point)
        Ricci = self.ricci_tensor(shape_point)
        return np.einsum('ij,ij->', g_inv, Ricci)

    def sectional_curvature(self, shape_point, u, v):
        """Compute sectional curvature for plane (u, v)."""
        g = self.metric_tensor(shape_point)
        R = self.riemann_tensor(shape_point)

        # Numerator: R_ijkl u^i v^j u^k v^l
        R_lower = np.einsum('lijk,lm->ijkm', R, g)  # Lower first index
        num = np.einsum('ijkl,i,j,k,l->', R_lower, u, v, u, v)

        # Denominator: (g_ik g_jl - g_il g_jk) u^i v^j u^k v^l
        term1 = np.einsum('ik,jl,i,j,k,l->', g, g, u, v, u, v)
        term2 = np.einsum('il,jk,i,j,k,l->', g, g, u, v, u, v)
        denom = term1 - term2

        return num / denom if abs(denom) > 1e-10 else np.nan

    def _kinetic_metric(self, shape_point):
        """Compute kinetic metric g_kin."""
        # Implementation depends on coordinate choice
        pass

    def _potential(self, shape_point):
        """Compute gravitational potential V(s)."""
        r12, r23, r31 = shape_point
        m1, m2, m3 = self.masses

        # Newtonian potential
        return -(m1*m2/r12 + m2*m3/r23 + m3*m1/r31)
```

---

## References

- Jacobi, C.G.J. (1884). *Vorlesungen über Dynamik*
- Arnold, V.I. (1989). *Mathematical Methods of Classical Mechanics*
- Knauf, A. (2018). *Mathematical Physics: Classical Mechanics*
- `Science-Research-Docs/WP1 – Foundations.pdf`
