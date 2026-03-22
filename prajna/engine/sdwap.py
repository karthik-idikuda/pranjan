"""PRAJNA — SDWAP: Subsystem Dependency Weighted Anomaly Propagation.

Novel Algorithm #1: Propagates anomaly scores through the spacecraft
dependency graph with confidence injection, temporal decay, and damping.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


class SDWAP:
    """Subsystem Dependency Weighted Anomaly Propagation.

    Given:
      - Local anomaly scores a_i for each node i
      - Dependency matrix W (N × N) with w_ij = "i affects j"
      - Confidence scores c_i for each local detector

    Computes the propagated anomaly score:
      a_i^(k+1) = (1 - γ) · a_i^(k) + γ · Σ_j [w_ji · c_j · a_j^(k) · decay(Δt_j)]

    Where:
      γ = damping factor (0.85)
      c_j = confidence of node j's local detector
      decay(Δt) = exp(-λ · Δt) temporal decay
    """

    def __init__(
        self,
        max_iterations: int = 5,
        damping_gamma: float = 0.85,
        temporal_decay_lambda: float = 0.1,
        convergence_threshold: float = 0.001,
        confidence_floor: float = 0.1,
    ):
        self.max_iterations = max_iterations
        self.gamma = damping_gamma
        self.decay_lambda = temporal_decay_lambda
        self.convergence_threshold = convergence_threshold
        self.confidence_floor = confidence_floor

    def propagate(
        self,
        local_scores: np.ndarray,
        adjacency: np.ndarray,
        confidences: np.ndarray | None = None,
        timestamps: np.ndarray | None = None,
    ) -> dict:
        """Run SDWAP anomaly propagation.

        Args:
            local_scores: (N,) local anomaly scores per node (0-1)
            adjacency: (N, N) dependency weight matrix
            confidences: (N,) confidence scores per detector (0-1)
            timestamps: (N,) last anomaly timestamp per node (for decay)

        Returns:
            dict with:
              - 'propagated_scores': (N,) final propagated anomaly scores
              - 'iterations': number of iterations until convergence
              - 'history': list of score vectors per iteration
              - 'contribution_map': (N, N) how much each node contributed
        """
        N = len(local_scores)

        # Default confidences to 1.0
        if confidences is None:
            confidences = np.ones(N, dtype=np.float32)
        confidences = np.clip(confidences, self.confidence_floor, 1.0)

        # Compute temporal decay factors
        if timestamps is not None:
            current_time = np.max(timestamps) if timestamps.sum() > 0 else 0
            deltas = np.abs(current_time - timestamps)
            decay_factors = np.exp(-self.decay_lambda * deltas)
        else:
            decay_factors = np.ones(N, dtype=np.float32)

        # Initialize
        scores = local_scores.copy().astype(np.float32)
        history = [scores.copy()]
        contribution_map = np.zeros((N, N), dtype=np.float32)

        # Iterative propagation
        for k in range(self.max_iterations):
            new_scores = np.zeros(N, dtype=np.float32)

            for i in range(N):
                # Incoming propagation from all neighbors j → i
                incoming = 0.0
                for j in range(N):
                    if j == i:
                        continue
                    w_ji = adjacency[j, i]
                    if w_ji > 0:
                        contrib = w_ji * confidences[j] * scores[j] * decay_factors[j]
                        incoming += contrib
                        contribution_map[j, i] += contrib

                # Damped update
                new_scores[i] = (1 - self.gamma) * scores[i] + self.gamma * incoming

            # Clip to [0, 1]
            new_scores = np.clip(new_scores, 0.0, 1.0)

            # Check convergence
            delta = np.max(np.abs(new_scores - scores))
            scores = new_scores
            history.append(scores.copy())

            if delta < self.convergence_threshold:
                logger.debug(f"SDWAP converged in {k + 1} iterations (Δ={delta:.6f})")
                break

        # Combine: max of local and propagated
        final_scores = np.maximum(local_scores, scores)

        return {
            "propagated_scores": final_scores,
            "raw_propagated": scores,
            "iterations": len(history) - 1,
            "history": history,
            "contribution_map": contribution_map,
        }

    def batch_propagate(
        self,
        local_scores_batch: np.ndarray,
        adjacency: np.ndarray,
        confidences: np.ndarray | None = None,
    ) -> list[dict]:
        """Run SDWAP on a batch of timesteps.

        Args:
            local_scores_batch: (T, N) local scores over time
            adjacency: (N, N) dependency matrix
            confidences: (N,) or (T, N) confidence scores

        Returns:
            List of result dicts per timestep
        """
        T, N = local_scores_batch.shape
        results = []

        for t in range(T):
            c = confidences[t] if confidences is not None and confidences.ndim == 2 else confidences
            result = self.propagate(local_scores_batch[t], adjacency, c)
            results.append(result)

        return results
