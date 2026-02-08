# WP 2.2 Part B: Extended Symplectic Form - Detailed Design

**Task**: WP 2.2 - S¹ "Untwisting" Lift Construction
**Part**: B - Extended Symplectic Form
**Status**: Design Phase
**Estimated Duration**: 2 days
**Dependencies**: WP 2.2 Part A Complete (Bundle Construction)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Data Structures](#data-structures)
4. [Core Algorithms](#core-algorithms)
5. [Implementation Details](#implementation-details)
6. [Validation Strategy](#validation-strategy)
7. [Performance Targets](#performance-targets)
8. [Integration Points](#integration-points)
9. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

Part B implements the **extended symplectic form** $\widetilde{\omega}$ on the S¹ bundle. This is the heart of the "untwisting" construction: by adding the fiber coordinate $\theta$ to the symplectic structure, we absorb the magnetic connection discovered in Task 2.1.2, creating a **closed** symplectic form in the lifted space.

**Key Mathematical Result**:
- Shape space has **non-closed** reduced symplectic form: $d\omega_{\text{red}} \neq 0$
- Bundle space has **closed** extended form: $d\widetilde{\omega} = 0$
- This makes the lifted dynamics simpler and potentially integrable

**Physical Interpretation**: The fiber coordinate $\theta$ "absorbs" the curvature (magnetic field) of the connection, flattening the geometry.

### Mathematical Formula

The extended symplectic form is:

$$\widetilde{\omega} = \omega_{\text{shape}} + d\theta \wedge d(L \cdot \mathcal{A})$$

where:
- $\omega_{\text{shape}}$ = canonical symplectic form on shape space phase space
- $\theta$ = fiber coordinate
- $L$ = conserved angular momentum
- $\mathcal{A}$ = connection one-form from Task 2.1.2

**Why this formula?**
- The connection $\mathcal{A}$ appears in reduced symplectic form as: $\omega_{\text{red}} = \omega_{\text{shape}} - d(L \cdot \mathcal{A})$
- The $-d(L \cdot \mathcal{A})$ term makes $\omega_{\text{red}}$ non-closed
- By replacing $d(L \cdot \mathcal{A})$ with $d\theta \wedge d(L \cdot \mathcal{A})$, we "twist" in the fiber direction
- The new form is **exactly closed**: $d\widetilde{\omega} = 0$

### Objectives

1. **Implement Extended Form**: Compute $\widetilde{\omega}(v_1, v_2)$ for tangent vectors
2. **Verify Closedness**: Numerically check $d\widetilde{\omega} = 0$
3. **Verify Non-Degeneracy**: Check $\widetilde{\omega}$ is invertible (defines proper symplectic structure)
4. **Compute Inverse**: Implement $\widetilde{\omega}^{-1}$ (needed for Hamiltonian vector fields)
5. **Poisson Brackets**: Implement $\{f, g\} = \widetilde{\omega}(X_f, X_g)$
6. **Validation**: Stokes' theorem tests, anti-symmetry, etc.

### Deliverables

- `ExtendedSymplecticForm` class
- Closedness verification algorithm
- Non-degeneracy tests
- Poisson bracket evaluator
- Matrix representation $\widetilde{\omega}_{ij}$
- Inverse form $\widetilde{\omega}^{ij}$
- Comprehensive validation suite

---

## Mathematical Background

### Symplectic Forms: Review

A **symplectic form** on a manifold $M$ is a 2-form $\omega$ that is:
1. **Closed**: $d\omega = 0$
2. **Non-degenerate**: For all $v \neq 0$, exists $w$ such that $\omega(v, w) \neq 0$

In coordinates $(q^i, p_i)$, the canonical symplectic form is:
$$\omega_{\text{can}} = \sum_i dp_i \wedge dq^i$$

**Matrix representation** (in phase space coordinates):
$$\Omega = \begin{pmatrix} 0 & I \\ -I & 0 \end{pmatrix}$$

where $I$ is the $n \times n$ identity matrix.

### The Reduced Symplectic Form Problem

After reduction by rotation symmetry, the shape space has a **magnetic symplectic form**:

$$\omega_{\text{red}} = \omega_{\text{shape}} - d(L \cdot \mathcal{A})$$

**Problem**: This form is **NOT closed** when $\mathcal{F} = d\mathcal{A} \neq 0$:

$$d\omega_{\text{red}} = d\omega_{\text{shape}} - d^2(L \cdot \mathcal{A}) = 0 - 0 = 0 \quad \text{(wrong!)}$$

Actually:
$$d\omega_{\text{red}} = -L \cdot d\mathcal{A} = -L \cdot \mathcal{F} \neq 0$$

The curvature $\mathcal{F}$ obstructs closedness, violating a fundamental requirement for Hamiltonian mechanics.

### The S¹ Lift Solution

By lifting to the bundle $P = S \times S^1$, we introduce a new coordinate $\theta$ and define:

$$\widetilde{\omega} = \omega_{\text{shape}} + d\theta \wedge d(L \cdot \mathcal{A})$$

**Key computation**:
\begin{align}
d\widetilde{\omega} &= d\omega_{\text{shape}} + d\left(d\theta \wedge d(L \cdot \mathcal{A})\right) \\
&= 0 + d(d\theta) \wedge d(L \cdot \mathcal{A}) - d\theta \wedge d^2(L \cdot \mathcal{A}) \\
&= 0 \wedge d(L \cdot \mathcal{A}) - d\theta \wedge 0 \\
&= 0
\end{align}

So $\widetilde{\omega}$ is **closed**! The fiber has "unwound" the curvature.

### Explicit Coordinate Expression

In bundle phase space coordinates $(s, \theta, p_s, p_\theta)$:

$$\widetilde{\omega} = \sum_{i=1}^3 dp_i \wedge ds^i + dp_\theta \wedge d\theta + L \sum_{i=1}^3 \frac{\partial \mathcal{A}_i}{\partial s^j} d\theta \wedge ds^j$$

**Matrix form** (8×8 for planar case):

$$\widetilde{\Omega} = \begin{pmatrix}
0_{3×3} & 0_{3×1} & I_{3×3} & 0_{3×1} \\
0_{1×3} & 0 & L \cdot \nabla \mathcal{A} & 1 \\
-I_{3×3} & -L \cdot (\nabla \mathcal{A})^T & 0_{3×3} & 0_{3×1} \\
0_{1×3} & -1 & 0_{1×3} & 0
\end{pmatrix}$$

where $\nabla \mathcal{A}$ is the $3 \times 1$ vector of connection components.

### Non-Degeneracy

To verify non-degeneracy, we check:
$$\det(\widetilde{\Omega}) \neq 0$$

For a $2n \times 2n$ symplectic matrix, the determinant is always $\pm 1$ if non-degenerate. We'll verify this numerically.

### Poisson Brackets

Given functions $f, g$ on the bundle, the Poisson bracket is:

$$\{f, g\} = \widetilde{\omega}(X_f, X_g) = \widetilde{\omega}^{ij} \frac{\partial f}{\partial z^i} \frac{\partial g}{\partial z^j}$$

where $\widetilde{\omega}^{ij}$ is the inverse matrix (contravariant form).

In components:
$$\{f, g\} = \sum_{i,j} \widetilde{\Omega}^{ij} \frac{\partial f}{\partial z^i} \frac{\partial g}{\partial z^j}$$

---

## Data Structures

### ExtendedSymplecticForm

```python
# File: src/python/lifts/extended_symplectic.py

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np
from .s1_bundle import BundleState
from ..connection.connection_form import ConnectionForm

@dataclass(frozen=True)
class ExtendedSymplecticForm:
    """
    Extended symplectic form on S¹ bundle.

    ω̃ = ω_shape + dθ ∧ d(L·A)

    This form is closed (dω̃ = 0) even though the reduced form is not.
    It defines the symplectic structure for Hamiltonian dynamics on the bundle.

    Attributes:
        connection: Connection one-form A from Task 2.1.2
        angular_momentum: Conserved L (appears in ω̃ definition)
        dimension: Phase space dimension (8 for planar case)
        _matrix_cache: Cached matrix representation
        _inverse_cache: Cached inverse matrix

    Examples:
        >>> connection = compute_connection_form(shape_state)
        >>> form = ExtendedSymplecticForm(connection, L=1.0)
        >>> v1 = np.array([0.1, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0])
        >>> v2 = np.array([0.0, 0.1, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0])
        >>> omega_value = form.evaluate(bundle_state, v1, v2)
    """
    connection: ConnectionForm
    angular_momentum: float
    dimension: int = 8  # 2 × (3 base + 1 fiber) for planar case
    _matrix_cache: Optional[np.ndarray] = None
    _inverse_cache: Optional[np.ndarray] = None

    def evaluate(
        self,
        bundle_state: BundleState,
        tangent_vector_1: np.ndarray,
        tangent_vector_2: np.ndarray
    ) -> float:
        """
        Evaluate ω̃(v₁, v₂) at a bundle point.

        Args:
            bundle_state: Point where to evaluate
            tangent_vector_1: First tangent vector in T(Bundle)
                             Format: [δs, δθ, δp_s, δp_θ]
            tangent_vector_2: Second tangent vector

        Returns:
            ω̃(v₁, v₂) (scalar)

        Examples:
            >>> # Evaluate on basis vectors
            >>> e1 = np.zeros(8); e1[0] = 1  # ∂/∂r12
            >>> e4 = np.zeros(8); e4[4] = 1  # ∂/∂p12
            >>> omega = form.evaluate(state, e1, e4)
            >>> # Should be 1 (canonical pairing)
        """
        if len(tangent_vector_1) != self.dimension:
            raise ValueError(
                f"tangent_vector_1 must have dimension {self.dimension}, "
                f"got {len(tangent_vector_1)}"
            )
        if len(tangent_vector_2) != self.dimension:
            raise ValueError(
                f"tangent_vector_2 must have dimension {self.dimension}, "
                f"got {len(tangent_vector_2)}"
            )

        # Get matrix representation
        omega_matrix = self.to_matrix(bundle_state)

        # Evaluate bilinear form: v₁^T Ω v₂
        result = tangent_vector_1 @ omega_matrix @ tangent_vector_2

        return result

    def to_matrix(
        self,
        bundle_state: BundleState,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Matrix representation Ω_ij of symplectic form.

        In phase space coordinates (s, θ, p_s, p_θ):
        Ω = [[0, 0, I, connection_term],
             [0, 0, -connection_term^T, 1],
             [-I, connection_term, 0, 0],
             [-connection_term^T, -1, 0, 0]]

        Args:
            bundle_state: Point where to evaluate
            use_cache: Whether to use cached matrix (if available)

        Returns:
            Matrix Ω of shape (dimension, dimension)

        Examples:
            >>> omega_matrix = form.to_matrix(state)
            >>> omega_matrix.shape
            (8, 8)
            >>> # Check anti-symmetry
            >>> np.allclose(omega_matrix, -omega_matrix.T)
            True
        """
        if use_cache and self._matrix_cache is not None:
            return self._matrix_cache

        n_base = 3  # Shape space dimension
        n_fiber = 1  # Fiber dimension
        n_total = n_base + n_fiber  # Total configuration dimension = 4

        # Initialize matrix
        omega = np.zeros((2 * n_total, 2 * n_total))

        # Block structure:
        # omega = [[A, B],
        #          [C, D]]
        # where A, D are (n_total × n_total), B, C are (n_total × n_total)

        # Canonical symplectic form contribution: dp ∧ dq
        # This gives the standard [[0, I], [-I, 0]] structure

        # Upper-right block: I for canonical coordinates
        for i in range(n_base):
            omega[i, n_total + i] = 1.0  # ds^i ∧ dp_i term

        # Fiber coordinate canonical term: dθ ∧ dp_θ
        omega[n_base, 2*n_total - 1] = 1.0

        # Lower-left block: -I (anti-symmetry)
        for i in range(n_base):
            omega[n_total + i, i] = -1.0

        omega[2*n_total - 1, n_base] = -1.0

        # Connection contribution: L dθ ∧ d(A_i ds^i)
        # This adds terms: L (∂A_i/∂s^j) dθ ∧ ds^j

        # Compute connection gradient
        connection_components = self.connection.evaluate(bundle_state.shape_state)
        connection_gradient = self.connection.compute_gradient(bundle_state.shape_state)

        # connection_gradient[i, j] = ∂A_i/∂s^j
        # We need: dθ ∧ d(L·A) = L (∂A_i/∂s^j) dθ ∧ ds^j

        # In phase space (s, θ, p_s, p_θ):
        # dθ is coordinate n_base (= 3)
        # ds^j are coordinates 0, 1, 2

        for j in range(n_base):  # Loop over base coordinates
            # Sum over connection components
            connection_term = self.angular_momentum * np.sum(
                connection_gradient[:, j]
            )

            # Add dθ ∧ ds^j terms
            # Position: (theta_index, s_j_index)
            theta_index = n_base
            s_j_index = j

            omega[theta_index, s_j_index] += connection_term
            omega[s_j_index, theta_index] -= connection_term  # Anti-symmetry

        # Cache if requested
        if use_cache:
            object.__setattr__(self, '_matrix_cache', omega)

        return omega

    def inverse(
        self,
        bundle_state: BundleState,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Inverse symplectic form Ω^(-1).

        Used to convert covectors (gradients) to vectors (Hamiltonian fields).

        Args:
            bundle_state: Point where to evaluate
            use_cache: Whether to use cached inverse

        Returns:
            Inverse matrix Ω^(-1)

        Examples:
            >>> omega_inv = form.inverse(state)
            >>> omega = form.to_matrix(state)
            >>> # Check: Ω^(-1) Ω = I
            >>> np.allclose(omega_inv @ omega, np.eye(8))
            True
        """
        if use_cache and self._inverse_cache is not None:
            return self._inverse_cache

        omega_matrix = self.to_matrix(bundle_state, use_cache=use_cache)

        try:
            omega_inv = np.linalg.inv(omega_matrix)
        except np.linalg.LinAlgError:
            raise RuntimeError(
                "Symplectic form is singular (degenerate). "
                "This should not happen for a valid symplectic structure."
            )

        # Cache if requested
        if use_cache:
            object.__setattr__(self, '_inverse_cache', omega_inv)

        return omega_inv

    def is_closed(
        self,
        bundle_state: BundleState,
        epsilon: float = 1e-6,
        method: str = 'stokes'
    ) -> dict:
        """
        Verify dω̃ = 0 (closedness condition).

        Two methods:
            1. 'stokes': Use Stokes' theorem on small region
            2. 'cartan': Compute exterior derivative directly

        Args:
            bundle_state: Point where to test
            epsilon: Size of test region
            method: Verification method ('stokes' or 'cartan')

        Returns:
            Dictionary with verification results

        Examples:
            >>> results = form.is_closed(state, epsilon=1e-6)
            >>> results['closed']
            True
            >>> results['max_error']
            1.234e-10
        """
        if method == 'stokes':
            return self._verify_closed_stokes(bundle_state, epsilon)
        elif method == 'cartan':
            return self._verify_closed_cartan(bundle_state, epsilon)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _verify_closed_stokes(
        self,
        bundle_state: BundleState,
        epsilon: float
    ) -> dict:
        """
        Verify closedness using Stokes' theorem.

        Stokes: ∫_{∂V} ω̃ = ∫_V dω̃

        If dω̃ = 0, then boundary integral should vanish.

        Args:
            bundle_state: Center point for test region
            epsilon: Size of test region

        Returns:
            Validation results
        """
        # Create small 3-cube in phase space
        # Integrate ω̃ over 2D boundary faces

        boundary_integral = self._compute_boundary_integral(
            bundle_state, epsilon
        )

        # If closed, this should be ≈ 0
        max_error = abs(boundary_integral)
        closed = max_error < 1e-10

        return {
            'closed': closed,
            'method': 'stokes',
            'boundary_integral': boundary_integral,
            'max_error': max_error,
            'tolerance': 1e-10
        }

    def _verify_closed_cartan(
        self,
        bundle_state: BundleState,
        epsilon: float
    ) -> dict:
        """
        Verify closedness by computing dω̃ directly.

        For ω̃ = ω_shape + dθ ∧ d(L·A):
            dω̃ = d(ω_shape) + d(dθ ∧ d(L·A))
                = 0 + d(dθ) ∧ d(L·A) - dθ ∧ d²(L·A)
                = 0 ∧ ... - dθ ∧ 0
                = 0

        So dω̃ = 0 exactly (up to numerical error).

        Args:
            bundle_state: Point where to evaluate
            epsilon: Finite difference step size

        Returns:
            Validation results
        """
        # Compute components of dω̃ (should all be zero)
        # dω̃ is a 3-form in 8D space

        # For our specific form, we know analytically dω̃ = 0
        # Numerical verification: compute Ω_ij,k - Ω_ik,j + Ω_jk,i = 0

        max_error = self._compute_exterior_derivative_error(
            bundle_state, epsilon
        )

        closed = max_error < 1e-8

        return {
            'closed': closed,
            'method': 'cartan',
            'max_error': max_error,
            'tolerance': 1e-8
        }

    def _compute_boundary_integral(
        self,
        center: BundleState,
        epsilon: float
    ) -> float:
        """
        Compute ∫_{∂V} ω̃ for small cube V around center.

        Args:
            center: Center of cube
            epsilon: Half-side length of cube

        Returns:
            Boundary integral value
        """
        # This is a simplified implementation
        # Full implementation would integrate over all 2D faces

        total_integral = 0.0

        # Sample points on boundary
        n_samples = 10
        for face in range(6):  # 6 faces of 3D cube in 4D config space
            face_integral = self._integrate_over_face(
                center, epsilon, face, n_samples
            )
            total_integral += face_integral

        return total_integral

    def _integrate_over_face(
        self,
        center: BundleState,
        epsilon: float,
        face_index: int,
        n_samples: int
    ) -> float:
        """
        Integrate ω̃ over one face of boundary cube.

        Args:
            center: Center of cube
            epsilon: Half-side length
            face_index: Which face (0-5)
            n_samples: Number of sample points per dimension

        Returns:
            Face integral value
        """
        # Placeholder implementation
        # Real implementation would use proper numerical integration
        return 0.0  # Should be small if dω̃ = 0

    def _compute_exterior_derivative_error(
        self,
        bundle_state: BundleState,
        epsilon: float
    ) -> float:
        """
        Compute ||dω̃|| (should be zero).

        Uses finite differences to estimate derivatives of Ω_ij.

        Args:
            bundle_state: Point where to compute
            epsilon: Finite difference step

        Returns:
            Maximum component of dω̃
        """
        # Compute Ω_ij at center
        omega_center = self.to_matrix(bundle_state)

        max_derivative = 0.0

        # For each coordinate direction
        for k in range(self.dimension):
            # Perturb in direction k
            perturbed_vector = bundle_state.to_vector().copy()
            perturbed_vector[k] += epsilon

            perturbed_state = BundleState.from_vector(
                perturbed_vector,
                L=bundle_state.shape_state.L
            )

            # Compute Ω at perturbed point
            omega_perturbed = self.to_matrix(perturbed_state)

            # Derivative: ∂Ω_ij/∂z^k
            omega_derivative = (omega_perturbed - omega_center) / epsilon

            # Check dω̃ components: Ω_ij,k + Ω_jk,i + Ω_ki,j = 0
            # (Simplified check: just look at maximum derivative)
            max_derivative = max(max_derivative, np.max(np.abs(omega_derivative)))

        return max_derivative

    def is_nondegenerate(
        self,
        bundle_state: BundleState
    ) -> dict:
        """
        Verify non-degeneracy: det(Ω) ≠ 0.

        For symplectic form, should have det(Ω) = ±1.

        Args:
            bundle_state: Point where to test

        Returns:
            Validation results

        Examples:
            >>> results = form.is_nondegenerate(state)
            >>> results['nondegenerate']
            True
            >>> results['determinant']
            1.0
        """
        omega = self.to_matrix(bundle_state)

        det = np.linalg.det(omega)
        rank = np.linalg.matrix_rank(omega)

        nondegenerate = (abs(det) > 1e-10) and (rank == self.dimension)

        return {
            'nondegenerate': nondegenerate,
            'determinant': det,
            'rank': rank,
            'dimension': self.dimension,
            'det_expected': 1.0,  # For symplectic form
            'det_error': abs(abs(det) - 1.0)
        }

    def is_antisymmetric(
        self,
        bundle_state: BundleState,
        tolerance: float = 1e-12
    ) -> dict:
        """
        Verify anti-symmetry: Ω_ij = -Ω_ji.

        All symplectic forms must be anti-symmetric.

        Args:
            bundle_state: Point where to test
            tolerance: Numerical tolerance

        Returns:
            Validation results

        Examples:
            >>> results = form.is_antisymmetric(state)
            >>> results['antisymmetric']
            True
        """
        omega = self.to_matrix(bundle_state)

        # Check Ω = -Ω^T
        symmetry_error = omega + omega.T

        max_error = np.max(np.abs(symmetry_error))
        antisymmetric = max_error < tolerance

        return {
            'antisymmetric': antisymmetric,
            'max_error': max_error,
            'tolerance': tolerance
        }

    def validate(
        self,
        bundle_state: BundleState
    ) -> dict:
        """
        Comprehensive validation of symplectic form.

        Checks:
            1. Anti-symmetry
            2. Non-degeneracy
            3. Closedness

        Args:
            bundle_state: Point where to validate

        Returns:
            Complete validation results

        Examples:
            >>> results = form.validate(state)
            >>> results['valid']
            True
        """
        results = {
            'antisymmetric': self.is_antisymmetric(bundle_state),
            'nondegenerate': self.is_nondegenerate(bundle_state),
            'closed': self.is_closed(bundle_state, method='cartan')
        }

        results['valid'] = all([
            results['antisymmetric']['antisymmetric'],
            results['nondegenerate']['nondegenerate'],
            results['closed']['closed']
        ])

        return results
```

### PoissonBracket

```python
# File: src/python/lifts/poisson_bracket.py

from typing import Callable
import numpy as np
from .extended_symplectic import ExtendedSymplecticForm
from .s1_bundle import BundleState

class PoissonBracket:
    """
    Poisson bracket {f, g} with respect to extended symplectic form.

    {f, g} = ω̃(X_f, X_g) = ω̃^{ij} ∂_i f ∂_j g

    Attributes:
        symplectic_form: Extended symplectic form ω̃
        gradient_epsilon: Finite difference step for gradients

    Examples:
        >>> bracket = PoissonBracket(extended_form)
        >>> f = lambda state: state.shape_state.r12**2
        >>> g = lambda state: state.shape_momenta[0]
        >>> result = bracket.evaluate(f, g, state)
    """

    def __init__(
        self,
        symplectic_form: ExtendedSymplecticForm,
        gradient_epsilon: float = 1e-8
    ):
        """
        Initialize Poisson bracket evaluator.

        Args:
            symplectic_form: Extended form ω̃
            gradient_epsilon: Step size for numerical gradients
        """
        self.symplectic_form = symplectic_form
        self.gradient_epsilon = gradient_epsilon

    def evaluate(
        self,
        f: Callable[[BundleState], float],
        g: Callable[[BundleState], float],
        state: BundleState
    ) -> float:
        """
        Compute {f, g} at state.

        {f, g} = ω̃^{ij} (∂f/∂z^i) (∂g/∂z^j)

        Args:
            f: First function on bundle
            g: Second function on bundle
            state: Point where to evaluate

        Returns:
            {f, g} (scalar)

        Examples:
            >>> # Canonical bracket: {q, p} = 1
            >>> f = lambda s: s.shape_state.r12
            >>> g = lambda s: s.shape_momenta[0]
            >>> bracket.evaluate(f, g, state)
            1.0
        """
        # Compute gradients
        df = self._compute_gradient(f, state)
        dg = self._compute_gradient(g, state)

        # Get inverse symplectic form
        omega_inv = self.symplectic_form.inverse(state)

        # Poisson bracket: {f, g} = df^T Ω^{-1} dg
        bracket = df @ omega_inv @ dg

        return bracket

    def _compute_gradient(
        self,
        f: Callable[[BundleState], float],
        state: BundleState
    ) -> np.ndarray:
        """
        Compute gradient ∂f/∂z via finite differences.

        Args:
            f: Function to differentiate
            state: Point where to compute gradient

        Returns:
            Gradient vector (dimension,)
        """
        f_center = f(state)
        gradient = np.zeros(self.symplectic_form.dimension)

        state_vector = state.to_vector()

        for i in range(self.symplectic_form.dimension):
            # Perturb coordinate i
            perturbed = state_vector.copy()
            perturbed[i] += self.gradient_epsilon

            state_perturbed = BundleState.from_vector(
                perturbed,
                L=state.shape_state.L
            )

            f_perturbed = f(state_perturbed)

            # Finite difference
            gradient[i] = (f_perturbed - f_center) / self.gradient_epsilon

        return gradient

    def verify_jacobi_identity(
        self,
        f: Callable,
        g: Callable,
        h: Callable,
        state: BundleState,
        tolerance: float = 1e-8
    ) -> dict:
        """
        Verify Jacobi identity: {{f,g},h} + {{g,h},f} + {{h,f},g} = 0.

        This is a fundamental property of Poisson brackets.

        Args:
            f, g, h: Three functions
            state: Point where to test
            tolerance: Numerical tolerance

        Returns:
            Validation results

        Examples:
            >>> results = bracket.verify_jacobi_identity(f, g, h, state)
            >>> results['jacobi_satisfied']
            True
        """
        # Compute three terms
        term1 = self.evaluate(
            lambda s: self.evaluate(f, g, s),
            h,
            state
        )

        term2 = self.evaluate(
            lambda s: self.evaluate(g, h, s),
            f,
            state
        )

        term3 = self.evaluate(
            lambda s: self.evaluate(h, f, s),
            g,
            state
        )

        jacobi_sum = term1 + term2 + term3
        satisfied = abs(jacobi_sum) < tolerance

        return {
            'jacobi_satisfied': satisfied,
            'jacobi_sum': jacobi_sum,
            'tolerance': tolerance,
            'terms': [term1, term2, term3]
        }

    def verify_antisymmetry(
        self,
        f: Callable,
        g: Callable,
        state: BundleState,
        tolerance: float = 1e-12
    ) -> dict:
        """
        Verify anti-symmetry: {f, g} = -{g, f}.

        Args:
            f, g: Two functions
            state: Point where to test
            tolerance: Numerical tolerance

        Returns:
            Validation results

        Examples:
            >>> results = bracket.verify_antisymmetry(f, g, state)
            >>> results['antisymmetric']
            True
        """
        fg = self.evaluate(f, g, state)
        gf = self.evaluate(g, f, state)

        error = abs(fg + gf)
        antisymmetric = error < tolerance

        return {
            'antisymmetric': antisymmetric,
            '{f,g}': fg,
            '{g,f}': gf,
            'error': error,
            'tolerance': tolerance
        }

    def verify_leibniz_rule(
        self,
        f: Callable,
        g: Callable,
        h: Callable,
        state: BundleState,
        tolerance: float = 1e-8
    ) -> dict:
        """
        Verify Leibniz rule: {f, g·h} = {f,g}·h + g·{f,h}.

        Args:
            f, g, h: Three functions
            state: Point where to test
            tolerance: Numerical tolerance

        Returns:
            Validation results
        """
        # Left side: {f, g·h}
        gh = lambda s: g(s) * h(s)
        left = self.evaluate(f, gh, state)

        # Right side: {f,g}·h + g·{f,h}
        fg = self.evaluate(f, g, state)
        fh = self.evaluate(f, h, state)
        right = fg * h(state) + g(state) * fh

        error = abs(left - right)
        satisfied = error < tolerance

        return {
            'leibniz_satisfied': satisfied,
            'left_side': left,
            'right_side': right,
            'error': error,
            'tolerance': tolerance
        }
```

---

## Core Algorithms

### B1: Matrix Construction

**Algorithm: Construct Symplectic Matrix**

```python
def construct_extended_symplectic_matrix(
    connection: ConnectionForm,
    bundle_state: BundleState,
    L: float
) -> np.ndarray:
    """
    Construct matrix representation of extended symplectic form.

    Structure (8×8 for planar case):
        Ω = [[0_{3×3}, 0_{3×1}, I_{3×3}, conn_term],
             [0_{1×3}, 0, -conn_term^T, 1],
             [-I_{3×3}, conn_term, 0_{3×3}, 0_{3×1}],
             [-conn_term^T, -1, 0_{1×3}, 0]]

    where conn_term = L ∇A (connection gradient contribution).

    Args:
        connection: Connection one-form A
        bundle_state: Point where to evaluate
        L: Angular momentum

    Returns:
        Symplectic matrix Ω (8×8)

    Performance:
        - Time: O(n²) for n=dimension
        - Space: O(n²)
    """
    n_base = 3  # Shape space dimension
    n_total = 4  # Total config dimension (3 + 1 fiber)
    dim = 2 * n_total  # Phase space dimension = 8

    omega = np.zeros((dim, dim))

    # Canonical symplectic structure: dp ∧ dq
    # Upper-right block: I
    for i in range(n_base):
        omega[i, n_total + i] = 1.0

    # Fiber canonical term: dθ ∧ dp_θ
    omega[n_base, dim - 1] = 1.0

    # Lower-left block: -I (anti-symmetry)
    for i in range(n_base):
        omega[n_total + i, i] = -1.0

    omega[dim - 1, n_base] = -1.0

    # Connection contribution: L dθ ∧ d(A_i ds^i)
    A = connection.evaluate(bundle_state.shape_state)
    dA = connection.compute_gradient(bundle_state.shape_state)

    for j in range(n_base):
        # Connection term for θ-s_j pairing
        conn_contribution = L * np.sum(dA[:, j])

        theta_idx = n_base
        omega[theta_idx, j] += conn_contribution
        omega[j, theta_idx] -= conn_contribution  # Anti-symmetry

    return omega
```

**Algorithm: Verify Closedness via Cartan Formula**

```python
def verify_closedness_cartan(
    form: ExtendedSymplecticForm,
    bundle_state: BundleState,
    epsilon: float = 1e-7
) -> dict:
    """
    Verify dω̃ = 0 using Cartan's formula.

    For a 2-form ω, closedness means:
        (dω)(X, Y, Z) = X(ω(Y,Z)) - Y(ω(X,Z)) + Z(ω(X,Y))
                       - ω([X,Y], Z) + ω([X,Z], Y) - ω([Y,Z], X)
                     = 0

    Simplified: For coordinate-based forms, check:
        ∂Ω_ij/∂z^k + ∂Ω_jk/∂z^i + ∂Ω_ki/∂z^j = 0

    Args:
        form: Extended symplectic form
        bundle_state: Point where to test
        epsilon: Finite difference step

    Returns:
        Dictionary with closedness verification results

    Performance:
        - Time: O(n³) for n=dimension (triple loop over indices)
        - Space: O(n²) for matrix storage
    """
    dim = form.dimension
    omega_center = form.to_matrix(bundle_state)

    max_error = 0.0
    worst_indices = None

    # Compute derivatives ∂Ω_ij/∂z^k via finite differences
    omega_derivatives = np.zeros((dim, dim, dim))

    for k in range(dim):
        # Perturb in direction k
        perturbed_vector = bundle_state.to_vector().copy()
        perturbed_vector[k] += epsilon

        perturbed_state = BundleState.from_vector(
            perturbed_vector,
            L=bundle_state.shape_state.L
        )

        omega_perturbed = form.to_matrix(perturbed_state)

        # Derivative: ∂Ω_ij/∂z^k
        omega_derivatives[:, :, k] = (
            omega_perturbed - omega_center
        ) / epsilon

    # Check closedness condition for each triple (i, j, k)
    for i in range(dim):
        for j in range(i+1, dim):  # Only upper triangle (by anti-symmetry)
            for k in range(j+1, dim):
                # dω component: ∂Ω_ij/∂z^k + cyclic permutations
                d_omega_ijk = (
                    omega_derivatives[i, j, k] +
                    omega_derivatives[j, k, i] +
                    omega_derivatives[k, i, j]
                )

                if abs(d_omega_ijk) > max_error:
                    max_error = abs(d_omega_ijk)
                    worst_indices = (i, j, k)

    closed = max_error < 1e-6

    return {
        'closed': closed,
        'max_error': max_error,
        'worst_indices': worst_indices,
        'tolerance': 1e-6,
        'method': 'cartan'
    }
```

### B2: Poisson Bracket Computation

**Algorithm: Efficient Bracket Evaluation**

```python
def compute_poisson_bracket_efficient(
    f: Callable,
    g: Callable,
    bundle_state: BundleState,
    symplectic_form: ExtendedSymplecticForm,
    gradient_cache: Optional[dict] = None
) -> float:
    """
    Compute {f, g} efficiently with gradient caching.

    {f, g} = ω̃^{ij} (∂f/∂z^i) (∂g/∂z^j)

    Args:
        f, g: Functions on bundle
        bundle_state: Point where to evaluate
        symplectic_form: Extended form
        gradient_cache: Optional cache of precomputed gradients

    Returns:
        {f, g} (scalar)

    Performance:
        - Time: O(n²) for matrix-vector products
        - Space: O(n²) for inverse matrix
        - With caching: O(n²) amortized

    Example:
        >>> cache = {}
        >>> bracket1 = compute_poisson_bracket_efficient(
        ...     f, g, state, form, cache
        ... )
        >>> # Second call reuses gradient of f
        >>> bracket2 = compute_poisson_bracket_efficient(
        ...     f, h, state, form, cache
        ... )
    """
    if gradient_cache is None:
        gradient_cache = {}

    # Check cache for gradients
    f_id = id(f)
    g_id = id(g)
    state_id = id(bundle_state)

    cache_key_f = (f_id, state_id)
    cache_key_g = (g_id, state_id)

    if cache_key_f in gradient_cache:
        df = gradient_cache[cache_key_f]
    else:
        df = compute_gradient_finite_diff(f, bundle_state)
        gradient_cache[cache_key_f] = df

    if cache_key_g in gradient_cache:
        dg = gradient_cache[cache_key_g]
    else:
        dg = compute_gradient_finite_diff(g, bundle_state)
        gradient_cache[cache_key_g] = dg

    # Compute bracket: df^T Ω^{-1} dg
    omega_inv = symplectic_form.inverse(bundle_state)
    bracket = df @ omega_inv @ dg

    return bracket


def compute_gradient_finite_diff(
    f: Callable,
    bundle_state: BundleState,
    epsilon: float = 1e-8
) -> np.ndarray:
    """
    Compute gradient ∂f/∂z via finite differences.

    Uses centered differences for better accuracy:
        ∂f/∂z^i ≈ (f(z + εe_i) - f(z - εe_i)) / (2ε)

    Args:
        f: Function to differentiate
        bundle_state: Point where to compute
        epsilon: Step size

    Returns:
        Gradient vector (dimension,)

    Performance:
        - Time: O(n) function evaluations
        - Space: O(n) for gradient vector
    """
    dim = 8  # For planar case
    gradient = np.zeros(dim)

    state_vector = bundle_state.to_vector()

    for i in range(dim):
        # Forward perturbation
        perturbed_fwd = state_vector.copy()
        perturbed_fwd[i] += epsilon
        state_fwd = BundleState.from_vector(
            perturbed_fwd,
            L=bundle_state.shape_state.L
        )
        f_fwd = f(state_fwd)

        # Backward perturbation
        perturbed_bwd = state_vector.copy()
        perturbed_bwd[i] -= epsilon
        state_bwd = BundleState.from_vector(
            perturbed_bwd,
            L=bundle_state.shape_state.L
        )
        f_bwd = f(state_bwd)

        # Centered difference
        gradient[i] = (f_fwd - f_bwd) / (2 * epsilon)

    return gradient
```

### B3: Validation Algorithms

**Algorithm: Comprehensive Symplectic Form Validation**

```python
def validate_extended_symplectic_form_complete(
    form: ExtendedSymplecticForm,
    n_test_states: int = 100
) -> dict:
    """
    Comprehensive validation of extended symplectic form.

    Tests:
        1. Anti-symmetry: Ω = -Ω^T
        2. Non-degeneracy: det(Ω) ≠ 0
        3. Closedness: dω̃ = 0
        4. Invertibility: Ω^{-1} Ω = I
        5. Canonical structure: Standard coordinates have {q^i, p_j} = δ^i_j

    Args:
        form: Extended symplectic form to validate
        n_test_states: Number of random test states

    Returns:
        Dictionary with comprehensive validation results

    Performance:
        - Time: O(n³ × n_test_states) for all tests
        - Space: O(n²) for matrices
    """
    from .s1_bundle import generate_random_bundle_state

    results = {
        'antisymmetry': [],
        'nondegeneracy': [],
        'closedness': [],
        'invertibility': [],
        'canonical_structure': [],
        'overall_valid': True,
        'summary': {}
    }

    print(f"Validating extended symplectic form on {n_test_states} random states...")

    for i in range(n_test_states):
        state = generate_random_bundle_state()

        # Test 1: Anti-symmetry
        antisym_result = form.is_antisymmetric(state)
        results['antisymmetry'].append(antisym_result['antisymmetric'])

        if not antisym_result['antisymmetric']:
            results['overall_valid'] = False

        # Test 2: Non-degeneracy
        nondeg_result = form.is_nondegenerate(state)
        results['nondegeneracy'].append(nondeg_result['nondegenerate'])

        if not nondeg_result['nondegenerate']:
            results['overall_valid'] = False

        # Test 3: Closedness (every 10th state, expensive)
        if i % 10 == 0:
            closed_result = form.is_closed(state, method='cartan')
            results['closedness'].append(closed_result['closed'])

            if not closed_result['closed']:
                results['overall_valid'] = False

        # Test 4: Invertibility
        omega = form.to_matrix(state)
        omega_inv = form.inverse(state)
        product = omega @ omega_inv
        identity_error = np.max(np.abs(product - np.eye(8)))
        invertible = identity_error < 1e-10

        results['invertibility'].append(invertible)

        if not invertible:
            results['overall_valid'] = False

        # Test 5: Canonical structure (spot check)
        if i < 10:  # Only first few states
            canonical_result = verify_canonical_structure(form, state)
            results['canonical_structure'].append(canonical_result['canonical'])

            if not canonical_result['canonical']:
                results['overall_valid'] = False

    # Summary statistics
    results['summary'] = {
        'antisymmetry_pass_rate': sum(results['antisymmetry']) / len(results['antisymmetry']),
        'nondegeneracy_pass_rate': sum(results['nondegeneracy']) / len(results['nondegeneracy']),
        'closedness_pass_rate': sum(results['closedness']) / max(len(results['closedness']), 1),
        'invertibility_pass_rate': sum(results['invertibility']) / len(results['invertibility']),
        'canonical_pass_rate': sum(results['canonical_structure']) / max(len(results['canonical_structure']), 1),
    }

    return results


def verify_canonical_structure(
    form: ExtendedSymplecticForm,
    bundle_state: BundleState,
    tolerance: float = 1e-10
) -> dict:
    """
    Verify canonical Poisson brackets: {q^i, p_j} = δ^i_j.

    Args:
        form: Symplectic form
        bundle_state: Point where to test
        tolerance: Numerical tolerance

    Returns:
        Validation results
    """
    bracket_calc = PoissonBracket(form)

    # Test canonical brackets
    errors = []

    # {r12, p12} = 1
    f1 = lambda s: s.shape_state.r12
    g1 = lambda s: s.shape_momenta[0]
    bracket1 = bracket_calc.evaluate(f1, g1, bundle_state)
    errors.append(abs(bracket1 - 1.0))

    # {r12, p23} = 0 (different coordinates)
    g2 = lambda s: s.shape_momenta[1]
    bracket2 = bracket_calc.evaluate(f1, g2, bundle_state)
    errors.append(abs(bracket2 - 0.0))

    # {θ, p_θ} = 1
    f3 = lambda s: s.theta
    g3 = lambda s: s.p_theta
    bracket3 = bracket_calc.evaluate(f3, g3, bundle_state)
    errors.append(abs(bracket3 - 1.0))

    max_error = max(errors)
    canonical = max_error < tolerance

    return {
        'canonical': canonical,
        'max_error': max_error,
        'errors': errors,
        'tolerance': tolerance
    }
```

---

## Implementation Details

### File Organization

```
src/python/lifts/
├── __init__.py
├── extended_symplectic.py         # ExtendedSymplecticForm class
├── poisson_bracket.py              # PoissonBracket class
└── validation.py                   # Validation utilities (Part A+B)
```

### Dependencies

```python
import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable, Dict
from .s1_bundle import BundleState, S1Bundle
from ..connection.connection_form import ConnectionForm
```

### Numerical Precision

- **Default precision**: `float64` (sufficient for most cases)
- **Gradient epsilon**: `1e-8` (balanced accuracy/stability)
- **Closedness tolerance**: `1e-6` (exterior derivative errors)
- **Invertibility check**: `1e-10` (matrix inversion stability)

### Performance Optimizations

1. **Matrix Caching**: Cache Ω and Ω^{-1} for repeated evaluations
2. **Gradient Caching**: Store gradients for bracket calculations
3. **Vectorization**: Use NumPy operations instead of loops where possible
4. **Lazy Evaluation**: Compute inverse only when needed

---

## Validation Strategy

### Unit Tests

```python
# File: tests/lifts/test_extended_symplectic.py

class TestExtendedSymplecticForm:
    """Test extended symplectic form"""

    def test_antisymmetry(self):
        """Test Ω = -Ω^T"""
        # Implementation in design above
        pass

    def test_nondegeneracy(self):
        """Test det(Ω) ≠ 0"""
        pass

    def test_closedness(self):
        """Test dω̃ = 0"""
        pass

    def test_invertibility(self):
        """Test Ω^{-1} Ω = I"""
        pass


class TestPoissonBracket:
    """Test Poisson brackets"""

    def test_antisymmetry(self):
        """{f,g} = -{g,f}"""
        pass

    def test_jacobi_identity(self):
        """{{f,g},h} + cyclic = 0"""
        pass

    def test_leibniz_rule(self):
        """{f, gh} = {f,g}h + g{f,h}"""
        pass

    def test_canonical_brackets(self):
        """{q^i, p_j} = δ^i_j"""
        pass
```

---

## Performance Targets

| Operation | Complexity | Target Time |
|-----------|-----------|-------------|
| Matrix construction | O(n²) | < 10 μs |
| Matrix inversion | O(n³) | < 50 μs |
| Gradient computation | O(n) | < 100 μs |
| Bracket evaluation | O(n²) | < 200 μs |
| Closedness check | O(n³) | < 10 ms |

---

## Integration Points

### With Part A (Bundle)
```python
from .s1_bundle import BundleState
# Use bundle states for evaluation
```

### With Task 2.1.2 (Connection)
```python
from ..connection.connection_form import ConnectionForm
# Connection appears in extended form
```

### With Part C (Dynamics)
```python
# Symplectic form used for Hamilton's equations
# X_H = ω̃^{-1}(dH)
```

---

## Success Criteria

### Part B Complete When:

- [  ] `ExtendedSymplecticForm` class implemented
- [  ] `PoissonBracket` class functional
- [  ] Anti-symmetry verified on all test cases
- [  ] Non-degeneracy verified (det(Ω) = ±1)
- [  ] Closedness verified (dω̃ = 0)
- [  ] Canonical brackets working: {q, p} = 1
- [  ] All Poisson bracket identities satisfied
- [  ] Performance targets met
- [  ] Unit tests passing (>95% coverage)
- [  ] Documentation complete

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 2 days
**Next**: Part C (Lifted Dynamics & Integration)
