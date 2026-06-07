# Kovacic Algorithm

Algorithm for determining the differential Galois group of second-order linear ODEs.

## Overview

Kovacic's algorithm (1986) is a complete decision procedure for determining whether a second-order linear ODE has Liouvillian solutions and, if so, computing them. It also determines the structure of the differential Galois group.

## Problem Statement

Given a second-order linear ODE:

```
y'' + a(x)y' + b(x)y = 0
```

where a(x), b(x) are rational functions, determine:
1. Whether solutions are Liouvillian (expressible via integrals, exponentials, algebraic operations)
2. The structure of the differential Galois group G
3. Explicit solutions when they exist

## Reduced Form

First, transform to **reduced form** by eliminating the y' term:

```
y = z · exp(-½∫a dx)
```

This gives:

```
z'' = r(x)z    where    r = b - ½a' - ¼a²
```

The Galois group of the reduced equation equals that of the original.

## The Four Cases

Kovacic identified four mutually exclusive cases based on the structure of G ⊆ SL(2, ℂ):

### Case 1: Triangular Group

**Condition**: G is conjugate to a subgroup of:
```
{ [a  b]  : a ∈ ℂ*, b ∈ ℂ }
  [0 1/a]
```

**Galois group**: G⁰ is abelian (diagonal or unipotent)

**Solution structure**: y = exp(∫ω dx) where ω is algebraic over ℂ(x)

### Case 2: Dihedral Group

**Condition**: G is conjugate to a subgroup of:
```
D_∞ = { diagonal and anti-diagonal matrices in SL(2,ℂ) }
```

**Galois group**: G⁰ is either {±I} or ℂ* (abelian)

**Solution structure**: y² ∈ ℂ(x) (solutions are square roots of rational functions)

### Case 3: Finite Primitive Group

**Condition**: G is finite and primitive (not reducible to Cases 1 or 2)

**Possible groups**: Tetrahedral (A₄), Octahedral (S₄), Icosahedral (A₅)

**Galois group**: G⁰ = {I} (trivial identity component, hence abelian)

**Solution structure**: Algebraic solutions

### Case 4: Full SL(2, ℂ)

**Condition**: None of Cases 1-3 apply

**Galois group**: G = SL(2, ℂ), G⁰ = SL(2, ℂ) (**non-abelian**)

**Solution structure**: No Liouvillian solutions

## Algorithm Implementation

### Step 1: Compute Poles and Orders

```python
def analyze_poles(r_rational):
    """
    Find poles of r(x) and classify by order.

    Returns:
        poles: List of (location, order) tuples
        infinity_order: Order of pole at infinity
    """
    # Factor numerator and denominator
    num, den = r_rational.as_numer_denom()

    poles = []
    # Find zeros of denominator
    roots = sp.solve(den, x)
    for root in roots:
        order = sp.Poly(den, x).order(root)
        poles.append((root, order))

    # Order at infinity
    deg_num = sp.degree(num, x) if num != 0 else -float('inf')
    deg_den = sp.degree(den, x) if den != 0 else 0
    infinity_order = deg_num - deg_den + 2

    return poles, infinity_order
```

### Step 2: Compute E-Sets

For each case, compute the set E of possible exponent differences:

```python
def compute_e_sets(poles, infinity_order, case):
    """
    Compute possible exponent sets E for given case.

    The exponents come from local behavior at poles.
    """
    E_sets = {'poles': {}, 'infinity': None}

    for pole, order in poles:
        if case == 1:
            # Case 1: E contains specific values based on pole order
            if order == 1:
                E = {1}
            elif order == 2:
                # Compute from local expansion
                E = compute_case1_exponents(pole, order)
            else:
                E = {order}
        elif case == 2:
            E = compute_case2_exponents(pole, order)
        elif case == 3:
            E = compute_case3_exponents(pole, order)

        E_sets['poles'][pole] = E

    E_sets['infinity'] = compute_infinity_exponents(infinity_order, case)

    return E_sets
```

### Step 3: Search for Solutions

```python
def kovacic_search(r_rational, case, E_sets):
    """
    Search for solution in given case.

    Parameters:
        r_rational: Coefficient r(x) as SymPy rational function
        case: 1, 2, or 3
        E_sets: Exponent sets from Step 2

    Returns:
        solution if found, None otherwise
    """
    x = sp.Symbol('x')

    # Enumerate possible exponent combinations
    for exponent_choice in iterate_exponent_choices(E_sets):
        # Compute degree bound for polynomial
        d = compute_degree_bound(exponent_choice)

        if d < 0:
            continue  # No valid polynomial

        # Build ansatz
        if case == 1:
            # y = exp(∫ω dx) where ω = P/Q for rational P, Q
            omega = build_case1_ansatz(exponent_choice, d)
        elif case == 2:
            # y² = rational function
            omega = build_case2_ansatz(exponent_choice, d)
        elif case == 3:
            # Algebraic solution of specific degree
            omega = build_case3_ansatz(exponent_choice, d)

        # Substitute and solve for coefficients
        solution = solve_for_coefficients(omega, r_rational)

        if solution is not None:
            return solution

    return None
```

### Main Algorithm

```python
def kovacic_algorithm(a_coeff, b_coeff):
    """
    Apply Kovacic algorithm to y'' + a(x)y' + b(x)y = 0.

    Returns:
        KovacicResult with case, galois_group, is_abelian, solution
    """
    x = sp.Symbol('x')

    # Convert to reduced form: z'' = r(x)z
    r = b_coeff - sp.Rational(1,2)*sp.diff(a_coeff, x) - sp.Rational(1,4)*a_coeff**2
    r = sp.simplify(r)

    # Analyze poles
    poles, inf_order = analyze_poles(r)

    # Try Case 1
    E1 = compute_e_sets(poles, inf_order, case=1)
    sol1 = kovacic_search(r, case=1, E_sets=E1)
    if sol1 is not None:
        return KovacicResult(
            case=1,
            galois_group='triangular',
            is_abelian=True,
            solution=sol1
        )

    # Try Case 2
    E2 = compute_e_sets(poles, inf_order, case=2)
    sol2 = kovacic_search(r, case=2, E_sets=E2)
    if sol2 is not None:
        return KovacicResult(
            case=2,
            galois_group='dihedral',
            is_abelian=True,
            solution=sol2
        )

    # Try Case 3
    E3 = compute_e_sets(poles, inf_order, case=3)
    sol3 = kovacic_search(r, case=3, E_sets=E3)
    if sol3 is not None:
        # Determine which finite group
        group_name = identify_finite_group(sol3)
        return KovacicResult(
            case=3,
            galois_group=group_name,
            is_abelian=True,
            solution=sol3
        )

    # Case 4: No Liouvillian solution
    return KovacicResult(
        case=4,
        galois_group='SL(2,C)',
        is_abelian=False,
        solution=None
    )


@dataclass
class KovacicResult:
    case: int
    galois_group: str
    is_abelian: bool
    solution: Optional[sp.Expr]
```

## Exponent Computation Details

### At Regular Singular Point (Order 1)

For a simple pole at c, expand r(x) as:
```
r(x) = r_{-1}/(x-c) + r_0 + r_1(x-c) + ...
```

Exponents from indicial equation: λ² - λ = r_{-1}

```python
def case1_exponents_order1(r_minus1):
    """Exponents for Case 1 at simple pole."""
    # λ² - λ = r_{-1}
    # λ = (1 ± √(1 + 4r_{-1}))/2
    disc = 1 + 4*r_minus1
    if disc >= 0:
        sqrt_disc = sp.sqrt(disc)
        e_plus = (1 + sqrt_disc)/2
        e_minus = (1 - sqrt_disc)/2
        return {e_plus, e_minus}
    else:
        return set()  # Complex exponents
```

### At Irregular Singular Point (Order ≥ 2)

Higher-order poles require more complex analysis involving Newton polygons.

```python
def case1_exponents_irregular(pole, r_expansion, order):
    """
    Exponents for Case 1 at irregular singular point.

    Uses Newton polygon method.
    """
    # Build Newton polygon from r expansion
    points = []
    for k, coeff in enumerate(r_expansion):
        if coeff != 0:
            points.append((k - order, sp.log(abs(coeff)) if coeff.is_real else 0))

    # Find lower convex hull
    hull = compute_lower_hull(points)

    # Slopes of hull give exponent candidates
    exponents = set()
    for i in range(len(hull)-1):
        slope = (hull[i+1][1] - hull[i][1]) / (hull[i+1][0] - hull[i][0])
        exponents.add(-slope)

    return exponents
```

## Practical Considerations

### Numerical Stability

When coefficients are numerical, use:

```python
def kovacic_numerical(a_func, b_func, x_domain, tolerance=1e-10):
    """
    Numerical Kovacic analysis for non-symbolic coefficients.

    Uses numerical integration and monodromy computation.
    """
    # Sample r(x) at many points
    x_samples = np.linspace(x_domain[0], x_domain[1], 1000)

    # Detect poles numerically
    poles = detect_numerical_poles(b_func, x_samples)

    # For each pole, estimate local behavior
    for pole in poles:
        order = estimate_pole_order(b_func, pole)
        residue = estimate_residue(b_func, pole, order)

    # Compute monodromy matrix numerically
    M = numerical_monodromy(a_func, b_func, poles)

    # Analyze monodromy eigenvalues
    eigenvalues = np.linalg.eigvals(M)

    # Determine case from eigenvalue structure
    if is_case1_monodromy(eigenvalues):
        return KovacicResult(case=1, galois_group='triangular', is_abelian=True)
    elif is_case2_monodromy(eigenvalues):
        return KovacicResult(case=2, galois_group='dihedral', is_abelian=True)
    elif is_case3_monodromy(eigenvalues):
        return KovacicResult(case=3, galois_group='finite', is_abelian=True)
    else:
        return KovacicResult(case=4, galois_group='SL(2,C)', is_abelian=False)
```

### Time-Dependent NVE

For NVE from periodic orbits, the coefficients are periodic:

```python
def kovacic_periodic(r_periodic, period):
    """
    Kovacic analysis for periodic coefficient r(t).

    The Galois group is determined by monodromy around one period.
    """
    # Compute Floquet-normalized monodromy
    M = floquet_monodromy(r_periodic, period)

    # Eigenvalue analysis
    mu1, mu2 = np.linalg.eigvals(M)

    # For symplectic: mu1 * mu2 = 1
    assert abs(mu1 * mu2 - 1) < 1e-10

    # Classification
    trace = mu1 + mu2

    if abs(trace) < 2:
        # Elliptic: bounded solutions → likely abelian
        theta = np.arccos(trace.real / 2)
        if is_rational_multiple_of_pi(theta):
            return KovacicResult(case=3, galois_group='finite', is_abelian=True)
        else:
            return KovacicResult(case=2, galois_group='circle', is_abelian=True)
    elif abs(trace) == 2:
        # Parabolic: marginal case
        return KovacicResult(case=1, galois_group='parabolic', is_abelian=True)
    else:
        # Hyperbolic: unbounded solutions → check for Case 4
        return KovacicResult(case=4, galois_group='SL(2,C)', is_abelian=False)
```

## Example: Harmonic Oscillator

```python
# y'' + y = 0  →  r(x) = -1 (constant)
x = sp.Symbol('x')
a = sp.Integer(0)
b = sp.Integer(1)

result = kovacic_algorithm(a, b)

# Result: Case 1 (triangular)
# Solutions: y = exp(±ix) = cos(x) ± i*sin(x)
# Galois group: G ≅ SO(2,ℂ) ≅ ℂ* (abelian)
```

## Example: Airy Equation

```python
# y'' = xy  →  r(x) = x (linear)
a = sp.Integer(0)
b = -x  # Note: y'' + by = 0, so b = -x

result = kovacic_algorithm(a, b)

# Result: Case 4 (SL(2,ℂ))
# No Liouvillian solutions
# Galois group: G = SL(2,ℂ) (non-abelian)
```

## References

- Kovacic, J.J. (1986). "An algorithm for solving second order linear homogeneous differential equations", J. Symbolic Computation 2:3-43
- Singer, M.F. (1981). "Liouvillian solutions of n-th order homogeneous linear differential equations"
- Duval, A. & Loday-Richaud, M. (1992). "Kovacic's algorithm and its application to some families of special functions"
- van der Put, M. & Singer, M.F. (2003). *Galois Theory of Linear Differential Equations*, Ch. 4
