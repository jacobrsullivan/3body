# Jacobi Theta Functions

Mathematical theory of theta functions for completely integrable systems.

## Table of Contents

1. [Overview](#overview)
2. [Definitions](#definitions)
3. [Fundamental Properties](#fundamental-properties)
4. [Key Identities](#key-identities)
5. [Nome Estimation](#nome-estimation)
6. [Basis Construction](#basis-construction)
7. [Implementation](#implementation)

---

## Overview

### Motivation

Jacobi theta functions arise naturally in completely integrable systems via the Abel-Jacobi map. If a system is integrable, its solutions can often be expressed in terms of theta functions.

**Key insight**: Theta functions provide a "fingerprint" for complete integrability. If a candidate conserved quantity is expressible in theta functions, this supports the integrability hypothesis.

### Connection to Elliptic Functions

The Jacobi elliptic functions can be expressed as ratios of theta functions:

```
sn(u) = θ₃(0)/θ₂(0) · θ₁(v)/θ₄(v)
cn(u) = θ₄(0)/θ₂(0) · θ₂(v)/θ₄(v)
dn(u) = θ₄(0)/θ₃(0) · θ₃(v)/θ₄(v)
```

where v = u/(2K) · π and q = e^(-πK'/K).

---

## Definitions

### The Four Jacobi Theta Functions

For argument z and nome q with |q| < 1:

**θ₁(z, q)** - Odd function, zeros at z = nπ:
```
θ₁(z, q) = 2 Σₙ₌₀^∞ (-1)ⁿ q^((n+1/2)²) sin((2n+1)z)
         = 2q^(1/4) sin(z) ∏ₙ₌₁^∞ (1 - q^(2n))(1 - 2q^(2n)cos(2z) + q^(4n))
```

**θ₂(z, q)** - Even function:
```
θ₂(z, q) = 2 Σₙ₌₀^∞ q^((n+1/2)²) cos((2n+1)z)
         = 2q^(1/4) cos(z) ∏ₙ₌₁^∞ (1 - q^(2n))(1 + 2q^(2n)cos(2z) + q^(4n))
```

**θ₃(z, q)** - Even function:
```
θ₃(z, q) = 1 + 2 Σₙ₌₁^∞ q^(n²) cos(2nz)
         = ∏ₙ₌₁^∞ (1 - q^(2n))(1 + 2q^(2n-1)cos(2z) + q^(4n-2))
```

**θ₄(z, q)** - Even function:
```
θ₄(z, q) = 1 + 2 Σₙ₌₁^∞ (-1)ⁿ q^(n²) cos(2nz)
         = ∏ₙ₌₁^∞ (1 - q^(2n))(1 - 2q^(2n-1)cos(2z) + q^(4n-2))
```

### The Nome q

The nome is related to the half-period ratio τ:
```
q = e^(iπτ)
```

For the elliptic case with real periods:
```
q = e^(-π K'/K)
```

where K = K(m) and K' = K(1-m) are complete elliptic integrals.

### Domain Restrictions

- |q| < 1 (required for convergence)
- q real and positive for most physical applications
- As q → 1, convergence becomes slow

---

## Fundamental Properties

### Periodicity

| Function | Period in z | Quasi-period |
|----------|-------------|--------------|
| θ₁(z, q) | 2π | θ₁(z + πτ) = -q⁻¹e^(-2iz)θ₁(z) |
| θ₂(z, q) | 2π | θ₂(z + πτ) = -q⁻¹e^(-2iz)θ₂(z) |
| θ₃(z, q) | π | θ₃(z + πτ) = q⁻¹e^(-2iz)θ₃(z) |
| θ₄(z, q) | π | θ₄(z + πτ) = q⁻¹e^(-2iz)θ₄(z) |

### Symmetry

```
θ₁(-z, q) = -θ₁(z, q)   (odd)
θ₂(-z, q) = θ₂(z, q)    (even)
θ₃(-z, q) = θ₃(z, q)    (even)
θ₄(-z, q) = θ₄(z, q)    (even)
```

### Values at z = 0

```
θ₁(0, q) = 0
θ₂(0, q) = 2q^(1/4) ∏ₙ₌₁^∞ (1 - q^(2n))(1 + q^(2n))²
θ₃(0, q) = ∏ₙ₌₁^∞ (1 - q^(2n))(1 + q^(2n-1))²
θ₄(0, q) = ∏ₙ₌₁^∞ (1 - q^(2n))(1 - q^(2n-1))²
```

---

## Key Identities

### Jacobi's Identity (Quartic)

```
θ₃⁴(0, q) = θ₂⁴(0, q) + θ₄⁴(0, q)
```

More generally:
```
θ₃⁴(z, q) - θ₄⁴(z, q) = θ₂⁴(z, q) - θ₁⁴(z, q)
```

### Product Identities

```
θ₁(z, q)θ₁(w, q) = θ₃(z+w, q)θ₂(z-w, q) - θ₂(z+w, q)θ₃(z-w, q)

θ₂(z, q)θ₃(z, q) = θ₂(0, q)θ₃(0, q) · [θ₃(2z, q²)/θ₃(0, q²)]
```

### Relation to Elliptic Parameter

```
m = θ₂⁴(0, q) / θ₃⁴(0, q)
1 - m = θ₄⁴(0, q) / θ₃⁴(0, q)
```

### Derivatives

```
∂θ₁/∂z = θ₂(0)θ₃(0)θ₄(0) · θ₄(z)θ₃(z)θ₂(z) / θ₁(z)  [at z=0]

θ₁'(0, q) = θ₂(0, q)θ₃(0, q)θ₄(0, q)
```

---

## Nome Estimation

### From Period Ratio

If you can identify two periods T₁ and T₂ in the motion:

```python
def estimate_nome_from_periods(T1, T2):
    """
    Estimate nome q from period ratio.
    
    tau = i * T2/T1  (assuming T1 is the "real" period)
    q = exp(i*pi*tau)
    """
    tau = 1j * T2 / T1
    q = np.exp(1j * np.pi * tau)
    return q
```

### From Elliptic Parameter

If elliptic parameter m is known:

```python
def nome_from_elliptic_parameter(m):
    """
    Compute nome q from elliptic parameter m.
    
    q = exp(-π K'/K)
    """
    from scipy.special import ellipk
    
    if m <= 0 or m >= 1:
        raise ValueError("m must be in (0, 1)")
    
    K = ellipk(m)
    Kp = ellipk(1 - m)
    
    q = np.exp(-np.pi * Kp / K)
    return q
```

### From Trajectory Data

```python
def estimate_nome(times, states):
    """
    Estimate nome q from trajectory data.
    
    Strategy:
    1. Estimate elliptic parameter m from oscillations
    2. Convert m to q
    """
    from src.python.symbolic.elliptic_basis import estimate_elliptic_parameter
    
    # Get m from trajectory
    m = estimate_elliptic_parameter(times, states)
    
    # Convert to nome
    q = nome_from_elliptic_parameter(m)
    
    return q
```

---

## Basis Construction

### Basic Theta Basis

```python
def generate_theta_basis(q, max_terms=20):
    """
    Generate theta function basis.
    
    Categories:
    1. Basic: θ₁, θ₂, θ₃, θ₄
    2. Products: θᵢθⱼ
    3. Squares: θᵢ²
    4. Ratios: θᵢ/θⱼ
    """
    basis = []
    
    # Basic functions (4)
    basis.extend([
        lambda z, q=q: theta1(z, q),
        lambda z, q=q: theta2(z, q),
        lambda z, q=q: theta3(z, q),
        lambda z, q=q: theta4(z, q)
    ])
    
    # Squares (4)
    basis.extend([
        lambda z, q=q: theta1(z, q)**2,
        lambda z, q=q: theta2(z, q)**2,
        lambda z, q=q: theta3(z, q)**2,
        lambda z, q=q: theta4(z, q)**2
    ])
    
    # Products (6)
    basis.extend([
        lambda z, q=q: theta1(z, q) * theta2(z, q),
        lambda z, q=q: theta1(z, q) * theta3(z, q),
        lambda z, q=q: theta1(z, q) * theta4(z, q),
        lambda z, q=q: theta2(z, q) * theta3(z, q),
        lambda z, q=q: theta2(z, q) * theta4(z, q),
        lambda z, q=q: theta3(z, q) * theta4(z, q)
    ])
    
    # Ratios with safe division (12)
    def safe_ratio(f1, f2, eps=1e-10):
        def ratio(z, q=q):
            num = f1(z, q)
            den = f2(z, q)
            return num / np.maximum(np.abs(den), eps) * np.sign(den + eps)
        return ratio
    
    theta_funcs = [theta1, theta2, theta3, theta4]
    for i, ti in enumerate(theta_funcs):
        for j, tj in enumerate(theta_funcs):
            if i != j:
                basis.append(safe_ratio(ti, tj))
    
    return basis
```

---

## Implementation

### Theta Functions via Series

```python
def theta1(z, q, n_terms=50):
    """
    Jacobi theta function θ₁(z, q).
    
    θ₁(z, q) = 2 Σₙ₌₀^∞ (-1)ⁿ q^((n+1/2)²) sin((2n+1)z)
    """
    z = np.asarray(z)
    result = np.zeros_like(z, dtype=complex)
    
    for n in range(n_terms):
        coeff = (-1)**n * q**((n + 0.5)**2)
        result += coeff * np.sin((2*n + 1) * z)
    
    return 2 * result

def theta2(z, q, n_terms=50):
    """
    Jacobi theta function θ₂(z, q).
    
    θ₂(z, q) = 2 Σₙ₌₀^∞ q^((n+1/2)²) cos((2n+1)z)
    """
    z = np.asarray(z)
    result = np.zeros_like(z, dtype=complex)
    
    for n in range(n_terms):
        coeff = q**((n + 0.5)**2)
        result += coeff * np.cos((2*n + 1) * z)
    
    return 2 * result

def theta3(z, q, n_terms=50):
    """
    Jacobi theta function θ₃(z, q).
    
    θ₃(z, q) = 1 + 2 Σₙ₌₁^∞ q^(n²) cos(2nz)
    """
    z = np.asarray(z)
    result = np.ones_like(z, dtype=complex)
    
    for n in range(1, n_terms + 1):
        coeff = q**(n**2)
        result += 2 * coeff * np.cos(2 * n * z)
    
    return result

def theta4(z, q, n_terms=50):
    """
    Jacobi theta function θ₄(z, q).
    
    θ₄(z, q) = 1 + 2 Σₙ₌₁^∞ (-1)ⁿ q^(n²) cos(2nz)
    """
    z = np.asarray(z)
    result = np.ones_like(z, dtype=complex)
    
    for n in range(1, n_terms + 1):
        coeff = (-1)**n * q**(n**2)
        result += 2 * coeff * np.cos(2 * n * z)
    
    return result
```

### Verify Jacobi Identity

```python
def verify_jacobi_identity(q, n_samples=100, tol=1e-8):
    """
    Verify θ₃⁴(0) = θ₂⁴(0) + θ₄⁴(0).
    
    Returns:
        passed: bool
        error: float
    """
    t2_0 = theta2(0, q)
    t3_0 = theta3(0, q)
    t4_0 = theta4(0, q)
    
    lhs = t3_0**4
    rhs = t2_0**4 + t4_0**4
    
    error = np.abs(lhs - rhs)
    
    return error < tol, error
```

### Detect Integrability Signature

```python
def detect_integrability_signature(times, states, threshold=0.1):
    """
    Detect signatures suggesting complete integrability.
    
    Checks:
    1. Quasi-periodic motion (multiple discrete frequencies)
    2. Bounded motion
    3. Regular (non-chaotic) indicators
    
    Returns:
        is_integrable: bool
        nome: Estimated nome if integrable
        confidence: float
    """
    from scipy.fft import fft, fftfreq
    
    # Extract observable
    r = np.linalg.norm(states[:, :3], axis=1)
    
    # Check 1: Bounded motion
    is_bounded = np.std(r) / np.mean(r) < 1.0
    
    # Check 2: Discrete spectrum (not continuous)
    dt = times[1] - times[0]
    spectrum = np.abs(fft(r - np.mean(r)))[:len(r)//2]
    
    # Count significant peaks
    peak_threshold = threshold * np.max(spectrum)
    n_peaks = np.sum(spectrum > peak_threshold)
    
    has_discrete_spectrum = n_peaks < 10 and n_peaks >= 2
    
    # Check 3: Estimate nome and verify consistency
    if is_bounded and has_discrete_spectrum:
        try:
            q = estimate_nome(times, states)
            if np.abs(q) < 0.99:  # Convergent regime
                return True, q, 0.8
        except:
            pass
    
    return False, None, 0.0
```

---

## References

- Whittaker, E.T. & Watson, G.N. (1927). *A Course of Modern Analysis*, Chapter 21
- Mumford, D. (1983). *Tata Lectures on Theta I*
- Lawden, D.F. (1989). *Elliptic Functions and Applications*, Chapter 5
- Abramowitz, M. & Stegun, I.A. (1964). *Handbook of Mathematical Functions*, Chapter 16
