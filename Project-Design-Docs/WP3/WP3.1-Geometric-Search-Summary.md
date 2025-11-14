# WP 3.1: Deterministic Geometric Search (Killing Fields/Tensors)
## Complete Implementation Summary

**Duration**: 15-18 days
**Approach**: Direct numerical solution of Killing PDEs
**Goal**: Discover conserved quantities via geometric symmetries

---

## Overview

WP 3.1 searches for hidden conserved quantities by solving the Killing field and Killing tensor equations on the lifted manifolds constructed in WP2. This is a deterministic, geometry-driven approach that directly targets the mathematical structures associated with integrability.

### Four-Task Pipeline

```
Task 3.1.1: Lifted JM Metric (3-4 days)
    ↓ Provides metric tensor g_JM
Task 3.1.2: Killing PDE Formulation (2-3 days)
    ↓ Provides discretized linear systems
Task 3.1.3: Numerical PDE Solution (5-6 days)
    ↓ Solves for Killing fields/tensors
Task 3.1.4: Integral Conversion & Filtering (3-4 days)
    ↓ Outputs candidate conserved quantities
```

---

## Task Summaries

### Task 3.1.1: Lifted JM Metric Implementation
**Deliverables**:
- JM metric on S¹ bundle: $g_{JM}^{(S^1)}(s, \theta) = 2(E-V)g_{\text{lift}}$
- JM metric on KS manifold: $g_{JM}^{(KS)}(\mathbf{u}) = 2(E-V)M(\mathbf{u})$
- Validation: Kepler limit, equal mass symmetry, positive definiteness

**Key Files**:
- `src/python/geometry/lifted_jm_metric.py`
- `src/python/geometry/s1_bundle.py`
- `src/python/geometry/ks_spinor.py`

---

### Task 3.1.2: Killing PDE Formulation
**Deliverables**:
- Christoffel symbols (symbolic and numerical)
- Killing vector PDE: $\nabla_{(i}K_{j)} = 0$ (n(n+1)/2 equations)
- Killing tensor PDE: $\nabla_{(k}K_{ij)} = 0$ (n(n+1)(n+2)/6 equations)
- Discretized sparse linear systems

**Key Files**:
- `src/python/pde/christoffel_symbols.py`
- `src/python/pde/killing_equations.py`
- `src/python/pde/mesh_discretization.py`

---

### Task 3.1.3: Numerical Solution
**Deliverables**:
- Sparse linear system solver (scipy.sparse.linalg or custom)
- Regularization techniques (smoothness, physical priors)
- Solution post-processing (eigenvalue analysis, filtering)
- Convergence analysis (mesh refinement)

**Key Files**:
- `src/python/pde/killing_solver.py`
- `src/python/pde/regularization.py`
- `src/python/analysis/solution_analysis.py`

**Numerical Strategy**:
1. Solve homogeneous system: $\mathbf{A}\mathbf{K} = \mathbf{0}$
2. Find null space (non-trivial solutions)
3. Apply regularization to select physical solutions
4. Verify convergence with mesh refinement

---

### Task 3.1.4: Integral Conversion & Filtering
**Deliverables**:
- Conversion: Killing fields → conserved quantities
- Triviality filter: Remove known integrals (E, L, $p_\theta$)
- Independence test: Verify functional independence (Jacobian rank)
- Conservation verification: Numerical time-evolution test

**Key Files**:
- `src/python/analysis/integral_from_killing.py`
- `src/python/analysis/triviality_filter.py`
- `src/python/analysis/independence_test.py`

**Filtering Pipeline**:
```
Raw Killing fields
    ↓ Convert to integrals I_K
Candidate integrals
    ↓ Remove trivial (E, L, p_θ, coordinates)
Non-trivial candidates
    ↓ Test functional independence
Independent candidates
    ↓ Verify conservation (numerical integration)
Final candidates → WP 3.3
```

---

## Expected Outcomes

### Best Case: Non-Trivial Killing Fields Discovered
- **S¹ Bundle**: Find additional Killing vectors beyond known ones
- **KS Manifold**: Discover Killing tensors analogous to Runge-Lenz
- **Result**: Analytical conserved quantities ready for WP4 validation

### Moderate Case: Only Low-Degree Fields
- **Find**: Killing vectors but no Killing tensors
- **Or**: Degree-2 polynomial integrals only
- **Result**: Partial integrability, still valuable

### Negative Case: No Non-Trivial Solutions
- **Rigorous bounds**: Establish degree N limit (e.g., "no polynomial integrals up to degree 4")
- **Scientific value**: Rules out simple hidden symmetries
- **Action**: Rely on WP 3.2 (ML) to find complex forms

---

## Technical Challenges

### Challenge 1: Computational Cost
**Problem**: PDEs are overdetermined and high-dimensional
- S¹ bundle: 10 equations, 4 unknowns, 4D mesh
- KS manifold: 45 equations, 9 unknowns, 9D mesh

**Solution**:
- Adaptive mesh refinement (focus on classically allowed regions)
- Symmetry reduction (permutation groups)
- Parallel computation (distribute over mesh regions)

### Challenge 2: Singular Regions
**Problem**: Metric blows up near collisions ($r_{ij} \to 0$)

**Solution**:
- Exclude collision regions (use KS regularization instead)
- Regularization parameter $\epsilon$ (softened potential)
- Focus on bounded orbits with minimum distance constraints

### Challenge 3: Null Space Degeneracy
**Problem**: Homogeneous system may have many trivial solutions

**Solution**:
- Gauge fixing (e.g., normalize Killing fields)
- Physical priors (smoothness regularization)
- Post-hoc filtering (triviality tests)

---

## Validation Strategy

### Level 1: Code Validation
- **Unit tests**: Each function (Christoffel, discretization, solver)
- **Integration tests**: Full pipeline on known cases (sphere, Kepler)

### Level 2: Mathematical Validation
- **Killing equation satisfaction**: Residual $< 10^{-8}$ on mesh
- **Mesh convergence**: Solution stable under refinement
- **Symmetry consistency**: Respect physical invariances

### Level 3: Physical Validation
- **Conservation**: $\frac{dI_K}{dt} < 10^{-6}$ on test trajectories
- **Independence**: Jacobian rank increases by 1
- **Generalization**: Works across parameter space

---

## Computational Resources

**Estimated Requirements**:
- **Memory**:
  - S¹ bundle: ~100 MB (10^4 mesh points)
  - KS manifold: ~10 GB (10^5 mesh points)
- **CPU Time**:
  - Mesh generation: 1-10 minutes
  - PDE assembly: 10-60 minutes
  - Solver: 1-10 hours (depending on preconditioner)
- **Storage**: ~1 GB for solution cache and visualization

**Optimization**:
- Use sparse matrix formats (CSR/CSC)
- GPU acceleration for matrix operations (CuPy/JAX)
- Parallel mesh computation (multiprocessing/MPI)

---

## Integration with Other WP3 Tasks

### Feed into WP 3.2 (ML)
- Use discovered Killing fields as **architectural priors** for HNN
- Constrain ML search space using geometric results
- If no fields found → ML explores without geometric guidance

### Feed into WP 3.3 (Symbolic Regression)
- Numerical Killing fields → symbolic basis functions
- Guide polynomial search space
- Validate ML discoveries against geometric predictions

---

## Deliverables Summary

### Code (4 main modules)
- [ ] `lifted_jm_metric.py` - Metric computation on lifts
- [ ] `killing_equations.py` - PDE formulation
- [ ] `killing_solver.py` - Numerical solution
- [ ] `integral_from_killing.py` - Conversion and filtering

### Documentation
- [ ] 4 detailed task implementation plans (✓ completed)
- [ ] API documentation (Sphinx)
- [ ] Technical report: "Geometric Search Results" (15-20 pages)
- [ ] Visualization gallery (Killing field streamlines, metric landscapes)

### Scientific Outputs
- [ ] List of candidate Killing fields (if found)
- [ ] Corresponding conserved quantities
- [ ] Negative results (if no non-trivial fields exist)
- [ ] Bounds on polynomial degree

---

## Success Metrics

**Minimum Success**:
- [ ] All four tasks implemented and tested
- [ ] Code validated on known cases (sphere, Kepler)
- [ ] Search completed to specified degree/resolution
- [ ] Negative result documented (if applicable)

**Target Success**:
- [ ] At least one non-trivial Killing vector discovered
- [ ] Conservation verified: $|\Delta I_K| / |I_K| < 10^{-6}$
- [ ] Functional independence confirmed
- [ ] Ready for WP4 validation

**Stretch Success**:
- [ ] Multiple independent integrals found
- [ ] Killing tensors (quadratic integrals) discovered
- [ ] Analytical expressions derived
- [ ] Universal across parameter space

---

## Risk Mitigation

| Risk | Probability | Mitigation |
|------|------------|------------|
| No solutions exist | Medium (40%) | Document negative result, proceed to ML |
| Computational cost too high | Low (20%) | Reduce mesh resolution, focus on S¹ only |
| Numerical instabilities | Medium (30%) | Adaptive precision, regularization |
| Solutions are trivial | Medium (30%) | Rigorous filtering pipeline |

---

## Timeline

**Week 1**: Tasks 3.1.1 + 3.1.2 (Metric + PDE formulation)
**Week 2**: Task 3.1.3 (Numerical solution - S¹ bundle)
**Week 3**: Task 3.1.3 (Numerical solution - KS manifold, if needed)
**Week 4**: Task 3.1.4 (Integral conversion and filtering)

**Total**: 15-18 days with flexibility based on results

---

## References

1. Benenti, S. "Intrinsic characterization of variable separation" (2002)
2. Kalnins et al., "Tools for verifying superintegrability" (2010)
3. Hauser & Malhiot, "Killing tensors in spacetimes" (1975)
4. Pettini, M. *Geometry and Topology in Hamiltonian Dynamics* (2007)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Complete Planning - Ready for Implementation
