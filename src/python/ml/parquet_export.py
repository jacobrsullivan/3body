"""Strict, qualification-aware Parquet export for WP1 trajectories.

Numeric trajectory columns remain float64.  For high-precision runs, decimal
state strings are exported alongside the float64 projection so publication
evidence is not destroyed by storage conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
import glob
import logging
import os
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np

from src.python.validation.qualification import (
    assert_metadata_matches,
    qualification_metadata,
)


logger = logging.getLogger(__name__)

STATE_NAMES = ("x", "y", "z", "vx", "vy", "vz")
QUALIFICATION_KEYS = (
    "wp1_qualification_id",
    "wp1_qualification_status",
    "wp1_qualification_lock_sha256",
    "wp1_qualification_record_sha256",
)


@dataclass
class ParquetExportConfig:
    """Configuration for strict Parquet export."""

    compression: str = "zstd"
    row_group_size: int = 10000
    partition_cols: list[str] | None = None
    require_qualification: bool = True
    qualification_record: str | None = None


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _schema(metadata: dict[bytes, bytes] | None = None):
    import pyarrow as pa

    fields = [
        ("orbit_id", pa.int64()),
        ("orbit_key", pa.string()),
        ("mu", pa.float64()),
        ("C", pa.float64()),
        ("t", pa.float64()),
    ]
    fields.extend((name, pa.float64()) for name in STATE_NAMES)
    fields.extend((f"{name}_inertial", pa.float64()) for name in STATE_NAMES)
    fields.extend(
        [
            ("MEGNO", pa.float64()),
            ("FLI", pa.float64()),
            ("chaos_class", pa.string()),
            ("precision", pa.string()),
            ("precision_bits", pa.int32()),
        ]
    )
    fields.extend((f"{name}_hp", pa.string()) for name in STATE_NAMES)
    fields.append(("t_hp", pa.string()))
    fields.extend((key, pa.string()) for key in QUALIFICATION_KEYS)
    return pa.schema(fields, metadata=metadata)


def _required_metadata(record_path: str | None, required: bool) -> dict[str, str]:
    if not required:
        return {}
    return qualification_metadata(record_path, require_pass=True)


def _validate_shapes(
    times: np.ndarray,
    corotating: np.ndarray,
    inertial: np.ndarray,
    megno: np.ndarray,
    fli: np.ndarray,
) -> None:
    count = len(times)
    expected_state_shape = (count, 6)
    if corotating.shape != expected_state_shape:
        raise ValueError(
            f"states_corotating shape {corotating.shape}, expected {expected_state_shape}"
        )
    if inertial.shape != expected_state_shape:
        raise ValueError(
            f"states_inertial shape {inertial.shape}, expected {expected_state_shape}"
        )
    if megno.shape != (count,) or fli.shape != (count,):
        raise ValueError("MEGNO/FLI arrays must align with trajectory times")
    arrays = (times, corotating, inertial)
    if not all(np.all(np.isfinite(array)) for array in arrays):
        raise ValueError("Trajectory contains non-finite time or state values")


def _high_precision_columns(handle: Any, count: int, precision: str) -> tuple[np.ndarray, np.ndarray]:
    if "states_corotating_high_precision" not in handle:
        if precision == "heyoka-real":
            raise ValueError(
                "High-precision trajectory is missing decimal state representation"
            )
        return np.full((count, 6), "", dtype=object), np.full(count, "", dtype=object)

    states = np.asarray(handle["states_corotating_high_precision"][:], dtype=object)
    times = np.asarray(handle["times_high_precision"][:], dtype=object)
    if states.shape != (count, 6) or times.shape != (count,):
        raise ValueError("High-precision decimal arrays do not align with float trajectory")
    decode = np.vectorize(_text, otypes=[object])
    return decode(states), decode(times)


def _table_data(
    handle: Any,
    orbit_number: int,
    expected_qualification: dict[str, str],
) -> dict[str, Any]:
    attrs = {key: _text(value) for key, value in handle.attrs.items()}
    if expected_qualification:
        assert_metadata_matches(attrs, expected_qualification)

    times = np.asarray(handle["times"][:], dtype=np.float64)
    corotating = np.asarray(handle["states_corotating"][:], dtype=np.float64)
    inertial = np.asarray(handle["states_inertial"][:], dtype=np.float64)
    megno = np.asarray(
        handle["MEGNO"][:] if "MEGNO" in handle else np.full(len(times), np.nan),
        dtype=np.float64,
    )
    fli = np.asarray(
        handle["FLI"][:] if "FLI" in handle else np.full(len(times), np.nan),
        dtype=np.float64,
    )
    _validate_shapes(times, corotating, inertial, megno, fli)

    count = len(times)
    precision = attrs.get("precision", "double")
    states_hp, times_hp = _high_precision_columns(handle, count, precision)
    orbit_key = attrs.get("orbit_id", f"orbit-{orbit_number:08d}")
    data: dict[str, Any] = {
        "orbit_id": np.full(count, orbit_number, dtype=np.int64),
        "orbit_key": np.full(count, orbit_key, dtype=object),
        "mu": np.full(count, float(handle.attrs.get("mu", np.nan)), dtype=np.float64),
        "C": np.full(count, float(handle.attrs.get("C", np.nan)), dtype=np.float64),
        "t": times,
        "MEGNO": megno,
        "FLI": fli,
        "chaos_class": np.full(count, attrs.get("chaos_class", "unknown"), dtype=object),
        "precision": np.full(count, precision, dtype=object),
        "precision_bits": np.full(
            count, int(handle.attrs.get("precision_bits", 53)), dtype=np.int32
        ),
        "t_hp": times_hp,
    }
    for column, name in enumerate(STATE_NAMES):
        data[name] = corotating[:, column]
        data[f"{name}_inertial"] = inertial[:, column]
        data[f"{name}_hp"] = states_hp[:, column]
    for key in QUALIFICATION_KEYS:
        data[key] = np.full(count, attrs.get(key, ""), dtype=object)
    return data


def _schema_metadata(expected: dict[str, str]) -> dict[bytes, bytes]:
    metadata = {
        b"wp1_schema_version": b"1.0",
        b"wp1_state_dtype": b"float64",
        b"wp1_high_precision_encoding": b"decimal-string",
    }
    metadata.update(
        {
            key.encode("ascii"): value.encode("ascii")
            for key, value in expected.items()
        }
    )
    return metadata


def _write_handles(
    handles: Iterable[tuple[str, Any]],
    output_path: str,
    config: ParquetExportConfig,
) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    expected = _required_metadata(
        config.qualification_record, config.require_qualification
    )
    schema = _schema(_schema_metadata(expected))
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with pq.ParquetWriter(destination, schema, compression=config.compression) as writer:
        for name, handle in handles:
            data = _table_data(handle, count, expected)
            table = pa.table(data, schema=schema)
            writer.write_table(table, row_group_size=config.row_group_size)
            count += 1
            if count % 100 == 0:
                logger.info("Exported %d trajectories", count)
    logger.info("Export complete: %d trajectories written to %s", count, destination)
    return count


class ParquetExporter:
    """Export a grouped HDF5 trajectory archive under the WP1 contract."""

    def __init__(self, config: Optional[ParquetExportConfig] = None):
        self.config = config or ParquetExportConfig()

    def export_from_hdf5(
        self, hdf5_path: str, parquet_path: str, chunk_size: int = 10000
    ) -> int:
        import h5py

        config = ParquetExportConfig(**vars(self.config))
        config.row_group_size = chunk_size
        with h5py.File(hdf5_path, "r") as archive:
            handles = []
            for mu_name in sorted(archive):
                for c_name in sorted(archive[mu_name]):
                    for orbit_name in sorted(archive[mu_name][c_name]):
                        handles.append(
                            (
                                f"{mu_name}/{c_name}/{orbit_name}",
                                archive[mu_name][c_name][orbit_name],
                            )
                        )
            if not handles:
                logger.warning("No trajectory groups found in %s", hdf5_path)
                return 0
            return _write_handles(handles, parquet_path, config)


def export_tier1_to_parquet(
    hdf5_dir: str,
    output_path: str,
    *,
    require_qualification: bool = True,
    qualification_record: str | None = None,
) -> int:
    """Export per-orbit HDF5 files without downcasting or silent skips."""
    import h5py

    files = sorted(glob.glob(os.path.join(hdf5_dir, "*.h5")))
    if not files:
        logger.warning("No HDF5 files found in %s", hdf5_dir)
        return 0

    config = ParquetExportConfig(
        require_qualification=require_qualification,
        qualification_record=qualification_record,
    )
    handles = []
    try:
        for filename in files:
            handle = h5py.File(filename, "r")
            handles.append((filename, handle))
        return _write_handles(handles, output_path, config)
    finally:
        for _, handle in handles:
            handle.close()
