# SINDy Theory

Sparse Identification of Nonlinear Dynamics for discovering conserved quantities.

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Formulation](#mathematical-formulation)
3. [Conservation Constraint](#conservation-constraint)
4. [LASSO Optimization](#lasso-optimization)
5. [Threshold Selection](#threshold-selection)
6. [Implementation](#implementation)

---

## Overview

### The SINDy Approach

**Sparse Identification of Nonlinear Dynamics (SINDy)** discovers governing equations from data by assuming the dynamics are sparse in a library of candidate functions.

**Key insight for invariant discovery**: A conserved quantity I(x) satisfies dI/dt = 0, so we seek sparse representations of functions whose time derivatives vanish.

### Advantages

- **Fast**: Linear algebra, not evolutionary search
- **Interpretable**: Sparse = few terms
- **Tunable**: Sparsity controlled by threshold
- **Physics-informed**: Basis encodes prior knowledge

### Limitations

- Requires good basis choice
- Cannot discover completely new functional forms
- Sensitive to noise

---

## Mathematical Formulation

### The Library Matrix

Given trajectory data {x(t₁), x(t₂), ..., x(tₙ)}, build library Φ:

```
Φ = [φ₁(x(t₁))  φ₂(x(t₁))  ...  φₘ(x(t₁))]
    [φ₁(x(t₂))  φ₂(x(t₂))  ...  φₘ(x(t₂))]
    [    ⋮           ⋮      ⋱       ⋮     ]
    [φ₁(x(tₙ))  φ₂(x(tₙ))  ...  φₘ(x(tₙ))]
```

where φⱼ are basis functions (polynomials, trig functions, spinors, etc.)

### Sparse Representation

A conserved quantity is:
```
I(x) = Σⱼ cⱼ φⱼ(x) = Φc
```

where c is sparse (most entries zero).

### Time Derivative Library

For conservation, we need dI/dt = 0. Compute:

```
Φ̇ = [φ̇₁(x(t₁))  φ̇₂(x(t₁))  ...  φ̇ₘ(x(t₁))]
    [φ̇₁(x(t₂))  φ̇₂(x(t₂))  ...  φ̇ₘ(x(t₂))]
    [    ⋮           ⋮      ⋱       ⋮     ]

where φ̇ⱼ = Σᵢ (∂φⱼ/∂xᵢ) ẋᵢ
```

---

## Conservation Constraint

### The Optimization Problem

Find sparse c such that:
```
dI/dt = Φ̇c ≈ 0
```

**Objective function**:
```
min_c ||Φ̇c||₂² + λ||c||₁

subject to: ||c||₂ = 1 (normalization)
```

### Components

1. **Data term** ||Φ̇c||₂²: Penalize non-conservation
2. **Sparsity term** λ||c||₁: Penalize many terms
3. **Normalization** ||c||₂ = 1: Prevent trivial solution c = 0

### Alternative: Variance-Based Objective

Instead of minimizing time derivative, minimize variance:
```
min_c Var(Φc) + λ||c||₁
```

A conserved quantity has constant value, hence zero variance.

---

## LASSO Optimization

### Standard LASSO

The L1-regularized least squares problem:
```
min_c (1/2n)||y - Xc||₂² + λ||c||₁
```

For conservation with y = 0:
```
min_c (1/2n)||Φ̇c||₂² + λ||c||₁
```

### Coordinate Descent Algorithm

```python
def lasso_coordinate_descent(X, y, lambda_, max_iter=1000, tol=1e-6):
    """
    Solve LASSO: min (1/2)||y - Xc||² + λ||c||₁
    """
    n, m = X.shape
    c = np.zeros(m)
    
    for iteration in range(max_iter):
        c_old = c.copy()
        
        for j in range(m):
            # Compute residual without feature j
            r_j = y - X @ c + X[:, j] * c[j]
            
            # Correlation
            rho_j = X[:, j] @ r_j / n
            
            # Soft thresholding
            c[j] = soft_threshold(rho_j, lambda_) / (np.sum(X[:, j]**2) / n)
        
        # Check convergence
        if np.linalg.norm(c - c_old) < tol:
            break
    
    return c

def soft_threshold(x, lambda_):
    """Soft thresholding operator."""
    return np.sign(x) * np.maximum(np.abs(x) - lambda_, 0)
```

### Using scikit-learn

```python
from sklearn.linear_model import Lasso

def sindy_lasso(Phi_dot, alpha=0.01):
    """
    SINDy via LASSO regression.
    
    Find sparse c such that Φ̇c ≈ 0.
    """
    n, m = Phi_dot.shape
    
    # Target is zero (conservation)
    y = np.zeros(n)
    
    # Fit LASSO
    model = Lasso(alpha=alpha, fit_intercept=False, max_iter=10000)
    
    # Add constraint to avoid trivial solution
    # Approach: Require one coefficient to be 1
    # Then solve for others
    
    best_result = None
    best_error = np.inf
    
    for anchor in range(m):
        # Fix c[anchor] = 1, solve for rest
        Phi_reduced = np.delete(Phi_dot, anchor, axis=1)
        target = -Phi_dot[:, anchor]
        
        model.fit(Phi_reduced, target)
        
        c = np.insert(model.coef_, anchor, 1.0)
        error = np.linalg.norm(Phi_dot @ c)
        
        if error < best_error:
            best_error = error
            best_result = c
    
    return best_result
```

---

## Threshold Selection

### Sequential Thresholding

After initial LASSO, apply hard threshold:

```python
def sequential_threshold(c, threshold):
    """
    Apply hard threshold: set small coefficients to zero.
    """
    c_thresh = c.copy()
    c_thresh[np.abs(c_thresh) < threshold] = 0
    return c_thresh
```

### Iterative Thresholding

```python
def iterative_threshold_sindy(Phi_dot, threshold=0.1, max_iter=10):
    """
    Iteratively threshold and re-fit.
    """
    n, m = Phi_dot.shape
    c = np.ones(m) / m  # Initial guess
    
    for iteration in range(max_iter):
        # Threshold
        mask = np.abs(c) > threshold
        
        if np.sum(mask) == 0:
            break
        
        # Refit on remaining features
        Phi_reduced = Phi_dot[:, mask]
        
        # Least squares with constraint
        c_reduced, _, _, _ = np.linalg.lstsq(Phi_reduced, np.zeros(n), rcond=None)
        
        # Expand back
        c_new = np.zeros(m)
        c_new[mask] = c_reduced
        
        if np.linalg.norm(c_new - c) < 1e-8:
            break
        
        c = c_new
    
    return c
```

### Cross-Validation for λ

```python
from sklearn.linear_model import LassoCV

def sindy_with_cv(Phi_dot, n_alphas=50):
    """
    SINDy with cross-validated regularization.
    """
    n, m = Phi_dot.shape
    
    # Use LassoCV to find optimal alpha
    model = LassoCV(
        n_alphas=n_alphas,
        cv=5,
        fit_intercept=False,
        max_iter=10000
    )
    
    # Fit with dummy target (we'll handle normalization separately)
    y_dummy = np.random.randn(n) * 1e-10  # Small noise to avoid singular
    model.fit(Phi_dot, y_dummy)
    
    print(f"Optimal alpha: {model.alpha_:.4e}")
    
    return model.coef_
```

---

## Implementation

### Complete SINDy Regressor

```python
class SINDyRegressor:
    """
    SINDy for discovering conserved quantities.
    """
    
    def __init__(self, basis_type='polynomial', max_degree=4,
                 threshold=0.1, alpha=0.01):
        self.basis_type = basis_type
        self.max_degree = max_degree
        self.threshold = threshold
        self.alpha = alpha
        self.basis_functions = None
        self.coefficients = None
    
    def _build_basis(self, states):
        """Build basis function library."""
        if self.basis_type == 'polynomial':
            from src.python.symbolic.basis_functions import generate_polynomial_basis
            self.basis_functions = generate_polynomial_basis(
                variables=states.shape[1],
                max_degree=self.max_degree
            )
        elif self.basis_type == 'spinor':
            from src.python.symbolic.spinor_basis import generate_spinor_basis
            self.basis_functions = generate_spinor_basis()
        else:
            raise ValueError(f"Unknown basis type: {self.basis_type}")
    
    def _compute_library(self, states):
        """Evaluate basis functions on states."""
        n = len(states)
        m = len(self.basis_functions)
        
        Phi = np.zeros((n, m))
        for j, func in enumerate(self.basis_functions):
            Phi[:, j] = func(states)
        
        return Phi
    
    def _compute_library_derivative(self, times, states):
        """Compute time derivatives of basis functions."""
        dt = times[1] - times[0]
        Phi = self._compute_library(states)
        
        # Numerical differentiation
        Phi_dot = np.gradient(Phi, dt, axis=0)
        
        return Phi_dot
    
    def fit(self, times, states):
        """
        Fit SINDy model to find conserved quantities.
        """
        # Build basis if needed
        if self.basis_functions is None:
            self._build_basis(states)
        
        # Compute library and derivatives
        Phi = self._compute_library(states)
        Phi_dot = self._compute_library_derivative(times, states)
        
        # LASSO regression
        from sklearn.linear_model import Lasso
        
        model = Lasso(alpha=self.alpha, fit_intercept=False, max_iter=10000)
        
        # Find coefficients that minimize ||Φ̇c||
        # Use iterative approach with anchoring
        best_c = None
        best_error = np.inf
        
        for anchor in range(len(self.basis_functions)):
            c = np.zeros(len(self.basis_functions))
            c[anchor] = 1.0
            
            # Solve for other coefficients
            mask = np.arange(len(c)) != anchor
            if np.sum(mask) > 0:
                model.fit(Phi_dot[:, mask], -Phi_dot[:, anchor])
                c[mask] = model.coef_
            
            # Apply threshold
            c[np.abs(c) < self.threshold] = 0
            
            # Evaluate error
            error = np.std(Phi @ c)  # Variance of candidate
            
            if error < best_error and np.sum(c != 0) <= 10:
                best_error = error
                best_c = c
        
        self.coefficients = best_c
        
        # Build result
        result = SINDyResult()
        result.coefficients = self.coefficients
        result.expression = self._build_expression()
        result.error = best_error
        result.eval_func = lambda x: self._compute_library(x) @ self.coefficients
        
        return result
    
    def _build_expression(self):
        """Build symbolic expression from coefficients."""
        terms = []
        for j, c in enumerate(self.coefficients):
            if c != 0:
                terms.append(f"{c:.4f} * φ{j}")
        return " + ".join(terms) if terms else "0"


class SINDyResult:
    """Container for SINDy results."""
    pass
```

---

## References

- Brunton, S.L. et al. (2016). "Discovering governing equations from data by sparse identification of nonlinear dynamical systems", *PNAS* 113(15):3932-3937
- Champion, K. et al. (2019). "Data-driven discovery of coordinates and governing equations", *PNAS* 116(45):22445-22451
- Tibshirani, R. (1996). "Regression shrinkage and selection via the Lasso", *JRSS-B* 58(1):267-288
