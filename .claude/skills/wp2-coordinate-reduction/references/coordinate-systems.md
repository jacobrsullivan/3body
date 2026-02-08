# Coordinate Systems Reference

Complete description of coordinate systems used in three-body reduction.

## Table of Contents

1. [Cartesian Coordinates](#cartesian-coordinates)
2. [Jacobi Coordinates](#jacobi-coordinates)
3. [Shape Space Coordinates](#shape-space-coordinates)
4. [Transformation Formulas](#transformation-formulas)
5. [Metric Tensors](#metric-tensors)

---

## Cartesian Coordinates

### Definition

Standard inertial frame coordinates for three bodies:

```
State = (r₁, r₂, r₃, p₁, p₂, p₃) ∈ ℝ¹⁸

where:
  rᵢ = (xᵢ, yᵢ, zᵢ) ∈ ℝ³  position of body i
  pᵢ = mᵢ vᵢ ∈ ℝ³         momentum of body i
```

### Kinetic Energy

```
T = Σᵢ |pᵢ|²/(2mᵢ) = Σᵢ ½ mᵢ |vᵢ|²
```

### Potential Energy

```
V = -G m₁m₂/|r₁-r₂| - G m₂m₃/|r₂-r₃| - G m₃m₁/|r₃-r₁|
```

(We set G = 1 in normalized units.)

### Symplectic Form

```
ω = Σᵢ dpᵢ ∧ drᵢ = Σᵢ Σⱼ dp_{ij} ∧ dr_{ij}
```

### Angular Momentum

```
L = Σᵢ rᵢ × pᵢ
```

---

## Jacobi Coordinates

### Definition

Hierarchical coordinates that automatically satisfy COM constraint:

```
Jacobi vectors:
  ρ₁ = r₂ - r₁                        (relative position of 2 wrt 1)
  ρ₂ = r₃ - (m₁r₁ + m₂r₂)/(m₁+m₂)    (position of 3 wrt COM of 1,2)

Jacobi momenta:
  π₁ = μ₁ ρ̇₁    where μ₁ = m₁m₂/(m₁+m₂)
  π₂ = μ₂ ρ̇₂    where μ₂ = m₃(m₁+m₂)/(m₁+m₂+m₃)
```

### Reduced Masses

```python
def compute_reduced_masses(masses):
    m1, m2, m3 = masses
    M = m1 + m2 + m3
    
    # First Jacobi pair
    mu1 = m1 * m2 / (m1 + m2)
    
    # Second Jacobi pair (body 3 vs COM of 1,2)
    mu2 = m3 * (m1 + m2) / M
    
    return mu1, mu2
```

### Inverse Transformation

From Jacobi back to Cartesian:

```python
def jacobi_to_cartesian(rho1, rho2, pi1, pi2, masses):
    m1, m2, m3 = masses
    M = m1 + m2 + m3
    M12 = m1 + m2
    
    # Positions (assuming COM at origin)
    r1 = -m2/M12 * rho1 - m3/M * rho2
    r2 = m1/M12 * rho1 - m3/M * rho2
    r3 = M12/M * rho2
    
    # Momenta
    mu1, mu2 = compute_reduced_masses(masses)
    v1 = pi1 / mu1
    v2 = pi2 / mu2
    
    p1 = m1 * (-m2/M12 * v1 - m3/M * v2)
    p2 = m2 * (m1/M12 * v1 - m3/M * v2)
    p3 = m3 * M12/M * v2
    
    return (r1, r2, r3), (p1, p2, p3)
```

### Kinetic Energy in Jacobi

```
T = |π₁|²/(2μ₁) + |π₂|²/(2μ₂)
```

This is diagonal in Jacobi coordinates!

### Angular Momentum

```
L = ρ₁ × π₁ + ρ₂ × π₂
```

---

## Shape Space Coordinates

### Definition

Pairwise distances (invariant under rigid motions):

```
Shape coordinates: (r₁₂, r₂₃, r₃₁)

where:
  r₁₂ = |r₂ - r₁|
  r₂₃ = |r₃ - r₂|
  r₃₁ = |r₁ - r₃|
```

### Triangle Inequality

Valid shapes must satisfy:

```
|rᵢⱼ - rⱼₖ| < rₖᵢ < rᵢⱼ + rⱼₖ
```

for all permutations (i,j,k) of (1,2,3).

### Shape Space Geometry

The shape space is the interior of a simplex:

```
S = {(r₁₂, r₂₃, r₃₁) : triangle inequalities satisfied}
```

Boundary ∂S corresponds to:
- Collinear configurations (one distance = sum of others)
- Collision configurations (one distance = 0)

### From Jacobi to Shape

```python
def jacobi_to_shape(rho1, rho2, masses):
    m1, m2, m3 = masses
    M12 = m1 + m2
    
    # Reconstruct Cartesian positions (COM = 0)
    r1 = -m2/M12 * rho1 - m3/sum(masses) * rho2
    r2 = m1/M12 * rho1 - m3/sum(masses) * rho2
    r3 = M12/sum(masses) * rho2
    
    # Pairwise distances
    r12 = np.linalg.norm(r2 - r1)
    r23 = np.linalg.norm(r3 - r2)
    r31 = np.linalg.norm(r1 - r3)
    
    return np.array([r12, r23, r31])
```

### Shape Momenta

The conjugate momenta to shape coordinates are more complex:

```python
def compute_shape_momenta(rho1, rho2, pi1, pi2, masses):
    """
    Compute momenta conjugate to shape coordinates.
    
    These are related to radial velocities of the pairwise distances.
    """
    # Get positions
    r1, r2, r3 = jacobi_to_positions(rho1, rho2, masses)
    
    # Get velocities
    v1, v2, v3 = jacobi_to_velocities(pi1, pi2, masses)
    
    # Radial momenta
    # p_rij = μij * d(rij)/dt = μij * (rj - ri)·(vj - vi) / rij
    
    r12_vec = r2 - r1
    r23_vec = r3 - r2
    r31_vec = r1 - r3
    
    r12 = np.linalg.norm(r12_vec)
    r23 = np.linalg.norm(r23_vec)
    r31 = np.linalg.norm(r31_vec)
    
    r12_dot = np.dot(r12_vec, v2 - v1) / r12
    r23_dot = np.dot(r23_vec, v3 - v2) / r23
    r31_dot = np.dot(r31_vec, v1 - v3) / r31
    
    # Reduced masses for pairs
    mu12 = masses[0] * masses[1] / (masses[0] + masses[1])
    mu23 = masses[1] * masses[2] / (masses[1] + masses[2])
    mu31 = masses[2] * masses[0] / (masses[2] + masses[0])
    
    p12 = mu12 * r12_dot
    p23 = mu23 * r23_dot
    p31 = mu31 * r31_dot
    
    return np.array([p12, p23, p31])
```

---

## Transformation Formulas

### Complete Pipeline

```python
class CoordinateTransformer:
    """Transform between all coordinate systems."""
    
    def __init__(self, masses):
        self.masses = masses
        self.M = sum(masses)
        self.mu1, self.mu2 = compute_reduced_masses(masses)
        
    def cartesian_to_jacobi(self, positions, momenta):
        """(r₁,r₂,r₃,p₁,p₂,p₃) → (ρ₁,ρ₂,π₁,π₂)"""
        r1, r2, r3 = positions
        p1, p2, p3 = momenta
        m1, m2, m3 = self.masses
        
        # Jacobi vectors
        rho1 = r2 - r1
        rho2 = r3 - (m1*r1 + m2*r2)/(m1+m2)
        
        # Jacobi momenta (requires velocity transformation)
        v1, v2, v3 = p1/m1, p2/m2, p3/m3
        
        vrho1 = v2 - v1
        vrho2 = v3 - (m1*v1 + m2*v2)/(m1+m2)
        
        pi1 = self.mu1 * vrho1
        pi2 = self.mu2 * vrho2
        
        return rho1, rho2, pi1, pi2
        
    def jacobi_to_cartesian(self, rho1, rho2, pi1, pi2):
        """(ρ₁,ρ₂,π₁,π₂) → (r₁,r₂,r₃,p₁,p₂,p₃)"""
        # Implementation as above
        pass
        
    def jacobi_to_shape(self, rho1, rho2, pi1, pi2):
        """(ρ₁,ρ₂,π₁,π₂) → (r₁₂,r₂₃,r₃₁,p₁₂,p₂₃,p₃₁)"""
        distances = jacobi_to_shape(rho1, rho2, self.masses)
        momenta = compute_shape_momenta(rho1, rho2, pi1, pi2, self.masses)
        return distances, momenta
        
    def cartesian_to_shape(self, positions, momenta):
        """Direct Cartesian to shape."""
        rho1, rho2, pi1, pi2 = self.cartesian_to_jacobi(positions, momenta)
        return self.jacobi_to_shape(rho1, rho2, pi1, pi2)
```

---

## Metric Tensors

### Cartesian Metric

Mass-weighted Euclidean:

```
g_cart = diag(m₁, m₁, m₁, m₂, m₂, m₂, m₃, m₃, m₃)
```

Kinetic energy: T = ½ g_cart(v, v)

### Jacobi Metric

Block diagonal in Jacobi coordinates:

```
g_jacobi = diag(μ₁, μ₁, μ₁, μ₂, μ₂, μ₂)
```

Kinetic energy: T = ½ g_jacobi(ρ̇, ρ̇)

### Shape Metric

More complex—depends on configuration:

```
g_shape = f(r₁₂, r₂₃, r₃₁, masses)
```

The explicit form requires computing the Jacobian of the shape → Jacobi map.

```python
def shape_metric(shape_point, masses):
    """
    Compute metric tensor on shape space.
    
    This is the induced metric from the Jacobi kinetic metric.
    """
    r12, r23, r31 = shape_point
    
    # The metric involves the area of the triangle
    # and the masses...
    
    # Heron's formula for area
    s = (r12 + r23 + r31) / 2
    A = np.sqrt(s * (s-r12) * (s-r23) * (s-r31))
    
    # Metric components (simplified form)
    g = np.zeros((3, 3))
    # ... complex expression involving masses and geometry
    
    return g
```

---

## References

- Littlejohn, R.G. & Reinsch, M. (1997). "Gauge fields in the separation of rotations and internal motions"
- Hsiang, W.-Y. (1995). "Geometric study of the three-body problem"
- Iwai, T. (1987). "A geometric setting for classical molecular dynamics"
