# Understanding Double-Double Arithmetic and the QD Library

## What Is "Precision" in Scientific Computing?
In scientific computing, **precision** refers to how many significant digits a numerical calculation can reliably use and produce. Most programming languages, including Python and C++, use **double precision** by default. This gives about **16 decimal digits** of accuracy.

But for cutting-edge problems like the **Three-Body Problem (3BP)**, especially in the context of Work Package 1 (WP1), this is *not enough*. WP1 targets errors less than 10^{-25} in the Jacobi constant over very long simulations (10,000+ orbits). Standard double precision will introduce errors that overwhelm this goal.

## What Is Double-Double Arithmetic?
**Double-Double (DD) arithmetic** extends standard precision to about **31 decimal digits** by representing a number as the **unevaluated sum of two doubles**:

> DD number = high_part + low_part

This way, it captures more subtle differences that would be lost due to rounding errors in regular double precision. It isn't quite as precise as true "quadruple precision" (about 34 digits), but it’s **much faster** and **more portable** on modern systems.

## Why Is It Important for This Project?
In WP1, we aim to:
- Integrate orbits in the Circular Restricted Three-Body Problem (CR3BP)
- Detect conserved quantities to machine precision
- Avoid misidentifying numerical artifacts as real physical phenomena

To do this, we must **track the Jacobi constant to 25+ digits of accuracy** across simulations that may span millions of integration steps. DD arithmetic offers a good balance: much higher accuracy than double precision, but more efficient than software-emulated quad precision.

Without DD arithmetic, we would not be able to:
- Detect tiny but meaningful drifts in conserved quantities
- Differentiate between chaotic and quasi-regular motion
- Validate candidate integrals proposed by machine learning

## What Is the QD Library?
The **QD (Quad-Double) Library** is a high-performance C++ library developed by **David H. Bailey, Xiaoye S. Li, and Yozo Hida**. It implements:
- **Double-Double arithmetic** (~31 digits)
- **Quad-Double arithmetic** (~62 digits)

It is widely used in high-precision computing for numerical integration, chaotic dynamics, and experimental mathematics.

### Why We Chose QD:
- **Proven Reliability:** Used in many peer-reviewed numerical studies
- **Optimized:** Written in C++ for performance
- **Compatibility:** Works well with Conda/Mamba environments and pybind11 for Python bindings
- **Documentation & Support:** Actively maintained with clear examples

## How Will We Use It in WP1?
In this project, the QD Library is used to:
1. **Compile a high-precision C++ toolchain** inside the isolated Conda environment.
2. **Run orbital integrations** (e.g., Keplerian or CR3BP) in Double-Double precision.
3. **Bridge C++ and Python** using pybind11 to expose DD-enabled computations to the Python layer.
4. **Validate core properties** like energy conservation over long time periods.

### Example Application:
On Day 3 of Week 1, we:
- Compile QD with Conda-provided compilers
- Create a small test program to print \u03c0 to 31 digits
- Integrate a simple Kepler problem and verify energy conservation to <10^{-28}

Later, we will:
- Integrate full CR3BP orbits using DD
- Use DD to compute chaos indicators like MEGNO and FLI
- Pass DD data into machine learning pipelines for invariant discovery

## Summary
| Term | Meaning |
|------|---------|
| **Double Precision** | ~16 digits; not sufficient for WP1 |
| **Double-Double** | ~31 digits; built from 2 doubles |
| **QD Library** | C++ library for DD and QD math |
| **Why DD?** | Needed for high-fidelity integrals in CR3BP |
| **Why QD?** | Fast, reliable, and Python-compatible |

DD arithmetic via the QD Library is a **critical enabler** of the scientific rigor and numerical precision required for WP1. It ensures that what we observe in our simulations is real—not an artifact of sloppy numerics.

---

**References:**
- Hida, Y., Li, X.S., & Bailey, D.H. (2000). "Algorithms for Quad-Double Precision Floating Point Arithmetic."
- QD Library GitHub: https://github.com/OSULab/QD
- WP1 Documentation【9†source】, Validation Plan【10†source】
