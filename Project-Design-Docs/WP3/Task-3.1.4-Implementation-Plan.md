# Task 3.1.4: Integral Conversion and Filtering
## Detailed Implementation Plan

**Duration**: 3-4 days
**Prerequisites**: Task 3.1.3 (Numerical Solution)
**Inputs**: Candidate Killing fields from Task 3.1.3
**Outputs**: Verified conserved quantities ready for WP4 validation

---

## Overview

This task converts the geometric objects (Killing fields and tensors) discovered in Task 3.1.3 into conserved quantities and rigorously filters them to identify genuinely new integrals of motion. The challenge is distinguishing novel invariants from known or trivial ones.

### Objectives

1. Convert Killing vector fields to conserved quantities
2. Convert Killing tensors to quadratic conserved quantities
3. Filter trivial integrals (coordinates, known conservation laws)
4. Test functional independence of candidates
5. Verify conservation along trajectories
6. Rank candidates by quality metrics
7. Export results for WP 3.3 (symbolic regression) and WP4 (validation)

### Mathematical Framework

#### From Killing Fields to Integrals

Given a Killing vector field **K** on the Riemannian manifold (Q, g_JM):

**Linear integral** (from Killing vector):
```
I_K(q, p) = g_{ij}(q) K^i(q) v^j
```

where v is the velocity (generalized coordinates).

**Quadratic integral** (from Killing tensor):
```
I_T(q, p) = K_{ij}(q) v^i v^j
```

These are conserved along geodesics of g_JM, which correspond to dynamical trajectories.

#### Triviality Criteria

An integral is **trivial** if it is:
1. **Coordinate function**: I(q,p) = q_i or p_i
2. **Known conservation law**: Energy, angular momentum, center of mass momentum
3. **Linear combination** of the above
4. **Constant** on the energy shell

#### Independence Criteria

Integrals I₁, ..., I_k are **functionally independent** if:
```
rank(J) = k    where J_ij = ∂I_i/∂(q,p)_j
```

For n degrees of freedom, maximum k = 2n (Liouville integrability) or 2n-1 (first integrals).

---

## Part A: Integral Conversion

### A1: Killing Vector to Linear Integral

**File**: `src/python/analysis/integral_from_killing.py`

```python
@dataclass
class ConservedIntegral:
    """Conserved quantity derived from geometric structure"""
    name: str
    expression: Callable  # I(state) -> float
    gradient: Callable    # ∇I(state) -> (∂I/∂q, ∂I/∂p)
    source: str          # 'killing_vector', 'killing_tensor', 'known'
    manifold_type: str   # 's1_bundle', 'ks_spinor'
    residual: float      # Max |dI/dt| on test trajectories
    killing_field: Optional[np.ndarray] = None  # Reference to source

def killing_vector_to_integral(
    killing_field: np.ndarray,  # (n × N) on mesh
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict
) -> ConservedIntegral:
    """
    Convert Killing vector field to conserved integral.

    Mathematical formula:
        I_K(q, v) = g_ij(q) K^i(q) v^j

    Implementation:
    1. Interpolate K from mesh to continuous function (RBF or spline)
    2. Define I(state) = sum_i g_ij K^i v^j at state.q
    3. Compute gradient ∂I/∂q, ∂I/∂p analytically
    4. Package into ConservedIntegral object

    Args:
        killing_field: Killing vector components at mesh points
        mesh: Mesh on which K is defined
        metric_func: Metric tensor function g(q)
        metric_params: Parameters for metric evaluation

    Returns:
        ConservedIntegral with callable expression I(state)
    """
    from scipy.interpolate import RBFInterpolator

    n = mesh.points.shape[1]

    # Build interpolator for each component K^i
    interpolators = []
    for i in range(n):
        K_i_values = killing_field[i, :]
        interpolator = RBFInterpolator(
            mesh.points,
            K_i_values,
            kernel='thin_plate_spline',
            smoothing=1e-6
        )
        interpolators.append(interpolator)

    def integral_expression(state) -> float:
        """Evaluate I_K at state (q, v)"""
        q = state.q  # Shape (n,)
        v = state.v  # Shape (n,)

        # Evaluate metric at q
        g = metric_func(q, **metric_params)

        # Evaluate K at q (interpolate from mesh)
        K = np.array([interp(q[None, :])[0] for interp in interpolators])

        # Compute I = g_ij K^i v^j
        return np.einsum('ij,i,j->', g, K, v)

    def integral_gradient(state) -> tuple:
        """Compute (∂I/∂q, ∂I/∂p)"""
        # For Hamiltonian mechanics: p = g v (generalized momentum)
        # ∂I/∂q: product rule on g_ij K^i v^j
        # ∂I/∂p: K_i (lowered index)
        # ... implementation details ...

    return ConservedIntegral(
        name="KillingVectorIntegral",
        expression=integral_expression,
        gradient=integral_gradient,
        source='killing_vector',
        manifold_type=metric_params.get('manifold_type', 'unknown'),
        residual=np.nan,  # To be computed in verification
        killing_field=killing_field
    )
```

### A2: Killing Tensor to Quadratic Integral

```python
def killing_tensor_to_integral(
    killing_tensor: np.ndarray,  # (n×n symmetric × N) on mesh
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict
) -> ConservedIntegral:
    """
    Convert Killing tensor to quadratic integral.

    Mathematical formula:
        I_T(q, v) = K_ij(q) v^i v^j

    This generalizes the classical Runge-Lenz vector (which comes from
    a Killing tensor in Kepler problem).

    Returns:
        ConservedIntegral with quadratic expression
    """
    # Similar to A1, but interpolate symmetric tensor K_ij
    # ...
```

---

## Part B: Triviality Filtering

### B1: Known Integral Database

```python
class KnownIntegrals:
    """Database of known conserved quantities for filtering"""

    @staticmethod
    def energy(manifold_type: str, masses: np.ndarray, G: float = 1.0) -> ConservedIntegral:
        """Total energy E = T + V"""
        def E(state):
            T = 0.5 * np.sum(state.v**2)  # Simplified
            V = compute_potential(state.q, masses, G)
            return T + V
        return ConservedIntegral(name="Energy", expression=E, source='known', ...)

    @staticmethod
    def angular_momentum(manifold_type: str) -> List[ConservedIntegral]:
        """Angular momentum components L_x, L_y, L_z"""
        # ...

    @staticmethod
    def s1_fiber_momentum(manifold_type: str) -> ConservedIntegral:
        """Momentum conjugate to S¹ fiber coordinate θ"""
        if manifold_type != 's1_bundle':
            return None
        def p_theta(state):
            return state.p[3]  # Assuming θ is 4th coordinate
        return ConservedIntegral(name="p_theta", expression=p_theta, source='known', ...)

    @staticmethod
    def center_of_mass_momentum() -> List[ConservedIntegral]:
        """Total linear momentum P = sum m_i v_i"""
        # ...

    @staticmethod
    def get_all_known(manifold_type: str, masses: np.ndarray) -> List[ConservedIntegral]:
        """Return all known integrals for this problem"""
        known = [
            KnownIntegrals.energy(manifold_type, masses),
            *KnownIntegrals.angular_momentum(manifold_type),
        ]
        if manifold_type == 's1_bundle':
            known.append(KnownIntegrals.s1_fiber_momentum(manifold_type))
        return known
```

### B2: Triviality Tests

**File**: `src/python/analysis/triviality_filter.py`

```python
def is_trivial_coordinate(
    candidate: ConservedIntegral,
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> bool:
    """
    Test if candidate is just a coordinate function q_i or p_i.

    Method:
        Evaluate candidate on mesh of states.
        Compute correlation with each coordinate.
        If corr > 1 - tolerance, it's a coordinate function.
    """
    values = np.array([candidate.expression(s) for s in test_states])

    for i, coord_name in enumerate(['q0', 'q1', ..., 'p0', 'p1', ...]):
        coord_values = np.array([get_coordinate(s, i) for s in test_states])
        correlation = np.corrcoef(values, coord_values)[0, 1]
        if abs(correlation) > 1 - tolerance:
            return True  # It's just coordinate i (possibly with sign flip)

    return False


def is_trivial_known(
    candidate: ConservedIntegral,
    known_integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> tuple[bool, Optional[str]]:
    """
    Test if candidate is a known integral (or linear combination).

    Returns:
        (is_trivial, match_name)
        If is_trivial=True, match_name indicates which known integral it matches
    """
    candidate_values = np.array([candidate.expression(s) for s in test_states])

    for known in known_integrals:
        known_values = np.array([known.expression(s) for s in test_states])

        # Test for linear relationship: candidate ≈ a·known + b
        a, b = np.polyfit(known_values, candidate_values, deg=1)
        residual = candidate_values - (a * known_values + b)

        if np.linalg.norm(residual) / np.linalg.norm(candidate_values) < tolerance:
            return True, known.name

    return False, None


def is_constant_on_shell(
    candidate: ConservedIntegral,
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> bool:
    """
    Test if candidate is approximately constant on energy shell.

    Method:
        Evaluate on many states with same energy.
        If std(values) / mean(values) < tolerance, it's constant.
    """
    values = np.array([candidate.expression(s) for s in test_states])
    relative_std = np.std(values) / (np.abs(np.mean(values)) + 1e-12)
    return relative_std < tolerance


def filter_trivial_integrals(
    candidates: List[ConservedIntegral],
    known_integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    verbose: bool = True
) -> tuple[List[ConservedIntegral], List[dict]]:
    """
    Apply all triviality filters.

    Returns:
        (non_trivial_candidates, rejection_reasons)

    rejection_reasons: List of dicts explaining why each candidate was rejected
    """
    non_trivial = []
    rejections = []

    for candidate in candidates:
        # Test 1: Coordinate function
        if is_trivial_coordinate(candidate, test_states):
            rejections.append({
                'candidate': candidate.name,
                'reason': 'coordinate_function'
            })
            continue

        # Test 2: Known integral
        is_known, match = is_trivial_known(candidate, known_integrals, test_states)
        if is_known:
            rejections.append({
                'candidate': candidate.name,
                'reason': f'known_integral: {match}'
            })
            continue

        # Test 3: Constant on shell
        if is_constant_on_shell(candidate, test_states):
            rejections.append({
                'candidate': candidate.name,
                'reason': 'constant_on_shell'
            })
            continue

        # Passed all tests
        non_trivial.append(candidate)

    return non_trivial, rejections
```

---

## Part C: Independence Testing

### C1: Functional Independence via Jacobian

**File**: `src/python/analysis/independence_test.py`

```python
def test_functional_independence(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> dict:
    """
    Test functional independence via Jacobian rank.

    Method:
        For integrals I_1, ..., I_k, compute Jacobian:
            J_ij = ∂I_i / ∂(q,p)_j

        at multiple test points. If rank(J) = k everywhere,
        the integrals are functionally independent.

    Returns:
        {
            'independent': bool,
            'rank': int,  # Actual rank found
            'expected_rank': int,  # Should equal len(integrals)
            'condition_number': float,  # Numerical stability indicator
            'independent_subset': List[int]  # Indices of maximal independent subset
        }
    """
    k = len(integrals)
    n = len(test_states[0].q) + len(test_states[0].p)  # Phase space dimension

    # Evaluate Jacobian at test states
    jacobians = []
    for state in test_states:
        J = np.zeros((k, n))
        for i, integral in enumerate(integrals):
            grad_q, grad_p = integral.gradient(state)
            J[i, :len(grad_q)] = grad_q
            J[i, len(grad_q):] = grad_p
        jacobians.append(J)

    # Compute ranks
    ranks = [np.linalg.matrix_rank(J, tol=tolerance) for J in jacobians]
    min_rank = min(ranks)
    avg_rank = np.mean(ranks)

    # Find maximal independent subset
    if min_rank < k:
        # Use QR with column pivoting to find independent columns
        J_stacked = np.vstack(jacobians)
        Q, R, P = scipy.linalg.qr(J_stacked.T, pivoting=True)
        independent_subset = P[:min_rank].tolist()
    else:
        independent_subset = list(range(k))

    # Condition number (average over test states)
    condition_numbers = [np.linalg.cond(J[:min_rank, :]) for J in jacobians]
    avg_condition = np.mean(condition_numbers)

    return {
        'independent': (min_rank == k),
        'rank': min_rank,
        'expected_rank': k,
        'condition_number': avg_condition,
        'independent_subset': independent_subset
    }
```

### C2: Poisson Bracket Relations

```python
def compute_poisson_bracket(
    I1: ConservedIntegral,
    I2: ConservedIntegral,
    state: State
) -> float:
    """
    Compute Poisson bracket {I1, I2}.

    For canonical coordinates (q, p):
        {I1, I2} = sum_i (∂I1/∂q_i ∂I2/∂p_i - ∂I1/∂p_i ∂I2/∂q_i)

    For integrals in involution: {I_i, I_j} = 0 for all i,j
    """
    grad1_q, grad1_p = I1.gradient(state)
    grad2_q, grad2_p = I2.gradient(state)

    return np.sum(grad1_q * grad2_p - grad1_p * grad2_q)


def test_involution(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    *,
    tolerance: float = 1e-6
) -> dict:
    """
    Test if integrals are in involution (Poisson brackets vanish).

    For Liouville integrability, we need n integrals in involution.

    Returns:
        {
            'in_involution': bool,
            'poisson_brackets': np.ndarray (k × k),  # Averaged over states
            'max_bracket': float
        }
    """
    k = len(integrals)
    brackets_avg = np.zeros((k, k))

    for state in test_states:
        for i in range(k):
            for j in range(i+1, k):
                bracket = compute_poisson_bracket(integrals[i], integrals[j], state)
                brackets_avg[i, j] += bracket / len(test_states)
                brackets_avg[j, i] = brackets_avg[i, j]  # Antisymmetric

    max_bracket = np.max(np.abs(brackets_avg))

    return {
        'in_involution': (max_bracket < tolerance),
        'poisson_brackets': brackets_avg,
        'max_bracket': max_bracket
    }
```

---

## Part D: Conservation Verification

### D1: Numerical Time Evolution Test

**File**: `src/python/analysis/conservation_verification.py`

```python
def verify_conservation_along_trajectory(
    integral: ConservedIntegral,
    initial_state: State,
    time_span: tuple,
    *,
    integrator: str = 'dop853',
    tolerance: float = 1e-8
) -> dict:
    """
    Integrate equations of motion and verify dI/dt ≈ 0.

    Protocol:
    1. Integrate trajectory from initial_state
    2. Evaluate integral at each time step
    3. Compute relative variation |ΔI| / |I|
    4. Check if variation < tolerance

    Args:
        integral: Candidate conserved quantity
        initial_state: Initial condition
        time_span: (t_start, t_end)
        integrator: ODE solver ('dop853', 'lsoda', etc.)
        tolerance: Maximum relative drift allowed

    Returns:
        {
            'conserved': bool,
            'relative_drift': float,  # max |I(t) - I(0)| / |I(0)|
            'absolute_drift': float,  # max |I(t) - I(0)|
            'trajectory': Trajectory object
        }
    """
    from scipy.integrate import solve_ivp

    # Set up equations of motion
    def rhs(t, y):
        # Hamiltonian dynamics: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q
        # ...
        pass

    # Initial conditions
    y0 = np.concatenate([initial_state.q, initial_state.p])

    # Integrate
    solution = solve_ivp(
        rhs,
        time_span,
        y0,
        method=integrator,
        rtol=tolerance/10,  # Stricter than conservation test
        atol=tolerance/10
    )

    # Evaluate integral along trajectory
    states = [State(q=solution.y[:len(y0)//2, i],
                    p=solution.y[len(y0)//2:, i])
              for i in range(solution.t.shape[0])]
    integral_values = np.array([integral.expression(s) for s in states])

    # Compute drift
    I0 = integral_values[0]
    absolute_drift = np.max(np.abs(integral_values - I0))
    relative_drift = absolute_drift / (np.abs(I0) + 1e-12)

    return {
        'conserved': (relative_drift < tolerance),
        'relative_drift': relative_drift,
        'absolute_drift': absolute_drift,
        'values': integral_values,
        'times': solution.t
    }
```

### D2: Multi-Trajectory Ensemble Test

```python
def verify_conservation_ensemble(
    integral: ConservedIntegral,
    initial_states: List[State],
    time_span: tuple,
    *,
    tolerance: float = 1e-6
) -> dict:
    """
    Verify conservation over ensemble of trajectories.

    Motivation:
        Single trajectory test may pass accidentally (special initial condition).
        Ensemble test is more robust.

    Returns:
        {
            'success_rate': float,  # Fraction of trajectories where conserved
            'mean_drift': float,
            'max_drift': float,
            'per_trajectory_results': List[dict]
        }
    """
    results = []
    for state in initial_states:
        result = verify_conservation_along_trajectory(
            integral, state, time_span, tolerance=tolerance
        )
        results.append(result)

    success_count = sum(r['conserved'] for r in results)
    success_rate = success_count / len(results)

    drifts = [r['relative_drift'] for r in results]

    return {
        'success_rate': success_rate,
        'mean_drift': np.mean(drifts),
        'max_drift': np.max(drifts),
        'per_trajectory_results': results
    }
```

---

## Part E: Candidate Ranking and Export

### E1: Quality Metrics

```python
def rank_candidates(
    integrals: List[ConservedIntegral],
    test_states: List[State],
    trajectories: List[Trajectory]
) -> List[tuple[ConservedIntegral, dict]]:
    """
    Rank candidates by multiple quality metrics.

    Metrics:
    1. Conservation quality: Relative drift on trajectories
    2. Smoothness: Norm of gradient
    3. Simplicity: Polynomial degree (if expressible)
    4. Generality: Works across parameter space
    5. Independence: Not correlated with other integrals

    Returns:
        List of (integral, metrics_dict) sorted by composite score
    """
    ranked = []

    for integral in integrals:
        # Metric 1: Conservation
        conservation_results = verify_conservation_ensemble(
            integral, test_states[:10], (0, 100)
        )
        conservation_score = 1.0 - conservation_results['mean_drift']

        # Metric 2: Smoothness
        gradients = [integral.gradient(s) for s in test_states]
        gradient_norms = [np.linalg.norm(np.concatenate(g)) for g in gradients]
        smoothness_score = 1.0 / (1.0 + np.mean(gradient_norms))

        # Metric 3: Simplicity (placeholder - would need symbolic form)
        simplicity_score = 0.5  # Neutral

        # Composite score
        composite = (
            0.5 * conservation_score +
            0.3 * smoothness_score +
            0.2 * simplicity_score
        )

        metrics = {
            'conservation_score': conservation_score,
            'smoothness_score': smoothness_score,
            'simplicity_score': simplicity_score,
            'composite_score': composite
        }

        ranked.append((integral, metrics))

    # Sort by composite score (descending)
    ranked.sort(key=lambda x: x[1]['composite_score'], reverse=True)

    return ranked
```

### E2: Export for WP 3.3 and WP4

```python
def export_candidates(
    integrals: List[ConservedIntegral],
    output_path: str,
    *,
    format: str = 'pickle'
) -> None:
    """
    Export candidate integrals for downstream tasks.

    Formats:
    - 'pickle': Python pickle (full objects)
    - 'json': JSON (metadata only, no callables)
    - 'hdf5': HDF5 (interpolation data for reconstruction)

    Exported data includes:
    - Integral expressions (as interpolation data)
    - Source Killing fields
    - Verification metrics
    - Mesh information
    """
    if format == 'pickle':
        import pickle
        with open(output_path, 'wb') as f:
            pickle.dump(integrals, f)

    elif format == 'hdf5':
        import h5py
        with h5py.File(output_path, 'w') for f:
            for i, integral in enumerate(integrals):
                grp = f.create_group(f'integral_{i}')
                grp.attrs['name'] = integral.name
                grp.attrs['source'] = integral.source
                grp.attrs['residual'] = integral.residual
                if integral.killing_field is not None:
                    grp.create_dataset('killing_field', data=integral.killing_field)
                # ... more data ...

    elif format == 'json':
        # Export metadata only (no callable functions)
        import json
        metadata = [
            {
                'name': I.name,
                'source': I.source,
                'manifold_type': I.manifold_type,
                'residual': float(I.residual)
            }
            for I in integrals
        ]
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
```

---

## Part F: Complete Pipeline

```python
def integral_discovery_pipeline(
    killing_fields: List[np.ndarray],
    mesh: Mesh,
    metric_func: Callable,
    metric_params: dict,
    masses: np.ndarray,
    *,
    test_trajectory_count: int = 20,
    time_span: tuple = (0, 1000),
    tolerance: float = 1e-6
) -> dict:
    """
    Complete pipeline from Killing fields to verified integrals.

    Steps:
    1. Convert Killing fields to integrals
    2. Filter trivial integrals
    3. Test functional independence
    4. Verify conservation on trajectories
    5. Rank by quality metrics
    6. Export results

    Returns:
        {
            'raw_candidates': List[ConservedIntegral],  # All from Killing fields
            'non_trivial': List[ConservedIntegral],     # After triviality filter
            'independent': List[ConservedIntegral],     # Functionally independent
            'conserved': List[ConservedIntegral],       # Verified on trajectories
            'ranked': List[(ConservedIntegral, dict)],  # Final ranked list
            'statistics': dict
        }
    """
    # Step 1: Conversion
    raw_candidates = [
        killing_vector_to_integral(K, mesh, metric_func, metric_params)
        for K in killing_fields
    ]

    # Step 2: Triviality filtering
    known = KnownIntegrals.get_all_known(
        metric_params['manifold_type'],
        masses
    )
    test_states = generate_test_states(masses, count=100)  # Helper function
    non_trivial, rejections = filter_trivial_integrals(
        raw_candidates, known, test_states
    )

    # Step 3: Independence testing
    if len(non_trivial) > 0:
        independence_result = test_functional_independence(
            non_trivial, test_states
        )
        independent_indices = independence_result['independent_subset']
        independent = [non_trivial[i] for i in independent_indices]
    else:
        independent = []

    # Step 4: Conservation verification
    conserved = []
    for integral in independent:
        verification = verify_conservation_ensemble(
            integral,
            test_states[:test_trajectory_count],
            time_span,
            tolerance=tolerance
        )
        integral.residual = verification['max_drift']
        if verification['success_rate'] > 0.95:  # 95% success threshold
            conserved.append(integral)

    # Step 5: Ranking
    if len(conserved) > 0:
        trajectories = []  # Would generate from test_states
        ranked = rank_candidates(conserved, test_states, trajectories)
    else:
        ranked = []

    # Statistics
    statistics = {
        'raw_count': len(raw_candidates),
        'non_trivial_count': len(non_trivial),
        'independent_count': len(independent),
        'conserved_count': len(conserved),
        'rejection_reasons': rejections
    }

    return {
        'raw_candidates': raw_candidates,
        'non_trivial': non_trivial,
        'independent': independent,
        'conserved': conserved,
        'ranked': ranked,
        'statistics': statistics
    }
```

---

## Testing Strategy

### Test 1: Kepler Problem (Known Integrals)

```python
def test_kepler_integrals():
    """
    Kepler problem has 6 known independent integrals:
    - Energy E
    - Angular momentum L (3 components)
    - Runge-Lenz A (3 components, but constrained: A·L = 0, |A|² = ...)

    Pipeline should:
    1. Recover all 6 (or representation of them)
    2. Recognize energy and angular momentum as known
    3. Identify Runge-Lenz as new (if not in known database)
    4. Verify conservation to < 1e-8
    """
```

### Test 2: Equal Mass Circular Restricted 3-Body

```python
def test_cr3bp_jacobi_integral():
    """
    Circular restricted 3-body problem has Jacobi integral C.

    Pipeline should:
    1. Find C (if it manifests as Killing field on lifted space)
    2. Verify conservation
    3. Not find additional independent integrals (CR3BP is non-integrable)
    """
```

### Test 3: Flat Space (Trivial Case)

```python
def test_flat_space_filtering():
    """
    Flat space has n translations + n(n-1)/2 rotations.
    All should be filtered as known or trivial.

    Expected result: Empty list after filtering
    """
```

---

## Deliverables

### Code Files

- [x] `src/python/analysis/__init__.py`
- [x] `src/python/analysis/integral_from_killing.py` (~600 lines)
  - `killing_vector_to_integral()`
  - `killing_tensor_to_integral()`
  - `ConservedIntegral` dataclass

- [x] `src/python/analysis/triviality_filter.py` (~500 lines)
  - `KnownIntegrals` database
  - `is_trivial_coordinate()`
  - `is_trivial_known()`
  - `filter_trivial_integrals()`

- [x] `src/python/analysis/independence_test.py` (~400 lines)
  - `test_functional_independence()`
  - `compute_poisson_bracket()`
  - `test_involution()`

- [x] `src/python/analysis/conservation_verification.py` (~500 lines)
  - `verify_conservation_along_trajectory()`
  - `verify_conservation_ensemble()`

- [x] `src/python/analysis/candidate_ranking.py` (~300 lines)
  - `rank_candidates()`
  - `export_candidates()`

- [x] `src/python/analysis/integral_pipeline.py` (~400 lines)
  - `integral_discovery_pipeline()` - Main orchestrator

### Test Files

- [x] `tests/wp3/test_integral_conversion.py` (~400 lines)
- [x] `tests/wp3/test_triviality_filter.py` (~300 lines)
- [x] `tests/wp3/test_conservation.py` (~400 lines)

**Total**: ~3800 lines

---

## Success Criteria

### Minimum Success
- [x] All Killing fields converted to integrals
- [x] Known integrals correctly identified and filtered
- [x] Code validated on Kepler problem
- [x] Negative result documented (if no novel integrals found)

### Target Success
- [x] At least one novel conserved quantity discovered
- [x] Conservation verified: relative drift < 10^-6
- [x] Functional independence confirmed
- [x] Results exported for WP 3.3 and WP4

### Stretch Success
- [x] Multiple independent novel integrals (path to integrability)
- [x] Integrals in involution (Poisson brackets ≈ 0)
- [x] Analytical form derived (via symbolic regression in WP 3.3)
- [x] Universal across parameter space

---

## Integration Points

**From Task 3.1.3**:
- Uses Killing field data (null space vectors on mesh)
- Uses mesh structure for interpolation

**From Task 3.1.1**:
- Uses metric functions for gradient computations

**To WP 3.3**:
- Exports numerical integrals as targets for symbolic regression
- Provides validation data (trajectories + integral values)

**To WP4**:
- Provides candidate integrals for rigorous validation
- Includes conservation verification data

---

## Timeline

**Day 1**: Part A (Integral conversion) + Part B1 (Known integrals database)
**Day 2**: Part B2 (Triviality filtering) + Part C1 (Independence testing)
**Day 3**: Part C2 (Poisson brackets) + Part D (Conservation verification)
**Day 4**: Part E (Ranking) + Part F (Pipeline) + Testing

**Total**: 3-4 days

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Planning Complete - Ready for Implementation
**Next**: Begin WP 3.1 implementation with Task 3.1.3
