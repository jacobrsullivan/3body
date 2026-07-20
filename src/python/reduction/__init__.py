"""Legacy exploratory reduction package.

This namespace is retained for compatibility and is not qualification-bearing.
Its Cartesian gauge representatives and historical dimension labels are not
the canonical full phase-space quotient qualified by WP2-3BRQ-v1. Use
``src.python.threebody_reduction`` for the qualified implementation.

The historical API contains:
- Translation reduction (quotient by ℝ³)
- Rotation reduction (quotient by SO(3))
- Mechanical connection computation

The mechanical-connection code here remains an unqualified research prototype.
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
