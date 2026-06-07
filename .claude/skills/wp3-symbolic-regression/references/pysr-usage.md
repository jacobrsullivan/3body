# PySR Usage Guide

Evolutionary symbolic regression with PySR for discovering conserved quantities.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Operator Configuration](#operator-configuration)
5. [Performance Tuning](#performance-tuning)
6. [Conservation Search](#conservation-search)
7. [Advanced Features](#advanced-features)

---

## Overview

### What is PySR?

PySR (Python Symbolic Regression) uses genetic programming to evolve mathematical expressions that fit data. Unlike SINDy, it can discover novel functional forms not in a predefined library.

### When to Use PySR

| Scenario | Use SINDy | Use PySR |
|----------|-----------|----------|
| Known functional form | ✓ | |
| Fast search needed | ✓ | |
| Novel form discovery | | ✓ |
| Complex expressions | | ✓ |
| Interpretability critical | ✓ | |

---

## Installation

```bash
# Install via pip
pip install pysr

# PySR requires Julia - it will auto-install on first use
# Or pre-install Julia for faster startup:
# julia -e 'using Pkg; Pkg.add("SymbolicRegression")'
```

---

## Basic Usage

### Simple Example

```python
from pysr import PySRRegressor
import numpy as np

# Generate data
X = np.random.randn(100, 5)  # 5 features
y = X[:, 0]**2 + np.sin(X[:, 1])  # Target

# Create regressor
model = PySRRegressor(
    niterations=40,
    binary_operators=["+", "-", "*", "/"],
    unary_operators=["sin", "cos", "exp", "sqrt"],
    populations=15,
    population_size=33,
)

# Fit
model.fit(X, y)

# Best expression
print(model.sympy())

# Pareto front (complexity vs accuracy trade-off)
print(model.equations_)
```

### For Conservation Search

```python
from pysr import PySRRegressor
import numpy as np

def search_conserved_quantity(times, states):
    """
    Use PySR to find conserved quantities.

    Strategy: Find expressions with minimal variance along trajectory.
    """
    # Compute variance of each candidate expression
    # PySR will optimize to minimize this

    model = PySRRegressor(
        niterations=50,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sin", "cos", "sqrt", "abs"],
        loss="loss(prediction, target) = (prediction - target)^2",
        populations=20,
        maxsize=15,
    )

    # Target = first state value (we want I constant = I(x₀))
    # This encourages finding quantities that don't vary
    target = np.full(len(states), states[0, 0]**2 + states[0, 1]**2)  # Example

    model.fit(states, target)

    return model
```

---

## Operator Configuration

### Binary Operators

```python
# Standard arithmetic
binary_operators = ["+", "-", "*", "/"]

# Add power
binary_operators = ["+", "-", "*", "/", "^"]

# Add max/min
binary_operators = ["+", "-", "*", "/", "max", "min"]
```

### Unary Operators

```python
# Trigonometric
unary_operators = ["sin", "cos", "tan"]

# Exponential/log
unary_operators = ["exp", "log", "log10"]

# Special
unary_operators = ["sqrt", "abs", "sign", "square", "cube"]

# Inverse trig
unary_operators = ["asin", "acos", "atan"]
```

### Custom Operators (Elliptic Functions)

```python
from pysr import PySRRegressor
from scipy.special import ellipj

# Define custom elliptic functions
def jacobi_sn(x, m=0.5):
    return ellipj(x, m)[0]

def jacobi_cn(x, m=0.5):
    return ellipj(x, m)[1]

def jacobi_dn(x, m=0.5):
    return ellipj(x, m)[2]

# Register with PySR
model = PySRRegressor(
    unary_operators=["sin", "cos", "sn", "cn", "dn"],
    extra_sympy_mappings={
        "sn": lambda x: jacobi_sn(x),
        "cn": lambda x: jacobi_cn(x),
        "dn": lambda x: jacobi_dn(x),
    },
    extra_torch_mappings={
        "sn": lambda x: jacobi_sn(x.numpy()),
        "cn": lambda x: jacobi_cn(x.numpy()),
        "dn": lambda x: jacobi_dn(x.numpy()),
    }
)
```

---

## Performance Tuning

### Key Parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `niterations` | 40 | More = better but slower |
| `populations` | 15 | Parallel islands |
| `population_size` | 33 | Individuals per island |
| `maxsize` | 20 | Max expression complexity |
| `timeout_in_seconds` | None | Time limit |

### Fast Search

```python
# Quick exploratory search
model = PySRRegressor(
    niterations=10,
    populations=5,
    population_size=20,
    maxsize=10,
    timeout_in_seconds=60,
)
```

### Thorough Search

```python
# Production quality search
model = PySRRegressor(
    niterations=100,
    populations=30,
    population_size=50,
    maxsize=25,
    timeout_in_seconds=3600,  # 1 hour
    parsimony=0.001,  # Encourage simplicity
)
```

### Constrained Search

```python
# Limit complexity aggressively
model = PySRRegressor(
    niterations=50,
    maxsize=12,  # Simple expressions only
    maxdepth=5,  # Shallow trees
    parsimony=0.01,  # Strong simplicity preference
    complexity_of_operators={
        "sin": 2,
        "cos": 2,
        "exp": 3,
        "/": 2,
    }
)
```

---

## Conservation Search

### Variance-Based Loss

```python
def conservation_loss():
    """
    Custom loss for conservation: minimize variance.
    """
    return """
    function loss(prediction, target)
        n = length(prediction)
        mean_pred = sum(prediction) / n
        variance = sum((prediction .- mean_pred).^2) / n
        return variance
    end
    """

model = PySRRegressor(
    niterations=50,
    loss=conservation_loss(),
    # ... other params
)
```

### Derivative-Based Loss

```python
def derivative_loss():
    """
    Custom loss: minimize |dI/dt| along trajectory.
    """
    return """
    function loss(prediction, target)
        # Approximate derivative via finite differences
        n = length(prediction)
        derivative = prediction[2:end] - prediction[1:end-1]
        return sum(derivative.^2) / (n-1)
    end
    """

model = PySRRegressor(
    niterations=50,
    loss=derivative_loss(),
)
```

### Multi-Objective Search

```python
# PySR automatically generates Pareto front
# balancing accuracy and complexity

model = PySRRegressor(
    niterations=50,
    select_k_features=5,  # Use top 5 features
    model_selection="accuracy",  # or "best", "score"
)

model.fit(X, y)

# Access Pareto front
pareto = model.equations_[['complexity', 'loss', 'equation']]
print(pareto)
```

---

## Advanced Features

### Feature Selection

```python
# Automatically select relevant features
model = PySRRegressor(
    niterations=50,
    select_k_features=10,  # Only use 10 most relevant
    feature_names=["x", "y", "z", "vx", "vy", "vz"],
)
```

### Constraints

```python
# Dimensional analysis constraints
model = PySRRegressor(
    niterations=50,
    dimensional_constraint_penalty=10.0,
    X_units=["m", "m", "m", "m/s", "m/s", "m/s"],
    y_units="J",  # Target has energy units
)
```

### Warm Start

```python
# Continue from previous run
model1 = PySRRegressor(niterations=20)
model1.fit(X, y)

# Warm start from model1
model2 = PySRRegressor(
    niterations=50,
    warm_start=True,
)
model2.fit(X, y, model=model1)
```

### Parallel Execution

```python
# Multi-core parallelism
model = PySRRegressor(
    niterations=50,
    procs=8,  # Use 8 CPU cores
    multithreading=True,
)
```

---

## Integration with WP3 Pipeline

```python
class PySRConservationSearch:
    """
    PySR wrapper for conservation search in WP3 pipeline.
    """

    def __init__(self, max_complexity=15, timeout=300):
        self.max_complexity = max_complexity
        self.timeout = timeout
        self.model = None

    def search(self, times, states, target='variance'):
        """
        Search for conserved quantities using PySR.
        """
        from pysr import PySRRegressor

        # Configure model
        self.model = PySRRegressor(
            niterations=50,
            populations=20,
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["sin", "cos", "sqrt"],
            maxsize=self.max_complexity,
            timeout_in_seconds=self.timeout,
            parsimony=0.001,
        )

        # Set target based on strategy
        if target == 'variance':
            # Minimize variance along trajectory
            y = np.zeros(len(states))  # Want constant output
        elif target == 'derivative':
            # Minimize time derivative
            y = np.zeros(len(states))
        else:
            y = target

        # Fit
        self.model.fit(states, y)

        # Extract candidates from Pareto front
        candidates = []
        for idx, row in self.model.equations_.iterrows():
            candidates.append({
                'expression': str(row['equation']),
                'complexity': row['complexity'],
                'loss': row['loss'],
                'sympy': self.model.sympy(idx),
            })

        return candidates
```

---

## References

- Cranmer, M. (2023). PySR: High-Performance Symbolic Regression in Python and Julia. https://github.com/MilesCranmer/PySR
- Cranmer et al. (2020). "Discovering symbolic models from deep learning with inductive biases", *NeurIPS*
- Schmidt, M. & Lipson, H. (2009). "Distilling free-form natural laws from experimental data", *Science*
