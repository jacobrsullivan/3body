---
name: wp4-rigor-protocols
description: Use when validating candidate integrals via analytical or numerical methods. Points to WP4 validation gauntlet.
---

# WP4 Validation Gauntlet

## Source of Truth
- **Code**: `src/python/validation/`
- **User Guide**: `User-Guides/User-Guide-WP4.md`
- **Tests**: `tests/validation/`

## Stage 1: Analytical Vetting
**Tool**: `src/python/validation/analytical_vetting.py`

**Tests**: Conservation, Involution, Independence

**Workflow**: See `User-Guides/User-Guide-WP4.md` Section 1

## Stage 2: Morales-Ramis Test
**Tool**: `src/python/validation/morales_ramis_validator.py`

**Kovacic's Algorithm**: `src/python/validation/kovacic.py`

**Theory**: Differential Galois obstruction (User-Guide-WP4.md Section 2)

## Stage 3: Numerical Robustness
**Tools**:
- `monte_carlo_validator.py` - Statistical sweeps
- `stress_tester.py` - Collision, escape, chaos scenarios
- `long_time_validator.py` - Shadow Hamiltonian analysis

**Workflow**: See `User-Guides/User-Guide-WP4.md` Section 3

## Chaos Indicators
**File**: `src/python/validation/chaos_indicators.py`

**Metrics**: MEGNO, FLI (for orbit classification)
