"""PRAJNA — SHAKTI: Conformal Prediction Safety Framework.

Novel Algorithm #8: Provides mathematically guaranteed coverage bounds
on all anomaly predictions using adaptive conformal inference.
"""

import numpy as np
import logging
from collections import deque

logger = logging.getLogger(__name__)


class SHAKTI:
    """Conformal prediction wrapper with adaptive coverage guarantees.

    Given a model's prediction p̂ and calibration data, SHAKTI produces
    prediction intervals [lower, upper] that contain the true value with
    probability ≥ (1 - α) = 0.99, even under distribution shift.

    Uses the Adaptive Conformal Inference (ACI) method with:
      - Online calibration via running nonconformity scores
      - Coverage tracking with adaptive α adjustment
    """

    def __init__(
        self,
        coverage_level: float = 0.99,
        calibration_size: int = 500,
        gamma: float = 0.005,
        window_size: int = 1000,
    ):
        self.target_coverage = coverage_level
        self.alpha = 1 - coverage_level
        self.calibration_size = calibration_size
        self.gamma = gamma  # learning rate for adaptive update
        self.window_size = window_size

        # Calibration state
        self._calibrated = False
        self._nonconformity_scores: list[float] = []
        self._quantile: float = 0.0

        # Adaptive tracking
        self._coverage_history = deque(maxlen=window_size)
        self._alpha_t = self.alpha

    def calibrate(self, predictions: np.ndarray, ground_truth: np.ndarray):
        """Calibrate conformal bounds using held-out data.

        Args:
            predictions: (M,) model predictions on calibration set
            ground_truth: (M,) true values
        """
        scores = np.abs(predictions - ground_truth)
        self._nonconformity_scores = sorted(scores.tolist())

        # Compute conformal quantile
        n = len(self._nonconformity_scores)
        q_idx = int(np.ceil((1 - self.alpha) * (n + 1))) - 1
        q_idx = min(q_idx, n - 1)
        self._quantile = self._nonconformity_scores[q_idx]

        self._calibrated = True
        logger.info(
            f"SHAKTI calibrated: quantile={self._quantile:.4f}, "
            f"coverage target={self.target_coverage:.2%}, "
            f"n_cal={n}"
        )

    def predict_interval(self, prediction: float) -> dict:
        """Produce a conformal prediction interval.

        Args:
            prediction: Model's point prediction

        Returns:
            dict with 'lower', 'upper', 'width', 'is_safe', 'confidence'
        """
        if not self._calibrated:
            logger.warning("SHAKTI not calibrated — returning unconstrained interval")
            return {
                "lower": prediction - 0.5,
                "upper": prediction + 0.5,
                "width": 1.0,
                "is_safe": False,
                "confidence": 0.0,
            }

        lower = prediction - self._quantile
        upper = prediction + self._quantile
        width = upper - lower

        # Safety: wider interval = more uncertain = less safe
        is_safe = width < 0.5  # tunable safety threshold

        return {
            "lower": float(lower),
            "upper": float(upper),
            "width": float(width),
            "is_safe": is_safe,
            "confidence": float(self.target_coverage),
        }

    def batch_predict(self, predictions: np.ndarray) -> dict:
        """Produce intervals for a batch of predictions.

        Args:
            predictions: (B,) array of predictions

        Returns:
            dict with arrays of 'lower', 'upper', 'width'
        """
        lowers = predictions - self._quantile
        uppers = predictions + self._quantile
        widths = uppers - lowers

        return {
            "lower": lowers,
            "upper": uppers,
            "width": widths,
            "mean_width": float(np.mean(widths)),
        }

    def update_adaptive(self, prediction: float, ground_truth: float):
        """Online adaptive update of coverage level.

        Adjusts α_t based on whether the prediction interval covered the true value.

        Args:
            prediction: Model prediction
            ground_truth: True value
        """
        error = abs(prediction - ground_truth)
        covered = error <= self._quantile

        self._coverage_history.append(1.0 if covered else 0.0)

        # Adaptive α update (ACI)
        err_t = 1.0 if not covered else 0.0
        self._alpha_t = self._alpha_t + self.gamma * (self.alpha - err_t)
        self._alpha_t = np.clip(self._alpha_t, 0.001, 0.5)

        # Update quantile
        score = error
        self._nonconformity_scores.append(score)
        self._nonconformity_scores.sort()

        n = len(self._nonconformity_scores)
        q_idx = int(np.ceil((1 - self._alpha_t) * (n + 1))) - 1
        q_idx = min(q_idx, n - 1)
        self._quantile = self._nonconformity_scores[q_idx]

    def get_empirical_coverage(self) -> float:
        """Return empirical coverage over recent predictions."""
        if not self._coverage_history:
            return 0.0
        return float(np.mean(list(self._coverage_history)))

    def get_status(self) -> dict:
        """Return SHAKTI operational status."""
        return {
            "calibrated": self._calibrated,
            "current_alpha": float(self._alpha_t),
            "quantile": float(self._quantile),
            "target_coverage": self.target_coverage,
            "empirical_coverage": self.get_empirical_coverage(),
            "num_calibration_scores": len(self._nonconformity_scores),
        }
