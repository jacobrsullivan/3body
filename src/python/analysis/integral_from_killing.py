"""
Convert Killing fields to conserved quantities (WP 3.1, Task 3.1.4, Part A).

A Killing vector field K on (Q, g_JM) generates a conserved quantity along
geodesics (which correspond to dynamical trajectories).

Mathematical Framework:
    For Killing vector K: I_K(q, v) = g_ij(q) K^i(q) v^j
    For Killing tensor T: I_T(q, v) = T_ij(q) v^i v^j

These quantities are conserved: dI/dt = 0 along trajectories.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, List
import numpy as np
from scipy.interpolate import RBFInterpolator

from ..pde.mesh_generation import Mesh


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class ConservedIntegral:
    """
    Conserved quantity derived from geometric structure.

    Attributes:
        name: Descriptive name
        expression: Callable I(state) -> float
        gradient: Callable returning (∂I/∂q, ∂I/∂p)
        source: Origin ('killing_vector', 'killing_tensor', 'known')
        manifold_type: 's1_bundle', 'ks_spinor', or 'generic'
        residual: Max |dI/dt| on test trajectories
        killing_field: Reference to source Killing field (if applicable)
        metadata: Additional information
    """
    name: str
    expression: Callable[[np.ndarray], float]
    gradient: Optional[Callable[[np.ndarray], Tuple[np.ndarray, np.ndarray]]] = None
    source: str = 'unknown'
    manifold_type: str = 'generic'
    residual: float = np.nan
    killing_field: Optional[np.ndarray] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def __call__(self, state: np.ndarray) -> float:
        """Evaluate integral at state"""
        return self.expression(state)


@dataclass
class State:
    """Phase space state (q, p) or (q, v)"""
    q: np.ndarray  # Configuration coordinates
    p: np.ndarray  # Momenta (or velocities)

    def __post_init__(self):
        assert len(self.q) == len(self.p), "Coordinates and momenta must have same dimension"

    @property
    def dimension(self) -> int:
        return len(self.q)

    def to_array(self) -> np.ndarray:
        """Flatten to 1D array [q, p]"""
        return np.concatenate([self.q, self.p])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'State':
        """Create from flattened array"""
        n = len(arr) // 2
        return cls(q=arr[:n], p=arr[n:])


# =============================================================================
# Part A1: Killing Vector to Linear Integral
# =============================================================================

def killing_vector_to_integral(
    killing_field: np.ndarray,
    mesh: Mesh,
    metric_func: Callable[[np.ndarray], np.ndarray],
    *,
    interpolation_method: str = 'rbf',
    name: Optional[str] = None,
    verbose: bool = False
) -> ConservedIntegral:
    """
    Convert Killing vector field to conserved integral.

    Mathematical formula:
        I_K(q, v) = g_ij(q) K^i(q) v^j = K_i v^i (with lowered indices)

    Implementation:
    1. Interpolate K from mesh to continuous function
    2. Define I(state) = g(q) · K(q) · v
    3. Compute gradient analytically (if possible) or numerically

    Args:
        killing_field: (n_total,) flattened Killing vector on mesh
                       Components: [K_0(pt_0), K_1(pt_0), ..., K_0(pt_1), ...]
        mesh: Mesh on which K is defined
        metric_func: Function g(q) → metric tensor (n×n)
        interpolation_method: 'rbf' or 'linear'
        name: Name for this integral (auto-generated if None)
        verbose: Print diagnostic info

    Returns:
        ConservedIntegral with callable expression I(state)
    """
    n = mesh.dimension
    N = mesh.num_points

    # Reshape killing field: (n_total,) → (N, n)
    K_field = killing_field.reshape((N, n))

    if verbose:
        print(f"Converting Killing vector to integral:")
        print(f"  Dimension: {n}")
        print(f"  Mesh points: {N}")
        print(f"  Interpolation: {interpolation_method}")

    # Build interpolators for each component K^i
    interpolators = []

    if interpolation_method == 'rbf':
        for i in range(n):
            K_i_values = K_field[:, i]
            interp = RBFInterpolator(
                mesh.points,
                K_i_values,
                kernel='thin_plate_spline',
                smoothing=1e-6,
                degree=1
            )
            interpolators.append(interp)

    elif interpolation_method == 'linear':
        # Linear interpolation (would need scipy.interpolate.LinearNDInterpolator)
        # For now, use nearest neighbor as fallback
        from scipy.spatial import cKDTree
        tree = cKDTree(mesh.points)

        def make_nearest_interp(values):
            def interp(q):
                if q.ndim == 1:
                    q = q[None, :]
                _, indices = tree.query(q)
                return values[indices]
            return interp

        for i in range(n):
            interpolators.append(make_nearest_interp(K_field[:, i]))

    else:
        raise ValueError(f"Unknown interpolation method: {interpolation_method}")

    # Define integral expression
    def integral_expression(state: np.ndarray) -> float:
        """
        Evaluate I_K at state.

        Args:
            state: Either State object or array [q, p] or [q, v]
        """
        if isinstance(state, State):
            q = state.q
            v = state.p  # Treat as velocity
        elif isinstance(state, np.ndarray):
            if len(state) == 2 * n:
                q = state[:n]
                v = state[n:]
            else:
                raise ValueError(f"State must be length {2*n}, got {len(state)}")
        else:
            raise TypeError(f"State must be State or ndarray, got {type(state)}")

        # Evaluate K at q
        K = np.array([interp(q[None, :])[0] for interp in interpolators])

        # Evaluate metric at q
        g = metric_func(q)

        # Lower index: K_i = g_ij K^j
        K_lowered = g @ K

        # Compute I = K_i v^i
        return np.dot(K_lowered, v)

    # Define gradient (simplified - exact formula would need metric derivatives)
    def integral_gradient(state: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute (∂I/∂q, ∂I/∂p).

        For I = g_ij K^i v^j:
            ∂I/∂q_k = (∂g_ij/∂q_k) K^i v^j + g_ij (∂K^i/∂q_k) v^j
            ∂I/∂v_k = g_ij K^i δ^j_k = g_ik K^i = K_k (lowered)
        """
        if isinstance(state, State):
            q = state.q
            v = state.p
        elif isinstance(state, np.ndarray):
            q = state[:n]
            v = state[n:]
        else:
            raise TypeError("State must be State or ndarray")

        # Evaluate K and metric at q
        K = np.array([interp(q[None, :])[0] for interp in interpolators])
        g = metric_func(q)
        K_lowered = g @ K

        # ∂I/∂v is straightforward
        dI_dv = K_lowered

        # ∂I/∂q requires finite differences (or automatic differentiation)
        eps = 1e-6
        dI_dq = np.zeros(n)
        I_0 = integral_expression(np.concatenate([q, v]))

        for k in range(n):
            q_plus = q.copy()
            q_plus[k] += eps
            I_plus = integral_expression(np.concatenate([q_plus, v]))
            dI_dq[k] = (I_plus - I_0) / eps

        return dI_dq, dI_dv

    # Create ConservedIntegral object
    if name is None:
        name = f"KillingVectorIntegral_{id(killing_field) % 10000}"

    return ConservedIntegral(
        name=name,
        expression=integral_expression,
        gradient=integral_gradient,
        source='killing_vector',
        manifold_type='generic',
        residual=np.nan,
        killing_field=killing_field,
        metadata={
            'dimension': n,
            'mesh_points': N,
            'interpolation': interpolation_method
        }
    )


# =============================================================================
# Part A2: Killing Tensor to Quadratic Integral
# =============================================================================

def killing_tensor_to_integral(
    killing_tensor: np.ndarray,
    mesh: Mesh,
    metric_func: Callable[[np.ndarray], np.ndarray],
    *,
    interpolation_method: str = 'rbf',
    name: Optional[str] = None,
    verbose: bool = False
) -> ConservedIntegral:
    """
    Convert Killing tensor to quadratic integral.

    Mathematical formula:
        I_T(q, v) = T_ij(q) v^i v^j

    Args:
        killing_tensor: (n_tensor_total,) flattened symmetric tensor on mesh
                        For n×n symmetric: n(n+1)/2 components per point
        mesh: Mesh structure
        metric_func: Metric function g(q)
        interpolation_method: Interpolation scheme
        name: Integral name
        verbose: Diagnostics

    Returns:
        ConservedIntegral for quadratic quantity
    """
    n = mesh.dimension
    N = mesh.num_points
    n_components = n * (n + 1) // 2

    # Reshape tensor: (n_components × N,) → (N, n, n) symmetric
    T_field = np.zeros((N, n, n))

    idx = 0
    for pt in range(N):
        comp_idx = 0
        for i in range(n):
            for j in range(i, n):
                value = killing_tensor[pt * n_components + comp_idx]
                T_field[pt, i, j] = value
                T_field[pt, j, i] = value  # Symmetry
                comp_idx += 1

    if verbose:
        print(f"Converting Killing tensor to integral:")
        print(f"  Dimension: {n}")
        print(f"  Tensor components: {n_components}")
        print(f"  Mesh points: {N}")

    # Build interpolators for each component T_ij (only upper triangle)
    interpolators = {}

    for i in range(n):
        for j in range(i, n):
            T_ij_values = T_field[:, i, j]

            if interpolation_method == 'rbf':
                interp = RBFInterpolator(
                    mesh.points,
                    T_ij_values,
                    kernel='thin_plate_spline',
                    smoothing=1e-6,
                    degree=1
                )
            else:  # nearest neighbor
                from scipy.spatial import cKDTree
                tree = cKDTree(mesh.points)
                def make_interp(vals):
                    def interp_func(q):
                        if q.ndim == 1:
                            q = q[None, :]
                        _, indices = tree.query(q)
                        return vals[indices]
                    return interp_func
                interp = make_interp(T_ij_values)

            interpolators[(i, j)] = interp

    # Define integral expression
    def integral_expression(state: np.ndarray) -> float:
        """Evaluate I_T = T_ij v^i v^j"""
        if isinstance(state, State):
            q = state.q
            v = state.p
        elif isinstance(state, np.ndarray):
            q = state[:n]
            v = state[n:]
        else:
            raise TypeError("State must be State or ndarray")

        # Evaluate T at q
        T = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                val = interpolators[(i, j)](q[None, :])[0]
                T[i, j] = val
                T[j, i] = val

        # Compute I = T_ij v^i v^j = v^T T v
        return v @ T @ v

    # Gradient (simplified)
    def integral_gradient(state: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """∂I/∂q, ∂I/∂v"""
        if isinstance(state, State):
            q = state.q
            v = state.p
        elif isinstance(state, np.ndarray):
            q = state[:n]
            v = state[n:]
        else:
            raise TypeError("State must be State or ndarray")

        # ∂I/∂v = 2 T v (since I = v^T T v and T symmetric)
        T = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                val = interpolators[(i, j)](q[None, :])[0]
                T[i, j] = val
                T[j, i] = val

        dI_dv = 2 * T @ v

        # ∂I/∂q via finite differences
        eps = 1e-6
        dI_dq = np.zeros(n)
        I_0 = integral_expression(np.concatenate([q, v]))

        for k in range(n):
            q_plus = q.copy()
            q_plus[k] += eps
            I_plus = integral_expression(np.concatenate([q_plus, v]))
            dI_dq[k] = (I_plus - I_0) / eps

        return dI_dq, dI_dv

    if name is None:
        name = f"KillingTensorIntegral_{id(killing_tensor) % 10000}"

    return ConservedIntegral(
        name=name,
        expression=integral_expression,
        gradient=integral_gradient,
        source='killing_tensor',
        manifold_type='generic',
        residual=np.nan,
        killing_field=killing_tensor,
        metadata={
            'dimension': n,
            'tensor_rank': 2,
            'mesh_points': N
        }
    )


# =============================================================================
# Batch Conversion
# =============================================================================

def convert_killing_fields_batch(
    killing_fields: List[np.ndarray],
    mesh: Mesh,
    metric_func: Callable,
    *,
    field_type: str = 'vector',
    names: Optional[List[str]] = None,
    verbose: bool = False
) -> List[ConservedIntegral]:
    """
    Convert multiple Killing fields to integrals.

    Args:
        killing_fields: List of Killing fields (vectors or tensors)
        mesh: Mesh structure
        metric_func: Metric function
        field_type: 'vector' or 'tensor'
        names: Optional names for each integral
        verbose: Print progress

    Returns:
        List of ConservedIntegral objects
    """
    integrals = []

    for idx, K in enumerate(killing_fields):
        if names is not None and idx < len(names):
            name = names[idx]
        else:
            name = f"Integral_{idx}"

        if field_type == 'vector':
            integral = killing_vector_to_integral(
                K, mesh, metric_func, name=name, verbose=verbose
            )
        elif field_type == 'tensor':
            integral = killing_tensor_to_integral(
                K, mesh, metric_func, name=name, verbose=verbose
            )
        else:
            raise ValueError(f"Unknown field type: {field_type}")

        integrals.append(integral)

        if verbose:
            print(f"  Converted {name}")

    return integrals
