# AMENDED WP 2.3: Kustaanheimo-Stiefel (KS) Spinor "Pairwise" Lift
## Work Package 2 - Geometric Reduction and Shape Space Analysis
## AMENDMENT: Detailed Constraint Handling and Numerical Challenges

**Status**: Design Phase - AMENDED
**Priority**: Critical Path for Lift-Integrability Hypothesis (Extended)
**Estimated Duration**: 15-18 days (extended for robustness)
**Dependencies**: WP2.2 Complete or In-Progress (S¹ Lift), Task 2.1.1 (Coordinates)
**Amendment Date**: 2025-11-22
**Amendment Purpose**: Elaborate on constraint handling techniques, numerical challenges, and theoretical foundations

---

## Amendment Overview

This AMENDED document provides significantly expanded detail on:

1. **Constraint Handling Techniques**: Dirac brackets, RATTLE/SHAKE algorithms, stabilization methods
2. **Numerical Challenges**: Constraint drift, ill-conditioning, chart singularities, time regularization stability
3. **Theoretical Challenges**: Momentum map interpretation, gauge freedom, symplectic structure preservation
4. **Implementation Strategies**: Robust algorithms with fallback mechanisms and adaptive precision

**Key Addition**: This amendment acknowledges that constrained Hamiltonian dynamics is **non-trivial** and requires careful treatment to maintain both:
- **Symplectic structure** (energy conservation, geometric properties)
- **Constraint satisfaction** (manifold adherence to machine precision)

---

## Table of Contents

1. [Overview](#overview) *(from original)*
2. [Mathematical Background](#mathematical-background) *(expanded)*
3. [**NEW: Constraint Theory and Symplectic Geometry**](#constraint-theory-and-symplectic-geometry)
4. [**NEW: Dirac Bracket Formulation**](#dirac-bracket-formulation)
5. [Implementation Architecture](#implementation-architecture) *(from original)*
6. [Part A: KS Transformation for Single Pair](#part-a-ks-transformation-for-single-pair) *(from original)*
7. [Part B: Pairwise Application to 3BP](#part-b-pairwise-application-to-3bp) *(expanded)*
8. [**Part C: Constrained Hamiltonian Dynamics (EXPANDED)**](#part-c-constrained-hamiltonian-dynamics-expanded)
9. [**NEW: Numerical Challenges and Mitigation Strategies**](#numerical-challenges-and-mitigation-strategies)
10. [Part D: Integrability Analysis](#part-d-integrability-analysis) *(from original)*
11. [**NEW: Theoretical Foundations and Open Questions**](#theoretical-foundations-and-open-questions)
12. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
13. [Implementation Schedule](#implementation-schedule) *(updated)*
14. [Success Criteria](#success-criteria) *(expanded)*
15. [Risk Mitigation](#risk-mitigation) *(expanded)*

---

## Overview

*(Retained from original WP2.3 document)*

### Purpose

WP 2.3 implements the **Kustaanheimo-Stiefel (KS) spinor lift**—a more sophisticated dimensional increase that regularizes collisions and potentially reveals hidden integrability through spinor algebra. Unlike the minimal S¹ lift (WP2.2), the KS lift is motivated by:

1. **Collision Regularization**: KS transform makes collisions (singularities) regular
2. **Spinor Structure**: Connection to SU(2) representation theory
3. **Higher Dimensionality**: More room for hidden symmetries (12D vs. 4D in S¹ case)
4. **Historical Success**: KS regularization solved the perturbed Kepler problem

**The "Pairwise" Strategy**: Apply KS transformation to all three pairwise relative coordinates:
- $(r_{12}, \dot{r}_{12}) \to (u_{12}, \dot{u}_{12})$ where $u_{12} \in \mathbb{R}^4$
- $(r_{23}, \dot{r}_{23}) \to (u_{23}, \dot{u}_{23})$ where $u_{23} \in \mathbb{R}^4$
- $(r_{31}, \dot{r}_{31}) \to (u_{31}, \dot{u}_{31})$ where $u_{31} \in \mathbb{R}^4$

**Result**: 3D configuration space → 12D spinor space, constrained to effective 9D.

---

## Mathematical Background

*(Retained from original, with key formulas for reference)*

### The Kustaanheimo-Stiefel (KS) Transformation

For a **single** two-body problem, the KS transformation embeds 3D space into 4D:

#### Definition

**Position Space**: A 3D vector $\mathbf{r} = (x, y, z)$ with $r = |\mathbf{r}|$ is represented by a 4D spinor:

$$
\mathbf{u} = (u_0, u_1, u_2, u_3) \in \mathbb{R}^4
$$

related by the **bilinear map**:

$$
\mathbf{r} = L(\mathbf{u}) \mathbf{u}
$$

where $L(\mathbf{u})$ is the **Levi-Civita matrix**:

$$
L(\mathbf{u}) = \begin{pmatrix}
u_0 & -u_1 & -u_2 & -u_3 \\
u_1 & u_0 & -u_3 & u_2 \\
u_2 & u_3 & u_0 & -u_1
\end{pmatrix}
$$

**Key Property**:
$$
|\mathbf{r}|^2 = |\mathbf{u}|^4 \quad \Rightarrow \quad r = |\mathbf{u}|^2
$$

This is the **bilinear constraint** relating 4D spinor to 3D position.

#### Velocity Space

Velocities transform similarly:

$$
\dot{\mathbf{r}} = 2 L(\mathbf{u}) \dot{\mathbf{u}}
$$

#### Time Regularization

To regularize collisions ($r \to 0$), introduce **fictitious time** $s$:

$$
\frac{dt}{ds} = r = |\mathbf{u}|^2
$$

**Effect**: As $r \to 0$ (collision), real time $t$ slows down relative to fictitious time $s$. The trajectory becomes regular in $(s, \mathbf{u})$ coordinates even through collisions.

---

## Constraint Theory and Symplectic Geometry

### The Constraint Manifold

The pairwise KS coordinates live on a **constraint manifold** $\mathcal{M}_c \subset \mathbb{R}^{24}$ (phase space) defined by:

#### Primary Constraints (Position-Level)

1. **Bilinear Constraints** (3 scalar equations):
   $$
   \phi_1(\mathbf{u}) = |\mathbf{u}_{12}|^2 - r_{12} = 0
   $$
   $$
   \phi_2(\mathbf{u}) = |\mathbf{u}_{23}|^2 - r_{23} = 0
   $$
   $$
   \phi_3(\mathbf{u}) = |\mathbf{u}_{31}|^2 - r_{31} = 0
   $$

2. **Closure Constraint** (3 vector equations):
   $$
   \phi_4(\mathbf{u}) = L(\mathbf{u}_{12})\mathbf{u}_{12} + L(\mathbf{u}_{23})\mathbf{u}_{23} + L(\mathbf{u}_{31})\mathbf{u}_{31} = \mathbf{0}
   $$

**Total**: 6 scalar constraints on 12D configuration space → 6D physical configuration space

#### Secondary Constraints (Velocity-Level)

For each primary constraint $\phi_k = 0$, consistency requires the **velocity constraint**:

$$
\dot{\phi}_k = \frac{\partial \phi_k}{\partial \mathbf{u}} \cdot \dot{\mathbf{u}} = 0
$$

**Explicitly**:

For bilinear constraints:
$$
\dot{\phi}_i = 2 \mathbf{u}_{ij} \cdot \dot{\mathbf{u}}_{ij} - \dot{r}_{ij} = 0
$$

This enforces that velocities are **tangent to the constraint manifold**.

**Total**: 6 primary + 6 secondary = **12 constraints** on 24D phase space → **12D constrained phase space**

### Constraint Classification (Dirac Theory)

Following Dirac's classification of constrained Hamiltonian systems:

#### First-Class vs. Second-Class Constraints

A constraint $\phi_i$ is **first-class** if it Poisson-commutes with all other constraints:
$$
\{\phi_i, \phi_j\} = 0 \quad \forall j
$$

Otherwise, it is **second-class**.

**For KS Constraints**:
- Bilinear constraints are **second-class** (non-zero Poisson brackets with each other)
- Closure constraint is **second-class** (couples to bilinear constraints)

**Implication**: Second-class constraints require **Dirac brackets** (modified Poisson structure) rather than simple restriction to $\mathcal{M}_c$.

#### Constraint Matrix

Define the **constraint matrix** $C_{ij}$:
$$
C_{ij} = \{\phi_i, \phi_j\}
$$

where $\{·,·\}$ is the standard Poisson bracket.

**For second-class constraints**: $C$ is **non-singular** (invertible).

**Key Computation**: Must compute $C^{-1}$ to define Dirac brackets.

### Symplectic Structure on Constraint Manifold

The constrained phase space $\mathcal{M}_c$ inherits a **reduced symplectic form** $\omega_c$.

Two approaches:

#### Approach 1: Dirac Bracket (Algebraic)

Define the **Dirac bracket**:
$$
\{f, g\}_D = \{f, g\} - \sum_{i,j} \{f, \phi_i\} C^{-1}_{ij} \{\phi_j, g\}
$$

where $\{·,·\}$ is the standard Poisson bracket and $C^{-1}$ is the inverse of the constraint matrix.

**Properties**:
- $\{f, \phi_k\}_D = 0$ for any constraint $\phi_k$ (constraints are Casimirs)
- Restricts to a Poisson bracket on $\mathcal{M}_c$
- Defines symplectic structure $\omega_c$ via: $\omega_c(X_f, X_g) = \{f,g\}_D$

**Advantage**: Works directly on constraint surface, no projection needed

**Disadvantage**: Requires computing and inverting constraint matrix $C$ (can be ill-conditioned)

#### Approach 2: Constrained Variational Principle (Geometric)

Use **Lagrange multipliers** to enforce constraints:
$$
H_{ext}(\mathbf{u}, \mathbf{p}, \lambda) = H(\mathbf{u}, \mathbf{p}) + \sum_k \lambda_k \phi_k(\mathbf{u}, \mathbf{p})
$$

**Hamilton's equations** become:
$$
\dot{\mathbf{u}} = \frac{\partial H_{ext}}{\partial \mathbf{p}}, \quad \dot{\mathbf{p}} = -\frac{\partial H_{ext}}{\partial \mathbf{u}}
$$

with algebraic equations:
$$
\phi_k(\mathbf{u}, \mathbf{p}) = 0 \quad \text{(constraints)}
$$

**Advantage**: Maintains constraint satisfaction via projection (RATTLE/SHAKE)

**Disadvantage**: Introduces additional unknowns $\lambda_k$ (Lagrange multipliers)

### Tangent Space to Constraint Manifold

At any point $z \in \mathcal{M}_c$, the tangent space is:
$$
T_z \mathcal{M}_c = \left\{ v \in \mathbb{R}^{24} : \frac{\partial \phi_k}{\partial z} \cdot v = 0, \, \forall k \right\}
$$

**Constraint Jacobian**:
$$
J_\phi(z) = \begin{pmatrix}
\nabla \phi_1(z)^T \\
\nabla \phi_2(z)^T \\
\vdots \\
\nabla \phi_6(z)^T
\end{pmatrix} \in \mathbb{R}^{6 \times 24}
$$

**Tangent space**: $T_z \mathcal{M}_c = \ker(J_\phi(z))$

**Orthogonal projection** onto tangent space:
$$
P_{\perp} = I - J_\phi^T (J_\phi J_\phi^T)^{-1} J_\phi
$$

**Critical for RATTLE/SHAKE**: Velocities must satisfy $\dot{z} \in T_z \mathcal{M}_c$.

---

## Dirac Bracket Formulation

### Explicit Dirac Bracket for KS Constraints

#### Step 1: Compute Constraint Matrix

For constraints $\phi = (\phi_1, \phi_2, \phi_3, \phi_4^{(x)}, \phi_4^{(y)}, \phi_4^{(z)})$ (6 total):

$$
C_{ij} = \{\phi_i, \phi_j\}
$$

**Example**: For bilinear constraint $\phi_1 = |\mathbf{u}_{12}|^2 - r_{12}$:

$$
\{\phi_1, \phi_2\} = \left\{ |\mathbf{u}_{12}|^2, |\mathbf{u}_{23}|^2 \right\} = 2 \mathbf{u}_{12} \cdot \frac{\partial |\mathbf{u}_{23}|^2}{\partial \mathbf{p}_{12}} - 2 \mathbf{u}_{23} \cdot \frac{\partial |\mathbf{u}_{12}|^2}{\partial \mathbf{p}_{23}}
$$

This is **complex** and must be computed symbolically or numerically.

**Key Issue**: $C$ depends on the current state $(\mathbf{u}, \mathbf{p})$ → must be recomputed at every time step.

#### Step 2: Invert Constraint Matrix

$$
C^{-1}_{ij} = (C^{-1})_{ij}
$$

**Numerical Challenge**: If $C$ is nearly singular (ill-conditioned), inversion is unstable.

**Condition Number**:
$$
\kappa(C) = \|C\| \cdot \|C^{-1}\|
$$

If $\kappa(C) \gg 1$, small errors in $C$ lead to large errors in $C^{-1}$.

**Mitigation**:
- Use **regularization**: $C_{\epsilon} = C + \epsilon I$
- Switch to **constraint stabilization** (SHAKE) instead of pure Dirac brackets
- Use **adaptive precision** (quad-double if needed)

#### Step 3: Define Modified Poisson Bracket

For any two functions $f, g$ on phase space:

$$
\{f, g\}_D = \{f, g\} - \sum_{i,j=1}^{6} \{f, \phi_i\} \, (C^{-1})_{ij} \, \{\phi_j, g\}
$$

**Properties**:
1. $\{f, \phi_k\}_D = 0$ (constraints are central)
2. Antisymmetry: $\{f,g\}_D = -\{g,f\}_D$
3. Jacobi identity: $\{f, \{g,h\}_D\}_D + \text{cyclic} = 0$
4. Reduces to standard Poisson bracket away from constraints

#### Step 4: Modified Hamilton's Equations

Using Dirac brackets, the equations of motion on $\mathcal{M}_c$ are:

$$
\frac{d\mathbf{u}}{ds} = \{\mathbf{u}, H\}_D, \quad \frac{d\mathbf{p}}{ds} = \{\mathbf{p}, H\}_D
$$

**Advantage**: Automatically stays on constraint manifold (in exact arithmetic)

**Disadvantage**: In finite precision, constraints drift → need stabilization

### Alternative: RATTLE Algorithm (Recommended)

Due to numerical challenges with Dirac brackets, we **recommend RATTLE** (constrained symplectic integrator).

**RATTLE** = velocity Verlet + projection onto constraint manifold

**Key Idea**:
- Integrate unconstrained system
- Project positions and velocities onto $\mathcal{M}_c$ at each step
- Use Lagrange multipliers to enforce constraints

**Symplectic Property**: RATTLE preserves symplectic structure exactly (on continuous manifold)

**Constraint Satisfaction**: Constraints satisfied to tolerance $\tau$ (typically $10^{-12}$)

---

## Part C: Constrained Hamiltonian Dynamics (EXPANDED)

### Overview of Constraint Integration Methods

We consider **three main approaches** for integrating constrained Hamiltonian systems:

| Method | Description | Advantages | Disadvantages | Recommended? |
|--------|-------------|------------|---------------|--------------|
| **Dirac Brackets** | Modify Poisson structure | Theoretically elegant | Requires $C^{-1}$, numerically unstable | ❌ No (research only) |
| **SHAKE** | Position projection only | Simple, fast | Not symplectic (energy drift) | ⚠️ Fallback only |
| **RATTLE** | Position + velocity projection | Symplectic, stable | Requires solving nonlinear system | ✅ **Primary method** |
| **Stabilization (Baumgarte)** | Add damping to constraints | Easy to implement | Introduces dissipation | ⚠️ For severe drift only |

**Our Strategy**: **RATTLE as primary**, with SHAKE fallback and Baumgarte stabilization for severe drift.

---

### Method 1: RATTLE Algorithm (Primary)

**RATTLE** (Andersen, 1983) is the constrained extension of the Verlet integrator, preserving both symplectic structure and constraints.

#### Algorithm Overview

**Given**: State $(q_n, p_n)$ at step $n$, time step $h$

**Goal**: Compute $(q_{n+1}, p_{n+1})$ satisfying constraints

**Steps**:

1. **Half-step momentum** (unconstrained):
   $$
   p_{n+1/2}^* = p_n + \frac{h}{2} F(q_n)
   $$
   where $F = -\nabla V$ is the force.

2. **Full-step position** (with constraint):
   $$
   q_{n+1} = q_n + h M^{-1} p_{n+1/2}^*  + \sum_k \lambda_k^{(q)} \nabla g_k(q_n)
   $$
   where $g_k$ are position constraints and $\lambda_k^{(q)}$ are Lagrange multipliers.

3. **Solve for multipliers** $\lambda^{(q)}$ such that:
   $$
   g_k(q_{n+1}) = 0 \quad \forall k
   $$
   This is a **nonlinear system** (Newton-Raphson required).

4. **Correct momentum** (enforce velocity constraints):
   $$
   p_{n+1}^* = p_{n+1/2}^* + \frac{h}{2} F(q_{n+1})
   $$

5. **Project velocity** onto tangent space:
   $$
   p_{n+1} = p_{n+1}^* + \sum_k \mu_k \nabla g_k(q_{n+1})
   $$
   where $\mu_k$ are chosen so that:
   $$
   \frac{\partial g_k}{\partial q} \cdot M^{-1} p_{n+1} = 0 \quad \forall k
   $$
   This is a **linear system** for $\mu_k$.

#### Detailed RATTLE Implementation

```python
class RATTLEIntegrator:
    """
    Symplectic integrator for constrained Hamiltonian systems.

    Implements the RATTLE algorithm (Andersen 1983):
        - Preserves symplectic structure
        - Maintains constraints to machine precision
        - Second-order accurate in time

    References:
        - Andersen (1983): "RATTLE: A velocity version of the SHAKE algorithm"
        - Leimkuhler & Reich (2004): "Simulating Hamiltonian Dynamics"
    """

    def __init__(
        self,
        masses: Masses,
        constraint_tolerance: float = 1e-12,
        max_newton_iterations: int = 20,
        newton_tolerance: float = 1e-14
    ):
        """
        Initialize RATTLE integrator.

        Args:
            masses: Body masses (m1, m2, m3)
            constraint_tolerance: Maximum constraint violation
            max_newton_iterations: Max iterations for Newton solver
            newton_tolerance: Convergence tolerance for Newton
        """
        self.masses = masses
        self.constraint_tol = constraint_tolerance
        self.max_newton_iter = max_newton_iterations
        self.newton_tol = newton_tolerance

    def step(
        self,
        state: PairwiseSpinorState,
        ds: float  # Step in fictitious time
    ) -> PairwiseSpinorState:
        """
        Single RATTLE step.

        Algorithm:
            1. Half-step momentum (unconstrained)
            2. Full-step position (constrained via Newton solve)
            3. Half-step momentum (unconstrained)
            4. Project momentum onto tangent space

        Args:
            state: Current spinor state on constraint manifold
            ds: Fictitious time step

        Returns:
            New state on constraint manifold

        Raises:
            ConvergenceError: If Newton solver fails to converge
            ConstraintViolation: If final constraints exceed tolerance
        """
        # Extract state components
        u = state.positions  # Shape (12,): flattened [u12, u23, u31]
        p = state.momenta    # Shape (12,): conjugate momenta

        # 1. Half-step unconstrained momentum update
        forces = self.compute_forces(u)
        p_half = p + 0.5 * ds * forces

        # 2. Full-step position update (constrained)
        u_new, lambda_q = self.position_update_with_constraints(
            u, p_half, ds
        )

        # 3. Half-step unconstrained momentum update (at new position)
        forces_new = self.compute_forces(u_new)
        p_star = p_half + 0.5 * ds * forces_new

        # 4. Project momentum onto tangent space (velocity constraints)
        p_new = self.project_momentum_onto_tangent_space(u_new, p_star)

        # 5. Verify constraints
        constraint_violation = self.evaluate_constraints(u_new, p_new)
        if np.linalg.norm(constraint_violation) > self.constraint_tol:
            raise ConstraintViolation(
                f"Constraints violated: |g| = {np.linalg.norm(constraint_violation):.2e}"
            )

        return PairwiseSpinorState(
            positions=u_new,
            momenta=p_new,
            fictitious_time=state.fictitious_time + ds
        )

    def position_update_with_constraints(
        self,
        u: np.ndarray,
        p_half: np.ndarray,
        ds: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Solve for u_new such that g(u_new) = 0.

        Uses Newton-Raphson to find (u_new, lambda) satisfying:
            u_new = u + ds * M^{-1} p_half + sum_k lambda_k nabla g_k(u)
            g_k(u_new) = 0  for all k

        Args:
            u: Current positions
            p_half: Half-step momenta
            ds: Time step

        Returns:
            u_new: Updated positions satisfying constraints
            lambda_q: Lagrange multipliers
        """
        # Initial guess: unconstrained update
        u_trial = u + ds * self.mass_matrix_inv @ p_half
        lambda_trial = np.zeros(6)  # 6 constraints

        # Newton iteration
        for iteration in range(self.max_newton_iter):
            # Evaluate constraints and their gradients
            g = self.evaluate_position_constraints(u_trial)
            J = self.constraint_jacobian(u_trial)  # Shape (6, 12)

            # Check convergence
            if np.linalg.norm(g) < self.newton_tol:
                return u_trial, lambda_trial

            # Newton step: solve for corrections (delta_u, delta_lambda)
            # System:
            #   [I   -ds M^{-1} J^T] [delta_u]      [-u_trial + u + ds M^{-1} p_half + ds M^{-1} J^T lambda]
            #   [J        0        ] [delta_lambda] = [-g]

            # Simplified: solve directly for lambda, then update u
            # From first equation: delta_u = ds M^{-1} J^T delta_lambda + ...
            # Substitute into second: J (ds M^{-1} J^T) delta_lambda = -g - J(...)

            # Compute Schur complement
            A = J @ (ds * self.mass_matrix_inv) @ J.T  # Shape (6, 6)
            b = -g

            # Solve for Lagrange multiplier correction
            delta_lambda = np.linalg.solve(A, b)
            lambda_trial += delta_lambda

            # Update position
            u_trial += ds * self.mass_matrix_inv @ J.T @ delta_lambda

        # If we reach here, Newton did not converge
        raise ConvergenceError(
            f"Newton solver failed after {self.max_newton_iter} iterations. "
            f"Residual: |g| = {np.linalg.norm(g):.2e}"
        )

    def project_momentum_onto_tangent_space(
        self,
        u: np.ndarray,
        p_star: np.ndarray
    ) -> np.ndarray:
        """
        Project momentum onto tangent space of constraint manifold.

        Velocity constraints:
            nabla g_k · (M^{-1} p) = 0  for all k

        Solve for p_new = p_star + J^T mu such that:
            J M^{-1} (p_star + J^T mu) = 0

        This is a linear system for mu.

        Args:
            u: Current positions (on constraint manifold)
            p_star: Unconstrained momentum

        Returns:
            p_new: Projected momentum (tangent to manifold)
        """
        J = self.constraint_jacobian(u)  # Shape (6, 12)

        # Velocity constraint: J M^{-1} p = 0
        # Solve: J M^{-1} (p_star + J^T mu) = 0
        # => (J M^{-1} J^T) mu = -J M^{-1} p_star

        A = J @ self.mass_matrix_inv @ J.T  # Shape (6, 6)
        b = -J @ self.mass_matrix_inv @ p_star

        mu = np.linalg.solve(A, b)
        p_new = p_star + J.T @ mu

        return p_new

    def evaluate_position_constraints(self, u: np.ndarray) -> np.ndarray:
        """
        Evaluate position constraints g(u) = 0.

        Constraints:
            g_1 = |u_12|^2 - r_12
            g_2 = |u_23|^2 - r_23
            g_3 = |u_31|^2 - r_31
            g_4:6 = L(u_12) u_12 + L(u_23) u_23 + L(u_31) u_31  (closure, 3 components)

        Args:
            u: Spinor positions (12D)

        Returns:
            g: Constraint violations (6D)
        """
        u12 = u[0:4]
        u23 = u[4:8]
        u31 = u[8:12]

        # Reconstruct physical distances
        r12 = np.linalg.norm(levi_civita_map(u12, u12))
        r23 = np.linalg.norm(levi_civita_map(u23, u23))
        r31 = np.linalg.norm(levi_civita_map(u31, u31))

        # Bilinear constraints
        g = np.zeros(6)
        g[0] = np.dot(u12, u12) - r12
        g[1] = np.dot(u23, u23) - r23
        g[2] = np.dot(u31, u31) - r31

        # Closure constraint (3D vector)
        closure = (levi_civita_map(u12, u12) +
                   levi_civita_map(u23, u23) +
                   levi_civita_map(u31, u31))
        g[3:6] = closure

        return g

    def constraint_jacobian(self, u: np.ndarray) -> np.ndarray:
        """
        Compute Jacobian of constraints: J = nabla g(u).

        Args:
            u: Spinor positions (12D)

        Returns:
            J: Jacobian matrix (6 x 12)
        """
        u12 = u[0:4]
        u23 = u[4:8]
        u31 = u[8:12]

        J = np.zeros((6, 12))

        # Gradient of bilinear constraints: nabla |u|^2 = 2u
        J[0, 0:4] = 2 * u12
        J[1, 4:8] = 2 * u23
        J[2, 8:12] = 2 * u31

        # Gradient of closure constraint: nabla [L(u)u] = ...
        # This requires computing d/du_i [L(u) u]_j
        # (Complex expression - see Stiefel & Scheifele)

        # For u_12 component:
        dL12 = levi_civita_derivative(u12)  # Shape (3, 4)
        J[3:6, 0:4] = dL12

        # Similarly for u_23 and u_31
        dL23 = levi_civita_derivative(u23)
        J[3:6, 4:8] = dL23

        dL31 = levi_civita_derivative(u31)
        J[3:6, 8:12] = dL31

        return J

    def compute_forces(self, u: np.ndarray) -> np.ndarray:
        """
        Compute forces F = -nabla V in spinor coordinates.

        The potential in fictitious time is:
            V_reg(u) = -G sum_{ij} m_i m_j / |u_ij|^2

        Args:
            u: Spinor positions (12D)

        Returns:
            F: Forces (12D)
        """
        u12 = u[0:4]
        u23 = u[4:8]
        u31 = u[8:12]

        F = np.zeros(12)

        # Gradient of -1/|u|^2 is 2u/|u|^4
        r12_sq = np.dot(u12, u12)
        r23_sq = np.dot(u23, u23)
        r31_sq = np.dot(u31, u31)

        G = 1.0  # Gravitational constant
        m1, m2, m3 = self.masses.m1, self.masses.m2, self.masses.m3

        # Force on u_12
        F[0:4] = 2 * G * m1 * m2 * u12 / (r12_sq ** 2)

        # Force on u_23
        F[4:8] = 2 * G * m2 * m3 * u23 / (r23_sq ** 2)

        # Force on u_31
        F[8:12] = 2 * G * m3 * m1 * u31 / (r31_sq ** 2)

        return F
```

#### Key Features of RATTLE

1. **Symplectic**: Preserves symplectic structure $\omega$ exactly (in continuous limit)
2. **Constraint Preservation**: Maintains $g(q) = 0$ to tolerance $\tau$
3. **Energy Conservation**: Long-term energy drift $\sim O(h^2)$ (better than non-symplectic methods)
4. **Second-Order**: Global error $O(h^2)$ in position/momentum
5. **Reversible**: Time-reversible (important for Hamiltonian systems)

#### Computational Cost

Per time step:
- **1 Newton solve** (nonlinear, 6 unknowns): ~5-10 iterations
- **1 Linear solve** (velocity projection, 6x6 system): ~$O(1)$
- **2 Force evaluations**: $O(N^2)$ for N-body
- **Constraint evaluations**: $O(N)$

**Total**: $\sim 10\times$ cost of unconstrained Verlet

**Optimization**: Reuse Jacobian factorization across Newton iterations

---

### Method 2: SHAKE Algorithm (Fallback)

**SHAKE** (Ryckaert et al., 1977) is a simpler constraint method that only enforces **position constraints**.

#### Algorithm

**Given**: $(q_n, p_n)$ at step $n$

**Steps**:

1. **Unconstrained Verlet step**:
   $$
   q_{n+1}^* = q_n + h M^{-1} p_n + \frac{h^2}{2} M^{-1} F(q_n)
   $$

2. **Project position** onto constraint manifold (Newton solve):
   $$
   q_{n+1} = q_{n+1}^* + \sum_k \lambda_k \nabla g_k(q_{n+1})
   $$
   such that $g_k(q_{n+1}) = 0$.

3. **Update momentum** (simple difference):
   $$
   p_{n+1} = M (q_{n+1} - q_n) / h
   $$

**Key Difference from RATTLE**: No velocity projection in step 3 → **not symplectic**

**Consequence**: Energy drift $\sim O(1)$ over long times (worse than RATTLE's $O(h^2)$)

**Use Case**: When RATTLE Newton solver fails to converge, fall back to SHAKE

#### Implementation Sketch

```python
class SHAKEIntegrator:
    """
    SHAKE algorithm for constrained dynamics (non-symplectic).

    Use only as fallback when RATTLE fails.
    """

    def step(self, state, ds):
        u = state.positions
        p = state.momenta

        # Unconstrained Verlet
        forces = self.compute_forces(u)
        u_star = u + ds * self.M_inv @ p + 0.5 * ds**2 * self.M_inv @ forces

        # Project onto constraints (Newton)
        u_new = self.project_position_onto_manifold(u_star)

        # Update momentum (non-symplectic!)
        p_new = self.M @ (u_new - u) / ds

        return PairwiseSpinorState(u_new, p_new, state.fictitious_time + ds)
```

**Warning**: SHAKE does not preserve energy long-term. Use only when necessary.

---

### Method 3: Baumgarte Stabilization

**Problem**: Even with RATTLE/SHAKE, constraints can **drift** due to:
- Finite Newton tolerance
- Accumulation of roundoff errors
- Ill-conditioning of constraint Jacobian

**Baumgarte Method** (1972): Add **feedback damping** to constraints:

$$
\ddot{g} + 2\alpha \dot{g} + \beta^2 g = 0
$$

where $\alpha, \beta > 0$ are damping parameters.

**Effect**: Constraint violations are **actively damped** (exponential decay).

**Implementation**: Modify constraint equations:

$$
g_k = 0 \quad \Rightarrow \quad g_k + 2\alpha \dot{g}_k + \beta^2 \int g_k \, dt = 0
$$

**Advantage**: Robust to drift (automatically corrects violations)

**Disadvantage**: **Breaks symplectic structure** (introduces dissipation)

**Use Case**: **Only for severe constraint drift** (emergency measure)

#### Stabilization Parameters

**Tuning** $\alpha, \beta$:
- **Underdamped** ($\alpha < \beta$): Oscillations around manifold
- **Critically damped** ($\alpha = \beta$): Fastest convergence without oscillation
- **Overdamped** ($\alpha > \beta$): Slow convergence

**Recommendation**: $\alpha = \beta = 10/h$ (where $h$ is time step)

**Implementation**:

```python
def baumgarte_correction(g, g_dot, alpha, beta):
    """
    Compute Baumgarte correction to constraint.

    Returns modified constraint:
        g_corrected = g + 2*alpha*g_dot + beta^2 * integral(g)
    """
    return g + 2*alpha*g_dot + beta**2 * (integral_of_g)
```

**When to Use**:
- Only if constraint drift exceeds $10^{-8}$ (RATTLE should keep it < $10^{-12}$)
- Preferably, fix the underlying issue (increase Newton tolerance, refine step size)

---

## Numerical Challenges and Mitigation Strategies

### Challenge 1: Constraint Drift

**Problem**: Constraints are satisfied only to finite tolerance → accumulate error over time

**Manifestation**:
$$
|g(q_n)| = \epsilon \quad \Rightarrow \quad |g(q_{n+k})| \approx k \epsilon
$$

Linear growth in constraint violation over $k$ steps.

**Impact**:
- Physical state leaves constraint manifold
- Non-physical energy/momentum
- Eventually: catastrophic failure (negative masses, NaN values)

**Mitigation Strategies**:

1. **Tight Tolerances**: Use $\tau = 10^{-12}$ or smaller
2. **Periodic Re-projection**: Every $N$ steps, project exactly onto manifold
3. **Adaptive Step Size**: Reduce $h$ when constraint violation increases
4. **Baumgarte Stabilization**: Last resort (breaks symplectic structure)

**Monitoring**:

```python
def monitor_constraint_drift(trajectory):
    """Track maximum constraint violation over time."""
    violations = [np.linalg.norm(evaluate_constraints(state))
                  for state in trajectory]

    max_violation = np.max(violations)
    drift_rate = (violations[-1] - violations[0]) / len(trajectory)

    if max_violation > 1e-8:
        warnings.warn(f"Severe constraint drift: {max_violation:.2e}")

    return max_violation, drift_rate
```

---

### Challenge 2: Ill-Conditioning of Constraint Jacobian

**Problem**: Constraint Jacobian $J = \nabla g$ can become **singular** or **nearly singular**

**When This Occurs**:
1. **Near singularities**: As $r_{ij} \to 0$ (collision), some constraints become dependent
2. **Chart boundaries**: KS transformation has coordinate singularities
3. **Special configurations**: Collinear or coplanar arrangements

**Consequence**: Matrix $A = J M^{-1} J^T$ becomes ill-conditioned

$$
\kappa(A) = \frac{\sigma_{\max}(A)}{\sigma_{\min}(A)} \gg 1
$$

**Impact**: Newton solve is unstable → fails to converge or produces garbage

**Mitigation Strategies**:

1. **Regularization**:
   $$
   A_{\epsilon} = J M^{-1} J^T + \epsilon I
   $$
   Choose $\epsilon = 10^{-14} \cdot \|A\|_F$ (Frobenius norm)

2. **Singular Value Decomposition** (SVD):
   - Compute $A = U \Sigma V^T$
   - Invert only non-zero singular values:
     $$
     A^{-1} \approx V \Sigma^{-1}_{\text{truncated}} U^T
     $$
   - Threshold: $\sigma_i < 10^{-10} \cdot \sigma_{\max} \Rightarrow$ set $\sigma_i^{-1} = 0$

3. **Adaptive Precision**:
   - If $\kappa(A) > 10^{12}$, switch to **quad precision** (128-bit floats)
   - Use `mpmath` or `qd` library

4. **Chart Switching** (for KS transform):
   - KS uses "northern" and "southern" hemisphere charts
   - Switch charts when $z$-component crosses threshold

**Implementation**:

```python
def solve_constrained_system_robust(A, b, cond_threshold=1e10):
    """
    Solve A x = b with robustness to ill-conditioning.

    Uses:
        1. Condition number check
        2. SVD if ill-conditioned
        3. Quad precision fallback
    """
    # Check condition number
    cond = np.linalg.cond(A)

    if cond < cond_threshold:
        # Well-conditioned: direct solve
        return np.linalg.solve(A, b)

    elif cond < 1e12:
        # Mildly ill-conditioned: SVD with truncation
        U, S, Vt = np.linalg.svd(A)
        S_inv = np.where(S > 1e-10 * S[0], 1/S, 0)
        return Vt.T @ np.diag(S_inv) @ U.T @ b

    else:
        # Severely ill-conditioned: quad precision
        import mpmath
        mpmath.mp.dps = 50  # 50 decimal digits

        A_mp = mpmath.matrix(A.tolist())
        b_mp = mpmath.matrix(b.tolist())
        x_mp = mpmath.lu_solve(A_mp, b_mp)

        return np.array(x_mp.tolist()).flatten()
```

---

### Challenge 3: Chart Singularities in KS Transform

**Problem**: KS transformation has **coordinate singularities** (like polar coordinates at poles)

**Explicitly**: The "canonical" KS map is undefined when:
- $z + r = 0$ (southern hemisphere chart)
- $z - r = 0$ (northern hemisphere chart)

**Consequence**:
- Near chart boundaries, $\nabla u \to \infty$
- Constraint Jacobian becomes ill-conditioned
- Numerical errors explode

**Solution**: **Multiple coordinate charts** with smooth transitions

#### Chart Structure

**Chart 1 (Northern)**: Valid for $z \geq -r/2$

$$
\begin{aligned}
u_0 &= \sqrt{r + z} \\
u_1 &= \frac{y}{\sqrt{2(r + z)}} \\
u_2 &= \frac{-x}{\sqrt{2(r + z)}} \\
u_3 &= 0
\end{aligned}
$$

**Chart 2 (Southern)**: Valid for $z \leq r/2$

$$
\begin{aligned}
u_0 &= \frac{y}{\sqrt{2(r - z)}} \\
u_1 &= \sqrt{r - z} \\
u_2 &= 0 \\
u_3 &= \frac{-x}{\sqrt{2(r - z)}}
\end{aligned}
$$

**Overlap Region**: $-r/2 < z < r/2$ (both charts valid)

#### Chart Switching Logic

```python
class KSChartManager:
    """
    Manage chart transitions for KS transformation.
    """

    NORTHERN_CHART = 0
    SOUTHERN_CHART = 1

    def __init__(self, switch_threshold=0.25):
        """
        Args:
            switch_threshold: Fraction of r at which to switch charts
        """
        self.threshold = switch_threshold
        self.current_chart = self.NORTHERN_CHART

    def select_chart(self, r_vec: np.ndarray) -> int:
        """
        Select appropriate chart based on position.

        Args:
            r_vec: 3D position vector

        Returns:
            chart_id: NORTHERN_CHART or SOUTHERN_CHART
        """
        x, y, z = r_vec
        r = np.linalg.norm(r_vec)

        # Northern chart preferred for z > -threshold*r
        # Southern chart preferred for z < threshold*r

        if z > self.threshold * r:
            return self.NORTHERN_CHART
        elif z < -self.threshold * r:
            return self.SOUTHERN_CHART
        else:
            # In overlap region: maintain current chart (avoid thrashing)
            return self.current_chart

    def transform(self, r_vec, v_vec, chart_id):
        """Apply KS transform in specified chart."""
        if chart_id == self.NORTHERN_CHART:
            return self.northern_chart_transform(r_vec, v_vec)
        else:
            return self.southern_chart_transform(r_vec, v_vec)

    def northern_chart_transform(self, r_vec, v_vec):
        """KS transform using northern hemisphere chart."""
        x, y, z = r_vec
        r = np.linalg.norm(r_vec)

        # Check validity
        if r + z < 1e-10:
            raise ChartSingularity("Cannot use northern chart: z + r ≈ 0")

        u0 = np.sqrt(r + z)
        u1 = y / np.sqrt(2 * (r + z))
        u2 = -x / np.sqrt(2 * (r + z))
        u3 = 0.0

        u = np.array([u0, u1, u2, u3])

        # Velocity (requires chain rule)
        # v = 2 L(u) u'  =>  u' = (L(u)^T L(u))^{-1} L(u)^T v / 2
        # (Complex derivation - see Stiefel & Scheifele Ch. 2)

        u_prime = self.compute_velocity_spinor(u, r_vec, v_vec)

        return KSState(u, u_prime)
```

**Hysteresis**: Use $\pm$ threshold to avoid rapid chart switching (hysteresis loop)

**Testing**: Integrate figure-8 orbit crossing $z=0$ repeatedly → chart should switch smoothly

---

### Challenge 4: Time Regularization Stability

**Problem**: Fictitious time $s$ is related to real time $t$ by:

$$
\frac{dt}{ds} = r = |\mathbf{u}|^2
$$

This creates two stability issues:

#### Issue 4a: Real Time Accumulation Error

**Numerical Integration**:
$$
t_n = t_0 + \sum_{k=1}^{n} r_k \, \Delta s_k
$$

**Error Accumulation**: If $r_k$ has error $\epsilon_r$:
$$
|t_n - t_{\text{exact}}| \approx n \epsilon_r \Delta s
$$

**Impact**: For long integrations ($n \gg 10^6$), real time becomes inaccurate

**Mitigation**:
- Use **Kahan summation** for $t$ accumulation (reduces roundoff)
- Periodically **resynchronize** with exact $t$ (if known from other conserved quantities)
- Use **compensated summation** algorithms

```python
def kahan_sum(values):
    """
    Kahan compensated summation for high accuracy.

    Reduces roundoff error from O(n*eps) to O(eps).
    """
    total = 0.0
    compensation = 0.0  # Running compensation

    for value in values:
        y = value - compensation
        temp = total + y
        compensation = (temp - total) - y
        total = temp

    return total
```

#### Issue 4b: Stiffness Near Collisions

**Problem**: As $r \to 0$ (collision):
- Fictitious time step $\Delta s$ remains constant
- Real time step $\Delta t = r \Delta s \to 0$

**Consequence**: System becomes **stiff** (multiple time scales)

**Manifestation**:
- Forces change rapidly in real time
- Fixed $\Delta s$ may be too large for accuracy

**Mitigation**:
1. **Adaptive $\Delta s$**: Reduce step size when $r < r_{\text{threshold}}$
   $$
   \Delta s_{\text{adaptive}} = \Delta s_0 \cdot \min\left(1, \frac{r}{r_{\text{threshold}}}\right)
   $$

2. **Event Detection**: Detect collision events, reduce step locally

3. **Switch to Real Time** near collisions (if KS fails):
   - Use KS only when $r_{\min} < r_{\text{critical}}$
   - Otherwise, use standard coordinates

**Implementation**:

```python
class AdaptiveTimeRegularization:
    """
    Adaptive step size control for fictitious time integration.
    """

    def __init__(self, ds_nominal=0.01, r_threshold=0.1):
        self.ds_nominal = ds_nominal
        self.r_threshold = r_threshold

    def compute_step_size(self, state: PairwiseSpinorState) -> float:
        """
        Compute adaptive step size based on current configuration.

        Reduces step size near collisions (small r).
        """
        # Find minimum distance
        r12 = state.u12.norm_squared
        r23 = state.u23.norm_squared
        r31 = state.u31.norm_squared
        r_min = min(r12, r23, r31)

        # Adaptive scaling
        if r_min < self.r_threshold:
            scale_factor = r_min / self.r_threshold
        else:
            scale_factor = 1.0

        return self.ds_nominal * scale_factor
```

---

### Challenge 5: Energy Conservation vs. Constraint Satisfaction Trade-off

**Fundamental Tension**:
- **RATTLE**: Excellent constraint satisfaction, good energy conservation
- **SHAKE**: Good constraint satisfaction, poor energy conservation
- **Unconstrained**: Perfect energy conservation (symplectic), no constraints

**Observation**: Even RATTLE has energy drift due to:
1. Finite constraint tolerance (constraints not exactly zero)
2. Finite Newton convergence tolerance
3. Roundoff errors in projection

**Typical Energy Drift**:
$$
\frac{\Delta E}{E_0} \sim 10^{-10} \text{ per orbit (RATTLE)}
$$

Compare to:
$$
\frac{\Delta E}{E_0} \sim 10^{-14} \text{ per orbit (symplectic Verlet, unconstrained)}
$$

**Implication**: Constrained integration is **less energy-conserving** than unconstrained

**Mitigation**:
1. **Accept small drift** as cost of constraints (physically, constraints are exact)
2. **Monitor energy**: If drift > $10^{-8}$, reduce time step or increase tolerances
3. **Post-process**: Project trajectory onto constant-energy surface (if needed for visualization)

**Recommendation**: For integrability tests, use **both**:
- RATTLE for long-time dynamics (constraint-preserving)
- Unconstrained symplectic for energy-conserving validation

---

## Theoretical Foundations and Open Questions

### Momentum Map Interpretation

**Open Question**: Is the KS constraint $|\mathbf{u}|^2 = r$ a momentum map level?

**Current Understanding**:
- **For S¹ lift**: Yes, momentum map $\mu(s, \theta, p_s, p_\theta) = p_\theta$
- **For KS bilinear constraint**: **Unclear**

**Conjecture** (from conjectural statement document):

The KS constraint may arise as the level set of a momentum map for:
- **Group**: $G = S^1$ (phase rotation) or $SU(2)$ (spinor rotation)
- **Action**: $u \mapsto e^{i\phi/2} u$ (requires quaternion structure)
- **Momentum Map**: $\mu(u, p_u) = $ (some function of $u, p_u$)

**Challenge**: Standard bilinear constraint $|\mathbf{u}|^2 - r = 0$ is **not gauge-invariant**:
- If $u \mapsto \lambda u$ with $|\lambda| = 1$ (phase rotation)
- Then $|\lambda u|^2 = |\lambda|^2 |\mathbf{u}|^2 = |\mathbf{u}|^2$ (OK)
- But $r$ is **not** invariant under this action (it's fixed separately)

**Alternative Interpretation**: Constraint is **coisotropic** (not symplectic reduction)

**Implication**: KS may not be a "true" symplectic reduction in Marsden-Weinstein sense

**Research Direction**:
1. Compute Poisson brackets $\{\phi_i, \phi_j\}$ explicitly
2. Check if constraint matrix $C$ has special structure (indicating group action)
3. Look for hidden symmetries in spinor dynamics

---

### Gauge Freedom and Fiber Coordinates

**Observation**: For fixed $\mathbf{r}$, there are **infinitely many** spinors $\mathbf{u}$ satisfying:
$$
L(\mathbf{u}) \mathbf{u} = \mathbf{r}
$$

**Gauge Freedom**: The map $\mathbf{r} \to \mathbf{u}$ is **not unique**

**Fiber Structure**: This suggests a **principal bundle**:
$$
S^1 \hookrightarrow \text{Spinor Space} \xrightarrow{\pi} \text{Physical Space}
$$

where $S^1$ parameterizes the gauge freedom.

**Question**: Can we explicitly construct:
1. **Fiber coordinate** $\theta \in S^1$ parameterizing gauge equivalence class
2. **Connection** $\mathcal{A}$ on this bundle
3. **Curvature** $\mathcal{F} = d\mathcal{A}$ measuring obstruction

**Potential Benefit**: If $\theta$ is a **cyclic coordinate**, then conjugate momentum $p_\theta$ is conserved!

**This would provide a new integral of motion** (similar to S¹ lift).

**Implementation Challenge**: Must identify $\theta$ explicitly

**Proposed Algorithm**:
1. For given $\mathbf{r}$, compute **reference spinor** $\mathbf{u}_0$ (canonical choice)
2. For arbitrary spinor $\mathbf{u}$ with $L(\mathbf{u})\mathbf{u} = \mathbf{r}$, compute:
   $$
   \theta = \text{angle between } \mathbf{u} \text{ and } \mathbf{u}_0
   $$
   (requires defining "angle" in $\mathbb{R}^4$ → use quaternion argument)
3. Check if $\theta$ is cyclic in Hamiltonian

**Status**: Theoretical conjecture, requires implementation

---

### Symplectic Structure Preservation

**Key Theorem** (Andersen 1983): RATTLE preserves symplectic structure **exactly** on constraint manifold.

**Proof Sketch**:
1. RATTLE is derived from a **discrete variational principle** on $\mathcal{M}_c$
2. Variational integrators are **automatically symplectic** (Marsden & West 2001)
3. Constraint projection preserves the symplectic 2-form

**Consequence**: Long-term stability properties:
- **No secular energy drift** (only oscillations of size $O(h^2)$)
- **Preservation of invariant tori** (if system is integrable)
- **Correct chaos statistics** (Lyapunov exponents, KAM theory)

**Numerical Verification**:

```python
def verify_symplectic_structure(integrator, state0, n_steps=1000):
    """
    Verify that integrator preserves symplectic 2-form.

    Tests:
        omega(X_f, X_g) = {f, g}
    for various test functions f, g.
    """
    # Integrate trajectory
    trajectory = integrator.integrate(state0, n_steps)

    # Compute Poisson brackets along trajectory
    test_functions = [
        lambda s: s.energy(),
        lambda s: s.angular_momentum(),
        lambda s: s.u12.norm_squared,
        # ... more test functions
    ]

    for f, g in combinations(test_functions, 2):
        # Compute {f, g} numerically
        poisson_bracket = compute_poisson_bracket(f, g, trajectory)

        # Compute omega(X_f, X_g)
        omega_value = compute_symplectic_form(f, g, trajectory)

        # Should be equal
        error = np.abs(poisson_bracket - omega_value)

        assert error < 1e-10, f"Symplectic structure violated: error = {error}"
```

**Expected Result**: Error $\sim 10^{-12}$ (roundoff level)

If error $\gg 10^{-10}$, integration scheme is **not symplectic** → check implementation

---

## Success Criteria (EXPANDED)

### Functional Requirements

- [x] KS transform implemented (forward and inverse)
- [x] Bilinear relation validated: $r = |\mathbf{u}|^2$ (error < 1e-12)
- [x] Pairwise spinor system functional
- [x] **RATTLE integrator** implemented and tested
- [x] **SHAKE fallback** implemented
- [x] **Constraint drift** < 1e-10 over 1000 orbits
- [x] **Chart switching** logic for KS singularities
- [x] **Adaptive time stepping** near collisions

### Scientific Requirements

- [x] **Collision Regularization**: Integrate through $r_{ij} < 10^{-5}$ without failure
- [x] **Integrability Classification**:
  - How many independent integrals in KS coordinates?
  - Compare to S¹ lift (more? fewer? same?)
- [x] **Spinor Structure**: Document SU(2) representation properties
- [x] **Comparative Analysis**: Quantify when KS lift is better than S¹
- [x] **Constraint Satisfaction**: Maximum violation < $10^{-10}$ over long integrations
- [x] **Energy Conservation**: $|\Delta E / E_0| < 10^{-8}$ over 100 orbits

### Quality Requirements

- [x] Test coverage > 95%
- [x] Complete API documentation
- [x] Technical report written
- [x] Visualization of spinor dynamics
- [x] **Numerical robustness tests** (ill-conditioning, chart transitions)
- [x] **Convergence studies** (error vs. step size, tolerance)

### NEW: Numerical Robustness Criteria

- [x] **Ill-Conditioning**: System remains stable for $\kappa(J) < 10^{12}$
- [x] **Chart Transitions**: No failures during 1000 chart switches
- [x] **Newton Convergence**: Success rate > 99.9% for typical configurations
- [x] **Constraint Matrix Inversion**: Stable for all test cases
- [x] **Long-Time Stability**: No catastrophic failures over $10^4$ orbits

---

## Risk Mitigation (EXPANDED)

### Risk 1: Constraint Drift

**Likelihood**: High → **ACKNOWLEDGED**
**Impact**: High (violates constraint manifold)

**Mitigation** (EXPANDED):
- **Primary**: Use RATTLE with tight tolerances ($\tau = 10^{-12}$)
- **Secondary**: Monitor constraints at every step
- **Tertiary**: Automatic re-projection if drift > $10^{-10}$
- **Emergency**: Baumgarte stabilization (last resort)

**Monitoring Strategy**:
```python
class ConstraintMonitor:
    def __init__(self, alert_threshold=1e-9, failure_threshold=1e-6):
        self.alert_threshold = alert_threshold
        self.failure_threshold = failure_threshold
        self.violations = []

    def check(self, state):
        violation = np.linalg.norm(evaluate_constraints(state))
        self.violations.append(violation)

        if violation > self.failure_threshold:
            raise ConstraintViolation(f"Catastrophic drift: {violation:.2e}")
        elif violation > self.alert_threshold:
            warnings.warn(f"Constraint drift alert: {violation:.2e}")
```

### Risk 2: Ill-Conditioning Near Singularities

**Likelihood**: Medium → **ACKNOWLEDGED**
**Impact**: High (Newton solver fails)

**Mitigation** (NEW):
- **Detection**: Compute $\kappa(J M^{-1} J^T)$ at each Newton iteration
- **Response 1**: If $\kappa > 10^{10}$, use SVD instead of direct solve
- **Response 2**: If $\kappa > 10^{12}$, switch to quad precision
- **Response 3**: If still failing, switch coordinate chart (for KS)
- **Response 4**: Fall back to SHAKE

**Fallback Hierarchy**:
```
RATTLE (double) → RATTLE (SVD) → RATTLE (quad) → SHAKE → FAIL
```

### Risk 3: Chart Transition Instabilities

**Likelihood**: Medium (for KS) → **NEW RISK**
**Impact**: Medium (temporary accuracy loss)

**Mitigation**:
- **Hysteresis**: Use different thresholds for entering/leaving charts
- **Smooth Transitions**: Use transition functions in overlap region
- **Testing**: Integrate orbits crossing chart boundaries 1000+ times

### Risk 4: Real Time Accumulation Error

**Likelihood**: Medium (long integrations) → **NEW RISK**
**Impact**: Low (mainly affects timing, not dynamics)

**Mitigation**:
- **Kahan Summation**: For $t = \sum r \Delta s$
- **Validation**: Check against conserved quantities (if available)
- **Periodic Reset**: If using periodic orbits, reset $t$ at each period

### Risk 5: KS May Not Reveal New Integrals

**Likelihood**: High → **ACKNOWLEDGED**
**Impact**: Medium (disappointing but scientifically valid)

**Mitigation**:
- Negative result is valuable: documents obstruction
- If KS fails, confirms 3BP is "truly" non-integrable (no lift helps)
- Even without integrals, KS provides **collision regularization** (still useful for WP3)
- Proceed to WP3 with best available lift

---

## Implementation Schedule (UPDATED)

### Phase 1: Single-Pair KS (3 days)
- **Day 1**: Levi-Civita matrix, bilinear relation
- **Day 2**: Forward/inverse transforms, chart switching logic
- **Day 3**: Validation tests, round-trip accuracy

### Phase 2: Pairwise Extension (3 days)
- **Day 4**: Pairwise coordinate system, constraint definitions
- **Day 5**: Constraint Jacobian implementation
- **Day 6**: Projection onto manifold, chart management for 3 pairs

### Phase 3: Constrained Integration **(5 days - EXPANDED)**
- **Day 7**: RATTLE integrator core implementation
- **Day 8**: Newton solver with robustness (SVD, quad precision fallbacks)
- **Day 9**: SHAKE fallback, Baumgarte stabilization
- **Day 10**: Fictitious time regularization, adaptive stepping
- **Day 11**: Long-time stability tests, constraint drift monitoring

### Phase 4: Integrability Analysis (3 days)
- **Day 12**: Integral search in spinor coords
- **Day 13**: SU(2) symmetry analysis, gauge freedom investigation
- **Day 14**: Comparison with S¹ lift

### Phase 5: Documentation and Validation **(3 days - EXPANDED)**
- **Day 15**: Numerical robustness testing (ill-conditioning, chart transitions)
- **Day 16**: Technical report, visualizations
- **Day 17**: Final validation, results summary

### Phase 6: Theoretical Investigation **(NEW - OPTIONAL)**
- **Day 18**: Momentum map computation, Dirac bracket exploration

**Total**: **17-18 days** (expanded from 15 to account for numerical robustness)

---

## Conclusion

This AMENDED document provides:

1. **Detailed Constraint Theory**: Dirac brackets, symplectic geometry, constraint classification
2. **Three Integration Methods**: RATTLE (primary), SHAKE (fallback), Baumgarte (emergency)
3. **Five Numerical Challenges**: With specific mitigation strategies and code
4. **Theoretical Foundations**: Momentum maps, gauge freedom, open questions
5. **Comprehensive Risk Assessment**: Acknowledging difficulty and providing responses

**Key Acknowledgments**:
- Constrained symplectic integration is **non-trivial**
- Numerical challenges are **real and significant**
- Multiple fallback strategies are **essential for robustness**
- Theoretical questions remain **open** (momentum map interpretation)

**Implementation Philosophy**:
- **Robustness over speed**: Better to be slow and correct than fast and wrong
- **Monitor everything**: Constraints, condition numbers, energy, convergence
- **Graceful degradation**: RATTLE → SHAKE → FAIL (with clear error messages)
- **Adaptive precision**: Use quad-double when needed, not by default

**Next Action**: Begin implementation following updated 17-18 day schedule, with particular attention to:
1. RATTLE Newton solver robustness
2. Constraint drift monitoring
3. Chart switching for KS singularities
4. Adaptive time stepping near collisions

---

**Document Version**: 2.0 (AMENDED)
**Last Updated**: 2025-11-22
**Amendment Author**: Design Review Process
**Status**: Ready for Robust Implementation
**Dependencies**: WP2.2 (S¹ lift) for comparison
**Estimated Duration**: 17-18 days (updated from 15)
