# Task 2.1.1 Part D: Documentation and Deliverables - Detailed Implementation Design

**Task**: WP 2.1.1 - Coordinate Systems and Reduction
**Part**: D - Documentation and Deliverables
**Status**: Design Phase
**Estimated Duration**: 2 days
**Dependencies**: Parts A, B, C Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [D1: API Documentation](#d1-api-documentation)
4. [D2: Technical Report](#d2-technical-report)
5. [D3: Tutorial Jupyter Notebook](#d3-tutorial-jupyter-notebook)
6. [Quality Assurance](#quality-assurance)
7. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Purpose

Part D completes Task 2.1.1 by creating comprehensive documentation and educational materials. This ensures the coordinate transformation and reduction machinery is accessible, well-documented, and scientifically rigorous.

### Scope

We produce three types of deliverables:

1. **API Documentation**: In-code documentation for all public interfaces
2. **Technical Report**: Publication-ready scientific documentation (LaTeX)
3. **Tutorial Notebook**: Interactive educational material (Jupyter)

### Key Design Goals

- **Clarity**: Documentation accessible to both users and developers
- **Completeness**: Cover all features, edge cases, and design decisions
- **Scientific Rigor**: Mathematically precise with proper citations
- **Reproducibility**: Examples that run successfully with minimal setup
- **Maintainability**: Documentation structure that evolves with code

---

## Architecture & Design Principles

### Documentation Structure

```
docs/
├── api/
│   ├── index.md                      # API overview
│   ├── coordinates.md                # Coordinate systems reference
│   ├── reduction.md                  # Reduction reference
│   └── examples.md                   # Code examples
├── technical_reports/
│   ├── Task_2.1.1_Technical_Report.tex
│   ├── Task_2.1.1_Technical_Report.pdf
│   ├── figures/                      # LaTeX figures
│   │   ├── coordinate_diagram.pdf
│   │   ├── reduction_pipeline.pdf
│   │   └── validation_results.pdf
│   └── bibliography.bib
└── user_guide/
    ├── getting_started.md
    ├── coordinate_systems.md
    └── reduction_guide.md

notebooks/
├── Tutorial_Coordinate_Systems.ipynb
├── Tutorial_Symplectic_Reduction.ipynb
└── examples/
    ├── lagrange_equilibrium.ipynb
    ├── figure8_orbit.ipynb
    └── shape_space_visualization.ipynb
```

### Documentation Standards

1. **Docstring Format**: NumPy style for Python code
2. **Mathematical Notation**: Consistent with Abraham & Marsden conventions
3. **Code Examples**: Runnable, self-contained, with expected output
4. **Version Control**: Documentation versioned alongside code
5. **Accessibility**: Clear language, progressive disclosure of complexity

### Design Patterns

1. **Literate Programming**: Interleave explanation with code
2. **Progressive Examples**: Simple → Complex
3. **Reference + Tutorial Split**: API reference separate from tutorials
4. **Living Documentation**: Tests validate documentation examples

---

## D1: API Documentation

### D1.1: Docstring Standards

All public functions, classes, and modules must have complete docstrings following NumPy style.

#### Template for Functions

```python
def cartesian_to_jacobi(state: CartesianState, masses: Masses) -> JacobiState:
    """
    Transform Cartesian coordinates to Jacobi coordinates.

    Jacobi coordinates are hierarchical mass-weighted coordinates that
    separate the center-of-mass motion from the internal dynamics. For
    the 3-body problem, they decompose the system into:
    - Relative motion of bodies 1-2
    - Motion of body 3 relative to the center of mass of 1-2
    - Overall center-of-mass motion (decoupled)

    Parameters
    ----------
    state : CartesianState
        State in Cartesian coordinates. Must be in barycentric frame
        (center of mass at origin) for the transformation to be valid.
    masses : Masses
        Mass parameters for the three bodies. Must have all positive masses.

    Returns
    -------
    JacobiState
        State in Jacobi coordinates with the same energy and angular
        momentum as the input state.

    Raises
    ------
    ValueError
        If masses are not positive or if state has invalid dimensions.
    AssertionError
        If barycentric constraint is violated beyond tolerance.

    Notes
    -----
    The transformation is defined by:

    .. math::
        \\mathbf{r}_{J,1} &= \\mathbf{r}_1 - \\mathbf{r}_2 \\\\
        \\mathbf{r}_{J,2} &= \\mathbf{r}_3 - \\mathbf{r}_{\\text{cm},12}

    where :math:`\\mathbf{r}_{\\text{cm},12} = (m_1 \\mathbf{r}_1 + m_2 \\mathbf{r}_2)/(m_1+m_2)`.

    The transformation is linear and symplectic, preserving the Hamiltonian
    structure. The inverse transformation is implemented in
    :func:`jacobi_to_cartesian`.

    References
    ----------
    .. [1] Wisdom, J. & Hernandez, D. M. "Symplectic maps for the n-body
           problem." Monthly Notices of the Royal Astronomical Society,
           1991.

    Examples
    --------
    Create a simple Cartesian state and transform to Jacobi coordinates:

    >>> import numpy as np
    >>> from coordinates.cartesian import CartesianState
    >>> from coordinates.jacobi import cartesian_to_jacobi
    >>> from coordinates.base import Masses
    >>>
    >>> # Equal mass system in equilateral triangle
    >>> positions = np.array([
    ...     [1.0, 0.0, 0.0],
    ...     [-0.5, 0.866, 0.0],
    ...     [-0.5, -0.866, 0.0]
    ... ])
    >>> velocities = np.zeros((3, 3))
    >>> state = CartesianState(positions, velocities)
    >>> masses = Masses(1.0, 1.0, 1.0)
    >>>
    >>> jacobi_state = cartesian_to_jacobi(state, masses)
    >>> print(jacobi_state.r1)  # Relative position of bodies 1-2
    [1.5, -0.866, 0.0]

    Verify the transformation is invertible:

    >>> from coordinates.jacobi import jacobi_to_cartesian
    >>> state_reconstructed = jacobi_to_cartesian(jacobi_state, masses)
    >>> np.allclose(state.positions, state_reconstructed.positions)
    True

    See Also
    --------
    jacobi_to_cartesian : Inverse transformation
    JacobiState : Data structure for Jacobi coordinates
    Masses : Mass parameter specification
    """
    # Implementation here
    pass
```

#### Template for Classes

```python
class CartesianState:
    """
    Cartesian coordinates in barycentric inertial frame.

    This class represents the state of a 3-body system in standard Cartesian
    coordinates. The positions and velocities are stored in a barycentric
    (center-of-mass) frame where the center of mass is at the origin and
    the total momentum is zero.

    Attributes
    ----------
    positions : ndarray, shape (3, 3)
        Position vectors for the three bodies. Each row is the position
        vector [x, y, z] for one body in meters.
    velocities : ndarray, shape (3, 3)
        Velocity vectors for the three bodies. Each row is the velocity
        vector [vx, vy, vz] for one body in m/s.
    dimension : {2, 3}
        Spatial dimension. 2 for planar motion (z-components zero),
        3 for full spatial motion.
    precision : {'double', 'quad'}
        Numerical precision. 'double' for standard 64-bit floats,
        'quad' for quad-double precision.

    Methods
    -------
    from_flat(z, dimension)
        Construct from flat array representation.
    to_flat()
        Convert to flat array for integration.
    validate()
        Check if state satisfies barycentric constraints.

    Notes
    -----
    The barycentric constraints are:

    .. math::
        \\sum_{i=1}^3 m_i \\mathbf{r}_i = \\mathbf{0} \\\\
        \\sum_{i=1}^3 m_i \\mathbf{v}_i = \\mathbf{0}

    These constraints remove 6 degrees of freedom (3 translation + 3 velocity)
    from the system.

    Examples
    --------
    Create a Cartesian state from explicit arrays:

    >>> import numpy as np
    >>> positions = np.array([[1, 0, 0], [-0.5, 0.866, 0], [-0.5, -0.866, 0]])
    >>> velocities = np.zeros((3, 3))
    >>> state = CartesianState(positions, velocities, dimension=2)

    Create from flat array (useful for integrators):

    >>> z = np.random.randn(18)
    >>> state = CartesianState.from_flat(z, dimension=3)
    >>> z_reconstructed = state.to_flat()
    >>> np.allclose(z, z_reconstructed)
    True

    See Also
    --------
    JacobiState : Alternative coordinate system
    ShapeSpaceState : Reduced coordinates after quotient
    """
    # Class implementation
    pass
```

### D1.2: Module Documentation

Each module must have a module-level docstring explaining its purpose, key concepts, and usage patterns.

#### Template: `coordinates/cartesian.py`

```python
"""
Cartesian coordinate system for the three-body problem.

This module implements the standard Cartesian representation of the 3-body
problem in a barycentric inertial frame. It provides data structures for
storing states and functions for computing dynamical quantities.

Overview
--------
Cartesian coordinates are the most direct representation of the 3-body
problem. Each body's position and velocity is represented by a 3D vector,
giving 18 total degrees of freedom (for 3D motion).

Key Features
------------
- CartesianState dataclass: Type-safe state representation
- Energy and momentum calculations with high precision
- Barycentric frame enforcement
- Conservation law monitoring
- Integration with WP1 integrators

Coordinate Representation
-------------------------
A state is represented as::

    z = (r1, r2, r3, v1, v2, v3)

where r_i ∈ ℝ³ are positions and v_i ∈ ℝ³ are velocities.

Barycentric Frame
-----------------
We work in a barycentric (center-of-mass) frame where::

    Σ m_i r_i = 0
    Σ m_i v_i = 0

This removes 6 trivial degrees of freedom.

Mathematical Background
-----------------------
The Hamiltonian in Cartesian coordinates is:

.. math::
    H = \\frac{1}{2}\\sum_{i=1}^3 m_i |\\mathbf{v}_i|^2
        - \\sum_{i<j} \\frac{G m_i m_j}{|\\mathbf{r}_i - \\mathbf{r}_j|}

The equations of motion are:

.. math::
    \\dot{\\mathbf{r}}_i &= \\mathbf{v}_i \\\\
    \\dot{\\mathbf{v}}_i &= \\sum_{j \\ne i} \\frac{G m_j (\\mathbf{r}_j - \\mathbf{r}_i)}{|\\mathbf{r}_{ij}|^3}

Examples
--------
Basic usage:

>>> from coordinates.cartesian import CartesianState, compute_energy
>>> from coordinates.base import Masses
>>> import numpy as np
>>>
>>> # Create initial state
>>> positions = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0]])
>>> velocities = np.zeros((3, 3))
>>> state = CartesianState(positions, velocities)
>>> masses = Masses(1.0, 1.0, 1.0)
>>>
>>> # Compute energy
>>> E = compute_energy(state, masses)
>>> print(f"Energy: {E:.6f}")

Enforce barycentric constraints:

>>> from coordinates.cartesian import enforce_barycenter
>>> state_bc = enforce_barycenter(state, masses)
>>> P = compute_linear_momentum(state_bc, masses)
>>> assert np.linalg.norm(P) < 1e-14

Monitor conservation laws during integration:

>>> from coordinates.cartesian import ConservationMonitor
>>> monitor = ConservationMonitor(state, masses)
>>>
>>> # During integration...
>>> for t, state_t in trajectory:
...     monitor.record(t, state_t, masses)
>>>
>>> # Check conservation
>>> tolerances = {'energy': 1e-12, 'angular_momentum': 1e-14, 'linear_momentum': 1e-14}
>>> assert monitor.validate(tolerances)

See Also
--------
coordinates.jacobi : Hierarchical coordinate system
coordinates.shape_space : Reduced coordinates
reduction.translation_reduction : Remove center-of-mass motion

References
----------
.. [1] Meyer, K. R., & Hall, G. R. "Introduction to Hamiltonian Dynamical
       Systems and the N-Body Problem." Springer, 2008.
.. [2] Hairer, E., Lubich, C., & Wanner, G. "Geometric Numerical
       Integration." Springer, 2006.
"""
```

### D1.3: API Reference Generation

Use Sphinx to automatically generate API documentation from docstrings.

#### Configuration: `docs/conf.py`

```python
"""Sphinx configuration for 3body project documentation."""

import os
import sys
sys.path.insert(0, os.path.abspath('../../src/python'))

# Project information
project = '3body'
copyright = '2025, 3body Development Team'
author = '3body Development Team'
version = '0.1.0'
release = '0.1.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # NumPy style docstrings
    'sphinx.ext.mathjax',   # Math rendering
    'sphinx.ext.viewcode',  # Source code links
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'nbsphinx',  # Jupyter notebook support
    'sphinx_rtd_theme',
]

# Napoleon settings (NumPy style)
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_rtype = True
napoleon_use_param = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Math rendering
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"

# Theme
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}
```

### D1.4: Usage Examples

Create standalone examples demonstrating common use cases.

#### Example: `docs/examples/basic_transformation.py`

```python
"""
Basic Coordinate Transformation Example
========================================

This example demonstrates how to transform between different coordinate
systems for the three-body problem.
"""

import numpy as np
from coordinates.cartesian import CartesianState, enforce_barycenter
from coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian
from coordinates.shape_space import cartesian_to_shape_distances
from coordinates.base import Masses

def main():
    """Run basic transformation examples."""

    # Setup: Equal mass system in roughly equilateral triangle
    print("=" * 60)
    print("Three-Body Coordinate Transformation Example")
    print("=" * 60)

    # Define masses
    masses = Masses(m1=1.0, m2=1.0, m3=1.0)
    print(f"\nMasses: m1={masses.m1}, m2={masses.m2}, m3={masses.m3}")
    print(f"Total mass: {masses.total}")
    print(f"Reduced mass μ₁₂: {masses.mu12:.4f}")
    print(f"Reduced mass μ₃: {masses.mu3:.4f}")

    # Initial Cartesian state (equilateral triangle)
    R = 1.0
    angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
    positions = R * np.column_stack([
        np.cos(angles),
        np.sin(angles),
        np.zeros(3)
    ])

    # Zero velocities initially
    velocities = np.zeros((3, 3))

    state_cart = CartesianState(positions, velocities, dimension=2)
    print("\n" + "-" * 60)
    print("Initial Cartesian State (before barycenter enforcement)")
    print("-" * 60)
    print("Positions:")
    print(state_cart.positions)

    # Enforce barycentric constraint
    state_cart = enforce_barycenter(state_cart, masses)
    print("\n" + "-" * 60)
    print("Cartesian State (barycentric frame)")
    print("-" * 60)
    print("Positions:")
    print(state_cart.positions)
    print("\nCenter of mass:", np.sum(state_cart.positions *
                                       np.array([masses.m1, masses.m2, masses.m3])[:, np.newaxis],
                                       axis=0))

    # Transform to Jacobi coordinates
    print("\n" + "-" * 60)
    print("Jacobi Coordinates")
    print("-" * 60)
    state_jacobi = cartesian_to_jacobi(state_cart, masses)
    print(f"r_J1 (relative 1-2): {state_jacobi.r1}")
    print(f"r_J2 (3 rel to cm_12): {state_jacobi.r2}")
    print(f"r_cm (barycenter): {state_jacobi.r_cm}")

    # Verify round-trip accuracy
    print("\n" + "-" * 60)
    print("Round-Trip Verification: Cartesian → Jacobi → Cartesian")
    print("-" * 60)
    state_cart_reconstructed = jacobi_to_cartesian(state_jacobi, masses)

    pos_error = np.linalg.norm(state_cart.positions -
                                state_cart_reconstructed.positions)
    vel_error = np.linalg.norm(state_cart.velocities -
                                state_cart_reconstructed.velocities)

    print(f"Position error: {pos_error:.2e}")
    print(f"Velocity error: {vel_error:.2e}")
    print(f"Round-trip successful: {pos_error < 1e-14 and vel_error < 1e-14}")

    # Transform to shape space
    print("\n" + "-" * 60)
    print("Shape Space Coordinates")
    print("-" * 60)
    state_shape = cartesian_to_shape_distances(state_cart, masses)
    print(f"r₁₂ (distance 1-2): {state_shape.r12:.6f}")
    print(f"r₂₃ (distance 2-3): {state_shape.r23:.6f}")
    print(f"r₃₁ (distance 3-1): {state_shape.r31:.6f}")
    print(f"Perimeter: {state_shape.perimeter:.6f}")
    print(f"Area: {state_shape.area:.6f}")
    print(f"Triangle inequality satisfied: {state_shape.validate()}")

    print("\n" + "=" * 60)
    print("Example Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

---

## D2: Technical Report

### D2.1: Report Structure

The technical report provides a comprehensive scientific documentation of the coordinate systems and reduction implementation.

#### LaTeX Structure: `docs/technical_reports/Task_2.1.1_Technical_Report.tex`

```latex
\documentclass[11pt,a4paper]{article}

% Packages
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{algorithm}
\usepackage{algorithmic}
\usepackage{cleveref}
\usepackage{natbib}

% Theorem environments
\newtheorem{theorem}{Theorem}[section]
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{remark}[theorem]{Remark}

% Custom commands
\newcommand{\R}{\mathbb{R}}
\newcommand{\C}{\mathbb{C}}
\newcommand{\SO}{\mathrm{SO}}
\newcommand{\diff}{\mathrm{d}}
\newcommand{\Lie}{\mathcal{L}}

\title{Coordinate Systems and Marsden-Weinstein Reduction \\
       for the Three-Body Problem}

\author{3body Development Team}

\date{\today}

\begin{document}

\maketitle

\begin{abstract}
We present a comprehensive implementation of coordinate transformations
and symplectic reduction for the general Newtonian three-body problem.
This work establishes the foundation for discovering hidden integrability
in shape space dynamics. We implement three coordinate systems (Cartesian,
Jacobi, and shape space) with rigorous validation, and develop the
Marsden-Weinstein reduction machinery for removing translational and
rotational symmetries. High-precision arithmetic ensures conservation
laws are maintained to machine precision over long integrations.
Validation against known solutions (Lagrange equilibria, Figure-8 orbit)
confirms the correctness of our implementation.
\end{abstract}

\tableofcontents

\section{Introduction}
\label{sec:introduction}

The three-body problem has captivated mathematicians and physicists for
over three centuries. While the general problem is non-integrable, recent
work suggests that "hidden integrability" may exist in reduced coordinate
systems. This report documents our implementation of the coordinate
transformation and symplectic reduction machinery necessary to explore
this conjecture.

\subsection{Motivation}

[Content explaining the scientific motivation...]

\subsection{Overview of Results}

[Summary of what was implemented and validated...]

\section{Mathematical Background}
\label{sec:background}

\subsection{The Newtonian Three-Body Problem}

Consider three point masses $m_1, m_2, m_3 > 0$ interacting under
Newtonian gravity...

[Mathematical foundations...]

\section{Coordinate Systems}
\label{sec:coordinates}

\subsection{Cartesian Coordinates}

\subsubsection{Definition}
[Mathematical definition...]

\subsubsection{Implementation}
[Code structure and algorithms...]

\subsubsection{Validation}
[Test results...]

\subsection{Jacobi Coordinates}

[Similar structure...]

\subsection{Shape Space Coordinates}

[Similar structure...]

\section{Marsden-Weinstein Symplectic Reduction}
\label{sec:reduction}

\subsection{Theoretical Framework}

\begin{definition}[Momentum Map]
Let $(M, \omega, H)$ be a Hamiltonian system with a Lie group $G$
acting on $M$ preserving $\omega$ and $H$. The momentum map
$\mu: M \to \mathfrak{g}^*$ is defined by...
\end{definition}

[Continue with theory...]

\subsection{Translation Reduction}

[Implementation of translation reduction...]

\subsection{Rotation Reduction}

[Implementation of rotation reduction...]

\section{Numerical Implementation}
\label{sec:implementation}

\subsection{High-Precision Arithmetic}

[Details on quad-double precision...]

\subsection{Performance Optimization}

[Benchmarks and optimization strategies...]

\section{Validation and Testing}
\label{sec:validation}

\subsection{Test Cases}

\subsubsection{Lagrange Equilibrium}

[Results for equilateral triangle...]

\subsubsection{Figure-8 Orbit}

[Results for Figure-8...]

\subsection{Conservation Laws}

[Tables and plots showing conservation...]

\section{Conclusion}
\label{sec:conclusion}

[Summary and future work...]

\appendix

\section{Coordinate Transformation Derivations}
\label{app:derivations}

[Detailed mathematical derivations...]

\section{Numerical Precision Analysis}
\label{app:precision}

[Error analysis...]

\bibliographystyle{plainnat}
\bibliography{bibliography}

\end{document}
```

### D2.2: Figures and Diagrams

Create publication-quality figures illustrating key concepts.

#### Figure 1: Coordinate Transformation Diagram

Create using Python/Matplotlib or TikZ:

```python
"""
Generate coordinate transformation diagram for technical report.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def create_coordinate_diagram():
    """Create diagram showing relationships between coordinate systems."""

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Define box positions
    boxes = {
        'cartesian': (1, 4, 2, 1),
        'jacobi': (4, 4, 2, 1),
        'shape': (7, 4, 2, 1),
        'trans_reduced': (2.5, 2, 2, 0.8),
        'rot_reduced': (5.5, 2, 2, 0.8),
    }

    # Draw boxes
    for name, (x, y, w, h) in boxes.items():
        if name in ['cartesian', 'jacobi', 'shape']:
            color = 'lightblue'
        else:
            color = 'lightcoral'

        box = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.1",
                              facecolor=color,
                              edgecolor='black',
                              linewidth=2)
        ax.add_patch(box)

        # Labels
        labels = {
            'cartesian': 'Cartesian\n$\\mathbb{R}^{18}$',
            'jacobi': 'Jacobi\n$\\mathbb{R}^{18}$',
            'shape': 'Shape Space\n(distances)',
            'trans_reduced': 'Trans. Reduced\n$\\mathbb{R}^{15}$',
            'rot_reduced': 'Rot. Reduced\n$\\mathbb{R}^{12}$ (planar: 7)',
        }

        ax.text(x + w/2, y + h/2, labels[name],
                ha='center', va='center',
                fontsize=10, weight='bold')

    # Draw arrows
    arrows = [
        ('cartesian', 'jacobi', 'Linear\nSymplectic'),
        ('jacobi', 'shape', 'Quotient\nNonlinear'),
        ('cartesian', 'trans_reduced', 'Remove\nCOM'),
        ('trans_reduced', 'rot_reduced', 'Fix\nOrientation'),
    ]

    # (Add arrow drawing code...)

    plt.title('Coordinate System Transformations', fontsize=14, weight='bold')
    plt.tight_layout()
    plt.savefig('figures/coordinate_diagram.pdf', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    create_coordinate_diagram()
```

### D2.3: Results Tables

Include tables summarizing validation results:

```latex
\begin{table}[h]
\centering
\caption{Conservation Law Validation for Lagrange Equilibrium}
\label{tab:conservation_lagrange}
\begin{tabular}{lccc}
\hline
Quantity & Initial Value & Final Value (t=100) & Relative Error \\
\hline
Energy $E$ & -1.500000 & -1.500000 & $2.3 \times 10^{-13}$ \\
Angular Momentum $L_z$ & 2.598076 & 2.598076 & $1.1 \times 10^{-14}$ \\
Linear Momentum $|\mathbf{P}|$ & 0 & $8.9 \times 10^{-16}$ & — \\
\hline
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Round-Trip Transformation Errors}
\label{tab:roundtrip_errors}
\begin{tabular}{lcc}
\hline
Transformation & Max Error (1000 tests) & Mean Error \\
\hline
Cartesian → Jacobi → Cartesian & $3.2 \times 10^{-15}$ & $1.1 \times 10^{-15}$ \\
Cartesian → Shape → Cartesian$^*$ & $2.1 \times 10^{-14}$ & $8.3 \times 10^{-15}$ \\
\hline
\multicolumn{3}{l}{\small $^*$Fixing canonical orientation} \\
\end{tabular}
\end{table}
```

---

## D3: Tutorial Jupyter Notebook

### D3.1: Notebook Structure

The tutorial notebook provides an interactive introduction to coordinate systems and reduction.

#### Outline: `notebooks/Tutorial_Coordinate_Systems.ipynb`

```markdown
# Three-Body Problem: Coordinate Systems Tutorial

## Table of Contents
1. [Introduction](#introduction)
2. [Setup and Imports](#setup)
3. [Part 1: Cartesian Coordinates](#part1)
4. [Part 2: Jacobi Coordinates](#part2)
5. [Part 3: Shape Space](#part3)
6. [Part 4: Symplectic Reduction](#part4)
7. [Interactive Exploration](#interactive)
8. [Exercises](#exercises)

---

## 1. Introduction {#introduction}

Welcome to the coordinate systems tutorial for the three-body problem!

This notebook will guide you through:
- Different coordinate representations
- Transformations between coordinate systems
- Symplectic reduction to shape space
- Visualization of trajectories

### Learning Objectives

By the end of this tutorial, you will be able to:
- [ ] Create and manipulate states in different coordinate systems
- [ ] Transform between Cartesian, Jacobi, and shape space coordinates
- [ ] Understand the geometric meaning of symplectic reduction
- [ ] Visualize three-body dynamics in different representations

### Prerequisites

Basic knowledge of:
- Classical mechanics (Hamiltonian formulation)
- Linear algebra
- Python/NumPy

---

## 2. Setup and Imports {#setup}

Let's start by importing the necessary libraries.
```

#### Cell 1: Imports and Setup

```python
# Standard libraries
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML
import ipywidgets as widgets

# 3body library
from coordinates.cartesian import (
    CartesianState, enforce_barycenter,
    compute_energy, compute_angular_momentum
)
from coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian
from coordinates.shape_space import cartesian_to_shape_distances
from coordinates.base import Masses
from reduction.translation_reduction import TranslationReduction
from reduction.rotation_reduction import RotationReduction

# Plotting style
plt.style.use('seaborn-v0_8-notebook')
%matplotlib inline

print("✓ Imports successful")
print(f"NumPy version: {np.__version__}")
```

#### Cell 2: Creating Your First Three-Body State

```python
# Create an equilateral triangle configuration
R = 1.0  # radius
angles = np.array([0, 2*np.pi/3, 4*np.pi/3])

positions = R * np.column_stack([
    np.cos(angles),
    np.sin(angles),
    np.zeros(3)
])

# Start with zero velocities
velocities = np.zeros((3, 3))

# Create state
state = CartesianState(positions, velocities, dimension=2)

# Define masses
masses = Masses(m1=1.0, m2=1.0, m3=1.0)

print("Initial Cartesian State Created!")
print(f"\nPositions:\n{state.positions}")
print(f"\nMasses: {masses.m1}, {masses.m2}, {masses.m3}")
```

#### Cell 3: Visualizing the Configuration

```python
def plot_configuration(state, masses, title="Three-Body Configuration"):
    """Plot the positions of three bodies."""
    fig, ax = plt.subplots(figsize=(8, 8))

    colors = ['red', 'blue', 'green']
    labels = [f'Body {i+1} (m={m})' for i, m in enumerate([masses.m1, masses.m2, masses.m3])]

    for i in range(3):
        ax.scatter(state.positions[i, 0], state.positions[i, 1],
                   s=300*[masses.m1, masses.m2, masses.m3][i],
                   c=colors[i], label=labels[i],
                   edgecolor='black', linewidth=2, zorder=3)

    # Draw triangle
    triangle = np.vstack([state.positions[:, :2], state.positions[0, :2]])
    ax.plot(triangle[:, 0], triangle[:, 1], 'k--', alpha=0.3, linewidth=1)

    # Center of mass
    m_array = np.array([masses.m1, masses.m2, masses.m3])
    com = np.sum(state.positions * m_array[:, np.newaxis], axis=0) / masses.total
    ax.scatter(com[0], com[1], s=100, c='black', marker='x',
               linewidth=3, label='Center of Mass', zorder=4)

    ax.set_xlabel('x', fontsize=12)
    ax.set_ylabel('y', fontsize=12)
    ax.set_title(title, fontsize=14, weight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.show()

plot_configuration(state, masses)
```

#### Cell 4: Coordinate Transformations

```python
# Enforce barycentric constraint
state_bc = enforce_barycenter(state, masses)

print("Before barycenter enforcement:")
m_array = np.array([masses.m1, masses.m2, masses.m3])
com_before = np.sum(state.positions * m_array[:, np.newaxis], axis=0)
print(f"  Center of mass: {com_before}")

print("\nAfter barycenter enforcement:")
com_after = np.sum(state_bc.positions * m_array[:, np.newaxis], axis=0)
print(f"  Center of mass: {com_after}")
print(f"  Norm: {np.linalg.norm(com_after):.2e}")

# Transform to Jacobi
state_jacobi = cartesian_to_jacobi(state_bc, masses)

print("\n" + "="*50)
print("Jacobi Coordinates")
print("="*50)
print(f"r_J1 (1-2 relative): {state_jacobi.r1}")
print(f"r_J2 (3 rel to cm12): {state_jacobi.r2}")
print(f"r_cm (barycenter): {state_jacobi.r_cm}")
print(f"  Norm of r_cm: {np.linalg.norm(state_jacobi.r_cm):.2e}")
```

### D3.2: Interactive Widgets

Create interactive visualizations to explore parameter space.

```python
def create_interactive_three_body():
    """Interactive widget for exploring three-body configurations."""

    @widgets.interact(
        m1=widgets.FloatSlider(min=0.1, max=3.0, step=0.1, value=1.0, description='Mass 1:'),
        m2=widgets.FloatSlider(min=0.1, max=3.0, step=0.1, value=1.0, description='Mass 2:'),
        m3=widgets.FloatSlider(min=0.1, max=3.0, step=0.1, value=1.0, description='Mass 3:'),
        shape=widgets.Dropdown(
            options=['Equilateral', 'Isosceles', 'Scalene', 'Collinear'],
            value='Equilateral',
            description='Shape:'
        ),
        show_jacobi=widgets.Checkbox(value=False, description='Show Jacobi coords')
    )
    def plot_interactive(m1, m2, m3, shape, show_jacobi):
        """Plot configuration based on parameters."""

        masses = Masses(m1, m2, m3)

        # Create configuration based on shape
        if shape == 'Equilateral':
            angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
            positions = np.column_stack([np.cos(angles), np.sin(angles), np.zeros(3)])
        elif shape == 'Isosceles':
            positions = np.array([[1, 0, 0], [-1, 0, 0], [0, 1.5, 0]])
        elif shape == 'Scalene':
            positions = np.array([[1, 0, 0], [-0.5, 0, 0], [0.3, 1.2, 0]])
        elif shape == 'Collinear':
            positions = np.array([[-1, 0, 0], [0, 0, 0], [1, 0, 0]])

        velocities = np.zeros((3, 3))
        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        # Compute properties
        E = compute_energy(state, masses)
        L = compute_angular_momentum(state, masses)

        # Plot
        fig, axes = plt.subplots(1, 2 if show_jacobi else 1, figsize=(15 if show_jacobi else 8, 6))
        if not show_jacobi:
            axes = [axes]

        # Cartesian plot
        ax = axes[0]
        colors = ['red', 'blue', 'green']
        sizes = 300 * np.array([m1, m2, m3]) / max(m1, m2, m3)

        for i in range(3):
            ax.scatter(state.positions[i, 0], state.positions[i, 1],
                       s=sizes[i], c=colors[i],
                       label=f'Body {i+1} (m={[m1,m2,m3][i]:.1f})',
                       edgecolor='black', linewidth=2)

        ax.scatter(0, 0, s=100, c='black', marker='x', linewidth=3, label='COM')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(f'Cartesian\nE = {E:.3f}, L_z = {L[2]:.3f}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # Jacobi plot (if requested)
        if show_jacobi:
            ax_jac = axes[1]
            state_jac = cartesian_to_jacobi(state, masses)

            # Plot Jacobi vectors
            ax_jac.arrow(0, 0, state_jac.r1[0], state_jac.r1[1],
                         head_width=0.1, head_length=0.1, fc='blue', ec='blue',
                         label='r_J1 (1-2 relative)')
            ax_jac.arrow(0, 0, state_jac.r2[0], state_jac.r2[1],
                         head_width=0.1, head_length=0.1, fc='green', ec='green',
                         label='r_J2 (3 rel to cm12)')

            ax_jac.scatter(0, 0, s=100, c='black', marker='o')
            ax_jac.set_xlabel('x')
            ax_jac.set_ylabel('y')
            ax_jac.set_title('Jacobi Coordinates')
            ax_jac.legend()
            ax_jac.grid(True, alpha=0.3)
            ax_jac.set_aspect('equal')

        plt.tight_layout()
        plt.show()

create_interactive_three_body()
```

### D3.3: Exercises

Include exercises for self-study:

```markdown
## 8. Exercises {#exercises}

### Exercise 1: Round-Trip Accuracy

Test the accuracy of coordinate transformations:

1. Create a random Cartesian state
2. Transform to Jacobi and back
3. Compute the error
4. Repeat for 1000 random states
5. Plot histogram of errors

**Expected Result**: Errors should be < 1e-13 for double precision.

```python
# Your code here
```

### Exercise 2: Conservation Laws

Integrate the Lagrange equilibrium configuration for 10 periods:

1. Set up the initial condition
2. Integrate using your favorite integrator
3. Monitor energy, angular momentum, and linear momentum
4. Plot conservation errors vs time

**Questions**:
- How does the error grow with time?
- Is it linear, quadratic, or exponential?
- Does it depend on the integrator?

```python
# Your code here
```

### Exercise 3: Shape Space Exploration

Explore the shape space for different mass ratios:

1. Create configurations with masses (1, 1, 1), (1, 1, 0.1), (1, 0.1, 0.1)
2. Transform to shape space (distances)
3. Plot the configurations in the (r12, r23, r31) space
4. Add constraints (triangle inequality)

```python
# Your code here
```

---

## Further Reading

1. Abraham & Marsden, *Foundations of Mechanics* (1978)
2. Meyer & Hall, *Introduction to Hamiltonian Dynamical Systems* (2008)
3. Valtonen & Karttunen, *The Three-Body Problem* (2006)

## Acknowledgments

This tutorial was developed as part of the 3body project.
```

---

## Quality Assurance

### Documentation Review Checklist

- [ ] **Accuracy**: All mathematical statements verified
- [ ] **Completeness**: All public APIs documented
- [ ] **Clarity**: Technical terms defined on first use
- [ ] **Examples**: All code examples run successfully
- [ ] **Citations**: All references properly formatted
- [ ] **Figures**: High-quality, publication-ready
- [ ] **Consistency**: Notation consistent throughout
- [ ] **Accessibility**: Clear for target audience

### Testing Documentation Examples

Create tests that validate documentation examples:

```python
# tests/test_documentation_examples.py

def test_basic_transformation_example():
    """Verify the basic transformation example from docs runs correctly."""

    # This should match exactly what's in docs/examples/basic_transformation.py
    import numpy as np
    from coordinates.cartesian import CartesianState, enforce_barycenter
    from coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian
    from coordinates.base import Masses

    masses = Masses(m1=1.0, m2=1.0, m3=1.0)

    R = 1.0
    angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
    positions = R * np.column_stack([
        np.cos(angles),
        np.sin(angles),
        np.zeros(3)
    ])
    velocities = np.zeros((3, 3))

    state_cart = CartesianState(positions, velocities, dimension=2)
    state_cart = enforce_barycenter(state_cart, masses)

    state_jacobi = cartesian_to_jacobi(state_cart, masses)
    state_cart_reconstructed = jacobi_to_cartesian(state_jacobi, masses)

    pos_error = np.linalg.norm(state_cart.positions -
                                state_cart_reconstructed.positions)

    assert pos_error < 1e-14, "Documentation example failed!"
```

### Documentation Build Process

```bash
#!/bin/bash
# scripts/build_docs.sh

set -e

echo "Building documentation..."

# Generate API reference
cd docs
sphinx-apidoc -f -o api ../src/python/

# Build HTML
make html

# Build PDF (requires LaTeX)
cd technical_reports
pdflatex Task_2.1.1_Technical_Report.tex
bibtex Task_2.1.1_Technical_Report
pdflatex Task_2.1.1_Technical_Report.tex
pdflatex Task_2.1.1_Technical_Report.tex

cd ../..

# Execute notebooks to verify they run
jupyter nbconvert --to notebook --execute notebooks/Tutorial_Coordinate_Systems.ipynb

echo "✓ Documentation built successfully"
echo "  HTML: docs/_build/html/index.html"
echo "  PDF: docs/technical_reports/Task_2.1.1_Technical_Report.pdf"
```

---

## Implementation Checklist

### D1: API Documentation
- [ ] All public functions have complete NumPy-style docstrings
- [ ] All classes have complete docstrings with examples
- [ ] All modules have descriptive module docstrings
- [ ] Mathematical notation is consistent and properly formatted
- [ ] Code examples in docstrings are tested
- [ ] Sphinx configuration complete
- [ ] API reference generated successfully
- [ ] Cross-references working
- [ ] Standalone examples created and tested

### D2: Technical Report
- [ ] LaTeX template set up
- [ ] All sections outlined
- [ ] Introduction written
- [ ] Mathematical background complete
- [ ] Coordinate systems section complete
- [ ] Reduction section complete
- [ ] Implementation details documented
- [ ] Validation results included
- [ ] All figures created
- [ ] All tables formatted
- [ ] Bibliography complete
- [ ] Appendices written
- [ ] Report compiles without errors
- [ ] Proofreading complete
- [ ] PDF generated

### D3: Tutorial Notebook
- [ ] Notebook structure finalized
- [ ] Introduction section complete
- [ ] Setup and imports tested
- [ ] Part 1 (Cartesian) complete
- [ ] Part 2 (Jacobi) complete
- [ ] Part 3 (Shape space) complete
- [ ] Part 4 (Reduction) complete
- [ ] Interactive widgets working
- [ ] Visualizations rendering correctly
- [ ] Exercises included with solutions
- [ ] Notebook executes without errors
- [ ] Clear learning objectives
- [ ] Further reading section

### Integration & Quality
- [ ] Documentation examples validated with tests
- [ ] Sphinx build successful
- [ ] LaTeX compilation successful
- [ ] Notebook execution successful
- [ ] Links and cross-references verified
- [ ] Figures display correctly
- [ ] Code snippets syntax-highlighted
- [ ] Documentation reviewed by team
- [ ] Accessibility checked
- [ ] Version controlled with code

---

## Timeline

### Day 1: API Documentation and Examples
- **Morning**: Write docstrings for all coordinate system modules
- **Afternoon**: Write docstrings for reduction modules
- **Evening**: Create standalone examples, run tests

### Day 2: Technical Report and Tutorial
- **Morning**: Complete LaTeX report structure and main sections
- **Afternoon**: Generate figures and tables, finalize report
- **Evening**: Create and test tutorial notebook

---

## Success Criteria

### Functional Requirements
- [ ] All public APIs documented to NumPy standard
- [ ] Technical report is publication-ready (15-20 pages)
- [ ] Tutorial notebook executes without errors
- [ ] All documentation examples validated by tests

### Quality Requirements
- [ ] No mathematical errors in technical report
- [ ] All figures are publication-quality (300+ DPI)
- [ ] Sphinx documentation builds without warnings
- [ ] LaTeX compiles without errors
- [ ] Notebook cells execute in under 2 minutes total

### User Experience Requirements
- [ ] New users can get started from tutorial in < 30 minutes
- [ ] API documentation answers common questions
- [ ] Technical report suitable for peer review
- [ ] Examples are copy-paste ready

---

## Future Enhancements

1. **Video Tutorials**: Screen-capture walkthroughs
2. **Interactive Demos**: Web-based visualizations
3. **FAQ Section**: Common questions and troubleshooting
4. **Performance Guide**: Optimization tips
5. **Contributing Guide**: For external developers

---

**Document Version**: 1.0
**Created**: 2025-11-10
**Status**: Design Complete → Ready for Implementation
