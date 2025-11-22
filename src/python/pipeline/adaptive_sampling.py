"""
Adaptive Sampling Strategy for Parameter Space Refinement (WP1 Phase 5).

Implements dynamically-informed parameter refinement near separatrices
and resonances based on chaos indicator maps.

Strategy:
=========
1. Pilot run: Generate FLI/MEGNO maps on coarse grid
2. Identify high-gradient regions (resonances, separatrices)
3. Refine sampling density in these regions
4. Final production run with adaptively refined grid

References:
-----------
- WP1 Specification, Section 2.3 (Parameter-Space Design and Sampling)
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveRefinementResult:
    """Results from adaptive refinement."""
    original_samples: np.ndarray
    refined_samples: np.ndarray
    refinement_regions: List[Tuple[int, float]]  # (index, gradient magnitude)
    total_samples: int


class AdaptiveSampler:
    """Adaptive parameter space sampling based on chaos indicators."""

    def __init__(
        self,
        gradient_threshold_percentile: float = 90.0,
        refinement_factor: int = 4
    ):
        """
        Initialize adaptive sampler.

        Args:
            gradient_threshold_percentile: Percentile for high-gradient detection
            refinement_factor: How many additional samples per refinement region
        """
        self.gradient_threshold_percentile = gradient_threshold_percentile
        self.refinement_factor = refinement_factor

    def compute_gradient_magnitude(
        self,
        samples: np.ndarray,
        indicator_values: np.ndarray
    ) -> np.ndarray:
        """
        Compute gradient magnitude of chaos indicator field.

        Args:
            samples: Parameter samples (N, d)
            indicator_values: Chaos indicator values (N,)

        Returns:
            Gradient magnitudes (N,)
        """
        N, d = samples.shape
        gradients = np.zeros(N)

        # Simple finite difference on k-nearest neighbors
        k = min(10, N // 10)  # Adaptive k

        for i in range(N):
            # Find k nearest neighbors
            distances = np.linalg.norm(samples - samples[i], axis=1)
            nearest_idx = np.argsort(distances)[1:k+1]  # Exclude self

            # Estimate gradient from neighbors
            for j in nearest_idx:
                if distances[j] > 1e-10:
                    grad_est = abs(indicator_values[j] - indicator_values[i]) / distances[j]
                    gradients[i] = max(gradients[i], grad_est)

        return gradients

    def refine_sampling(
        self,
        samples: np.ndarray,
        indicator_values: np.ndarray
    ) -> AdaptiveRefinementResult:
        """
        Perform adaptive refinement.

        Args:
            samples: Original parameter samples
            indicator_values: Chaos indicator values

        Returns:
            AdaptiveRefinementResult
        """
        logger.info(f"Adaptive refinement of {len(samples)} samples...")

        # Compute gradients
        gradients = self.compute_gradient_magnitude(samples, indicator_values)

        # Identify high-gradient regions
        threshold = np.percentile(gradients, self.gradient_threshold_percentile)
        high_gradient_mask = gradients > threshold

        refinement_indices = np.where(high_gradient_mask)[0]
        logger.info(f"Identified {len(refinement_indices)} regions for refinement")

        # Generate additional samples near high-gradient points
        refined_samples_list = []

        for idx in refinement_indices:
            center = samples[idx]

            # Estimate local scale
            distances = np.linalg.norm(samples - center, axis=1)
            local_scale = np.median(distances[distances > 0])

            # Generate local samples (Gaussian cloud)
            for _ in range(self.refinement_factor):
                perturbation = np.random.randn(len(center)) * local_scale * 0.1
                new_sample = center + perturbation
                refined_samples_list.append(new_sample)

        refined_samples = np.array(refined_samples_list) if refined_samples_list else np.array([])

        refinement_regions = [(int(idx), float(gradients[idx])) for idx in refinement_indices]

        logger.info(f"Generated {len(refined_samples)} additional samples")

        return AdaptiveRefinementResult(
            original_samples=samples,
            refined_samples=refined_samples,
            refinement_regions=refinement_regions,
            total_samples=len(samples) + len(refined_samples)
        )
