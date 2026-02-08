---
name: wp1-chaos-analysis
description: >
  Chaos detection and classification for CR3BP orbits using MEGNO, FLI, and 
  auxiliary indicators. Use when: (1) analyzing orbit stability, (2) detecting 
  chaos vs regular motion, (3) computing Lyapunov-type indicators, (4) classifying 
  trajectories for WP3 invariant search, (5) preparing orbits for WP4 Morales-Ramis 
  validation, (6) mapping chaos across parameter space, or (7) computing variational 
  equations alongside chaos indicators. Triggers on requests involving chaos detection, 
  MEGNO, FLI, OFLI, SALI, regular/chaotic classification, Lyapunov exponents, orbit 
  stability analysis, monodromy matrix, Floquet multipliers, or variational equation 
  preparation.
---

# WP1 Chaos Analysis

Chaos detection workflows for classifying CR3BP orbits as regular or chaotic, with integration into the project's validation pipeline.

## Indicator Overview

| Indicator | Regular Value | Chaotic Value | Integration Time | Best For |
|-----------|--------------|---------------|------------------|----------|
| MEGNO | → 2.0 | grows linearly | 100+ periods | Final classification |
| FLI | < 3.0 | > 4.0 | 50 periods | Quick screening |
| OFLI | < 3.0 | > 4.0 | 50 periods | Isotropic chaos detection |
| SALI | → 0 slowly | → 0 exponentially | 100+ periods | Weak chaos distinction |

**Mathematical relation**: MEGNO = 2×(FLI - time-average of FLI) (Mestre et al. 2011)

**Decision tree:**
- Quick screening? → Use FLI (fastest)
- Final classification? → Use MEGNO (most reliable)
- Isotropic analysis? → Use OFLI
- Weak chaos detection? → Use SALI
- WP4 preparation? → Use `ChaosVariationalAnalyzer` (runs all + variational equations)

## Precision Tiers for Chaos Analysis

| Analysis Type | Precision Tier | Target ΔC | Indicator Accuracy | Use Case |
|---------------|----------------|-----------|-------------------|----------|
| Quick screening | Tier 1 | < 10⁻¹⁴ | FLI sufficient | Parameter sweeps |
| Final classification | Tier 1 | < 10⁻¹⁴ | MEGNO recommended | Catalogue generation |
| Morales-Ramis prep | Tier 2 | < 10⁻²⁵ | Both + QD arithmetic | WP4 validation |

See `references/precision-requirements.md` for detailed precision analysis.

## Quick Start

```python
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer
import numpy as np

mu = 0.012150585609624
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])

# Create analyzer
analyzer = create_cr3bp_chaos_analyzer(mu=mu)

# Analyze orbit
result = analyzer.analyze(
    state0=state0,
    t_max=100 * 2*np.pi,  # 100 periods
    dt=0.1
)

print(f"MEGNO: {result['megno']:.3f}")
print(f"FLI: {result['fli']:.3f}")
print(f"Classification: {result['classification']}")
```

## Integration Time Selection

Proper time scaling is critical for reliable chaos detection:

```python
from src.python.utils.dynamics import estimate_orbital_period

# Compute orbital period for time scaling
T_period = estimate_orbital_period(state0, mu)

# Recommended integration times by use case
t_fli = 50 * T_period           # FLI: 50 periods (quick screening)
t_megno = 100 * T_period        # MEGNO: 100+ periods (classification)
t_validation = 1000 * T_period  # WP4 validation: 1000+ periods
t_resonance = 500 * T_period    # Near-resonance orbits: 500+ periods
```

See `references/integration-guidelines.md` for period estimation methods.

## MEGNO Indicator

**Theory**: Mean Exponential Growth of Nearby Orbits

- Regular motion: MEGNO → 2.0 (bounded oscillations)
- Chaotic motion: MEGNO grows linearly with time

**Location**: `src/python/validation/chaos_indicators.py`

```python
from src.python.validation.chaos_indicators import MEGNOIndicator
from src.python.utils.dynamics import cr3bp_dynamics

indicator = MEGNOIndicator(
    dynamics_func=cr3bp_dynamics,
    mu=mu
)

megno = indicator.compute(
    state0=initial_state,
    t_max=100 * T_period,
    dt=0.01
)

# Interpretation
if megno < 2.5:
    print("Regular orbit")
elif megno > 3.0:
    print("Chaotic orbit")
else:
    print("Borderline - extend integration time")
```

**Thresholds:**
- MEGNO < 2.5 → Regular
- MEGNO > 3.0 → Chaotic
- 2.5 ≤ MEGNO ≤ 3.0 → Borderline (extend integration)

See `references/indicator-theory.md` for mathematical foundations.

## FLI Indicator

**Theory**: Fast Lyapunov Indicator - tracks logarithmic growth of deviation vector.

```python
from src.python.validation.chaos_indicators import FLIIndicator

indicator = FLIIndicator(
    dynamics_func=cr3bp_dynamics,
    mu=mu
)

fli = indicator.compute(
    state0=initial_state,
    t_max=50 * T_period,
    dt=0.01
)

# Interpretation
if fli < 3.0:
    print("Regular orbit")
elif fli > 4.0:
    print("Chaotic orbit")
else:
    print("Uncertain - use MEGNO for confirmation")
```

**Thresholds:**
- FLI < 3.0 → Regular
- FLI > 4.0 → Chaotic
- 3.0 ≤ FLI ≤ 4.0 → Uncertain

## Tier 2 High-Precision Analysis

For WP4 Morales-Ramis preparation, use Tier 2 precision:

```python
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

# Tier 2 chaos analysis with QD arithmetic
analyzer = create_cr3bp_chaos_analyzer(
    mu=mu,
    integrator='adaptive_symplectic',
    integrator_kwargs={
        'order': 6,
        'tol': 1e-20,
        'sundman_strategy': 'sum'
    },
    precision='qd'  # Double-double arithmetic (~31 digits)
)

result = analyzer.analyze(
    state0=state0,
    t_max=1000 * T_period,  # Extended for validation
    dt=0.01
)

# Verify precision achieved
print(f"Jacobi constant drift: {result['jacobi_drift']:.2e}")
assert result['jacobi_drift'] < 1e-25, "Tier 2 precision not achieved"
```

## Combined Chaos + Variational Analysis

For WP4 Morales-Ramis test preparation, compute variational equations alongside chaos indicators:

```python
from src.python.validation.chaos_indicators import ChaosVariationalAnalyzer

analyzer = ChaosVariationalAnalyzer(mu=mu)

# Full analysis with monodromy matrix (for periodic orbits)
result = analyzer.analyze_with_variational(
    state0=state0,
    t_max=100 * T_period,
    compute_monodromy=True,      # Extract monodromy matrix
    compute_floquet=True         # Compute Floquet multipliers
)

print(f"MEGNO: {result['megno']:.3f}")
print(f"FLI: {result['fli']:.3f}")
print(f"Classification: {result['classification']}")

# Variational equation outputs (for WP4)
if result['is_periodic']:
    print(f"Monodromy eigenvalues: {result['floquet_multipliers']}")
    print(f"Stability type: {result['stability_type']}")
    
    # Pass to WP4 Morales-Ramis validator
    monodromy_matrix = result['monodromy_matrix']
```

**Connection to Differential Galois Theory**: The monodromy matrix eigenvalues (Floquet multipliers) determine if the Differential Galois Group identity component is abelian. Non-abelian → non-integrable.

## Shadow Hamiltonian Validation

Validate chaos indicators against numerical noise:

```python
from src.python.validation.shadow_hamiltonian import ShadowHamiltonianAnalyzer
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

# Run chaos analysis
analyzer = create_cr3bp_chaos_analyzer(mu=mu)
result = analyzer.analyze(state0, t_max=100*T_period, dt=0.1)

# Validate with shadow Hamiltonian
shadow = ShadowHamiltonianAnalyzer(dynamics_func=cr3bp_dynamics)
shadow_result = shadow.analyze(
    times=result['times'],
    states=result['states'],
    dt=0.1
)

# Check if numerical noise affects classification
if shadow_result['drift_rate'] > 1e-14:
    print("⚠️  Warning: Numerical noise may affect chaos classification")
    print(f"   Shadow Hamiltonian drift: {shadow_result['drift_rate']:.2e}")
    print("   Recommend: Use Tier 2 precision or reduce timestep")
else:
    print(f"✓ Shadow Hamiltonian drift: {shadow_result['drift_rate']:.2e} (acceptable)")
```

## Resonance Detection

Near-resonance orbits require extended integration times:

```python
from src.python.utils.resonance import detect_resonance

# Check for resonance before chaos analysis
resonance = detect_resonance(state0, mu, max_order=10)

if resonance['is_resonant']:
    print(f"Near {resonance['ratio']} resonance detected")
    print(f"Resonance strength: {resonance['strength']:.3f}")
    
    # Extend integration time for resonant orbits
    t_max = 500 * T_period  # 5x longer than standard
    
    # FLI and MEGNO may disagree near resonance - trust MEGNO
    result = analyzer.analyze(state0, t_max=t_max)
else:
    result = analyzer.analyze(state0, t_max=100*T_period)
```

## Batch Analysis with Parallelization

### Serial Batch (Small catalogues)

```python
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

analyzer = create_cr3bp_chaos_analyzer(mu=mu)

orbits = [state0_1, state0_2, state0_3, ...]
results = []

for state0 in orbits:
    result = analyzer.analyze(
        state0=state0,
        t_max=100 * 2*np.pi,
        dt=0.1
    )
    results.append({
        'state0': state0,
        'megno': result['megno'],
        'fli': result['fli'],
        'classification': result['classification']
    })

# Stratify by chaos
regular = [r for r in results if r['classification'] == 'regular']
chaotic = [r for r in results if r['classification'] == 'chaotic']
```

### Parallel Batch with Dask (Large catalogues)

```python
from dask import delayed, compute
from dask.distributed import Client
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

# Start Dask cluster
client = Client(n_workers=8)

@delayed
def analyze_orbit(state0, mu, t_max):
    analyzer = create_cr3bp_chaos_analyzer(mu=mu)
    return analyzer.analyze(state0, t_max=t_max)

# Parallel analysis of 10⁵ orbits
t_max = 100 * 2 * np.pi
tasks = [analyze_orbit(s, mu, t_max) for s in initial_conditions]
results = compute(*tasks)

client.close()
```

### Snakemake Pipeline Integration

```python
# In Snakefile - chaos analysis rule
rule chaos_analysis:
    input:
        trajectories="results/tier1/trajectories.parquet"
    output:
        chaos_map="results/tier1/chaos_classification.parquet"
    threads: 8
    script:
        "scripts/batch_chaos_analysis.py"
```

## Use Cases

### 1. Pre-filter for WP3 Discovery

Only search for integrals in regular regions:

```python
# Generate candidates
candidates = generate_initial_conditions(n=1000)

# Filter to regular orbits
analyzer = create_cr3bp_chaos_analyzer(mu=mu)
regular_orbits = []

for c in candidates:
    result = analyzer.analyze(c, t_max=50*T_period, dt=0.1)
    if result['classification'] == 'regular':
        regular_orbits.append(c)

print(f"Regular orbits for WP3: {len(regular_orbits)}/{len(candidates)}")
# Proceed with regular orbits only for invariant search
```

### 2. Parameter Space Mapping

Map chaos across (C, x₀) space:

```python
import numpy as np
import matplotlib.pyplot as plt

C_values = np.linspace(2.8, 3.5, 50)
x_values = np.linspace(0.8, 1.5, 50)

chaos_map = np.zeros((len(C_values), len(x_values)))

for i, C in enumerate(C_values):
    for j, x0 in enumerate(x_values):
        state0 = initial_condition_from_C_x(C, x0, mu)
        result = analyzer.analyze(state0, t_max=50*T_period, dt=0.1)
        chaos_map[i, j] = result['megno']

# Plot chaos map
plt.figure(figsize=(10, 8))
plt.contourf(x_values, C_values, chaos_map, levels=20, cmap='viridis')
plt.colorbar(label='MEGNO')
plt.xlabel('x₀')
plt.ylabel('C (Jacobi constant)')
plt.title('Chaos Map: MEGNO across Parameter Space')
plt.axhline(y=2.0, color='white', linestyle='--', label='MEGNO=2 threshold')
plt.savefig('chaos_map.png', dpi=150)
```

### 3. Validation Stratification

Ensure validation covers both regular and chaotic regimes:

```python
# Load trajectory catalogue
trajectories = load_catalogue('tier1')

# Classify all
classifications = []
for traj in trajectories:
    result = analyzer.analyze(traj['state0'], t_max=100*T_period)
    classifications.append(result['classification'])

# Report distribution
from collections import Counter
dist = Counter(classifications)
print(f"Regular: {dist['regular']}, Chaotic: {dist['chaotic']}, Borderline: {dist['borderline']}")

# Verify adequate coverage for WP4
assert dist['regular'] >= 1000, "Need more regular orbits for WP4"
assert dist['chaotic'] >= 1000, "Need more chaotic orbits for WP4"
```

### 4. WP4 Morales-Ramis Preparation

Prepare classified orbits for differential Galois theory analysis:

```python
from src.python.validation.chaos_indicators import ChaosVariationalAnalyzer
from src.python.validation.periodic_orbits import find_periodic_orbit

# Find periodic orbit for Morales-Ramis test
periodic_state, period = find_periodic_orbit(mu=mu, family='lyapunov', L_point='L2')

# Full analysis with variational equations
analyzer = ChaosVariationalAnalyzer(mu=mu, precision='qd')
result = analyzer.analyze_with_variational(
    state0=periodic_state,
    t_max=period,           # Exactly one period
    compute_monodromy=True,
    compute_floquet=True
)

# Export for WP4
wp4_input = {
    'state0': periodic_state,
    'period': period,
    'monodromy_matrix': result['monodromy_matrix'],
    'floquet_multipliers': result['floquet_multipliers'],
    'megno': result['megno'],
    'fli': result['fli'],
    'classification': result['classification']
}

# Pass to WP4 Morales-Ramis validator
from src.python.validation.morales_ramis_validator import MoralesRamisValidator
mr_validator = MoralesRamisValidator(mu=mu)
mr_result = mr_validator.test_downstairs(wp4_input)
```

## Pipeline Role

```
┌─────────────────────────────────────────────────────────────┐
│ WP1: Trajectory Generation                                  │
│ • IAS15/Yoshida8/AdaptiveSymplectic integrators            │
│ • Tier 1 (10⁵ orbits) + Tier 2 (10⁴ orbits)               │
└────────────────────────┬────────────────────────────────────┘
                         │ Trajectories
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ WP1: Chaos Analysis (THIS SKILL)                           │
│ • MEGNO/FLI classification → {regular, chaotic, borderline}│
│ • Variational equations for periodic orbits                 │
│ • Shadow Hamiltonian validation                             │
└────────────────────────┬────────────────────────────────────┘
                         │ Classified orbits + variational data
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ WP3: Invariant Discovery                                    │
│ • Focus on REGULAR orbits only                              │
│ • HNN/SympNets + AI Feynman symbolic regression            │
└────────────────────────┬────────────────────────────────────┘
                         │ Candidate integrals
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ WP4: Morales-Ramis Validation                              │
│ • Uses monodromy matrices from chaos analysis               │
│ • Phase I: Downstairs non-abelian (confirms non-integrable)│
│ • Phase II: Upstairs abelian (validates lift-integrability)│
└─────────────────────────────────────────────────────────────┘
```

## Common Issues

**MEGNO oscillating around 2.0 but not converging?**
- Normal for regular orbits - small oscillations expected
- Extend integration time for more stable average
- Check for near-resonance conditions

**FLI and MEGNO disagree?**
- Trust MEGNO (more reliable for borderline cases)
- Extend both integrations
- Check for near-resonance: `detect_resonance(state0, mu)`
- Near resonance, MEGNO is definitive

**Very large MEGNO (> 10)?**
- Strongly chaotic orbit
- May indicate proximity to collision or escape
- Verify with shadow Hamiltonian analysis

**Shadow Hamiltonian drift too large?**
- Switch to Tier 2 precision (AdaptiveSymplectic + QD)
- Reduce timestep
- Chaos classification may be unreliable - flag for review

**Variational equations diverging?**
- Expected for chaotic orbits (exponential divergence)
- For periodic orbits, ensure t_max = exact period
- Use Tier 2 precision for Morales-Ramis preparation

## Tests

```bash
# Core chaos indicator tests
pytest tests/validation/test_chaos_indicators.py -v

# Specific tests
pytest tests/validation/test_chaos_indicators.py::test_megno_regular_vs_chaotic -v
pytest tests/validation/test_chaos_indicators.py::test_fli_thresholds -v
pytest tests/validation/test_chaos_indicators.py::test_combined_analyzer -v

# Variational equation tests
pytest tests/validation/test_variational_equations.py -v

# Integration tests with shadow Hamiltonian
pytest tests/validation/test_shadow_hamiltonian.py -v
```

## References

- `references/indicator-theory.md` - Mathematical foundations of MEGNO, FLI, OFLI, SALI
- `references/precision-requirements.md` - Tier 1/2 precision for chaos analysis
- `references/integration-guidelines.md` - Period estimation and time selection
- `src/python/validation/chaos_indicators.py` - Implementation
- `Science-Research-Docs/Research_Synthesis_Variational_Equations.md` - DGG theory
- Cincotta & Simó (2000) - MEGNO reference
- Mestre et al. (2011) - MEGNO-FLI relationship
