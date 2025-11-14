# Task 2.1.2 Part C: Numerical Implementation - Detailed Design

**Task**: WP 2.1.2 - Computation of the "Magnetic Twist" (Connection and Curvature)
**Part**: C - Numerical Implementation & Optimization
**Status**: Design Phase
**Estimated Duration**: 2-3 days
**Dependencies**: Task 2.1.2 Parts A & B Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Performance Requirements](#performance-requirements)
3. [C1: Vectorized Batch Operations](#c1-vectorized-batch-operations)
4. [C2: Adaptive Precision Control](#c2-adaptive-precision-control)
5. [C3: Caching and Memoization](#c3-caching-and-memoization)
6. [C4: Parallel Computation](#c4-parallel-computation)
7. [C5: Numerical Stability](#c5-numerical-stability)
8. [Implementation Details](#implementation-details)
9. [Profiling and Benchmarks](#profiling-and-benchmarks)
10. [Integration Guide](#integration-guide)

---

## Overview

### Purpose

Part C focuses on making the connection and curvature computations from Parts A & B **production-ready** through:

1. **Performance optimization** - Vectorization, batching, parallelization
2. **Precision control** - Adaptive escalation from double → quad → symbolic
3. **Caching strategies** - Intelligent memoization for repeated queries
4. **Numerical stability** - Handling near-collision and near-collinear cases
5. **Profiling infrastructure** - Tools to identify and fix bottlenecks

### Key Design Principles

1. **Fast by Default**: Most computations should use optimized double-precision
2. **Precision on Demand**: Automatically escalate to higher precision when needed
3. **Cache Intelligently**: Memoize expensive operations without memory bloat
4. **Fail Gracefully**: Handle singular/degenerate cases without crashes
5. **Profile Everything**: Built-in timing and profiling for optimization

### Deliverables

- `src/python/geometry/batch_ops.py` - Vectorized batch operations
- `src/python/geometry/precision.py` - Adaptive precision control
- `src/python/geometry/cache.py` - Intelligent caching system
- `src/python/geometry/parallel.py` - Parallel computation utilities
- `src/python/geometry/profiler.py` - Performance profiling tools
- Performance targets achieved and documented

---

## Performance Requirements

### Target Performance (Single Point)

| Operation | Target Time | Acceptable Range | Notes |
|-----------|-------------|------------------|-------|
| Connection evaluation | < 100 μs | 50-150 μs | Part A core operation |
| Curvature evaluation | < 1 ms | 0.5-2 ms | Includes 6 connection evals |
| Locked inertia tensor | < 20 μs | 10-50 μs | Frequently called |
| Shape→Cartesian conversion | < 10 μs | 5-20 μs | Simple geometry |

### Target Performance (Batch Operations)

| Operation | Batch Size | Target Time | Throughput |
|-----------|------------|-------------|------------|
| Connection field | 1000 points | < 100 ms | 10,000 pts/sec |
| Curvature field | 1000 points | < 1 sec | 1,000 pts/sec |
| Grid evaluation (50×50) | 2500 points | < 2 sec | 1,250 pts/sec |

### Memory Constraints

- **Cache size**: < 100 MB for typical workloads
- **Working memory**: < 1 GB per parallel worker
- **Total memory**: < 4 GB for full visualization pipeline

---

## C1: Vectorized Batch Operations

### NumPy Vectorization Strategy

**Goal**: Process multiple points simultaneously using NumPy array operations.

```python
# File: src/python/geometry/batch_ops.py

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from .connection import ConnectionForm
from .curvature import CurvatureForm


@dataclass
class BatchShapeSpace:
    """
    Batch of shape space states for vectorized operations.

    Attributes:
        r12: (N,) array of r12 values
        r23: (N,) array of r23 values
        r31: (N,) array of r31 values
        L: (N,) array of angular momentum values (or scalar if constant)
    """
    r12: np.ndarray
    r23: np.ndarray
    r31: np.ndarray
    L: np.ndarray | float

    @property
    def size(self) -> int:
        """Number of points in batch."""
        return len(self.r12)

    def __getitem__(self, idx: int) -> ShapeSpaceState:
        """Extract single state from batch."""
        L_val = self.L if isinstance(self.L, float) else self.L[idx]
        return ShapeSpaceState(
            r12=self.r12[idx],
            r23=self.r23[idx],
            r31=self.r31[idx],
            L=L_val
        )

    @classmethod
    def from_states(cls, states: list[ShapeSpaceState]) -> 'BatchShapeSpace':
        """Construct from list of individual states."""
        r12 = np.array([s.r12 for s in states])
        r23 = np.array([s.r23 for s in states])
        r31 = np.array([s.r31 for s in states])

        # Check if L is constant
        L_vals = np.array([s.L for s in states])
        if np.allclose(L_vals, L_vals[0]):
            L = float(L_vals[0])
        else:
            L = L_vals

        return cls(r12=r12, r23=r23, r31=r31, L=L)

    def validate_triangle_inequality(self) -> np.ndarray:
        """
        Check triangle inequality for all points.

        Returns:
            Boolean array of valid points
        """
        valid = (
            (self.r12 + self.r23 > self.r31) &
            (self.r23 + self.r31 > self.r12) &
            (self.r31 + self.r12 > self.r23) &
            (self.r12 > 0) &
            (self.r23 > 0) &
            (self.r31 > 0)
        )
        return valid


def compute_locked_inertia_batch(
    batch: BatchShapeSpace,
    masses: Masses
) -> np.ndarray:
    """
    Compute locked inertia tensors for batch of points.

    Fully vectorized implementation.

    Args:
        batch: Batch of N shape space points
        masses: Body masses

    Returns:
        (N, 3, 3) array of inertia tensors
    """
    N = batch.size

    # Convert batch to Cartesian (vectorized)
    # This is the expensive part - we'll optimize it
    positions_batch = np.zeros((N, 3, 3))  # (N, 3 bodies, 3 coords)

    for i in range(N):
        # For now, loop (can vectorize further with careful indexing)
        state = batch[i]
        cart_state = _shape_to_cartesian_canonical(state)
        positions_batch[i] = cart_state.positions

    # Vectorized inertia computation
    m = np.array([masses.m1, masses.m2, masses.m3])  # (3,)

    # Compute r_squared for each body at each point
    r_squared = np.sum(positions_batch**2, axis=2)  # (N, 3)

    # Initialize inertia tensors
    I_batch = np.zeros((N, 3, 3))

    # Vectorized accumulation
    for body_idx in range(3):
        r = positions_batch[:, body_idx, :]  # (N, 3) positions of body i
        r_sq = r_squared[:, body_idx]        # (N,) |r_i|^2
        m_i = m[body_idx]

        # Diagonal part: m_i (r^2 δ_αβ - r_α r_β)
        for alpha in range(3):
            I_batch[:, alpha, alpha] += m_i * (r_sq - r[:, alpha]**2)

        # Off-diagonal: -m_i r_α r_β
        for alpha in range(3):
            for beta in range(alpha+1, 3):
                I_batch[:, alpha, beta] -= m_i * r[:, alpha] * r[:, beta]
                I_batch[:, beta, alpha] = I_batch[:, alpha, beta]

    return I_batch


def compute_connection_batch(
    batch: BatchShapeSpace,
    masses: Masses,
    use_cache: bool = True
) -> np.ndarray:
    """
    Compute connection coefficients for batch of points.

    Args:
        batch: Batch of N points
        masses: Body masses
        use_cache: Use cached results if available

    Returns:
        (N, 3) array of connection coefficients [A_r12, A_r23, A_r31]
    """
    N = batch.size
    coefficients = np.zeros((N, 3))

    # Check cache first
    if use_cache:
        cache = get_connection_cache()
        for i in range(N):
            state = batch[i]
            cached = cache.get(state, masses)
            if cached is not None:
                coefficients[i] = cached.coefficients
            else:
                # Compute and cache
                conn = _compute_connection_single(state, masses)
                coefficients[i] = conn.coefficients
                cache.put(state, masses, conn)
    else:
        # Compute without caching (for profiling/testing)
        from .connection import compute_connection_form
        for i in range(N):
            state = batch[i]
            conn = compute_connection_form(state, masses)
            coefficients[i] = conn.coefficients

    return coefficients


def compute_curvature_batch(
    batch: BatchShapeSpace,
    masses: Masses,
    parallel: bool = True,
    n_workers: Optional[int] = None
) -> np.ndarray:
    """
    Compute curvature for batch of points.

    Uses parallel processing for large batches.

    Args:
        batch: Batch of N points
        masses: Body masses
        parallel: Use multiprocessing if True
        n_workers: Number of parallel workers (default: cpu_count)

    Returns:
        (N, 3, 3) array of curvature matrices
    """
    N = batch.size

    if not parallel or N < 100:
        # Serial computation for small batches
        return _compute_curvature_batch_serial(batch, masses)

    # Parallel computation
    from multiprocessing import Pool, cpu_count
    from functools import partial

    if n_workers is None:
        n_workers = cpu_count()

    # Split batch into chunks
    chunk_size = max(1, N // n_workers)
    chunks = [
        BatchShapeSpace(
            r12=batch.r12[i:i+chunk_size],
            r23=batch.r23[i:i+chunk_size],
            r31=batch.r31[i:i+chunk_size],
            L=batch.L if isinstance(batch.L, float) else batch.L[i:i+chunk_size]
        )
        for i in range(0, N, chunk_size)
    ]

    # Process chunks in parallel
    compute_func = partial(_compute_curvature_batch_serial, masses=masses)

    with Pool(n_workers) as pool:
        results = pool.map(compute_func, chunks)

    # Concatenate results
    curvatures = np.concatenate(results, axis=0)

    return curvatures


def _compute_curvature_batch_serial(
    batch: BatchShapeSpace,
    masses: Masses
) -> np.ndarray:
    """Serial curvature computation for a batch."""
    from .connection import compute_connection_form
    from .curvature import compute_curvature_form

    N = batch.size
    curvatures = np.zeros((N, 3, 3))

    connection_evaluator = lambda s: compute_connection_form(s, masses)

    for i in range(N):
        state = batch[i]
        curv = compute_curvature_form(connection_evaluator, state)
        curvatures[i] = curv.matrix

    return curvatures
```

### Grid-Based Evaluation

For visualization, we often need values on regular grids:

```python
def compute_connection_grid(
    r12_range: tuple[float, float],
    r23_range: tuple[float, float],
    r31_fixed: float,
    L: float,
    masses: Masses,
    resolution: int = 50
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute connection field on 2D grid.

    Args:
        r12_range: (min, max) for r12
        r23_range: (min, max) for r23
        r31_fixed: Fixed value for r31
        L: Angular momentum
        masses: Body masses
        resolution: Grid resolution (N×N)

    Returns:
        r12_grid: (N, N) grid of r12 values
        r23_grid: (N, N) grid of r23 values
        conn_field: (N, N, 3) array of connection coefficients
    """
    r12_vals = np.linspace(*r12_range, resolution)
    r23_vals = np.linspace(*r23_range, resolution)

    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    # Flatten for batch computation
    r12_flat = r12_grid.ravel()
    r23_flat = r23_grid.ravel()
    r31_flat = np.full_like(r12_flat, r31_fixed)

    batch = BatchShapeSpace(
        r12=r12_flat,
        r23=r23_flat,
        r31=r31_flat,
        L=L
    )

    # Filter valid triangles
    valid = batch.validate_triangle_inequality()

    # Compute connection only for valid points
    conn_coeffs = np.full((len(r12_flat), 3), np.nan)
    if np.any(valid):
        valid_batch = BatchShapeSpace(
            r12=r12_flat[valid],
            r23=r23_flat[valid],
            r31=r31_flat[valid],
            L=L
        )
        conn_coeffs[valid] = compute_connection_batch(valid_batch, masses)

    # Reshape to grid
    conn_field = conn_coeffs.reshape(resolution, resolution, 3)

    return r12_grid, r23_grid, conn_field
```

---

## C2: Adaptive Precision Control

### Precision Hierarchy

We support three precision levels:

1. **Double (float64)**: Default, fastest (~100 μs per point)
2. **Quad (float128)**: High precision (~500 μs per point)
3. **Symbolic (SymPy)**: Arbitrary precision (~10 ms per point)

```python
# File: src/python/geometry/precision.py

import numpy as np
from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from .connection import ConnectionForm


class PrecisionLevel(Enum):
    """Available precision levels."""
    DOUBLE = 'float64'
    QUAD = 'float128'
    SYMBOLIC = 'symbolic'


@dataclass
class PrecisionConfig:
    """
    Configuration for adaptive precision control.

    Attributes:
        default_level: Starting precision level
        auto_escalate: Automatically increase precision if needed
        error_threshold: Max acceptable relative error
        max_level: Don't escalate beyond this level
    """
    default_level: PrecisionLevel = PrecisionLevel.DOUBLE
    auto_escalate: bool = True
    error_threshold: float = 1e-10
    max_level: PrecisionLevel = PrecisionLevel.QUAD


class AdaptivePrecisionEvaluator:
    """
    Evaluator that automatically escalates precision when needed.

    Example:
        evaluator = AdaptivePrecisionEvaluator(masses)
        connection = evaluator.compute_connection(state)
        # Automatically uses double precision, escalates if unstable
    """

    def __init__(
        self,
        masses: Masses,
        config: PrecisionConfig = PrecisionConfig()
    ):
        self.masses = masses
        self.config = config
        self._precision_stats = {
            'double_count': 0,
            'quad_count': 0,
            'symbolic_count': 0
        }

    def compute_connection(
        self,
        state: ShapeSpaceState
    ) -> ConnectionForm:
        """
        Compute connection with adaptive precision.

        Tries double precision first, escalates if needed.
        """
        # Try double precision
        try:
            conn_double = self._compute_connection_double(state)

            if not self.config.auto_escalate:
                self._precision_stats['double_count'] += 1
                return conn_double

            # Check if result is stable
            if self._is_result_stable(conn_double, state):
                self._precision_stats['double_count'] += 1
                return conn_double

        except NumericalInstabilityError:
            pass  # Escalate to quad

        # Try quad precision
        if self.config.max_level.value >= PrecisionLevel.QUAD.value:
            try:
                conn_quad = self._compute_connection_quad(state)

                if self._is_result_stable(conn_quad, state):
                    self._precision_stats['quad_count'] += 1
                    return conn_quad

            except NumericalInstabilityError:
                pass  # Escalate to symbolic

        # Last resort: symbolic
        if self.config.max_level == PrecisionLevel.SYMBOLIC:
            conn_symbolic = self._compute_connection_symbolic(state)
            self._precision_stats['symbolic_count'] += 1
            return conn_symbolic

        # If we can't escalate further, return best available
        self._precision_stats['quad_count'] += 1
        return conn_quad

    def _compute_connection_double(
        self,
        state: ShapeSpaceState
    ) -> ConnectionForm:
        """Compute using double precision (float64)."""
        from .connection import compute_connection_form
        return compute_connection_form(state, self.masses)

    def _compute_connection_quad(
        self,
        state: ShapeSpaceState
    ) -> ConnectionForm:
        """Compute using quad precision (float128)."""
        # Convert to quad precision
        # (Requires reimplementing core routines with np.float128)

        # Placeholder implementation
        # In practice, we'd have separate quad-precision versions
        # of locked_inertia, shape_lifts, etc.

        raise NotImplementedError("Quad precision not yet implemented")

    def _compute_connection_symbolic(
        self,
        state: ShapeSpaceState
    ) -> ConnectionForm:
        """Compute using symbolic math (SymPy)."""
        from .symbolic_curvature import compute_connection_symbolic

        return compute_connection_symbolic(state, self.masses)

    def _is_result_stable(
        self,
        connection: ConnectionForm,
        state: ShapeSpaceState
    ) -> bool:
        """
        Check if result is numerically stable.

        Strategy:
            1. Re-compute with slightly perturbed input
            2. Check if result changes significantly
            3. If change is large → unstable
        """
        # Perturb state slightly
        epsilon = 1e-8
        state_perturbed = ShapeSpaceState(
            r12=state.r12 * (1 + epsilon),
            r23=state.r23,
            r31=state.r31,
            L=state.L
        )

        # Re-compute
        conn_perturbed = self._compute_connection_double(state_perturbed)

        # Check relative change
        relative_change = np.linalg.norm(
            conn_perturbed.coefficients - connection.coefficients
        ) / np.linalg.norm(connection.coefficients)

        # Expected change due to perturbation (from derivatives)
        # Actual change should be O(epsilon)
        expected_change = epsilon * 10  # Allow factor of 10 for derivatives

        return relative_change < expected_change

    def get_precision_stats(self) -> dict:
        """Return statistics on precision usage."""
        total = sum(self._precision_stats.values())
        if total == 0:
            return self._precision_stats

        return {
            'counts': self._precision_stats,
            'percentages': {
                k: 100 * v / total
                for k, v in self._precision_stats.items()
            }
        }


class NumericalInstabilityError(Exception):
    """Raised when numerical computation is unstable."""
    pass


def detect_numerical_issues(
    values: np.ndarray,
    operation_name: str = "computation"
) -> Optional[str]:
    """
    Detect common numerical issues in array.

    Returns:
        None if no issues, otherwise error message
    """
    if np.any(np.isnan(values)):
        return f"{operation_name}: NaN detected"

    if np.any(np.isinf(values)):
        return f"{operation_name}: Inf detected"

    # Check for very large values (potential overflow)
    if np.any(np.abs(values) > 1e100):
        return f"{operation_name}: Very large values (potential overflow)"

    # Check for underflow (all values tiny)
    if np.all(np.abs(values) < 1e-100) and values.size > 0:
        return f"{operation_name}: Very small values (potential underflow)"

    return None
```

### Precision Escalation Examples

```python
def test_precision_escalation():
    """
    Test adaptive precision on challenging cases.
    """
    from ..coordinates.base import Masses

    masses = Masses(1.0, 1.0, 1.0)

    # Case 1: Near-collinear (numerically challenging)
    state_collinear = ShapeSpaceState(
        r12=1.0,
        r23=0.5,
        r31=1.5 - 1e-6,  # Nearly collinear
        L=1.0
    )

    evaluator = AdaptivePrecisionEvaluator(masses)
    conn = evaluator.compute_connection(state_collinear)

    print(f"Precision used: {evaluator.get_precision_stats()}")

    # Should have escalated to quad or symbolic
    assert evaluator._precision_stats['quad_count'] > 0 or \
           evaluator._precision_stats['symbolic_count'] > 0


def benchmark_precision_levels():
    """
    Compare speed vs accuracy for different precision levels.
    """
    import time

    state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)
    masses = Masses(1.0, 1.0, 1.0)

    # Double precision
    start = time.perf_counter()
    config_double = PrecisionConfig(
        default_level=PrecisionLevel.DOUBLE,
        auto_escalate=False
    )
    eval_double = AdaptivePrecisionEvaluator(masses, config_double)
    conn_double = eval_double.compute_connection(state)
    time_double = time.perf_counter() - start

    # Quad precision
    start = time.perf_counter()
    config_quad = PrecisionConfig(
        default_level=PrecisionLevel.QUAD,
        auto_escalate=False
    )
    eval_quad = AdaptivePrecisionEvaluator(masses, config_quad)
    conn_quad = eval_quad.compute_connection(state)
    time_quad = time.perf_counter() - start

    print(f"Double: {time_double*1e6:.1f} μs")
    print(f"Quad:   {time_quad*1e6:.1f} μs")
    print(f"Speedup: {time_quad/time_double:.1f}x slower")

    # Accuracy comparison
    error = np.linalg.norm(conn_double.coefficients - conn_quad.coefficients)
    print(f"Error: {error:.6e}")
```

---

## C3: Caching and Memoization

### Intelligent Cache System

```python
# File: src/python/geometry/cache.py

import numpy as np
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import hashlib
import pickle
from pathlib import Path

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from .connection import ConnectionForm
from .curvature import CurvatureForm


@dataclass
class CacheConfig:
    """
    Configuration for caching system.

    Attributes:
        max_memory_mb: Maximum cache memory in MB
        persistence: Save cache to disk
        cache_dir: Directory for persistent cache
        ttl_seconds: Time-to-live for cache entries (None = infinite)
    """
    max_memory_mb: int = 100
    persistence: bool = False
    cache_dir: Optional[Path] = None
    ttl_seconds: Optional[float] = None


class ConnectionCache:
    """
    Intelligent cache for connection computations.

    Features:
        - LRU eviction when memory limit reached
        - Optional disk persistence
        - Fast hash-based lookup
        - Thread-safe operations
    """

    def __init__(self, config: CacheConfig = CacheConfig()):
        self.config = config
        self._cache: Dict[str, Tuple[ConnectionForm, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._current_size_bytes = 0

        if config.persistence and config.cache_dir:
            self._load_from_disk()

    def _hash_key(
        self,
        state: ShapeSpaceState,
        masses: Masses
    ) -> str:
        """
        Create hash key for (state, masses).

        Uses rounded values for robustness.
        """
        # Round to 12 decimal places for hash stability
        key_tuple = (
            round(state.r12, 12),
            round(state.r23, 12),
            round(state.r31, 12),
            round(state.L, 12),
            round(masses.m1, 12),
            round(masses.m2, 12),
            round(masses.m3, 12)
        )

        # Create hash
        key_str = str(key_tuple)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self,
        state: ShapeSpaceState,
        masses: Masses
    ) -> Optional[ConnectionForm]:
        """
        Retrieve connection from cache.

        Returns None if not found or expired.
        """
        key = self._hash_key(state, masses)

        if key not in self._cache:
            return None

        connection, insert_time = self._cache[key]

        # Check TTL
        if self.config.ttl_seconds is not None:
            import time
            age = time.time() - insert_time
            if age > self.config.ttl_seconds:
                # Expired - remove
                del self._cache[key]
                return None

        # Update access time (for LRU)
        import time
        self._access_times[key] = time.time()

        return connection

    def put(
        self,
        state: ShapeSpaceState,
        masses: Masses,
        connection: ConnectionForm
    ):
        """
        Store connection in cache.

        Evicts LRU entries if memory limit reached.
        """
        key = self._hash_key(state, masses)

        # Estimate size
        entry_size = self._estimate_size(connection)

        # Check if we need to evict
        max_bytes = self.config.max_memory_mb * 1024 * 1024
        while (self._current_size_bytes + entry_size > max_bytes and
               len(self._cache) > 0):
            self._evict_lru()

        # Store
        import time
        self._cache[key] = (connection, time.time())
        self._access_times[key] = time.time()
        self._current_size_bytes += entry_size

        # Persist if enabled
        if self.config.persistence:
            self._save_to_disk()

    def _estimate_size(self, connection: ConnectionForm) -> int:
        """Estimate memory size of connection object."""
        # Rough estimate: coefficients array + overhead
        return connection.coefficients.nbytes + 1000  # ~1KB overhead

    def _evict_lru(self):
        """Evict least-recently-used entry."""
        if not self._access_times:
            return

        # Find LRU key
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]

        # Estimate size and remove
        connection, _ = self._cache[lru_key]
        size = self._estimate_size(connection)

        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._current_size_bytes -= size

    def _save_to_disk(self):
        """Save cache to disk (pickle format)."""
        if not self.config.cache_dir:
            return

        cache_file = self.config.cache_dir / 'connection_cache.pkl'
        with open(cache_file, 'wb') as f:
            pickle.dump(self._cache, f)

    def _load_from_disk(self):
        """Load cache from disk."""
        if not self.config.cache_dir:
            return

        cache_file = self.config.cache_dir / 'connection_cache.pkl'
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                self._cache = pickle.load(f)

            # Recompute sizes
            self._current_size_bytes = sum(
                self._estimate_size(conn)
                for conn, _ in self._cache.values()
            )

    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
        self._access_times.clear()
        self._current_size_bytes = 0

    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            'entries': len(self._cache),
            'size_mb': self._current_size_bytes / (1024 * 1024),
            'max_size_mb': self.config.max_memory_mb,
            'utilization': self._current_size_bytes / (self.config.max_memory_mb * 1024 * 1024)
        }


# Global cache instance
_global_connection_cache: Optional[ConnectionCache] = None


def get_connection_cache() -> ConnectionCache:
    """Get global connection cache (singleton)."""
    global _global_connection_cache
    if _global_connection_cache is None:
        _global_connection_cache = ConnectionCache()
    return _global_connection_cache


def set_cache_config(config: CacheConfig):
    """Configure global cache."""
    global _global_connection_cache
    _global_connection_cache = ConnectionCache(config)
```

### Cache Performance Testing

```python
def test_cache_hit_rate():
    """
    Test cache effectiveness on realistic workload.
    """
    import time
    from ..coordinates.base import Masses

    masses = Masses(1.0, 1.0, 1.0)

    # Create workload with repeated queries
    states = [
        ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0),
        ShapeSpaceState(r12=1.1, r23=1.0, r31=1.05, L=1.0),
        ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0),  # Repeat
        ShapeSpaceState(r12=1.05, r23=1.05, r31=1.05, L=1.0),
        ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0),  # Repeat
    ]

    cache = get_connection_cache()
    cache.clear()

    from .connection import compute_connection_form

    # Benchmark with cache
    start = time.perf_counter()
    for state in states:
        cached = cache.get(state, masses)
        if cached is None:
            conn = compute_connection_form(state, masses)
            cache.put(state, masses, conn)
    time_cached = time.perf_counter() - start

    # Benchmark without cache
    start = time.perf_counter()
    for state in states:
        conn = compute_connection_form(state, masses)
    time_uncached = time.perf_counter() - start

    print(f"With cache:    {time_cached*1e3:.2f} ms")
    print(f"Without cache: {time_uncached*1e3:.2f} ms")
    print(f"Speedup:       {time_uncached/time_cached:.2f}x")
    print(f"Cache stats:   {cache.stats()}")

    # Should see ~2x speedup due to repeated queries
    assert time_cached < time_uncached
```

---

## C4: Parallel Computation

### Multiprocessing Strategy

```python
# File: src/python/geometry/parallel.py

import numpy as np
from multiprocessing import Pool, cpu_count
from typing import Callable, List, Optional
from dataclasses import dataclass

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from .batch_ops import BatchShapeSpace


@dataclass
class ParallelConfig:
    """
    Configuration for parallel computation.

    Attributes:
        n_workers: Number of parallel workers (None = cpu_count)
        chunk_size: Points per chunk (None = auto-determine)
        use_threads: Use threading instead of processes
    """
    n_workers: Optional[int] = None
    chunk_size: Optional[int] = None
    use_threads: bool = False


def parallel_connection_eval(
    states: List[ShapeSpaceState],
    masses: Masses,
    config: ParallelConfig = ParallelConfig()
) -> List[np.ndarray]:
    """
    Evaluate connection at many points in parallel.

    Args:
        states: List of N shape space points
        masses: Body masses
        config: Parallel configuration

    Returns:
        List of N connection coefficient arrays
    """
    from .connection import compute_connection_form

    n_workers = config.n_workers or cpu_count()

    # Determine chunk size
    if config.chunk_size:
        chunk_size = config.chunk_size
    else:
        # Auto: aim for ~4 chunks per worker
        chunk_size = max(1, len(states) // (n_workers * 4))

    # Split into chunks
    chunks = [
        states[i:i+chunk_size]
        for i in range(0, len(states), chunk_size)
    ]

    # Define worker function
    def worker(chunk: List[ShapeSpaceState]) -> List[np.ndarray]:
        results = []
        for state in chunk:
            conn = compute_connection_form(state, masses)
            results.append(conn.coefficients)
        return results

    # Execute in parallel
    if config.use_threads:
        from multiprocessing.pool import ThreadPool as Pool_

        with Pool_(n_workers) as pool:
            chunk_results = pool.map(worker, chunks)
    else:
        with Pool(n_workers) as pool:
            chunk_results = pool.map(worker, chunks)

    # Flatten results
    results = [item for chunk in chunk_results for item in chunk]

    return results


def parallel_curvature_eval(
    states: List[ShapeSpaceState],
    masses: Masses,
    config: ParallelConfig = ParallelConfig()
) -> List[np.ndarray]:
    """
    Evaluate curvature at many points in parallel.

    More expensive than connection, so uses coarser chunking.
    """
    from .connection import compute_connection_form
    from .curvature import compute_curvature_form

    n_workers = config.n_workers or cpu_count()

    # Larger chunks for curvature (more expensive per point)
    if config.chunk_size:
        chunk_size = config.chunk_size
    else:
        chunk_size = max(1, len(states) // n_workers)

    chunks = [
        states[i:i+chunk_size]
        for i in range(0, len(states), chunk_size)
    ]

    def worker(chunk: List[ShapeSpaceState]) -> List[np.ndarray]:
        conn_eval = lambda s: compute_connection_form(s, masses)
        results = []
        for state in chunk:
            curv = compute_curvature_form(conn_eval, state)
            results.append(curv.matrix)
        return results

    with Pool(n_workers) as pool:
        chunk_results = pool.map(worker, chunks)

    results = [item for chunk in chunk_results for item in chunk]

    return results
```

### Parallel Performance Benchmark

```python
def benchmark_parallel_scaling():
    """
    Test parallel scaling efficiency.
    """
    import time
    from ..coordinates.base import Masses

    masses = Masses(1.0, 1.0, 1.0)

    # Create large batch
    N = 1000
    states = [
        ShapeSpaceState(
            r12=1.0 + 0.1 * np.random.rand(),
            r23=1.0 + 0.1 * np.random.rand(),
            r31=1.0 + 0.1 * np.random.rand(),
            L=1.0
        )
        for _ in range(N)
    ]

    # Benchmark serial
    start = time.perf_counter()
    from .connection import compute_connection_form
    results_serial = [
        compute_connection_form(s, masses).coefficients
        for s in states
    ]
    time_serial = time.perf_counter() - start

    # Benchmark parallel with different worker counts
    for n_workers in [2, 4, 8]:
        config = ParallelConfig(n_workers=n_workers)
        start = time.perf_counter()
        results_parallel = parallel_connection_eval(states, masses, config)
        time_parallel = time.perf_counter() - start

        speedup = time_serial / time_parallel
        efficiency = speedup / n_workers * 100

        print(f"Workers: {n_workers}")
        print(f"  Time:       {time_parallel:.2f} s")
        print(f"  Speedup:    {speedup:.2f}x")
        print(f"  Efficiency: {efficiency:.1f}%")

        # Verify correctness
        assert np.allclose(results_serial, results_parallel)
```

---

## C5: Numerical Stability

### Handling Degenerate Cases

```python
# File: src/python/geometry/stability.py

import numpy as np
from typing import Optional
from dataclasses import dataclass

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses


@dataclass
class StabilityMetrics:
    """
    Metrics for assessing numerical stability.

    Attributes:
        condition_number: Condition number of linear systems
        is_near_collision: True if any pair very close
        is_near_collinear: True if nearly on a line
        recommended_precision: Suggested precision level
    """
    condition_number: float
    is_near_collision: bool
    is_near_collinear: bool
    recommended_precision: str


def assess_stability(
    state: ShapeSpaceState,
    masses: Masses
) -> StabilityMetrics:
    """
    Assess numerical stability for a given state.

    Returns metrics and recommendations.
    """
    # Check for near-collision
    min_distance = min(state.r12, state.r23, state.r31)
    max_distance = max(state.r12, state.r23, state.r31)

    is_near_collision = min_distance < 0.01 * max_distance

    # Check for near-collinearity (triangle inequality nearly violated)
    s1 = state.r12 + state.r23 - state.r31
    s2 = state.r23 + state.r31 - state.r12
    s3 = state.r31 + state.r12 - state.r23

    triangle_margin = min(s1, s2, s3) / max_distance

    is_near_collinear = triangle_margin < 1e-6

    # Estimate condition number (from locked inertia matrix)
    from .locked_inertia import compute_locked_inertia_tensor
    from .connection import _shape_to_cartesian_canonical

    cart_state = _shape_to_cartesian_canonical(state)
    I_tensor = compute_locked_inertia_tensor(cart_state, masses)

    eigenvalues = np.linalg.eigvalsh(I_tensor.components)
    condition_number = eigenvalues.max() / eigenvalues.min()

    # Recommend precision
    if is_near_collision or is_near_collinear:
        recommended = 'symbolic'
    elif condition_number > 1e10:
        recommended = 'quad'
    else:
        recommended = 'double'

    return StabilityMetrics(
        condition_number=condition_number,
        is_near_collision=is_near_collision,
        is_near_collinear=is_near_collinear,
        recommended_precision=recommended
    )


def regularize_near_collision(
    state: ShapeSpaceState,
    min_distance: float = 0.01
) -> ShapeSpaceState:
    """
    Regularize state if near collision.

    Slightly increases small distances to avoid singularities.
    """
    r12 = max(state.r12, min_distance)
    r23 = max(state.r23, min_distance)
    r31 = max(state.r31, min_distance)

    return ShapeSpaceState(
        r12=r12,
        r23=r23,
        r31=r31,
        L=state.L
    )
```

---

## Implementation Details

### Module Structure

```
src/python/geometry/
├── batch_ops.py         # C1: Vectorized batch operations
├── precision.py         # C2: Adaptive precision control
├── cache.py             # C3: Caching system
├── parallel.py          # C4: Parallel computation
├── stability.py         # C5: Numerical stability
└── profiler.py          # Performance profiling tools
```

---

## Profiling and Benchmarks

### Profiling Infrastructure

```python
# File: src/python/geometry/profiler.py

import time
import numpy as np
from typing import Callable, Dict, List
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class ProfileEntry:
    """Single profiling measurement."""
    function_name: str
    duration_seconds: float
    call_count: int = 1
    metadata: dict = field(default_factory=dict)


class GeometryProfiler:
    """
    Profiler for geometry computations.

    Usage:
        with profiler.time('connection_eval'):
            conn = compute_connection_form(state, masses)
    """

    def __init__(self):
        self._entries: List[ProfileEntry] = []
        self._active_timers: Dict[str, float] = {}

    @contextmanager
    def time(self, name: str, **metadata):
        """Context manager for timing a code block."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self._entries.append(
                ProfileEntry(name, duration, metadata=metadata)
            )

    def summary(self) -> dict:
        """Generate summary statistics."""
        if not self._entries:
            return {}

        # Group by function name
        by_function = {}
        for entry in self._entries:
            if entry.function_name not in by_function:
                by_function[entry.function_name] = []
            by_function[entry.function_name].append(entry.duration_seconds)

        # Compute statistics
        summary = {}
        for func, durations in by_function.items():
            summary[func] = {
                'count': len(durations),
                'total_time': sum(durations),
                'mean_time': np.mean(durations),
                'std_time': np.std(durations),
                'min_time': min(durations),
                'max_time': max(durations)
            }

        return summary

    def print_summary(self):
        """Print formatted summary."""
        summary = self.summary()

        print("\n" + "="*70)
        print("Geometry Computation Profile")
        print("="*70)
        print(f"{'Function':<30} {'Count':>8} {'Total (ms)':>12} {'Mean (μs)':>12}")
        print("-"*70)

        for func, stats in sorted(summary.items(), key=lambda x: x[1]['total_time'], reverse=True):
            print(f"{func:<30} {stats['count']:>8} "
                  f"{stats['total_time']*1e3:>12.2f} "
                  f"{stats['mean_time']*1e6:>12.1f}")

        print("="*70)


# Global profiler instance
_global_profiler: Optional[GeometryProfiler] = None


def get_profiler() -> GeometryProfiler:
    """Get global profiler."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = GeometryProfiler()
    return _global_profiler
```

---

## Integration Guide

### Example: Complete Optimized Pipeline

```python
from geometry.batch_ops import BatchShapeSpace, compute_connection_batch
from geometry.cache import set_cache_config, CacheConfig
from geometry.parallel import parallel_connection_eval, ParallelConfig
from geometry.profiler import get_profiler
from coordinates.base import Masses

# Configure cache
set_cache_config(CacheConfig(
    max_memory_mb=200,
    persistence=True,
    cache_dir=Path('./cache')
))

# Create profiler
profiler = get_profiler()

# Create batch
masses = Masses(1.0, 1.0, 1.0)
N = 10000

batch = BatchShapeSpace(
    r12=np.random.uniform(0.8, 1.2, N),
    r23=np.random.uniform(0.8, 1.2, N),
    r31=np.random.uniform(0.8, 1.2, N),
    L=1.0
)

# Filter valid
valid = batch.validate_triangle_inequality()
batch_valid = BatchShapeSpace(
    r12=batch.r12[valid],
    r23=batch.r23[valid],
    r31=batch.r31[valid],
    L=1.0
)

# Compute with profiling
with profiler.time('full_batch'):
    connections = compute_connection_batch(batch_valid, masses)

# Print results
profiler.print_summary()
print(f"Computed {len(connections)} connections")
```

---

## Success Criteria

### Part C Complete When:

- [ ] Vectorized batch operations implemented
- [ ] Adaptive precision control working
- [ ] Caching system functional with configurable limits
- [ ] Parallel computation achieves >80% efficiency on 4 cores
- [ ] Numerical stability handling for edge cases
- [ ] All performance targets met:
  - [ ] Connection: < 100 μs per point
  - [ ] Curvature: < 1 ms per point
  - [ ] Batch (1000 pts): < 100 ms
- [ ] Profiling infrastructure in place
- [ ] Documentation complete with performance guides

**Ready to proceed to Part D** when all boxes checked.

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 2-3 days
**Next**: Part D (Visualization & Validation)
