"""PRAJNA — Local Anomaly Detectors: z-score and Isolation Forest."""

import numpy as np
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)


class LocalDetector:
    """Per-node anomaly scoring using z-score and Isolation Forest ensemble.

    Produces a local anomaly score a_i ∈ [0, 1] and confidence c_i for each node.
    """

    def __init__(self, z_threshold: float = 3.0, contamination: float = 0.005):
        self.z_threshold = z_threshold
        self.contamination = contamination
        self._means: dict[int, np.ndarray] = {}
        self._stds: dict[int, np.ndarray] = {}
        self._iforests: dict[int, IsolationForest] = {}

    def fit(self, telemetry: np.ndarray) -> "LocalDetector":
        """Fit z-score stats and Isolation Forest per node.

        Args:
            telemetry: (T, N, D) training telemetry
        """
        T, N, D = telemetry.shape
        for n in range(N):
            node_data = telemetry[:, n, :]
            self._means[n] = np.mean(node_data, axis=0)
            self._stds[n] = np.std(node_data, axis=0)
            self._stds[n][self._stds[n] < 1e-8] = 1.0

            iforest = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
            )
            iforest.fit(node_data)
            self._iforests[n] = iforest

        logger.info(f"Fit {N} local detectors")
        return self

    def score(self, telemetry_t: np.ndarray) -> dict:
        """Score a single timestep across all nodes.

        Args:
            telemetry_t: (N, D) features at one timestep

        Returns:
            dict with 'scores' (N,), 'confidences' (N,), 'details' per node
        """
        N, D = telemetry_t.shape
        scores = np.zeros(N, dtype=np.float32)
        confidences = np.zeros(N, dtype=np.float32)
        details = []

        for n in range(N):
            x = telemetry_t[n]

            # Z-score based scoring
            if n in self._means:
                z = np.abs((x - self._means[n]) / self._stds[n])
                z_max = np.max(z)
                z_score = min(1.0, z_max / (2 * self.z_threshold))
            else:
                z_max = 0
                z_score = 0

            # Isolation Forest scoring (-1 = anomaly, 1 = normal)
            if n in self._iforests:
                iforest_raw = -self._iforests[n].score_samples(x.reshape(1, -1))[0]
                # Convert to 0-1 (higher = more anomalous)
                if_score = min(1.0, max(0.0, (iforest_raw - 0.4) / 0.2))
            else:
                if_score = 0

            # Ensemble: weighted average
            combined = 0.4 * z_score + 0.6 * if_score
            scores[n] = float(combined)

            # Confidence: higher if both detectors agree
            agreement = 1.0 - abs(z_score - if_score)
            confidences[n] = float(agreement)

            details.append({
                "node": n,
                "z_max": float(z_max),
                "z_score": float(z_score),
                "iforest_score": float(if_score),
                "combined": float(combined),
            })

        return {
            "scores": scores,
            "confidences": confidences,
            "details": details,
        }

    def batch_score(self, telemetry: np.ndarray) -> dict:
        """Score multiple timesteps.

        Args:
            telemetry: (T, N, D)

        Returns:
            dict with 'scores' (T, N), 'confidences' (T, N)
        """
        T, N, D = telemetry.shape
        all_scores = np.zeros((T, N), dtype=np.float32)
        all_confidences = np.zeros((T, N), dtype=np.float32)

        for t in range(T):
            result = self.score(telemetry[t])
            all_scores[t] = result["scores"]
            all_confidences[t] = result["confidences"]

        return {
            "scores": all_scores,
            "confidences": all_confidences,
        }
