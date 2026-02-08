# Task 3.2.1: High-Precision Data Generation
## Implementation Plan

**Duration**: 4-5 days
**Priority**: Critical (blocks all other WP 3.2 tasks)
**Dependencies**: WP1 (integrators), WP2 (lifted dynamics)

---

## Overview

Generate 10⁵-10⁶ high-quality trajectory segments on lifted manifolds (S¹ bundle and KS-Spinor) to train structure-preserving neural networks.

**Quality Requirements**:
- Energy conservation: |ΔE|/E < 10⁻¹²
- Symplectic structure preservation
- Diverse parameter space coverage
- Time-reversibility verification

---

## Part A: Parameter Space Sampling

### A.1: Latin Hypercube Sampling (1 day)

**File**: `src/python/ml/parameter_sampling.py`

```python
from dataclasses import dataclass
from typing import Tuple, Dict
import numpy as np
from scipy.stats import qmc

@dataclass
class ParameterRanges:
    """Parameter space for 3-body problem."""
    mass_ratio: Tuple[float, float]      # μ = m₂/m₁ ∈ [0.01, 0.5]
    mass_3_ratio: Tuple[float, float]    # m₃/(m₁+m₂) ∈ [0.01, 1.0]
    energy: Tuple[float, float]          # E ∈ [-2, -0.1] (bound orbits)
    angular_momentum: Tuple[float, float] # L ∈ [0.5, 3.0]
    eccentricity: Tuple[float, float]    # e ∈ [0, 0.9] (avoid parabolic)

@dataclass
class InitialCondition:
    """Single initial condition sample."""
    masses: np.ndarray  # (3,)
    energy: float
    angular_momentum: float
    position: np.ndarray  # (3, 3) in center-of-mass frame
    velocity: np.ndarray  # (3, 3)
    metadata: Dict

def generate_lhs_samples(
    param_ranges: ParameterRanges,
    num_samples: int,
    seed: int = 42
) -> List[InitialCondition]:
    """
    Generate initial conditions via Latin Hypercube Sampling.

    Steps:
    1. Sample parameter space (μ, m₃, E, L, e) via LHS
    2. For each sample, construct consistent IC:
       a) Fix total mass M = 1 (normalize)
       b) Compute individual masses from ratios
       c) Sample positions on energy surface
       d) Compute velocities from E, L constraints
       e) Apply center-of-mass correction
    3. Validate: E_computed ≈ E_target, L_computed ≈ L_target

    Returns:
        List of validated initial conditions
    """
    sampler = qmc.LatinHypercube(d=5, seed=seed)
    samples = sampler.random(n=num_samples)

    # Scale to parameter ranges
    scaled = qmc.scale(
        samples,
        [
            param_ranges.mass_ratio,
            param_ranges.mass_3_ratio,
            param_ranges.energy,
            param_ranges.angular_momentum,
            param_ranges.eccentricity
        ]
    )

    initial_conditions = []
    for i in range(num_samples):
        mu, m3_ratio, E, L, e = scaled[i]

        # Construct masses
        m1 = 1.0 / (1 + mu + m3_ratio * (1 + mu))
        m2 = mu * m1
        m3 = m3_ratio * (m1 + m2)
        masses = np.array([m1, m2, m3])

        # Generate position/velocity via Keplerian sampling
        # (use restricted problem as template, perturb for 3rd body)
        q, v = _sample_keplerian_like(masses, E, L, e)

        # Validate constraints
        E_actual = compute_energy(q, v, masses)
        L_actual = compute_angular_momentum(q, v, masses)

        if abs(E_actual - E) / abs(E) < 0.01 and abs(L_actual - L) / L < 0.01:
            ic = InitialCondition(
                masses=masses,
                energy=E,
                angular_momentum=L,
                position=q,
                velocity=v,
                metadata={'eccentricity': e, 'sample_id': i}
            )
            initial_conditions.append(ic)

    return initial_conditions

def _sample_keplerian_like(
    masses: np.ndarray,
    E: float,
    L: float,
    e: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sample position/velocity for given E, L, e.

    Strategy:
    - Start with 2-body Keplerian orbit (m₁-m₂)
    - Place m₃ at random position respecting E, L
    - Iterate to satisfy constraints (Newton's method)
    """
    # TODO: Implement iterative constraint satisfaction
    pass
```

**Deliverables**:
- [ ] `parameter_sampling.py` (~300 lines)
- [ ] Unit tests: uniform coverage, constraint satisfaction
- [ ] Validation: Plot parameter space distribution (corner plots)

---

## Part B: Trajectory Integration (2 days)

### B.1: High-Precision Integration

**File**: `src/python/ml/trajectory_integration.py`

```python
from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np
from scipy.integrate import solve_ivp

@dataclass
class Trajectory:
    """Single integrated trajectory."""
    times: np.ndarray          # (N_steps,)
    states: np.ndarray         # (N_steps, dim)
    derivatives: np.ndarray    # (N_steps, dim)
    energy_drift: float        # |ΔE|/E
    symplectic_error: float    # ||dω||
    initial_condition: InitialCondition
    manifold_type: str         # 's1' or 'ks'
    integration_time: float    # seconds

@dataclass
class IntegrationConfig:
    """Integration parameters."""
    integrator: str = 'DOP853'  # Runge-Kutta 8(5,3)
    rtol: float = 1e-13
    atol: float = 1e-14
    max_step: float = 0.01
    dense_output: bool = True

def integrate_s1_bundle_trajectory(
    ic: InitialCondition,
    t_span: float,
    dt_output: float,
    config: IntegrationConfig
) -> Optional[Trajectory]:
    """
    Integrate on S¹ bundle with lifted Jacobi-Maupertuis metric.

    State vector: z = (s, θ, p_s, p_θ) ∈ ℝ³ × S¹ × ℝ⁴
    - s: shape space coordinates (3D)
    - θ: fiber coordinate (S¹)
    - p_s, p_θ: conjugate momenta

    Equations of motion: dz/dt = J ∇H_JM(z)

    Returns:
        Trajectory if successful (energy drift < 1e-10)
        None if integration failed quality checks
    """
    from ..lifts.s1_bundle import lift_to_s1_bundle, s1_hamiltonian

    # Convert IC to lifted coordinates
    z0 = lift_to_s1_bundle(ic.position, ic.velocity, ic.masses)

    # Define dynamics
    def rhs(t, z):
        return s1_hamiltonian.dynamics(z, ic.masses, ic.energy)

    # Integrate
    times = np.arange(0, t_span, dt_output)
    sol = solve_ivp(
        rhs,
        t_span=(0, t_span),
        y0=z0,
        method=config.integrator,
        t_eval=times,
        rtol=config.rtol,
        atol=config.atol,
        max_step=config.max_step,
        dense_output=config.dense_output
    )

    if not sol.success:
        return None

    # Compute derivatives at each point
    derivatives = np.array([rhs(t, sol.y[:, i]) for i, t in enumerate(sol.t)])

    # Quality checks
    energies = np.array([
        s1_hamiltonian.energy(sol.y[:, i], ic.masses)
        for i in range(len(sol.t))
    ])
    energy_drift = np.abs(energies - energies[0]).max() / np.abs(energies[0])

    # Symplectic check: ω(dz/dt, dz/dt) should be conserved
    symplectic_error = _check_symplectic_structure(sol.y, derivatives)

    if energy_drift > 1e-10:
        return None  # Reject poor integration

    return Trajectory(
        times=sol.t,
        states=sol.y.T,  # (N_steps, dim)
        derivatives=derivatives,
        energy_drift=energy_drift,
        symplectic_error=symplectic_error,
        initial_condition=ic,
        manifold_type='s1',
        integration_time=sol.t[-1]
    )

def integrate_ks_spinor_trajectory(
    ic: InitialCondition,
    t_span: float,
    dt_output: float,
    config: IntegrationConfig
) -> Optional[Trajectory]:
    """
    Integrate on KS-Spinor manifold (9D).

    State vector: z = (u, v, τ) ∈ ℝ¹² × ℝ × ℝ
    - u: spinor coordinates (4D × 3 bodies = 12D)
    - v: spinor velocities (12D)
    - τ: fictitious time

    Similar structure to S¹ bundle version.
    """
    # TODO: Implement KS integration
    pass

def _check_symplectic_structure(
    states: np.ndarray,
    derivatives: np.ndarray
) -> float:
    """
    Verify symplectic 2-form is preserved.

    For Hamiltonian systems: ω = dq ∧ dp is conserved.
    Numerically: ω_ij = ∂q_i/∂t · ∂p_j/∂t - ∂q_j/∂t · ∂p_i/∂t
    Should remain constant along trajectory.
    """
    n = states.shape[1] // 2
    q_dot = derivatives[:, :n]
    p_dot = derivatives[:, n:]

    # Compute ω at each timestep
    omega_values = []
    for i in range(len(states)):
        omega = np.sum(q_dot[i] * p_dot[i])  # Simplified check
        omega_values.append(omega)

    omega_drift = np.std(omega_values) / (np.abs(np.mean(omega_values)) + 1e-14)
    return omega_drift
```

**Deliverables**:
- [ ] `trajectory_integration.py` (~400 lines)
- [ ] Integration tests on known cases (harmonic, Kepler)
- [ ] Quality validation: Energy drift histograms, symplectic error plots

---

## Part C: Data Augmentation (1 day)

### C.1: Symmetry Transformations

**File**: `src/python/ml/data_augmentation.py`

```python
def augment_via_permutations(
    trajectory: Trajectory
) -> List[Trajectory]:
    """
    Apply permutation symmetry for equal-mass bodies.

    For m₁ = m₂ = m₃: 3! = 6 permutations
    Each permutation gives equivalent trajectory

    Returns:
        List of 6 trajectories (including original)
    """
    if not _are_masses_equal(trajectory.initial_condition.masses):
        return [trajectory]  # No symmetry

    # Generate all permutations
    permutations = [
        (0, 1, 2), (0, 2, 1), (1, 0, 2),
        (1, 2, 0), (2, 0, 1), (2, 1, 0)
    ]

    augmented = []
    for perm in permutations:
        states_perm = _permute_states(trajectory.states, perm)
        deriv_perm = _permute_states(trajectory.derivatives, perm)

        traj_perm = Trajectory(
            times=trajectory.times,
            states=states_perm,
            derivatives=deriv_perm,
            energy_drift=trajectory.energy_drift,
            symplectic_error=trajectory.symplectic_error,
            initial_condition=_permute_ic(trajectory.initial_condition, perm),
            manifold_type=trajectory.manifold_type,
            integration_time=trajectory.integration_time
        )
        augmented.append(traj_perm)

    return augmented

def augment_via_time_reversal(
    trajectory: Trajectory
) -> Trajectory:
    """
    Hamiltonian systems are time-reversible: H(q, p) = H(q, -p).

    Time-reversed trajectory: (t, q, p) → (-t, q, -p)
    """
    reversed_traj = Trajectory(
        times=-trajectory.times[::-1],
        states=_reverse_momenta(trajectory.states[::-1]),
        derivatives=-trajectory.derivatives[::-1],
        energy_drift=trajectory.energy_drift,
        symplectic_error=trajectory.symplectic_error,
        initial_condition=trajectory.initial_condition,
        manifold_type=trajectory.manifold_type,
        integration_time=trajectory.integration_time
    )
    return reversed_traj

def augment_via_virial_scaling(
    trajectory: Trajectory,
    scale_factor: float
) -> Trajectory:
    """
    Virial theorem: Scaling transformation preserves dynamics.

    For gravitational potential V = -G m₁m₂/r:
    - Positions: q → λq
    - Velocities: v → v/√λ
    - Time: t → λ^(3/2) t
    - Energy: E → E/λ
    """
    # TODO: Implement virial scaling
    pass
```

**Deliverables**:
- [ ] `data_augmentation.py` (~250 lines)
- [ ] Tests: Verify symmetries preserve energy, angular momentum
- [ ] Documentation: When to use each augmentation

---

## Part D: Dataset Assembly and Storage (1 day)

### D.1: HDF5 Dataset Format

**File**: `src/python/ml/dataset_builder.py`

```python
import h5py
from typing import List

class TrajectoryDataset:
    """
    HDF5 dataset for trajectory data.

    Structure:
    dataset.h5
    ├── metadata/
    │   ├── param_ranges
    │   ├── integration_config
    │   └── statistics
    ├── train/
    │   ├── states (N, T, dim)
    │   ├── derivatives (N, T, dim)
    │   ├── times (N, T)
    │   ├── energies (N,)
    │   ├── masses (N, 3)
    │   └── trajectory_ids (N,)
    ├── validation/
    │   └── [same structure]
    └── test/
        └── [same structure]
    """

    def __init__(self, filepath: str, mode: str = 'r'):
        self.filepath = filepath
        self.file = h5py.File(filepath, mode)

    def create_dataset_structure(
        self,
        train_size: int,
        val_size: int,
        test_size: int,
        trajectory_length: int,
        state_dim: int
    ):
        """Initialize HDF5 structure with chunking and compression."""
        for split in ['train', 'validation', 'test']:
            if split == 'train':
                N = train_size
            elif split == 'validation':
                N = val_size
            else:
                N = test_size

            grp = self.file.create_group(split)

            # States and derivatives: chunk by trajectory for fast random access
            grp.create_dataset(
                'states',
                shape=(N, trajectory_length, state_dim),
                dtype=np.float32,  # Mixed precision
                chunks=(1, trajectory_length, state_dim),
                compression='gzip',
                compression_opts=4
            )
            grp.create_dataset(
                'derivatives',
                shape=(N, trajectory_length, state_dim),
                dtype=np.float32,
                chunks=(1, trajectory_length, state_dim),
                compression='gzip',
                compression_opts=4
            )
            grp.create_dataset('times', shape=(N, trajectory_length), dtype=np.float32)
            grp.create_dataset('energies', shape=(N,), dtype=np.float64)
            grp.create_dataset('masses', shape=(N, 3), dtype=np.float64)
            grp.create_dataset('trajectory_ids', shape=(N,), dtype=np.int64)

    def add_trajectories(
        self,
        split: str,
        trajectories: List[Trajectory],
        start_idx: int = 0
    ):
        """Add batch of trajectories to dataset."""
        grp = self.file[split]

        for i, traj in enumerate(trajectories):
            idx = start_idx + i
            grp['states'][idx] = traj.states
            grp['derivatives'][idx] = traj.derivatives
            grp['times'][idx] = traj.times
            grp['energies'][idx] = traj.initial_condition.energy
            grp['masses'][idx] = traj.initial_condition.masses
            grp['trajectory_ids'][idx] = idx

    def close(self):
        self.file.close()

def build_dataset(
    num_trajectories: int,
    param_ranges: ParameterRanges,
    integration_config: IntegrationConfig,
    output_path: str,
    manifold_type: str = 's1',
    train_split: float = 0.7,
    val_split: float = 0.15,
    test_split: float = 0.15,
    num_workers: int = 8
) -> TrajectoryDataset:
    """
    Main pipeline to generate complete dataset.

    Steps:
    1. Generate parameter samples (LHS)
    2. Integrate trajectories (parallel)
    3. Apply augmentation
    4. Quality filtering
    5. Train/val/test split
    6. Write to HDF5

    Uses multiprocessing for parallel integration.
    """
    from multiprocessing import Pool

    # Step 1: Sample parameters
    ics = generate_lhs_samples(param_ranges, num_trajectories)

    # Step 2: Integrate (parallel)
    integrate_func = (
        integrate_s1_bundle_trajectory if manifold_type == 's1'
        else integrate_ks_spinor_trajectory
    )

    with Pool(num_workers) as pool:
        trajectories = pool.starmap(
            integrate_func,
            [(ic, 100.0, 0.01, integration_config) for ic in ics]
        )

    # Filter failed integrations
    trajectories = [t for t in trajectories if t is not None]

    # Step 3: Augmentation
    augmented = []
    for traj in trajectories:
        augmented.extend(augment_via_permutations(traj))
        augmented.append(augment_via_time_reversal(traj))

    # Step 4: Train/val/test split
    np.random.shuffle(augmented)
    n = len(augmented)
    train_end = int(n * train_split)
    val_end = train_end + int(n * val_split)

    train_trajs = augmented[:train_end]
    val_trajs = augmented[train_end:val_end]
    test_trajs = augmented[val_end:]

    # Step 5: Write to HDF5
    dataset = TrajectoryDataset(output_path, mode='w')
    dataset.create_dataset_structure(
        train_size=len(train_trajs),
        val_size=len(val_trajs),
        test_size=len(test_trajs),
        trajectory_length=len(train_trajs[0].times),
        state_dim=train_trajs[0].states.shape[1]
    )

    dataset.add_trajectories('train', train_trajs)
    dataset.add_trajectories('validation', val_trajs)
    dataset.add_trajectories('test', test_trajs)

    # Add metadata
    dataset.file.create_group('metadata')
    dataset.file['metadata'].attrs['manifold_type'] = manifold_type
    dataset.file['metadata'].attrs['num_trajectories'] = n
    dataset.file['metadata'].attrs['integration_time'] = 100.0

    dataset.close()
    return dataset
```

**Deliverables**:
- [ ] `dataset_builder.py` (~350 lines)
- [ ] CLI script: `scripts/generate_dataset.py`
- [ ] Validation script: Check dataset statistics, visualize samples

---

## Part E: Dataset Validation (0.5 days)

### E.1: Quality Control Checks

**File**: `src/python/ml/dataset_validation.py`

```python
def validate_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Comprehensive validation of generated dataset.

    Checks:
    1. Energy conservation statistics
    2. Symplectic error distribution
    3. Parameter space coverage (corner plots)
    4. Trajectory diversity (PCA on initial conditions)
    5. No duplicates (hash check)
    6. No NaN/Inf values

    Returns:
        Validation report dictionary
    """
    dataset = TrajectoryDataset(dataset_path, mode='r')

    report = {
        'energy_drift': {},
        'symplectic_error': {},
        'parameter_coverage': {},
        'data_quality': {}
    }

    # Energy conservation
    for split in ['train', 'validation', 'test']:
        energies = dataset.file[split]['energies'][:]
        # Compute energy drift across trajectory
        # (requires recomputing energy at each timestep)
        report['energy_drift'][split] = {
            'mean': 0.0,  # TODO
            'max': 0.0,
            'std': 0.0
        }

    # Parameter coverage
    all_masses = np.concatenate([
        dataset.file['train']['masses'][:],
        dataset.file['validation']['masses'][:],
        dataset.file['test']['masses'][:]
    ])
    all_energies = np.concatenate([
        dataset.file['train']['energies'][:],
        dataset.file['validation']['energies'][:],
        dataset.file['test']['energies'][:]
    ])

    # Create corner plot (requires matplotlib)
    # report['parameter_coverage']['corner_plot'] = ...

    dataset.close()
    return report

def plot_dataset_statistics(dataset_path: str, output_dir: str):
    """Generate validation plots."""
    # Energy drift histogram
    # Parameter space corner plot
    # Trajectory samples (position space)
    # Phase space portraits
    pass
```

**Deliverables**:
- [ ] `dataset_validation.py` (~200 lines)
- [ ] Validation plots: Energy drift, parameter coverage, trajectory samples
- [ ] Report: Dataset statistics summary

---

## Integration Points

### From WP1 (Integrators)
- **Required**: `IAS15` or `DOP853` high-precision integrators
- **Location**: Should exist in `src/python/integrators/` (verify)
- **Interface**: `solve_ivp` compatible

### From WP2 (Lifted Dynamics)
- **Required**: S¹ bundle and KS-Spinor coordinate transformations
- **Location**: `src/python/lifts/s1_bundle.py`, `src/python/lifts/ks_regularization.py`
- **Interface**:
  - `lift_to_s1_bundle(q, v, masses) -> z_s1`
  - `s1_hamiltonian.dynamics(z, masses, energy) -> dz/dt`

### To WP 3.2.2 (HNN Architecture)
- **Output**: HDF5 datasets (`s1_bundle_train.h5`, `ks_spinor_train.h5`)
- **Format**: States (N, T, dim), derivatives (N, T, dim)
- **Expected size**: 10-50 GB

---

## Implementation Schedule

### Day 1: Parameter Sampling
- [ ] Implement `parameter_sampling.py`
- [ ] Test LHS coverage
- [ ] Validate constraint satisfaction (E, L)

### Day 2-3: Trajectory Integration
- [ ] Implement `trajectory_integration.py` for S¹ bundle
- [ ] Integrate with WP1/WP2
- [ ] Test on small batch (100 trajectories)

### Day 4: Augmentation & Assembly
- [ ] Implement `data_augmentation.py`
- [ ] Implement `dataset_builder.py`
- [ ] Generate small validation dataset (1000 trajectories)

### Day 5: Full Dataset & Validation
- [ ] Generate full dataset (100K trajectories, ~8 hours compute)
- [ ] Run validation suite
- [ ] Generate quality report and plots

---

## Testing Strategy

### Unit Tests
- [ ] `test_parameter_sampling.py`: LHS uniformity, constraint satisfaction
- [ ] `test_trajectory_integration.py`: Known cases (harmonic, Kepler), energy conservation
- [ ] `test_data_augmentation.py`: Symmetry preservation, reversibility

### Integration Tests
- [ ] `test_dataset_builder.py`: End-to-end pipeline on small dataset (100 trajectories)
- [ ] `test_dataset_validation.py`: Quality metrics

### Validation Tests
- [ ] Energy drift < 10⁻¹⁰ for all trajectories
- [ ] Symplectic error < 10⁻⁸
- [ ] Parameter space coverage verified via corner plots
- [ ] No NaN/Inf in datasets

---

## Computational Requirements

**Hardware**:
- CPU: 16+ cores (parallel integration)
- RAM: 32 GB
- Storage: 100 GB

**Software Dependencies**:
- NumPy, SciPy (existing)
- h5py (for HDF5)
- matplotlib (for validation plots)
- tqdm (progress bars)

**Runtime Estimates**:
- 100K trajectories × 100 time units × 0.1s/trajectory = ~2.8 hours (16 cores)
- Augmentation: ~30 minutes
- Dataset writing: ~1 hour
- Total: ~5 hours

---

## Deliverables Summary

### Code
- [ ] `src/python/ml/parameter_sampling.py` (~300 lines)
- [ ] `src/python/ml/trajectory_integration.py` (~400 lines)
- [ ] `src/python/ml/data_augmentation.py` (~250 lines)
- [ ] `src/python/ml/dataset_builder.py` (~350 lines)
- [ ] `src/python/ml/dataset_validation.py` (~200 lines)

### Datasets
- [ ] `s1_bundle_train.h5` (~20-30 GB)
- [ ] `ks_spinor_train.h5` (optional, ~30-40 GB)

### Documentation
- [ ] Dataset README with statistics
- [ ] Validation report with plots
- [ ] Usage guide for Task 3.2.2

### Tests
- [ ] `tests/wp3/test_data_generation.py` (~300 lines)

**Total**: ~1,500 lines code + datasets + tests

---

## Success Criteria

**Minimum**:
- [ ] 10K trajectories generated successfully
- [ ] Energy drift < 10⁻⁸ (acceptable)
- [ ] HDF5 dataset readable by PyTorch/JAX

**Target**:
- [ ] 100K trajectories
- [ ] Energy drift < 10⁻¹⁰
- [ ] Full augmentation applied (3× dataset size)

**Stretch**:
- [ ] 1M trajectories
- [ ] Both S¹ and KS datasets
- [ ] Adaptive sampling (focus on interesting regimes)

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Next Task**: Task 3.2.2 (HNN Architecture)
