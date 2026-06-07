# Jacobi Elliptic Functions

Mathematical theory of Jacobi elliptic functions for invariant discovery.

## Table of Contents

1. [Overview](#overview)
2. [Definitions](#definitions)
3. [Fundamental Identities](#fundamental-identities)
4. [Parameter Estimation](#parameter-estimation)
5. [Quasi-Periodic Detection](#quasi-periodic-detection)
6. [Basis Construction](#basis-construction)
7. [Implementation](#implementation)

---

## Overview

### Motivation

Quasi-periodic motion appears naturally in celestial mechanics when a system has two (or more) incommensurable frequencies. Jacobi elliptic functions are the natural language for such motion.

**Key insight**: If a trajectory shows quasi-periodic structure, conserved quantities may be expressible in terms of elliptic functions.

### Physical Interpretation

| System | Motion Type | Elliptic Description |
|--------|-------------|---------------------|
| Kepler problem | Elliptical orbit | sn(u,m) parameterizes eccentric anomaly |
| Pendulum | Oscillation | cn(u,m) gives position |
| 3-body near resonance | Quasi-periodic | Mixed sn, cn, dn |

---

## Definitions

### The Three Jacobi Elliptic Functions

Starting from the incomplete elliptic integral of the first kind:
```
u = F(φ, m) = ∫₀^φ dθ / √(1 - m·sin²θ)
```

The Jacobi elliptic functions are:
```
sn(u, m) = sin(φ)    (sine amplitude)
cn(u, m) = cos(φ)    (cosine amplitude)
dn(u, m) = √(1 - m·sin²φ)    (delta amplitude)
```

### The Elliptic Parameter m

- m ∈ [0, 1] is the **elliptic parameter** (modulus squared)
- Sometimes written as k² where k is the modulus
- Also expressed via nome: q = exp(-π K'/K)

### Complete Elliptic Integrals

```
K(m) = F(π/2, m) = ∫₀^(π/2) dθ / √(1 - m·sin²θ)    (first kind)
E(m) = ∫₀^(π/2) √(1 - m·sin²θ) dθ                   (second kind)
K'(m) = K(1-m)                                       (complementary)
```

---

## Fundamental Identities

### Pythagorean-Type Identities

```
sn²(u, m) + cn²(u, m) = 1           (fundamental)
dn²(u, m) + m·sn²(u, m) = 1         (m-dependent)
dn²(u, m) - m·cn²(u, m) = 1 - m     (consequence)
```

### Periodicity

| Function | Period in u |
|----------|-------------|
| sn(u, m) | 4K(m) |
| cn(u, m) | 4K(m) |
| dn(u, m) | 2K(m) |

### Limiting Cases

**As m → 0** (circular limit):
```
sn(u, 0) = sin(u)
cn(u, 0) = cos(u)
dn(u, 0) = 1
```

**As m → 1** (hyperbolic/separatrix limit):
```
sn(u, 1) = tanh(u)
cn(u, 1) = sech(u)
dn(u, 1) = sech(u)
```

### Derivatives

```
d/du sn(u) = cn(u)·dn(u)
d/du cn(u) = -sn(u)·dn(u)
d/du dn(u) = -m·sn(u)·cn(u)
```

### Addition Formulas

```
sn(u+v) = [sn(u)cn(v)dn(v) + sn(v)cn(u)dn(u)] / [1 - m·sn²(u)sn²(v)]
cn(u+v) = [cn(u)cn(v) - sn(u)dn(u)sn(v)dn(v)] / [1 - m·sn²(u)sn²(v)]
```

---

## Parameter Estimation

### From Trajectory Oscillations

Given a time series of radial distance r(t):

1. **Find extrema**: r_min, r_max
2. **Compute eccentricity-like ratio**:
   ```
   e_eff = (r_max - r_min) / (r_max + r_min)
   ```
3. **Estimate m**:
   ```
   m ≈ 16·e_eff²·(1 + O(e_eff²))
   ```

For higher accuracy, use the period ratio:
```
m from K(m)/K'(m) = T_1/T_2 (ratio of periods)
```

### Algorithm

```python
def estimate_elliptic_parameter(times, states):
    """
    Estimate elliptic parameter m from trajectory data.

    Uses FFT to find dominant frequencies, then fits m.
    """
    from scipy.fft import fft, fftfreq
    from scipy.optimize import minimize_scalar

    # Extract radial distance
    r = np.linalg.norm(states[:, :3], axis=1)

    # Find dominant frequencies via FFT
    dt = times[1] - times[0]
    freqs = fftfreq(len(r), dt)
    spectrum = np.abs(fft(r - np.mean(r)))

    # Get top 2 positive frequencies
    pos_mask = freqs > 0
    pos_freqs = freqs[pos_mask]
    pos_spectrum = spectrum[pos_mask]

    sorted_idx = np.argsort(pos_spectrum)[::-1]
    f1 = pos_freqs[sorted_idx[0]]
    f2 = pos_freqs[sorted_idx[1]] if len(sorted_idx) > 1 else f1/2

    # Period ratio
    T1, T2 = 1/f1, 1/f2
    ratio = T1 / T2 if T1 > T2 else T2 / T1

    # Fit m from K(m)/K'(m) = ratio
    from scipy.special import ellipk

    def objective(m):
        if m <= 0 or m >= 1:
            return 1e10
        K = ellipk(m)
        Kp = ellipk(1 - m)
        return (K / Kp - ratio)**2

    result = minimize_scalar(objective, bounds=(0.01, 0.99), method='bounded')
    return result.x
```

---

## Quasi-Periodic Detection

### FFT-Based Detection

A trajectory is quasi-periodic if:
1. Power spectrum shows discrete peaks (not continuous)
2. At least 2 peaks with incommensurable frequencies
3. Frequency ratio is not a simple rational (p/q with small p, q)

```python
def detect_quasi_periodic(times, states, freq_threshold=0.1):
    """
    Detect quasi-periodic motion via FFT analysis.

    Returns:
        is_quasi_periodic: bool
        frequencies: List of dominant frequencies
        frequency_ratio: Ratio of top 2 frequencies
    """
    from scipy.fft import fft, fftfreq

    # Use radial distance as proxy
    r = np.linalg.norm(states[:, :3], axis=1)
    r_centered = r - np.mean(r)

    dt = times[1] - times[0]
    n = len(r)

    # FFT
    spectrum = np.abs(fft(r_centered))[:n//2]
    freqs = fftfreq(n, dt)[:n//2]

    # Find peaks above threshold
    threshold = freq_threshold * np.max(spectrum)
    peaks = []
    for i in range(1, len(spectrum) - 1):
        if spectrum[i] > threshold:
            if spectrum[i] > spectrum[i-1] and spectrum[i] > spectrum[i+1]:
                peaks.append((freqs[i], spectrum[i]))

    if len(peaks) < 2:
        return False, [], None

    # Sort by amplitude
    peaks.sort(key=lambda x: -x[1])
    f1, f2 = peaks[0][0], peaks[1][0]

    # Check if ratio is irrational-like
    ratio = max(f1, f2) / min(f1, f2)

    # Test against simple rationals
    is_rational = False
    for p in range(1, 10):
        for q in range(1, 10):
            if abs(ratio - p/q) < 0.01:
                is_rational = True
                break

    return not is_rational, [f1, f2], ratio
```

---

## Basis Construction

### Basic Elliptic Basis

```python
def generate_elliptic_basis(m, variables=['r']):
    """
    Generate elliptic function basis with parameter m.

    Categories:
    1. Basic: sn, cn, dn
    2. Products: sn*cn, sn*dn, cn*dn
    3. Powers: sn², cn², dn², ...
    4. Ratios: sn/cn, cn/dn, ...
    """
    from scipy.special import ellipj

    basis = []

    # Helper to evaluate Jacobi functions
    def make_sn(m):
        return lambda r: ellipj(r, m)[0]
    def make_cn(m):
        return lambda r: ellipj(r, m)[1]
    def make_dn(m):
        return lambda r: ellipj(r, m)[2]

    sn = make_sn(m)
    cn = make_cn(m)
    dn = make_dn(m)

    # Basic (3)
    basis.extend([sn, cn, dn])

    # Products (3)
    basis.append(lambda r: sn(r) * cn(r))
    basis.append(lambda r: sn(r) * dn(r))
    basis.append(lambda r: cn(r) * dn(r))

    # Powers (9)
    for power in [2, 3, 4]:
        basis.append(lambda r, p=power: sn(r)**p)
        basis.append(lambda r, p=power: cn(r)**p)
        basis.append(lambda r, p=power: dn(r)**p)

    # Ratios (6) - with safe division
    def safe_div(a, b, eps=1e-10):
        return a / np.maximum(np.abs(b), eps) * np.sign(b + eps)

    basis.append(lambda r: safe_div(sn(r), cn(r)))  # tan-like
    basis.append(lambda r: safe_div(sn(r), dn(r)))
    basis.append(lambda r: safe_div(cn(r), dn(r)))
    basis.append(lambda r: safe_div(cn(r), sn(r)))  # cot-like
    basis.append(lambda r: safe_div(dn(r), sn(r)))
    basis.append(lambda r: safe_div(dn(r), cn(r)))

    return basis
```

### Extended Basis with Coordinates

```python
def generate_extended_elliptic_basis(m, state_dim=6):
    """
    Generate elliptic basis mixed with phase space coordinates.
    """
    from scipy.special import ellipj

    basis = []

    def jacobi(r, m):
        sn, cn, dn, _ = ellipj(r, m)
        return sn, cn, dn

    # Mixed with position components
    for i in range(3):
        # x_i * sn(r)
        basis.append(lambda state, i=i, m=m:
            state[:, i] * ellipj(np.linalg.norm(state[:, :3], axis=1), m)[0])
        # x_i * cn(r)
        basis.append(lambda state, i=i, m=m:
            state[:, i] * ellipj(np.linalg.norm(state[:, :3], axis=1), m)[1])

    # Mixed with velocity components
    for i in range(3, 6):
        # v_i * dn(r)
        basis.append(lambda state, i=i, m=m:
            state[:, i] * ellipj(np.linalg.norm(state[:, :3], axis=1), m)[2])

    return basis
```

---

## Implementation

### Jacobi Elliptic Functions

```python
from scipy.special import ellipj, ellipk, ellipe

def jacobi_sn(u, m):
    """Jacobi sn(u, m)."""
    sn, cn, dn, ph = ellipj(u, m)
    return sn

def jacobi_cn(u, m):
    """Jacobi cn(u, m)."""
    sn, cn, dn, ph = ellipj(u, m)
    return cn

def jacobi_dn(u, m):
    """Jacobi dn(u, m)."""
    sn, cn, dn, ph = ellipj(u, m)
    return dn

def complete_elliptic_K(m):
    """Complete elliptic integral of first kind K(m)."""
    return ellipk(m)

def complete_elliptic_E(m):
    """Complete elliptic integral of second kind E(m)."""
    return ellipe(m)
```

### Verify Identities

```python
def verify_elliptic_identities(u, m, tol=1e-10):
    """
    Verify fundamental elliptic identities.

    Returns:
        passed: bool
        errors: Dict of identity errors
    """
    sn, cn, dn, _ = ellipj(u, m)

    errors = {}

    # sn² + cn² = 1
    errors['pythagorean'] = np.max(np.abs(sn**2 + cn**2 - 1))

    # dn² + m*sn² = 1
    errors['dn_identity'] = np.max(np.abs(dn**2 + m * sn**2 - 1))

    # Derivative check: d(sn)/du = cn*dn
    du = 1e-6
    sn_plus, cn_plus, dn_plus, _ = ellipj(u + du, m)
    d_sn_numerical = (sn_plus - sn) / du
    d_sn_analytical = cn * dn
    errors['derivative'] = np.max(np.abs(d_sn_numerical - d_sn_analytical))

    passed = all(e < tol for e in errors.values())
    return passed, errors
```

### Elliptic Search Pipeline

```python
def search_elliptic_integral(times, states, mu=None):
    """
    Search for conserved quantities in elliptic function basis.

    Returns:
        result: SearchResult with expression, m, confidence, error
    """
    from src.python.symbolic.regression_pipeline import SINDyRegressor

    # Step 1: Estimate elliptic parameter
    m = estimate_elliptic_parameter(times, states)

    # Step 2: Generate basis
    basis = generate_elliptic_basis(m)

    # Step 3: SINDy regression
    sindy = SINDyRegressor(
        basis_functions=basis,
        threshold=0.1,
        alpha=0.01
    )

    result = sindy.fit(times, states)
    result.elliptic_parameter = m

    return result
```

---

## References

- Abramowitz, M. & Stegun, I.A. (1964). *Handbook of Mathematical Functions*, Chapter 16
- Byrd, P.F. & Friedman, M.D. (1971). *Handbook of Elliptic Integrals*
- Lawden, D.F. (1989). *Elliptic Functions and Applications*
- Whittaker, E.T. & Watson, G.N. (1927). *A Course of Modern Analysis*, Chapter 22
