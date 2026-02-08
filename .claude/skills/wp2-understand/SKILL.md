---
name: wp2-understand
description: >
  Conceptual understanding and orientation for WP2 (Geometric Reduction and Shape Space Analysis).
  Use when asked to explain WP2 goals, geometric foundations, connection/curvature, JM metric,
  lift constructions (S1, KS-Spinor), or how WP2 fits into the WP1→WP5 pipeline. Trigger on
  requests for overviews, summaries, architecture maps, reading guidance, or status context for WP2.
---

# WP2 Understand

## Overview
Explain WP2's purpose, architecture, and outputs, then map the user to the right docs and code.

## Workflow
1. Clarify intent: overview, theory refresh, implementation map, or status context.
2. Read the minimal source(s) needed:
   - `User-Guides/User-Guide-WP2.md` (overview, tests, workflows)
   - `Project-Design-Docs/WP2/WP2-Overview.md` (design architecture)
   - `Project-Design-Docs/WP2/WP2-Complete-Summary-and-Handoff.md` (handoff/status)
   - `README.md` (project-wide context)
3. Deliver a concise narrative:
   - Problem: reduced 3BP is non-integrable due to curvature obstruction.
   - WP2 outputs: coordinate reduction, mechanical connection/curvature, JM metric, S1 + KS lifts.
   - Why it matters: builds the "upstairs" spaces for WP3 discovery.
4. Provide a file map and "where to look next" list.

## Core Map (Short)
- Coordinates and reduction: `src/python/coordinates/`, `src/python/reduction/`
- Connection/curvature/JM metric: `src/python/geometry/`
- Lifts and integrability: `src/python/lifts/`, `src/python/symbolic_lifts/`
- Regularization and KS: `src/python/regularization/`
- Tests: `tests/unit/reduction/`, `tests/geometry/`, `tests/lifts/`, `tests/regularization/`, `tests/symbolic_lifts/`

## Standard Explanation Outline
- What WP2 does and why (geometric foundations, obstruction via curvature)
- Main deliverables (coordinates, reduction, connection/curvature, JM metric, lifts)
- Interfaces (inputs: masses, state, energy, L; outputs: A, F, R, lifted Hamiltonians)
- Validation (key tests and typical sanity checks)
- Hand-off to WP3 (lifted spaces for invariant discovery)

## References
- `User-Guides/User-Guide-WP2.md` (primary guide)
- `Project-Design-Docs/WP2/WP2-Overview.md`
- `Project-Design-Docs/WP2/WP2-Complete-Summary-and-Handoff.md`
- `Science-Research-Docs/WP1 – Foundations: Symplectic Reduction, Moment Maps, Principal Bundles, Magnetic Terms.pdf`
- `Science-Research-Docs/WP2 – 2-Body Kepler + KS: Prototype Constraint-as-Moment-Map Testbed.pdf`

## Resources
### references/
- `reading-map.md` (doc map and intent-driven reading guide)
