"""
Parquet Export for ML-Ready Data (WP1 Phase 5).

Converts HDF5 trajectory archives to flattened Apache Parquet format
for high-throughput ML training.

Benefits of Parquet:
- Columnar storage (10x faster for ML I/O)
- Efficient compression
- Cloud-optimized
- Native PyTorch/TensorFlow support

Schema:
=======
- orbit_id: int64
- mu: float64
- C: float64
- t: float64
- x, y, z, vx, vy, vz: float32
- x_inertial, y_inertial, z_inertial: float32
- vx_inertial, vy_inertial, vz_inertial: float32
- MEGNO: float32
- FLI: float32
- chaos_class: category
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParquetExportConfig:
    """Configuration for Parquet export."""

    compression: str = "snappy"  # or "gzip", "zstd"
    row_group_size: int = 10000
    partition_cols: list = None  # e.g., ["mu", "chaos_class"]


class ParquetExporter:
    """Export HDF5 trajectory data to Parquet format."""

    def __init__(self, config: Optional[ParquetExportConfig] = None):
        """
        Initialize Parquet exporter.

        Args:
            config: Export configuration
        """
        self.config = config or ParquetExportConfig()
        logger.info(
            f"Initialized ParquetExporter (compression={self.config.compression})"
        )

    def export_from_hdf5(
        self, hdf5_path: str, parquet_path: str, chunk_size: int = 10000
    ):
        """
        Convert HDF5 archive to Parquet.

        Args:
            hdf5_path: Path to HDF5 file
            parquet_path: Output Parquet path
            chunk_size: Rows per chunk for streaming
        """
        try:
            import h5py
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            logger.error("h5py and pyarrow required for Parquet export")
            raise

        logger.info(f"Exporting {hdf5_path} to {parquet_path}")

        # Define schema
        schema = pa.schema(
            [
                ("orbit_id", pa.int64()),
                ("mu", pa.float64()),
                ("C", pa.float64()),
                ("t", pa.float64()),
                ("x", pa.float32()),
                ("y", pa.float32()),
                ("z", pa.float32()),
                ("vx", pa.float32()),
                ("vy", pa.float32()),
                ("vz", pa.float32()),
                ("x_inertial", pa.float32()),
                ("y_inertial", pa.float32()),
                ("z_inertial", pa.float32()),
                ("vx_inertial", pa.float32()),
                ("vy_inertial", pa.float32()),
                ("vz_inertial", pa.float32()),
                ("MEGNO", pa.float32()),
                ("FLI", pa.float32()),
                ("chaos_class", pa.dictionary(pa.int8(), pa.string())),
            ]
        )

        # Open HDF5 and Parquet writer
        with h5py.File(hdf5_path, "r") as hf:
            with pq.ParquetWriter(
                parquet_path, schema, compression=self.config.compression
            ) as writer:

                # Iterate over orbits in HDF5
                orbit_count = 0

                for mu_group_name in hf.keys():
                    mu_group = hf[mu_group_name]

                    for C_group_name in mu_group.keys():
                        C_group = mu_group[C_group_name]

                        for orbit_name in C_group.keys():
                            orbit_data = C_group[orbit_name]

                            # Extract data
                            mu_val = orbit_data.attrs.get("mu", 0.0)
                            C_val = orbit_data.attrs.get("C", 0.0)

                            times = orbit_data["times"][:]
                            states_corot = orbit_data["states_corotating"][:]
                            states_inert = orbit_data["states_inertial"][:]

                            megno = orbit_data.get("MEGNO", np.zeros(len(times)))
                            fli = orbit_data.get("FLI", np.zeros(len(times)))
                            chaos_class = orbit_data.attrs.get("chaos_class", "unknown")

                            # Create table chunk
                            n_points = len(times)
                            table_data = {
                                "orbit_id": np.full(
                                    n_points, orbit_count, dtype=np.int64
                                ),
                                "mu": np.full(n_points, mu_val, dtype=np.float64),
                                "C": np.full(n_points, C_val, dtype=np.float64),
                                "t": times.astype(np.float64),
                                "x": states_corot[:, 0].astype(np.float32),
                                "y": states_corot[:, 1].astype(np.float32),
                                "z": states_corot[:, 2].astype(np.float32),
                                "vx": states_corot[:, 3].astype(np.float32),
                                "vy": states_corot[:, 4].astype(np.float32),
                                "vz": states_corot[:, 5].astype(np.float32),
                                "x_inertial": states_inert[:, 0].astype(np.float32),
                                "y_inertial": states_inert[:, 1].astype(np.float32),
                                "z_inertial": states_inert[:, 2].astype(np.float32),
                                "vx_inertial": states_inert[:, 3].astype(np.float32),
                                "vy_inertial": states_inert[:, 4].astype(np.float32),
                                "vz_inertial": states_inert[:, 5].astype(np.float32),
                                "MEGNO": megno[:].astype(np.float32),
                                "FLI": fli[:].astype(np.float32),
                                "chaos_class": np.full(n_points, chaos_class),
                            }

                            # Write to Parquet
                            table = pa.table(table_data, schema=schema)
                            writer.write_table(table)

                            orbit_count += 1

                            if orbit_count % 100 == 0:
                                logger.info(f"Exported {orbit_count} orbits...")

        logger.info(f"Export complete: {orbit_count} orbits written to {parquet_path}")


def export_tier1_to_parquet(hdf5_dir: str, output_path: str):
    """
    Export Tier 1 dataset to Parquet.

    Args:
        hdf5_dir: Directory containing Tier 1 HDF5 files
        output_path: Output Parquet file path
    """
    import glob as _glob
    import os

    try:
        import h5py
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        logger.error("h5py and pyarrow required for Parquet export")
        raise

    hdf5_files = sorted(_glob.glob(os.path.join(hdf5_dir, "*.h5")))
    if not hdf5_files:
        logger.warning(f"No HDF5 files found in {hdf5_dir}")
        return

    logger.info(
        f"Exporting {len(hdf5_files)} HDF5 files from {hdf5_dir} to {output_path}"
    )

    schema = pa.schema(
        [
            ("orbit_id", pa.int64()),
            ("mu", pa.float64()),
            ("C", pa.float64()),
            ("t", pa.float64()),
            ("x", pa.float32()),
            ("y", pa.float32()),
            ("z", pa.float32()),
            ("vx", pa.float32()),
            ("vy", pa.float32()),
            ("vz", pa.float32()),
            ("x_inertial", pa.float32()),
            ("y_inertial", pa.float32()),
            ("z_inertial", pa.float32()),
            ("vx_inertial", pa.float32()),
            ("vy_inertial", pa.float32()),
            ("vz_inertial", pa.float32()),
            ("MEGNO", pa.float32()),
            ("FLI", pa.float32()),
            ("chaos_class", pa.dictionary(pa.int8(), pa.string())),
        ]
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with pq.ParquetWriter(output_path, schema, compression="snappy") as writer:
        for orbit_count, fp in enumerate(hdf5_files):
            try:
                with h5py.File(fp, "r") as f:
                    mu_val = float(f.attrs.get("mu", 0.0))
                    C_val = float(f.attrs.get("C", 0.0))
                    chaos_class = str(f.attrs.get("chaos_class", "unknown"))

                    times = f["times"][:] if "times" in f else np.array([0.0])
                    n_points = len(times)

                    states_corot = (
                        f["states_corotating"][:]
                        if "states_corotating" in f
                        else np.zeros((n_points, 6))
                    )
                    states_inert = (
                        f["states_inertial"][:]
                        if "states_inertial" in f
                        else np.zeros((n_points, 6))
                    )
                    megno = f["MEGNO"][:] if "MEGNO" in f else np.zeros(n_points)
                    fli = f["FLI"][:] if "FLI" in f else np.zeros(n_points)

                    table_data = {
                        "orbit_id": np.full(n_points, orbit_count, dtype=np.int64),
                        "mu": np.full(n_points, mu_val, dtype=np.float64),
                        "C": np.full(n_points, C_val, dtype=np.float64),
                        "t": times.astype(np.float64),
                        "x": states_corot[:, 0].astype(np.float32),
                        "y": states_corot[:, 1].astype(np.float32),
                        "z": states_corot[:, 2].astype(np.float32),
                        "vx": states_corot[:, 3].astype(np.float32),
                        "vy": states_corot[:, 4].astype(np.float32),
                        "vz": states_corot[:, 5].astype(np.float32),
                        "x_inertial": states_inert[:, 0].astype(np.float32),
                        "y_inertial": states_inert[:, 1].astype(np.float32),
                        "z_inertial": states_inert[:, 2].astype(np.float32),
                        "vx_inertial": states_inert[:, 3].astype(np.float32),
                        "vy_inertial": states_inert[:, 4].astype(np.float32),
                        "vz_inertial": states_inert[:, 5].astype(np.float32),
                        "MEGNO": megno[:].astype(np.float32),
                        "FLI": fli[:].astype(np.float32),
                        "chaos_class": pa.DictionaryArray.from_arrays(
                            np.zeros(n_points, dtype=np.int8),
                            pa.array([chaos_class]),
                        ),
                    }

                    chunk = pa.table(table_data, schema=schema)
                    writer.write_table(chunk)

            except Exception as e:
                logger.warning(f"Skipping {fp}: {e}")
                continue

            if (orbit_count + 1) % 100 == 0:
                logger.info(f"Exported {orbit_count + 1} orbits...")

    logger.info(f"Export complete: {len(hdf5_files)} files written to {output_path}")
