# Chaos Indicator Theory

Mathematical foundations for MEGNO, FLI, OFLI, and SALI chaos indicators.

## Table of Contents

1. [Variational Equations Foundation](#variational-equations-foundation)
2. [MEGNO Theory](#megno-theory)
3. [FLI Theory](#fli-theory)
4. [OFLI Theory](#ofli-theory)
5. [SALI Theory](#sali-theory)
6. [Indicator Relationships](#indicator-relationships)
7. [Connection to Differential Galois Theory](#connection-to-differential-galois-theory)

---

## Variational Equations Foundation

All chaos indicators are based on the **variational equations** (also called tangent map equations), which describe the evolution of infinitesimal perturbations.

### Definition

For a dynamical system ẋ = f(x), the variational equations along a reference trajectory x(t) are:

```
δẋ = Df(x(t)) · δx
```

where Df is the Jacobian matrix of f.

### For CR3BP

The CR3BP Hamiltonian in the rotating frame:

```
H = ½(ṗx² + ṗy² + ṗz²) - Ω(x, y, z)

Ω = ½(x² + y²) + (1-μ)/r₁ + μ/r₂ + μ(1-μ)/2
```

The variational equations form a 12-dimensional system (6 state + 6 perturbation):

```
d/dt [x]   = [    f(x)    ]
     [δx]    [Df(x(t))·δx]
```

### Lyapunov Exponent

The maximal Lyapunov exponent (MLE) measures the average exponential rate of divergence:

```
λ = lim(t→∞) (1/t) ln(|δx(t)|/|δx(0)|)
```

- λ > 0 → Chaotic (exponential divergence)
- λ = 0 → Regular (bounded or polynomial growth)
- λ < 0 → Asymptotically stable (convergence)

---

## MEGNO Theory

**Mean Exponential Growth factor of Nearby Orbits** (Cincotta & Simó, 2000)

### Definition

The instantaneous MEGNO is:

```
Y(t) = (2/t) ∫₀ᵗ (ẏ(s)/y(s)) · s ds
```

where y(t) = |δx(t)| is the norm of the deviation vector.

The time-averaged MEGNO is:

```
⟨Y⟩(t) = (1/t) ∫₀ᵗ Y(s) ds
```

### Asymptotic Behavior

| Motion Type | ⟨Y⟩(t→∞) | Y(t) Behavior |
|-------------|----------|---------------|
| Stable periodic | → 0 | Oscillates → 0 |
| Quasi-periodic (regular) | → 2 | Oscillates around 2 |
| Chaotic | → ∞ linearly | ⟨Y⟩ ≈ λt/2 |
| Unstable periodic | → 0 | Oscillates → 0 |

### Physical Interpretation

- **⟨Y⟩ → 2**: The deviation vector grows at most polynomially (t^α for some α), characteristic of motion on invariant tori
- **⟨Y⟩ → ∞**: Exponential growth, characteristic of positive Lyapunov exponent

### Numerical Implementation

```python
def compute_megno(times, deviation_norms):
    """
    Compute MEGNO from deviation vector history.
    
    Parameters:
        times: array of time values
        deviation_norms: array of |δx(t)| values
    
    Returns:
        megno: time-averaged MEGNO value
    """
    y = deviation_norms
    y_dot = np.gradient(y, times)
    
    # Instantaneous MEGNO integrand
    integrand = (y_dot / y) * times
    
    # Y(t) = (2/t) * integral
    Y = 2.0 * cumulative_trapezoid(integrand, times, initial=0) / times
    Y[0] = 0  # Handle t=0
    
    # Time-averaged MEGNO
    megno_avg = cumulative_trapezoid(Y, times, initial=0) / times
    
    return megno_avg[-1]
```

### Thresholds (Empirical)

| ⟨Y⟩ Value | Classification | Confidence |
|-----------|----------------|------------|
| < 2.0 | Regular (stable periodic) | High |
| 2.0 - 2.5 | Regular (quasi-periodic) | High |
| 2.5 - 3.0 | Borderline | Medium - extend integration |
| 3.0 - 5.0 | Weakly chaotic | High |
| > 5.0 | Strongly chaotic | Very high |

---

## FLI Theory

**Fast Lyapunov Indicator** (Froeschlé et al., 1997)

### Definition

The FLI tracks the logarithmic growth of the deviation vector:

```
FLI(t) = sup_{0≤s≤t} ln(|δx(s)|/|δx(0)|)
```

In practice, implemented as:

```
FLI(t) = ln(|δx(t)|/|δx(0)|)
```

### Asymptotic Behavior

| Motion Type | FLI(t→∞) | Growth Rate |
|-------------|----------|-------------|
| Regular | ~ ln(t) | Logarithmic |
| Chaotic | ~ λt | Linear |

### Physical Interpretation

- **Logarithmic growth**: Polynomial divergence of nearby orbits (regular)
- **Linear growth**: Exponential divergence (chaotic)

### Advantages

1. **Speed**: Requires shorter integration than MEGNO
2. **Simplicity**: Single scalar tracking
3. **Robustness**: Less sensitive to initial deviation direction

### Disadvantages

1. **Less precise** for borderline cases
2. **Cannot distinguish** stable periodic from quasi-periodic
3. **Threshold sensitivity**: Fixed thresholds may not apply universally

### Thresholds (Empirical, t = 50 periods)

| FLI Value | Classification | Notes |
|-----------|----------------|-------|
| < 3.0 | Regular | High confidence |
| 3.0 - 4.0 | Uncertain | Use MEGNO for confirmation |
| > 4.0 | Chaotic | High confidence |

---

## OFLI Theory

**Orthogonal Fast Lyapunov Indicator** (Fouchard et al., 2002)

### Definition

OFLI uses the component of the deviation vector orthogonal to the flow:

```
δx_⊥ = δx - (δx · f̂) f̂
```

where f̂ = f/|f| is the unit tangent to the flow.

```
OFLI(t) = ln(|δx_⊥(t)|/|δx_⊥(0)|)
```

### Advantages over FLI

1. **Removes secular growth** along the orbit direction
2. **Better for detecting chaos** in systems with strong shear
3. **Isotropic**: Less dependent on initial deviation direction

### When to Use

- Systems with significant rotational motion
- When FLI gives ambiguous results
- For mapping chaos in configuration space

---

## SALI Theory

**Smaller Alignment Index** (Skokos, 2001)

### Definition

SALI uses two deviation vectors δx₁ and δx₂ with different initial directions:

```
SALI(t) = min(|δ̂x₁ + δ̂x₂|, |δ̂x₁ - δ̂x₂|)
```

where δ̂x = δx/|δx| are normalized deviation vectors.

### Asymptotic Behavior

| Motion Type | SALI(t→∞) | Rate |
|-------------|-----------|------|
| Regular | → constant ≠ 0 | Algebraic decay |
| Chaotic | → 0 | Exponential decay |

### Physical Interpretation

- **Regular motion**: Deviation vectors maintain distinct directions (SALI stays finite)
- **Chaotic motion**: Both vectors align with the most unstable direction (SALI → 0)

### Advantages

1. **Distinguishes weak chaos** from strong chaos
2. **More sensitive** than FLI for weak instabilities
3. **Quantifies alignment** of Lyapunov directions

### Disadvantages

1. **Computationally expensive**: Requires two deviation vectors
2. **Slower convergence**: Needs longer integration times
3. **More complex** to interpret intermediate values

---

## Indicator Relationships

### MEGNO-FLI Relationship

**Mestre et al. (2011)** proved:

```
⟨Y⟩(t) = 2 × (FLI(t) - ⟨FLI⟩(t))
```

where ⟨FLI⟩ is the time average of FLI.

### Implications

1. For **regular orbits**: FLI ~ ln(t), ⟨FLI⟩ ~ ln(t), so ⟨Y⟩ → 2
2. For **chaotic orbits**: FLI ~ λt, ⟨FLI⟩ ~ λt/2, so ⟨Y⟩ ~ λt

### Comparison Summary

| Indicator | Computation Cost | Precision | Best Use Case |
|-----------|-----------------|-----------|---------------|
| FLI | Low | Medium | Quick screening |
| MEGNO | Medium | High | Final classification |
| OFLI | Medium | Medium | Rotational systems |
| SALI | High | High | Weak chaos detection |

### Decision Matrix

```
                    ┌─────────────────┐
                    │ Quick screening │
                    │    needed?      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │ YES          │ NO           │
              ▼              │              ▼
         ┌────────┐          │         ┌────────┐
         │ Use FLI│          │         │ Use    │
         └────┬───┘          │         │ MEGNO  │
              │              │         └────┬───┘
              │              │              │
         FLI uncertain?      │              │
         (3.0-4.0)           │              │
              │              │              │
              └──────────────┼──────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Weak chaos      │
                    │ suspected?      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │ YES          │ NO           │
              ▼              │              ▼
         ┌────────┐          │         ┌────────┐
         │Use SALI│          │         │ Done   │
         └────────┘          │         └────────┘
```

---

## Connection to Differential Galois Theory

The chaos indicators connect directly to the **Morales-Ramis theorem** used in WP4.

### Variational Equations and Galois Groups

The variational equations along a particular solution form a **linear ODE system**:

```
δẋ = A(t) · δx
```

This system has an associated **Differential Galois Group (DGG)** - the group of differential automorphisms preserving the solution structure.

### Morales-Ramis Theorem

**If a Hamiltonian system is Liouville integrable, then the identity component of the DGG of its variational equations (along any particular solution) is abelian.**

### Monodromy Matrix

For a **periodic orbit** with period T, the monodromy matrix M is:

```
M = Φ(T)
```

where Φ(t) is the fundamental matrix solution of the variational equations.

### Floquet Multipliers

The **Floquet multipliers** are eigenvalues of M. They determine:

1. **Orbital stability**: |λᵢ| < 1 → stable, |λᵢ| > 1 → unstable
2. **DGG structure**: If multipliers are resonant, DGG may have non-trivial structure

### Connection to Chaos

| Chaos Classification | Floquet Behavior | DGG Implication |
|---------------------|------------------|-----------------|
| Regular | Multipliers on unit circle | May be abelian |
| Chaotic | Multipliers off unit circle | Likely non-abelian |

### WP4 Integration

1. **Chaos analysis** (this skill) computes monodromy matrices for periodic orbits
2. **WP4 Phase I** verifies the DGG is non-abelian (confirms non-integrability downstairs)
3. **WP4 Phase II** checks if DGG becomes abelian in lifted space (validates lift-integrability)

---

## References

1. Cincotta, P. M., & Simó, C. (2000). Simple tools to study global dynamics in non-axisymmetric galactic potentials. *Astronomy & Astrophysics Supplement Series*, 147(2), 205-228.

2. Froeschlé, C., Lega, E., & Gonczi, R. (1997). Fast Lyapunov indicators. *Celestial Mechanics and Dynamical Astronomy*, 67(1), 41-62.

3. Fouchard, M., Lega, E., Froeschlé, C., & Froeschlé, C. (2002). On the relationship between fast Lyapunov indicator and periodic orbits for continuous flows. *Celestial Mechanics and Dynamical Astronomy*, 83(1), 205-222.

4. Skokos, C. (2001). Alignment indices: a new, simple method for determining the ordered or chaotic nature of orbits. *Journal of Physics A: Mathematical and General*, 34(47), 10029.

5. Mestre, M. F., Cincotta, P. M., & Giordano, C. M. (2011). Analytical relation between two chaos indicators: FLI and MEGNO. *Monthly Notices of the Royal Astronomical Society*, 414(1), L100-L103.

6. Morales-Ruiz, J. J., & Ramis, J. P. (2001). Galoisian obstructions to integrability of Hamiltonian systems. *Methods and Applications of Analysis*, 8(1), 33-96.
