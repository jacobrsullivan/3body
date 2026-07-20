# WP1Q-N3BP-v1 Core Boundary

## Bounded claim

This package propagates declared inertial Newtonian states for exactly three
positive point masses and measures their classical first integrals. It supplies
an implementation core and benchmark tests; it is not itself a qualification
record or a production periodic-orbit catalogue.

## State and equations

- Every state is an 18-element float64 vector: three 3D positions followed by
  three 3D velocities, in body order.
- Coordinates are inertial Cartesian coordinates. A center-of-mass frame is
  optional and must be requested explicitly.
- Masses, the gravitational constant, state epoch, and time use one consistent
  unit system chosen by the caller.
- Dynamics are exact point-mass Newtonian gravity with no softening, rotating
  frame terms, relativistic corrections, regularization, or collision model.
- A binary or triple collision is outside this core's propagation domain.

## Numerical independence

- The production propagator is SciPy `solve_ivp(method="DOP853")` over the
  package's own Newtonian right-hand side.
- The reference propagator independently constructs particles in REBOUND and
  uses its C implementation of IAS15. It does not call the production right-hand
  side and does not silently move the supplied state to a barycentric frame.
- Qualification uses IAS15's global adaptive criterion for the figure-eight,
  whose zero-acceleration body makes a per-particle relative criterion poorly
  conditioned. The pinned SJTU cases use IAS15's PRS23 criterion; both choices
  are fixed per benchmark class in the executable specification.
- Both engines use IEEE float64 storage. IAS15 is a high-order independent
  reference, not arbitrary-precision or interval-arithmetic validation.

## Initial benchmark tier

- Equal-mass Lagrange equilateral relative equilibrium, with an analytic state
  at every time.
- The rounded published Chenciner-Montgomery figure-eight initial conditions,
  whose achievable closure is limited by the number of published digits.
- Nine exact decimal rows from the authors' pinned unequal-mass SJTU
  supplementary table, propagated without differential correction.
- Covariance checks under simultaneous body permutation, proper spatial
  rotation, and Newtonian position/time scaling.

## Model boundary

This package does not import CR3BP WP1 qualification code or WP2 geometry and
regularization code. CR3BP six-state rotating-frame artifacts cannot be passed
to this API. Any future WP2 consumer must declare a full 18D state, masses,
gravitational constant, inertial frame, epoch, and time unit; conversion or
reconstruction from a different model is outside the qualification claim.
