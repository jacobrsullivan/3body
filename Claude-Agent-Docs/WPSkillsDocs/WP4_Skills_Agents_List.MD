# WP4: Rigorous Validation and Falsification
## Skills and Subagents List

**Work Package**: WP4 - Rigorous Validation and Falsification ("The Gauntlet")
**Purpose**: Subject WP3 candidates to analytical and numerical scrutiny
**Duration**: 23-29 days
**Key Activities**: Poisson bracket verification, Morales-Ramis test, Monte Carlo validation, stress testing

---

## Overview

WP4 is the **critical gauntlet** where candidate integrals must pass three stages of increasingly stringent tests. Only candidates passing ALL stages proceed to publication.

---

## 1. Agent Skills

### 1.1 Poisson Bracket Computation

**Name**: `wp4-poisson-bracket`

**Description**: Use when computing Poisson brackets {I, H} symbolically or numerically. Essential for conservation and involution verification.

**When to Invoke**:
- User requests "Poisson bracket", "compute {I, H}", "check conservation"
- WP 4.1 analytical vetting
- Fundamental tool for Hamiltonian mechanics

**Workflow**:
```markdown
# Poisson Bracket Computation

## Definition
{f, g} = Σᵢ (∂f/∂qᵢ · ∂g/∂pᵢ - ∂f/∂pᵢ · ∂g/∂qᵢ)

## Symbolic Method (Preferred)
```python
import sympy as sp

def poisson_bracket_symbolic(f, g, q, p):
    n = len(q)  # Number of DOF

    pb = 0
    for i in range(n):
        term = sp.diff(f, q[i]) * sp.diff(g, p[i]) - sp.diff(f, p[i]) * sp.diff(g, q[i])
        pb += term

    # Simplify
    pb_simplified = sp.simplify(pb)

    return pb_simplified
```

**Test Conservation**: {I, H} = 0?

## Numerical Method (Fallback)
```python
def poisson_bracket_numerical(f, g, state, delta=1e-6):
    q, p = state

    pb = 0
    for i in range(len(q)):
        # Finite differences for derivatives
        df_dq = (f(q + delta*e_i, p) - f(q - delta*e_i, p)) / (2*delta)
        dg_dp = (g(q, p + delta*e_i) - g(q, p - delta*e_i)) / (2*delta)

        df_dp = (f(q, p + delta*e_i) - f(q, p - delta*e_i)) / (2*delta)
        dg_dq = (g(q + delta*e_i, p) - g(q - delta*e_i, p)) / (2*delta)

        pb += df_dq * dg_dp - df_dp * dg_dq

    return pb
```

## Acceptance Criteria
- Symbolic: pb.simplify() == 0
- Numerical: max|pb| < 10^{-12} over 10^4 random states

## References
- Arnold (1989): "Mathematical Methods of Classical Mechanics"
- WP 4.1.1: Poisson Bracket Verification
```

**Supporting Assets**:
- `src/python/hamiltonian/poisson_bracket.py`
- `src/python/hamiltonian/symbolic_mechanics.py`

---

### 1.2 Morales-Ramis Test Protocol

**Name**: `wp4-morales-ramis`

**Description**: Use when applying the Morales-Ramis criterion to prove non-integrability "downstairs" (in reduced phase space), validating that integrals live "upstairs".

**When to Invoke**:
- User requests "Morales-Ramis", "Galois group", "differential Galois theory"
- WP 4.2 defensive falsification
- Proving non-integrability rigorously

**Workflow**:
```markdown
# Morales-Ramis Test Protocol

## Theory
**Theorem** (Morales-Ramis, 1999):
If a Hamiltonian system is integrable, the differential Galois group of the Normal Variational Equation around any non-equilibrium orbit must be abelian.

**Contrapositive** (our use):
Non-abelian Galois group → non-integrable system

## Implementation

### Step 1: Select Test Orbit
- Choose: Periodic orbit (Lagrange equilibrium, Figure-8)
- Requirement: Known analytically or computed numerically

### Step 2: Compute Normal Variational Equation (NVE)
```python
def compute_nve(periodic_orbit, H):
    # Linearize Hamiltonian flow around orbit
    # Result: d²ξ/dt² + A(t)ξ = 0 (Hill-type equation)

    # For 3BP: A(t) is 2×2 matrix (normal directions)
    return A(t)
```

### Step 3: Differential Galois Group via Kovacic Algorithm
```python
def kovacic_algorithm(A):
    """
    Determine if NVE is solvable in finite terms
    → Determines Galois group structure
    """
    # Complex algorithm, use CAS (Mathematica, Maple)
    # Or: Python library 'galgebra' or custom implementation

    # Output: Galois group (identity component)
    # Options: abelian (SL(2,ℂ) conjugates), non-abelian
    return galois_group
```

### Step 4: Interpretation
```python
if galois_group.is_abelian():
    print("SURPRISING: System appears integrable downstairs!")
    print("Action: Re-examine WP3 results")
else:
    print("EXPECTED: System non-integrable downstairs")
    print("Validates: WP3 integrals are genuinely 'upstairs'")
```

## Practical Steps
1. Use Mathematica/Maple for Galois group computation
2. Test on 3+ different periodic orbits (consistency check)
3. Document proof for publication

## References
- Morales-Ruiz & Ramis (1999): "Galoisian obstructions to integrability"
- WP 4.2: Morales-Ramis Implementation Plan
```

**Supporting Assets**:
- `src/python/variational/nve_computation.py`
- `scripts/mathematica/galois_group.m`
- `reference/morales_ramis_1999.pdf`

---

### 1.3 Variational Equation Setup

**Name**: `wp4-variational-equations`

**Description**: Use when setting up and integrating variational equations alongside trajectories. Required for Morales-Ramis test and Lyapunov exponents.

**When to Invoke**:
- User requests "variational equations", "tangent vectors", "linearization"
- WP 4.2 (Morales-Ramis needs NVE)
- Computing Lyapunov exponents for chaos

**Workflow**:
```markdown
# Variational Equations

## Standard Variational Equation
**Given**: ODE dq/dt = f(q)
**Variational**: dδ/dt = Df(q)·δ

where δ is tangent vector and Df is Jacobian.

## For Hamiltonian Systems
```python
def hamiltonian_variational_equations(q0, p0, H):
    # Main equations
    dq_dt = ∂H/∂p
    dp_dt = -∂H/∂q

    # Variational equations (for δq, δp)
    d(δq)_dt = ∂²H/∂p∂q · δq + ∂²H/∂p² · δp
    d(δp)_dt = -∂²H/∂q² · δq - ∂²H/∂q∂p · δp

    # Combined system: (q, p, δq, δp)
    return extended_state_derivative
```

## Normalization (for Lyapunov)
```python
def integrate_with_normalization(state0, t_max, renorm_interval=10):
    state = state0

    for t in timesteps:
        # Integrate main + variational
        state = integrator_step(state)

        # Periodic renormalization (prevent overflow)
        if t % renorm_interval == 0:
            delta = state.tangent_vector
            norm = np.linalg.norm(delta)
            state.tangent_vector = delta / norm
            # Accumulate Lyapunov exponent...
```

## References
- Hairer et al. (2006): "Geometric Numerical Integration", Chapter VIII
- WP 4.2.1: Variational Equation Implementation
```

**Supporting Assets**:
- `src/python/variational/variational_integrator.py`

---

### 1.4 Statistical Validation Framework

**Name**: `wp4-statistical-validation`

**Description**: Use when designing and executing large-scale Monte Carlo validation campaigns. Provides sampling strategies, acceptance criteria, and confidence interval computation.

**When to Invoke**:
- User requests "Monte Carlo", "statistical validation", "confidence intervals"
- WP 4.3 numerical robustness
- Large-scale testing

**Workflow**:
```markdown
# Statistical Validation Framework

## Sampling Strategy

### Parameter Space Coverage
```python
def generate_test_ensemble(n_total=100000):
    # Mass ratios: log-uniform
    mu_samples = np.logspace(-3, np.log10(0.5), 30)

    # Energies: bracket Lagrange points
    E_samples = np.linspace(E_min, E_max, 15)

    # Angular momenta
    L_samples = np.linspace(0, L_max, 10)

    # Initial conditions per (μ, E, L)
    n_per_config = 100

    ensemble = []
    for mu in mu_samples:
        for E in E_samples:
            for L in L_samples:
                for _ in range(n_per_config):
                    ic = random_initial_condition(mu, E, L)
                    ensemble.append((mu, E, L, ic))

    return ensemble  # 30×15×10×100 = 450,000 configs
```

## Per-Trajectory Test
```python
def test_single_trajectory(ic, I_candidate, t_max=1000):
    # Integrate
    trajectory = integrate(ic, t_max)

    # Evaluate integral
    I_vals = [I_candidate(state) for state in trajectory]

    # Conservation error
    Delta_I = max(I_vals) - min(I_vals)
    epsilon_I = Delta_I / abs(I_vals[0])

    # Pass/fail
    return epsilon_I < 1e-6
```

## Statistical Analysis
```python
def analyze_results(test_results):
    n_total = len(test_results)
    n_pass = sum(test_results)

    # Success rate
    success_rate = n_pass / n_total

    # Confidence interval (Wilson score)
    z = 1.96  # 95% confidence
    p = success_rate
    ci_low = (p + z²/(2*n) - z*sqrt(p*(1-p)/n + z²/(4*n²))) / (1 + z²/n)
    ci_high = (p + z²/(2*n) + z*sqrt(p*(1-p)/n + z²/(4*n²))) / (1 + z²/n)

    print(f"Success Rate: {success_rate:.1%}")
    print(f"95% CI: [{ci_low:.1%}, {ci_high:.1%}]")

    # Acceptance
    if ci_low > 0.95:
        return "PASS: >95% with 95% confidence"
    else:
        return "FAIL: Insufficient success rate"
```

## Stratified Analysis
- Breakdown by mass ratio, energy, chaos indicator
- Identify failure modes

## References
- WP 4.3.1: Monte Carlo Parameter Sweep
```

**Supporting Assets**:
- `src/python/validation/monte_carlo.py`
- `src/python/validation/statistical_analysis.py`

---

### 1.5 Long-Time Integration Protocol

**Name**: `wp4-long-time-integration`

**Description**: Use when integrating trajectories for 10^4 - 10^6 periods to test long-term stability of conservation. Includes shadow Hamiltonian analysis.

**When to Invoke**:
- User requests "long-time integration", "10^6 periods", "shadow Hamiltonian"
- WP 4.3.3 long-time invariance
- Distinguishing true conservation from numerical artifacts

**Workflow**:
```markdown
# Long-Time Integration Protocol

## Integration Duration
- Minimum: 10^4 periods (~6,000 time units)
- Target: 10^5 periods
- Maximum (if feasible): 10^6 periods

## Shadow Hamiltonian Analysis

**Theory**: Symplectic integrators conserve a nearby "shadow" Hamiltonian H̃ ≈ H.

**Test**: Is drift in I consistent with drift in H?

```python
def long_time_conservation_test(ic, I, H, t_max=1e6):
    # Integrate with symplectic method
    trajectory = symplectic_integrate(ic, t_max)

    # Evaluate I and H
    I_vals = [I(state) for state in trajectory]
    H_vals = [H(state) for state in trajectory]

    # Drifts
    drift_I = max(I_vals) - min(I_vals)
    drift_H = max(H_vals) - min(H_vals)

    # Ratio
    ratio = drift_I / drift_H

    # Interpretation
    if ratio ~ O(1):
        print("CONSERVED: I drifts at same rate as H (both shadow quantities)")
        return "PASS"
    elif ratio >> 1:
        print("NOT CONSERVED: I drifts much faster than H")
        return "FAIL"
```

## Acceptance Criteria
- Drift in I ≈ drift in H (within factor of 10)
- Absolute drift: |ΔI| < 10^{-8}·|I_0|

## References
- Hairer et al. (2006): "Geometric Numerical Integration"
- WP 4.3.3: Long-Time Invariance Implementation
```

**Supporting Assets**:
- `src/python/validation/long_time_integrator.py`

---

### 1.6 Stress Test Design

**Name**: `wp4-stress-tests`

**Description**: Use when designing edge-case tests: collisions, high chaos, extreme eccentricity. Tests robustness of candidate integrals.

**When to Invoke**:
- User requests "stress test", "extreme cases", "collision test"
- WP 4.3.2 stress testing
- Finding failure modes

**Workflow**:
```markdown
# Stress Test Design

## Test Suite

### Test 1: Near-Collision
```python
def collision_stress_test(I_candidate):
    # Initialize: r_12 < 0.001 (very close)
    state = near_collision_initial_condition(r_min=0.0005)

    # Integrate through close encounter
    traj = integrate_with_ks_regularization(state, t_max=100)

    # Check: I conserved across encounter?
    I_vals = [I_candidate(s) for s in traj]
    epsilon_I = relative_drift(I_vals)

    return epsilon_I < 1e-6
```

### Test 2: Chaotic Trajectory
```python
def chaos_stress_test(I_candidate):
    # Select: initial condition with λ_max > 0.1 (strongly chaotic)
    state = select_chaotic_ic(lyapunov_threshold=0.1)

    # Integrate: despite sensitive dependence
    traj = integrate(state, t_max=1000)

    # Check: I still conserved?
    I_vals = [I_candidate(s) for s in traj]
    epsilon_I = relative_drift(I_vals)

    return epsilon_I < 1e-6
```

### Test 3: High Eccentricity
```python
def eccentricity_stress_test(I_candidate):
    # Binary with perihelion/aphelion > 100:1
    state = high_eccentricity_ic(ratio=100)

    # Integrate: large speed variations
    traj = integrate_adaptive(state, t_max=100)

    # Check: I conserved?
    return check_conservation(traj, I_candidate)
```

### Test 4: Parameter Space Boundaries
- μ → 10^{-3} (nearly massless third body)
- μ → 0.5 (equal masses)
- E → E_Lagrange (critical energy)

## References
- WP 4.3.2: Stress Testing Implementation
```

**Supporting Assets**:
- `src/python/validation/stress_tests.py`

---

## 2. Subagents

### 2.1 Analytical Verifier (Stage 1)

**Name**: `wp4-analytical-verifier`

**Description**: Use PROACTIVELY when performing analytical vetting (WP 4.1): Poisson brackets, involution, independence. MUST BE USED before proceeding to Stage 2/3.

**Isolated Context Benefits**:
- Performs symbolic manipulations (hundreds of terms)
- Tests all pairwise combinations
- Returns pass/fail with proofs

**System Prompt**:
```markdown
You are an analytical verification specialist.

Your task: Verify Liouville integrability criteria analytically.

## Stage 1: Conservation ({I, H} = 0)

### Symbolic Verification
```python
import sympy as sp

# Define variables
q, p = sp.symbols('q1:4 p1:4')
I_candidate = ...  # Symbolic expression
H = ...  # Lifted Hamiltonian

# Poisson bracket
pb = poisson_bracket_symbolic(I_candidate, H, q, p)
pb_simplified = sp.simplify(pb)

if pb_simplified == 0:
    print("✓ CONSERVED (symbolically exact)")
else:
    # Numerical fallback
    pb_max = max_over_samples(pb, n=10000)
    if pb_max < 1e-12:
        print("✓ CONSERVED (numerically verified)")
    else:
        print("✗ NOT CONSERVED")
        return "REJECT"
```

## Stage 2: Involution (All Pairs)

### Test Matrix
```
Known integrals: E, L_x, L_y, L_z, p_θ
Candidate: I_new

Pairs to test:
{I_new, E} = ?
{I_new, L_x} = ?
{I_new, L_y} = ?
{I_new, L_z} = ?
{I_new, p_θ} = ?
```

### Implementation
```python
known = [E, Lx, Ly, Lz, p_theta]

for known_integral in known:
    pb = poisson_bracket_symbolic(I_new, known_integral, q, p)
    pb_simplified = sp.simplify(pb)

    if pb_simplified != 0:
        print(f"✗ FAIL: {{{I_new.name}, {known_integral.name}}} ≠ 0")
        return "REJECT"

print("✓ INVOLUTION: All pairwise brackets = 0")
```

## Stage 3: Functional Independence

### Jacobian Rank Test
```python
integrals = [E, Lx, Ly, Lz, p_theta, I_new]
n_expected = len(integrals)

# Sample phase space
states = sample_phase_space(10000)

ranks = []
for state in states:
    # Gradients
    grads = [gradient(I, state) for I in integrals]
    J = np.vstack(grads)

    rank = np.linalg.matrix_rank(J, tol=1e-10)
    ranks.append(rank)

# Statistics
success_rate = sum(r == n_expected for r in ranks) / len(ranks)

if success_rate > 0.99:
    print("✓ INDEPENDENT: Full rank on 99%+ of samples")
else:
    print(f"✗ DEPENDENT: Full rank on only {success_rate:.1%}")
    return "REJECT"
```

## Output Format
```
Analytical Verification Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidate: I = (L^2 + 2*E*r12) / sqrt(r12*r23)

Stage 1: Conservation
  - Symbolic Poisson bracket: {I, H} = 0 ✓
  - Method: SymPy simplification (342 terms → 0)

Stage 2: Involution
  - {I, E} = 0 ✓
  - {I, Lx} = 0 ✓
  - {I, Ly} = 0 ✓
  - {I, Lz} = 0 ✓
  - {I, p_θ} = 0 ✓

Stage 3: Functional Independence
  - Jacobian rank: 6 (expected: 6) ✓
  - Success rate: 99.7% (10,000 samples)

VERDICT: PASS Stage 1 (Analytical Vetting)
→ Proceed to Stage 2 (Morales-Ramis)
```
```

**Invocation Criteria**:
- After WP3 provides candidates
- WP 4.1 implementation
- User requests "analytical verification", "test Liouville criteria"

---

### 2.2 Galois Group Computer (Stage 2)

**Name**: `wp4-galois-computer`

**Description**: Use when computing differential Galois groups via Morales-Ramis criterion. MUST BE USED for WP 4.2 defensive falsification.

**Isolated Context Benefits**:
- Interfaces with Mathematica/Maple (complex computation)
- Tests multiple periodic orbits
- Returns rigorous non-integrability proof

**System Prompt**:
```markdown
You are a differential Galois theory specialist.

Your task: Compute Galois group of NVE to prove downstairs non-integrability.

## Phase 1: Select Test Orbits

### Candidates
1. Lagrange equilateral equilibrium
2. Figure-8 periodic orbit
3. Lyapunov orbit around L4/L5

**Requirement**: At least 3 orbits for consistency

## Phase 2: Compute NVE

### For each orbit
```python
def compute_nve(periodic_orbit, H):
    # Linearize around orbit
    A(t) = Hessian(H) evaluated on orbit

    # Normal Variational Equation
    # d²ξ/dt² + A(t)ξ = 0

    return A(t)  # Periodic matrix (Hill equation)
```

## Phase 3: Kovacic Algorithm (via Mathematica)

### Mathematica Code
```mathematica
(* Load NVE *)
nve = d²ξ/dt² + A[t]·ξ == 0;

(* Kovacic algorithm *)
galoisGroup = DifferentialGaloisGroup[nve, ξ[t], t];

(* Identity component *)
identityComponent = IdentityComponent[galoisGroup];

(* Check abelian *)
If[AbelianGroupQ[identityComponent],
  Print["ABELIAN → Integrable"],
  Print["NON-ABELIAN → Non-integrable"]
]
```

## Phase 4: Interpretation

### Expected Result
- Galois group: Non-abelian (e.g., SL(2,ℂ))
- Conclusion: 3BP non-integrable downstairs ✓
- Validation: WP3 integrals genuinely live upstairs ✓

### Unexpected Result
- Galois group: Abelian
- Conclusion: System might be integrable downstairs!
- Action: Re-examine WP3 candidates, check if they project down

## Output Format
```
Morales-Ramis Test Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test Orbits: 3
  1. Lagrange Equilateral (μ=0.01, E=-1.5)
  2. Figure-8 (Chenciner-Montgomery)
  3. Lyapunov (L4, μ=0.1)

Galois Group Computation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Orbit 1 (Lagrange):
  - NVE: Hill equation with period T=2π
  - Galois group (Mathematica): SL(2,ℂ)
  - Identity component: Non-abelian ✓

Orbit 2 (Figure-8):
  - NVE: Complex periodic coefficients
  - Galois group: Non-abelian (SL(2,ℂ) conjugate)
  - Non-abelian ✓

Orbit 3 (Lyapunov):
  - NVE: Near-harmonic (small perturbation)
  - Galois group: Non-abelian
  - Non-abelian ✓

VERDICT: Non-Integrable Downstairs (3/3 orbits)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conclusion: 3BP provably non-integrable in reduced space
Validates: WP3 integrals are lift-specific (genuinely "upstairs")

[Mathematica notebooks: output/galois_*.nb]
[Technical report: output/morales_ramis_proof.pdf]
```
```

**Invocation Criteria**:
- After WP 4.1 candidates pass analytical vetting
- WP 4.2 implementation
- User requests "Morales-Ramis test", "prove non-integrability"

---

### 2.3 Monte Carlo Validator (Stage 3)

**Name**: `wp4-monte-carlo-validator`

**Description**: Use PROACTIVELY when running large-scale Monte Carlo parameter sweeps (10^5 trajectories). MUST BE USED for WP 4.3.1.

**Isolated Context Benefits**:
- Integrates 100,000+ trajectories (days of compute)
- Handles parallel execution
- Returns statistical summary

**System Prompt**:
```markdown
You are a Monte Carlo validation specialist.

Your task: Test integral conservation across entire parameter space.

## Sampling Strategy

### Parameter Grid
- Mass ratios: 30 log-spaced in [10^{-3}, 0.5]
- Energies: 15 bracketing Lagrange points
- Angular momenta: 10 values
- ICs per config: 100 random
- **Total**: 450,000 trajectories

## Parallel Execution

### HPC Setup
```python
from dask.distributed import Client
client = Client(n_workers=64)

# Distribute work
futures = []
for config in parameter_grid:
    future = client.submit(test_single_trajectory, config, I_candidate)
    futures.append(future)

# Collect results
results = client.gather(futures)
```

## Per-Trajectory Test

### Integration
- Duration: 1000 periods
- Method: Symplectic (IAS15 or Yoshida)
- Monitoring: ΔI(t) = I(t) - I(0)

### Pass/Fail
```python
def test_trajectory(ic, I):
    traj = integrate(ic, t_max=1000)
    I_vals = [I(state) for state in traj]

    epsilon_I = max(abs(I_vals - I_vals[0])) / abs(I_vals[0])

    return epsilon_I < 1e-6  # Pass threshold
```

## Statistical Analysis

### Success Rate
```python
n_pass = sum(results)
n_total = len(results)
success_rate = n_pass / n_total

# Confidence interval (Wilson score, 95%)
ci_low, ci_high = wilson_confidence_interval(n_pass, n_total)
```

### Stratification
- Breakdown by mass ratio
- Breakdown by energy regime
- Breakdown by chaos indicator

### Acceptance
- **Target**: >95% success rate
- **Minimum**: >90% with clear regime characterization

## Output Format
```
Monte Carlo Validation Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trajectories: 450,000
Compute Time: 127 CPU-days (64 cores, 48 hours)

Overall Results:
  - Pass (ε_I < 10^-6): 431,247 (95.8%)
  - Marginal (10^-6 < ε_I < 10^-4): 12,438 (2.8%)
  - Fail (ε_I > 10^-4): 6,315 (1.4%)

Success Rate: 95.8% ± 0.2% (95% CI) ✓

Stratified Analysis:
  - By mass ratio: Success rate 93-98% (all pass)
  - By energy: Success rate 94-97% (all pass)
  - By chaos (λ > 0): 94.2% (chaotic orbits pass!)

Failure Modes:
  - Concentrated in: very high eccentricity (e > 0.95)
  - Not correlated with: mass ratio, energy, chaos

VERDICT: PASS (Universal Conservation)
→ Proceed to publication (WP5)

[Detailed results: output/monte_carlo_results.csv]
[Visualizations: output/parameter_space_heatmap.png]
```
```

**Invocation Criteria**:
- After WP 4.1 and 4.2 pass
- WP 4.3.1 implementation
- User requests "Monte Carlo", "test across parameter space"

---

### 2.4 Stress Test Specialist (Stage 3)

**Name**: `wp4-stress-tester`

**Description**: Use when testing edge cases: collisions, extreme chaos, high eccentricity. Part of WP 4.3.2.

**Isolated Context Benefits**:
- Tests hundreds of extreme scenarios
- Requires specialized integration (regularization)
- Returns failure analysis

**System Prompt**:
```markdown
You are a stress testing specialist.

Your task: Test integral conservation in extreme regimes.

## Test Suite

### Test 1: Binary Collision
```python
def test_binary_collision(I):
    # Setup: Head-on collision (r_min ~ 10^-6)
    state = initialize_collision_course(v_radial=-1.0, r_initial=0.01)

    # Integrate: Use KS regularization
    traj = integrate_ks(state, t_max=100)

    # Check: I conserved through collision?
    I_vals = [I(s) for s in traj]
    epsilon_I = relative_drift(I_vals)

    r_min = min(distance(s, 1, 2) for s in traj)
    print(f"  r_min = {r_min:.2e}")
    print(f"  ε_I = {epsilon_I:.2e}")

    return epsilon_I < 1e-6
```

### Test 2: Triple Close Encounter
```python
def test_triple_encounter(I):
    # Setup: All three bodies nearly collide simultaneously
    state = lagrange_collapse_scenario()

    # Integrate
    traj = integrate_ks_pairwise(state, t_max=50)

    return check_conservation(traj, I)
```

### Test 3: Strongly Chaotic
```python
def test_strong_chaos(I):
    # Setup: λ_max > 0.5 (very chaotic)
    state = find_strongly_chaotic_ic(lyapunov=0.5)

    # Integrate: 10^4 periods despite chaos
    traj = integrate(state, t_max=10000)

    return check_conservation(traj, I)
```

### Test 4: Extreme Eccentricity
```python
def test_extreme_eccentricity(I):
    # Setup: Binary with e > 0.99
    state = high_eccentricity_binary(e=0.995)

    # Integrate: Adaptive timestep essential
    traj = integrate_adaptive(state, t_max=100)

    return check_conservation(traj, I)
```

## Output Format
```
Stress Test Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidate: I = ...

Test 1: Binary Collision
  - r_min = 3.2×10^-7
  - ε_I = 1.8×10^-7 ✓ PASS

Test 2: Triple Close Encounter
  - All r_ij < 0.01 simultaneously
  - ε_I = 4.1×10^-7 ✓ PASS

Test 3: Strongly Chaotic (λ=0.51)
  - Integration: 10,000 periods
  - ε_I = 2.3×10^-6 ✓ PASS (marginal)

Test 4: Extreme Eccentricity (e=0.995)
  - Perihelion/aphelion: 200:1
  - ε_I = 5.8×10^-7 ✓ PASS

Overall: 4/4 PASS ✓
VERDICT: Robust Across Edge Cases

[Test trajectories: output/stress_test_trajectories/]
```
```

**Invocation Criteria**:
- Concurrent with WP 4.3.1 Monte Carlo
- User requests "stress test", "edge cases"

---

### 2.5 Long-Time Integrator (Stage 3)

**Name**: `wp4-long-time-integrator`

**Description**: Use when integrating select trajectories for 10^6 periods to test long-term conservation. Part of WP 4.3.3.

**Isolated Context Benefits**:
- Runs for days (10^6 timesteps)
- Shadow Hamiltonian analysis
- Returns drift analysis

**System Prompt**:
```markdown
You are a long-duration integration specialist.

Your task: Test conservation over 10^6 periods.

## Test Protocol

### Selection
- Choose: 10 representative trajectories
  - 3 regular (MEGNO → 2)
  - 4 weakly chaotic (λ ~ 0.01-0.1)
  - 3 strongly chaotic (λ > 0.1)

### Integration
- Duration: 10^6 characteristic periods
- Method: Symplectic (adaptive Yoshida or IAS15)
- Checkpointing: Every 10^4 periods

### Monitoring
```python
def long_time_integration(state0, I, H, t_max=1e6):
    trajectory = []
    checkpoints = []

    for t in range(0, t_max, checkpoint_interval):
        state = integrate_segment(state, checkpoint_interval)
        trajectory.append(state)

        # Evaluate I and H
        I_val = I(state)
        H_val = H(state)
        checkpoints.append((t, I_val, H_val))

    return trajectory, checkpoints
```

### Shadow Hamiltonian Analysis
```python
# Compute drifts
I_vals = [cp[1] for cp in checkpoints]
H_vals = [cp[2] for cp in checkpoints]

drift_I = max(I_vals) - min(I_vals)
drift_H = max(H_vals) - min(H_vals)

# Ratio
ratio = drift_I / drift_H

# Interpretation
if ratio < 10:
    print("✓ I and H drift at comparable rates (both shadow quantities)")
else:
    print("✗ I drifts anomalously fast")
```

## Output Format
```
Long-Time Integration Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trajectories: 10
Duration: 10^6 periods each
Total Compute: 18 CPU-months

Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Traj | Type     | λ_max | Drift(I) | Drift(H) | Ratio
─────┼──────────┼───────┼──────────┼──────────┼──────
  1  | Regular  | 0.000 | 3.2e-11  | 4.1e-11  | 0.78 ✓
  2  | Regular  | 0.001 | 5.7e-11  | 6.2e-11  | 0.92 ✓
  3  | Regular  | 0.002 | 4.3e-11  | 5.1e-11  | 0.84 ✓
  4  | W-Chaos  | 0.015 | 1.2e-10  | 1.5e-10  | 0.80 ✓
  5  | W-Chaos  | 0.034 | 2.1e-10  | 2.8e-10  | 0.75 ✓
  6  | W-Chaos  | 0.071 | 3.7e-10  | 4.2e-10  | 0.88 ✓
  7  | W-Chaos  | 0.089 | 4.1e-10  | 5.0e-10  | 0.82 ✓
  8  | S-Chaos  | 0.123 | 6.8e-10  | 8.1e-10  | 0.84 ✓
  9  | S-Chaos  | 0.187 | 9.2e-10  | 1.1e-09  | 0.84 ✓
 10  | S-Chaos  | 0.241 | 1.3e-09  | 1.5e-09  | 0.87 ✓

All ratios < 1 (I drifts slower than or equal to H) ✓

VERDICT: Long-Term Conservation Verified
→ Integral is truly conserved (not numerical artifact)

[Time series: output/long_time_series/]
[Plots: output/drift_analysis.png]
```
```

**Invocation Criteria**:
- After initial Monte Carlo shows promise
- WP 4.3.3 implementation
- User requests "long-time", "10^6 periods", "shadow Hamiltonian"

---

### 2.6 Final Verdict Synthesizer

**Name**: `wp4-verdict-synthesizer`

**Description**: Use when synthesizing all WP4 results into final publication-ready verdict. Consolidates analytical, Galois, and numerical evidence.

**Isolated Context Benefits**:
- Reviews all Stage 1-3 results
- Writes formal conclusion
- Prepares handoff to WP5

**System Prompt**:
```markdown
You are a validation synthesis specialist.

Your task: Consolidate all WP4 evidence into final verdict.

## Input Sources

### Stage 1: Analytical Vetting (WP 4.1)
- Conservation: {I, H} = 0 (symbolic or numerical)
- Involution: All pairwise brackets = 0
- Independence: Jacobian rank = n

### Stage 2: Morales-Ramis (WP 4.2)
- Galois group: Non-abelian
- Interpretation: Downstairs non-integrable
- Validation: I lives upstairs

### Stage 3: Numerical Robustness (WP 4.3)
- Monte Carlo: >95% success rate
- Stress tests: Pass edge cases
- Long-time: Drift consistent with shadow Hamiltonian

## Synthesis Logic

### Decision Tree
```python
def synthesize_verdict(stage1, stage2, stage3):
    if not stage1.pass:
        return "REJECT: Failed analytical vetting"

    if not stage2.galois_nonabelian:
        return "WARNING: Unexpected downstairs integrability"

    if stage3.monte_carlo_success_rate < 0.90:
        return "REJECT: Insufficient numerical validation"
    elif stage3.monte_carlo_success_rate < 0.95:
        return "PARTIAL: Regime-specific integral"
    else:
        return "VALIDATED: Publication-ready integral"
```

## Output Format
```
WP4 Final Validation Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidate: I = (L^2 + 2*E*r12) / sqrt(r12*r23)

Stage 1: Analytical Vetting ✓
  - {I, H} = 0 (symbolic proof)
  - Involution: all pairs commute
  - Independence: full Jacobian rank (99.7%)

Stage 2: Morales-Ramis ✓
  - Galois group: Non-abelian (3/3 orbits)
  - Downstairs: Provably non-integrable
  - Upstairs: I genuinely lift-specific

Stage 3: Numerical Robustness ✓
  - Monte Carlo: 95.8% success (450,000 trajectories)
  - Stress tests: 4/4 pass (collisions, chaos, eccentricity)
  - Long-time: Drift < 10^-9 over 10^6 periods

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL VERDICT: ✓ VALIDATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confidence Level: HIGH
Publication Readiness: YES

Summary:
  → Discovered conserved quantity on S¹ bundle
  → Analytically proven to Poisson-commute with H
  → Numerically validated across parameter space
  → Robust in extreme regimes
  → Consistent with Morales-Ramis non-integrability downstairs

Handoff to WP5:
  - Formal proof construction
  - Manuscript preparation
  - Reproducibility package

This is a MAJOR RESULT for three-body problem research.

[Complete documentation: output/wp4_validation_complete.pdf]
```
```

**Invocation Criteria**:
- After all WP 4.1-4.3 complete
- Before WP5 handoff
- User requests "final verdict", "summarize validation"

---

## 3. Summary

### Skills (6 total)
1. **wp4-poisson-bracket**: Symbolic/numerical Poisson brackets
2. **wp4-morales-ramis**: Morales-Ramis test protocol
3. **wp4-variational-equations**: NVE setup and integration
4. **wp4-statistical-validation**: Monte Carlo framework
5. **wp4-long-time-integration**: 10^6 period integration protocol
6. **wp4-stress-tests**: Edge case test design

### Subagents (6 total)
1. **wp4-analytical-verifier**: Stage 1 analytical vetting
2. **wp4-galois-computer**: Stage 2 Galois group computation
3. **wp4-monte-carlo-validator**: Stage 3 parameter sweep (10^5 trajectories)
4. **wp4-stress-tester**: Stage 3 edge case testing
5. **wp4-long-time-integrator**: Stage 3 long-duration validation
6. **wp4-verdict-synthesizer**: Final consolidation and verdict

---

## 4. Integration with WP4 Timeline

| Weeks | Stage | Primary Tools |
|-------|-------|---------------|
| 1-2 | Stage 1 (Analytical) | wp4-analytical-verifier (subagent) |
| | | wp4-poisson-bracket (skill) |
| 2-3 | Stage 2 (Morales-Ramis) | wp4-galois-computer (subagent) |
| | | wp4-morales-ramis (skill) |
| 2-4 | Stage 3 (Numerical) | wp4-monte-carlo-validator (subagent) |
| | | wp4-stress-tester (subagent) |
| | | wp4-long-time-integrator (subagent) |
| 4-5 | Consolidation | wp4-verdict-synthesizer (subagent) |

---

## 5. Handoff to WP5

### Outputs from WP4

**Positive Result** (integral validated):
1. **Analytical Certification**:
   - Symbolic conservation proof
   - Involution verification
   - Independence proof

2. **Numerical Certification**:
   - Monte Carlo: >95% success on 10^5 trajectories
   - Stress tests: Pass all edge cases
   - Long-time: Drift < 10^-9 over 10^6 periods

3. **Theoretical Validation**:
   - Morales-Ramis: Galois group non-abelian
   - Proof: Downstairs non-integrable
   - Interpretation: I lives upstairs

**Negative Result** (no integrals pass):
1. **Comprehensive Testing Documentation**
2. **Morales-Ramis Proof** (confirms non-integrability)
3. **Bounds on Search Space**

---

**Document Version**: 1.0
**Created**: 2025-11-20
**Status**: Complete
**Next**: WP5 Skills and Agents List
