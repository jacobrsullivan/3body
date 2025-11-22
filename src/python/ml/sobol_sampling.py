"""
Sobol Sequence Sampling for Low-Discrepancy Parameter Space Coverage (WP1 Phase 5).

Implements Sobol quasi-random sequences for efficient parameter space exploration.
Superior to Latin Hypercube Sampling (LHS) for high-dimensional spaces.

Mathematical Background:
========================

Sobol Sequences:
----------------
Quasi-random (low-discrepancy) sequences that provide more uniform coverage
of parameter space than pseudo-random sequences.

Key Properties:
- Star discrepancy: D*_N ~ O((log N)^d / N) for d dimensions
- Better than LHS for d > 3
- Deterministic and reproducible
- Works best when N is a power of 2

Applications in WP1:
--------------------
- Parameter space: (μ, C, e, φ, θ) - 5 dimensions
- Tier 1: 10⁵ samples (2¹⁷ ≈ 131,072 optimal)
- Adaptive refinement based on FLI/MEGNO maps

References:
-----------
- Sobol (1967): "Distribution of points in a cube and approximate evaluation
  of integrals"
- Joe & Kuo (2008): "Constructing Sobol sequences with better two-dimensional
  projections"
- WP1 Specification, Section 2.3 (Parameter-Space Design and Sampling)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParameterRange:
    """
    Parameter range specification.

    Attributes:
        name: Parameter name
        min_value: Minimum value
        max_value: Maximum value
        scale: "linear" or "log" scaling
        description: Parameter description
    """
    name: str
    min_value: float
    max_value: float
    scale: str = "linear"  # "linear" or "log"
    description: str = ""

    def transform_from_unit(self, u: float) -> float:
        """
        Transform from unit interval [0,1] to parameter range.

        Args:
            u: Value in [0, 1]

        Returns:
            Scaled parameter value
        """
        if self.scale == "log":
            # Log-uniform distribution
            log_min = np.log10(self.min_value)
            log_max = np.log10(self.max_value)
            log_val = log_min + u * (log_max - log_min)
            return 10**log_val
        else:
            # Linear distribution
            return self.min_value + u * (self.max_value - self.min_value)


class SobolSampler:
    """
    Sobol sequence generator for parameter space sampling.

    Uses scipy's quasi-Monte Carlo Sobol implementation.
    """

    def __init__(
        self,
        parameter_ranges: List[ParameterRange],
        scramble: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize Sobol sampler.

        Args:
            parameter_ranges: List of parameter range specifications
            scramble: Whether to scramble sequence (recommended)
            seed: Random seed for scrambling (for reproducibility)
        """
        self.parameter_ranges = parameter_ranges
        self.n_params = len(parameter_ranges)
        self.scramble = scramble
        self.seed = seed

        logger.info(f"Initialized SobolSampler for {self.n_params} parameters")
        for pr in parameter_ranges:
            logger.info(f"  {pr.name}: [{pr.min_value}, {pr.max_value}] ({pr.scale})")

    def generate_samples(self, n_samples: int) -> np.ndarray:
        """
        Generate Sobol sequence samples.

        Args:
            n_samples: Number of samples to generate
                      (recommend power of 2 for optimal properties)

        Returns:
            Samples array of shape (n_samples, n_params)
        """
        # Check if scipy is available
        try:
            from scipy.stats import qmc
        except ImportError:
            logger.warning("scipy not available, falling back to pseudo-random sampling")
            return self._fallback_random_samples(n_samples)

        # Generate Sobol sequence in unit hypercube
        logger.info(f"Generating {n_samples} Sobol samples...")

        sampler = qmc.Sobol(d=self.n_params, scramble=self.scramble, seed=self.seed)
        samples_unit = sampler.random(n_samples)

        # Transform to parameter ranges
        samples = np.zeros_like(samples_unit)
        for i, pr in enumerate(self.parameter_ranges):
            samples[:, i] = np.array([
                pr.transform_from_unit(u) for u in samples_unit[:, i]
            ])

        logger.info(f"Generated {n_samples} samples")
        return samples

    def _fallback_random_samples(self, n_samples: int) -> np.ndarray:
        """
        Fallback to pseudo-random sampling if scipy unavailable.

        Args:
            n_samples: Number of samples

        Returns:
            Random samples (n_samples, n_params)
        """
        logger.warning("Using pseudo-random sampling (not low-discrepancy)")

        if self.seed is not None:
            np.random.seed(self.seed)

        samples_unit = np.random.rand(n_samples, self.n_params)

        samples = np.zeros_like(samples_unit)
        for i, pr in enumerate(self.parameter_ranges):
            samples[:, i] = np.array([
                pr.transform_from_unit(u) for u in samples_unit[:, i]
            ])

        return samples

    def compute_discrepancy(self, samples: np.ndarray) -> float:
        """
        Compute star discrepancy of sample set (quality metric).

        Lower discrepancy = better space-filling properties.

        Args:
            samples: Sample array (already transformed to parameter space)

        Returns:
            Discrepancy estimate
        """
        try:
            from scipy.stats import qmc

            # Transform samples back to unit hypercube for discrepancy computation
            samples_unit = np.zeros_like(samples)
            for i, pr in enumerate(self.parameter_ranges):
                if pr.scale == "log":
                    log_min = np.log10(pr.min_value)
                    log_max = np.log10(pr.max_value)
                    log_vals = np.log10(samples[:, i])
                    samples_unit[:, i] = (log_vals - log_min) / (log_max - log_min)
                else:
                    samples_unit[:, i] = (samples[:, i] - pr.min_value) / (
                        pr.max_value - pr.min_value
                    )

            discrepancy = qmc.discrepancy(samples_unit)
            return discrepancy

        except ImportError:
            logger.warning("scipy not available, cannot compute discrepancy")
            return -1.0


# Convenience function for CR3BP parameter sampling


def create_cr3bp_parameter_ranges(
    mu_range: Tuple[float, float] = (1e-3, 0.5),
    C_range: Tuple[float, float] = (2.5, 3.5),
    n_C_values: int = 15
) -> List[ParameterRange]:
    """
    Create parameter ranges for CR3BP trajectory sampling.

    WP1 Specification:
    - Mass ratio μ: 30 samples, log-uniform in [10⁻³, 0.5]
    - Jacobi constant C: 15 values bracketing L1...L5

    Args:
        mu_range: (min, max) for mass ratio
        C_range: (min, max) for Jacobi constant
        n_C_values: Number of C values

    Returns:
        List of ParameterRange objects
    """
    # For initial condition sampling, we need (x, y, vx, vy) on Poincaré section
    # Simplified: sample in position-velocity space

    ranges = [
        ParameterRange(
            name="mu",
            min_value=mu_range[0],
            max_value=mu_range[1],
            scale="log",
            description="Mass parameter (M2/(M1+M2))"
        ),
        ParameterRange(
            name="C",
            min_value=C_range[0],
            max_value=C_range[1],
            scale="linear",
            description="Jacobi constant"
        ),
        ParameterRange(
            name="x",
            min_value=-1.5,
            max_value=1.5,
            scale="linear",
            description="Initial x position"
        ),
        ParameterRange(
            name="y",
            min_value=-1.0,
            max_value=1.0,
            scale="linear",
            description="Initial y position"
        ),
        ParameterRange(
            name="vx",
            min_value=-2.0,
            max_value=2.0,
            scale="linear",
            description="Initial x velocity"
        ),
    ]

    return ranges


def generate_tier1_parameters(
    n_samples: int = 100000,
    scramble: bool = True,
    seed: Optional[int] = 42
) -> Tuple[np.ndarray, List[str]]:
    """
    Generate Tier 1 parameter samples for WP1 production run.

    Args:
        n_samples: Number of samples (recommend 2^17 = 131072)
        scramble: Use scrambled Sobol sequence
        seed: Random seed for reproducibility

    Returns:
        (samples array, parameter names)
    """
    ranges = create_cr3bp_parameter_ranges()
    sampler = SobolSampler(ranges, scramble=scramble, seed=seed)

    samples = sampler.generate_samples(n_samples)
    param_names = [r.name for r in ranges]

    logger.info(f"Generated {n_samples} Tier 1 parameter samples")
    logger.info(f"Parameters: {param_names}")

    # Compute and log discrepancy
    discrepancy = sampler.compute_discrepancy(samples)
    if discrepancy >= 0:
        logger.info(f"Star discrepancy: {discrepancy:.4f}")

    return samples, param_names
