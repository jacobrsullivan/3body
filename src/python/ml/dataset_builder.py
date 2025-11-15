"""
HDF5 dataset assembly and storage (Task 3.2.1, Part D).

This module builds HDF5 datasets from integrated trajectories, organizing
them into train/validation/test splits with proper metadata.

Dataset structure:
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

import h5py
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path

from .parameter_sampling import ParameterRanges, InitialCondition, generate_lhs_samples
from .trajectory_integration import (
    Trajectory, IntegrationConfig, integrate_batch, integrate_batch_parallel
)
from .data_augmentation import augment_trajectory


class TrajectoryDataset:
    """
    HDF5 dataset for trajectory data.

    Handles creation, writing, and reading of trajectory datasets
    stored in HDF5 format for efficient access.
    """

    def __init__(self, filepath: str, mode: str = 'r'):
        """
        Initialize dataset.

        Args:
            filepath: Path to HDF5 file
            mode: File mode ('r', 'w', 'a')
        """
        self.filepath = filepath
        self.mode = mode
        self.file = None

    def __enter__(self):
        """Context manager entry."""
        self.file = h5py.File(self.filepath, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.file is not None:
            self.file.close()

    def create_structure(
        self,
        train_size: int,
        val_size: int,
        test_size: int,
        trajectory_length: int,
        state_dim: int,
        compression: str = 'gzip',
        compression_level: int = 4
    ):
        """
        Initialize HDF5 structure with chunking and compression.

        Args:
            train_size: Number of training trajectories
            val_size: Number of validation trajectories
            test_size: Number of test trajectories
            trajectory_length: Number of timesteps per trajectory
            state_dim: Phase space dimension
            compression: Compression algorithm ('gzip', 'lzf')
            compression_level: Compression level (1-9 for gzip)
        """
        for split, N in [('train', train_size), ('validation', val_size), ('test', test_size)]:
            grp = self.file.create_group(split)

            # States: (N, T, dim) - chunk by trajectory for random access
            grp.create_dataset(
                'states',
                shape=(N, trajectory_length, state_dim),
                dtype=np.float32,  # Mixed precision for storage
                chunks=(1, trajectory_length, state_dim),
                compression=compression,
                compression_opts=compression_level if compression == 'gzip' else None
            )

            # Derivatives: (N, T, dim)
            grp.create_dataset(
                'derivatives',
                shape=(N, trajectory_length, state_dim),
                dtype=np.float32,
                chunks=(1, trajectory_length, state_dim),
                compression=compression,
                compression_opts=compression_level if compression == 'gzip' else None
            )

            # Times: (N, T)
            grp.create_dataset(
                'times',
                shape=(N, trajectory_length),
                dtype=np.float32,
                chunks=(1, trajectory_length),
                compression=compression
            )

            # Energies: (N,)
            grp.create_dataset('energies', shape=(N,), dtype=np.float64)

            # Masses: (N, 3)
            grp.create_dataset('masses', shape=(N, 3), dtype=np.float64)

            # Trajectory IDs: (N,)
            grp.create_dataset('trajectory_ids', shape=(N,), dtype=np.int64)

            # Quality metrics
            grp.create_dataset('energy_drifts', shape=(N,), dtype=np.float32)
            grp.create_dataset('symplectic_errors', shape=(N,), dtype=np.float32)

    def add_trajectories(
        self,
        split: str,
        trajectories: List[Trajectory],
        start_idx: int = 0
    ):
        """
        Add batch of trajectories to dataset.

        Args:
            split: Dataset split ('train', 'validation', 'test')
            trajectories: List of trajectories to add
            start_idx: Starting index in dataset
        """
        grp = self.file[split]

        for i, traj in enumerate(trajectories):
            idx = start_idx + i

            # Store trajectory data
            grp['states'][idx] = traj.states.astype(np.float32)
            grp['derivatives'][idx] = traj.derivatives.astype(np.float32)
            grp['times'][idx] = traj.times.astype(np.float32)
            grp['energies'][idx] = traj.initial_condition.energy
            grp['masses'][idx] = traj.initial_condition.masses
            grp['trajectory_ids'][idx] = idx
            grp['energy_drifts'][idx] = traj.energy_drift
            grp['symplectic_errors'][idx] = traj.symplectic_error

    def add_metadata(
        self,
        param_ranges: ParameterRanges,
        integration_config: IntegrationConfig,
        manifold_type: str,
        num_trajectories: int,
        **kwargs
    ):
        """
        Add metadata to dataset.

        Args:
            param_ranges: Parameter space ranges
            integration_config: Integration configuration
            manifold_type: 's1' or 'ks'
            num_trajectories: Total number of trajectories
            **kwargs: Additional metadata
        """
        if 'metadata' not in self.file:
            meta_grp = self.file.create_group('metadata')
        else:
            meta_grp = self.file['metadata']

        # Store as attributes
        meta_grp.attrs['manifold_type'] = manifold_type
        meta_grp.attrs['num_trajectories'] = num_trajectories
        meta_grp.attrs['integrator'] = integration_config.integrator
        meta_grp.attrs['rtol'] = integration_config.rtol
        meta_grp.attrs['atol'] = integration_config.atol

        # Store parameter ranges
        meta_grp.attrs['mass_ratio_min'] = param_ranges.mass_ratio[0]
        meta_grp.attrs['mass_ratio_max'] = param_ranges.mass_ratio[1]
        meta_grp.attrs['energy_min'] = param_ranges.energy[0]
        meta_grp.attrs['energy_max'] = param_ranges.energy[1]
        meta_grp.attrs['L_min'] = param_ranges.angular_momentum[0]
        meta_grp.attrs['L_max'] = param_ranges.angular_momentum[1]

        # Additional metadata
        for key, value in kwargs.items():
            meta_grp.attrs[key] = value

    def get_trajectory(self, split: str, idx: int) -> Dict:
        """
        Retrieve single trajectory from dataset.

        Args:
            split: Dataset split
            idx: Trajectory index

        Returns:
            Dictionary with trajectory data
        """
        grp = self.file[split]

        return {
            'states': grp['states'][idx],
            'derivatives': grp['derivatives'][idx],
            'times': grp['times'][idx],
            'energy': grp['energies'][idx],
            'masses': grp['masses'][idx],
            'energy_drift': grp['energy_drifts'][idx],
            'symplectic_error': grp['symplectic_errors'][idx]
        }

    def get_size(self, split: str) -> int:
        """Get number of trajectories in split."""
        return self.file[split]['states'].shape[0]


def build_dataset(
    output_path: str,
    num_trajectories: int,
    param_ranges: Optional[ParameterRanges] = None,
    integration_config: Optional[IntegrationConfig] = None,
    manifold_type: str = 's1',
    t_span: float = 100.0,
    train_split: float = 0.7,
    val_split: float = 0.15,
    test_split: float = 0.15,
    use_augmentation: bool = True,
    num_workers: int = 1,
    seed: int = 42
) -> TrajectoryDataset:
    """
    Complete pipeline to generate and store trajectory dataset.

    Steps:
    1. Generate parameter samples (LHS)
    2. Integrate trajectories (parallel if num_workers > 1)
    3. Apply augmentation (optional)
    4. Quality filtering
    5. Train/val/test split
    6. Write to HDF5

    Args:
        output_path: Path for output HDF5 file
        num_trajectories: Number of initial conditions to sample
        param_ranges: Parameter space ranges (default if None)
        integration_config: Integration configuration (default if None)
        manifold_type: 's1' or 'ks'
        t_span: Integration time
        train_split: Fraction for training
        val_split: Fraction for validation
        test_split: Fraction for testing
        use_augmentation: Apply data augmentation
        num_workers: Number of parallel workers (1 = serial)
        seed: Random seed

    Returns:
        TrajectoryDataset object (closed)
    """
    print("=" * 70)
    print("BUILDING TRAJECTORY DATASET")
    print("=" * 70)

    # Default configurations
    if param_ranges is None:
        param_ranges = ParameterRanges()
    if integration_config is None:
        integration_config = IntegrationConfig()

    # Step 1: Generate parameter samples
    print(f"\n[1/6] Generating {num_trajectories} parameter samples via LHS...")
    initial_conditions = generate_lhs_samples(param_ranges, num_trajectories, seed=seed)
    print(f"      Generated {len(initial_conditions)} valid initial conditions")

    # Step 2: Integrate trajectories
    print(f"\n[2/6] Integrating trajectories (t_span={t_span})...")
    if num_workers > 1:
        trajectories = integrate_batch_parallel(
            initial_conditions,
            t_span,
            integration_config,
            manifold_type,
            num_workers
        )
    else:
        trajectories = integrate_batch(
            initial_conditions,
            t_span,
            integration_config,
            manifold_type,
            verbose=True
        )

    print(f"      Successfully integrated {len(trajectories)} trajectories")

    # Step 3: Augmentation
    if use_augmentation:
        print(f"\n[3/6] Applying data augmentation...")
        augmented_trajectories = []
        for traj in trajectories:
            aug_trajs = augment_trajectory(
                traj,
                use_permutations=True,
                use_time_reversal=True,
                use_virial=False
            )
            augmented_trajectories.extend(aug_trajs)

        print(f"      Augmented to {len(augmented_trajectories)} trajectories")
        trajectories = augmented_trajectories
    else:
        print(f"\n[3/6] Skipping data augmentation")

    # Step 4: Quality filtering (already done during integration)
    print(f"\n[4/6] Quality filtering complete (done during integration)")

    # Step 5: Train/val/test split
    print(f"\n[5/6] Splitting dataset ({train_split:.0%}/{val_split:.0%}/{test_split:.0%})...")
    np.random.seed(seed)
    np.random.shuffle(trajectories)

    n_total = len(trajectories)
    n_train = int(n_total * train_split)
    n_val = int(n_total * val_split)

    train_trajs = trajectories[:n_train]
    val_trajs = trajectories[n_train:n_train + n_val]
    test_trajs = trajectories[n_train + n_val:]

    print(f"      Train: {len(train_trajs)} trajectories")
    print(f"      Validation: {len(val_trajs)} trajectories")
    print(f"      Test: {len(test_trajs)} trajectories")

    # Step 6: Write to HDF5
    print(f"\n[6/6] Writing to HDF5: {output_path}...")

    # Get dimensions from first trajectory
    trajectory_length = len(train_trajs[0].times)
    state_dim = train_trajs[0].states.shape[1]

    # Create HDF5 file
    with TrajectoryDataset(output_path, mode='w') as dataset:
        # Create structure
        dataset.create_structure(
            train_size=len(train_trajs),
            val_size=len(val_trajs),
            test_size=len(test_trajs),
            trajectory_length=trajectory_length,
            state_dim=state_dim
        )

        # Add trajectories
        dataset.add_trajectories('train', train_trajs)
        dataset.add_trajectories('validation', val_trajs)
        dataset.add_trajectories('test', test_trajs)

        # Add metadata
        dataset.add_metadata(
            param_ranges=param_ranges,
            integration_config=integration_config,
            manifold_type=manifold_type,
            num_trajectories=n_total,
            t_span=t_span,
            augmentation_applied=use_augmentation,
            seed=seed
        )

    file_size_mb = Path(output_path).stat().st_size / (1024**2)
    print(f"      Dataset written successfully ({file_size_mb:.1f} MB)")

    print("\n" + "=" * 70)
    print("DATASET GENERATION COMPLETE")
    print("=" * 70)

    return TrajectoryDataset(output_path, mode='r')


def quick_dataset(
    output_path: str = 'data/test_dataset.h5',
    num_trajectories: int = 10,
    t_span: float = 10.0
):
    """
    Generate small test dataset quickly.

    Useful for testing and development.

    Args:
        output_path: Output file path
        num_trajectories: Number of trajectories (small)
        t_span: Integration time (short)
    """
    print("Generating quick test dataset...")

    # Use fast settings
    config = IntegrationConfig(
        t_eval_dt=0.1,  # Coarse timestep
        rtol=1e-9,
        atol=1e-10
    )

    dataset = build_dataset(
        output_path=output_path,
        num_trajectories=num_trajectories,
        integration_config=config,
        t_span=t_span,
        use_augmentation=False,  # Skip for speed
        num_workers=1
    )

    print(f"\nTest dataset created: {output_path}")
    return dataset


if __name__ == "__main__":
    # Quick test
    import os

    # Create data directory if needed
    os.makedirs('data', exist_ok=True)

    # Generate test dataset
    dataset = quick_dataset(
        output_path='data/test_dataset.h5',
        num_trajectories=5,
        t_span=5.0
    )

    # Verify dataset
    with dataset:
        print(f"\nDataset contents:")
        print(f"  Train size: {dataset.get_size('train')}")
        print(f"  Val size: {dataset.get_size('validation')}")
        print(f"  Test size: {dataset.get_size('test')}")

        # Read one trajectory
        traj_data = dataset.get_trajectory('train', 0)
        print(f"\n  First trajectory:")
        print(f"    States shape: {traj_data['states'].shape}")
        print(f"    Energy: {traj_data['energy']:.4f}")
        print(f"    Energy drift: {traj_data['energy_drift']:.2e}")
