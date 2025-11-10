"""
Symplectic reduction for three-body problem.

This module implements Marsden-Weinstein reduction for the 3BP:
- Translation reduction (quotient by ℝ³)
- Rotation reduction (quotient by SO(3))
- Mechanical connection computation

Part of WP 2.1 - Geometric Reduction and Shape Space Analysis.
"""

from .base import SymplecticReduction
from .translation_reduction import (
    TranslationReduction,
    TranslationReducedState,
)
from .rotation_reduction import (
    RotationReduction,
    RotationReducedState,
    OrientationConvention,
)
from .connection import MechanicalConnection

__all__ = [
    'SymplecticReduction',
    'TranslationReduction',
    'TranslationReducedState',
    'RotationReduction',
    'RotationReducedState',
    'OrientationConvention',
    'MechanicalConnection',
]
