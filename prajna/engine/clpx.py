"""PRAJNA — CLPX: Cross-Lifecycle Pattern Exchange Bridge.

Novel Algorithm #6: Bidirectional transfer learning between in-flight
monitoring and post-flight requalification pipelines.

Forward transfer:  In-flight anomaly patterns → Post-flight priors
Backward transfer: Post-flight damage knowledge → In-flight sensitivity
"""

import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CLPX:
    """Cross-Lifecycle Pattern Exchange bridge.

    Maintains a shared embedding space where:
      - In-flight TGN embeddings are projected via forward_proj
      - Post-flight THERMAL-DIFF-GNN features are projected via backward_proj
      - Trust adaptation λ_trust controls how much transfer is applied

    Transfer improves with each flight cycle as the shared space stabilizes.
    """

    def __init__(
        self,
        embedding_dim: int = 64,
        shared_dim: int = 32,
        initial_trust: float = 0.1,
        trust_growth_rate: float = 0.15,
        max_trust: float = 0.8,
    ):
        self.embedding_dim = embedding_dim
        self.shared_dim = shared_dim
        self.trust = initial_trust
        self.trust_growth_rate = trust_growth_rate
        self.max_trust = max_trust

        # Projection matrices (learned via gradient-free adaptation)
        self._forward_proj = np.random.randn(embedding_dim, shared_dim).astype(np.float32) * 0.1
        self._backward_proj = np.random.randn(embedding_dim, shared_dim).astype(np.float32) * 0.1

        # Flight history
        self._flight_embeddings: list[np.ndarray] = []
        self._postflight_embeddings: list[np.ndarray] = []
        self._flight_count = 0

    def forward_transfer(
        self,
        inflight_embeddings: np.ndarray,
        num_nodes: int = 13,
    ) -> dict:
        """Transfer in-flight anomaly patterns to post-flight priors.

        Projects in-flight TGN embeddings into the shared space to
        create informed priors for post-flight damage assessment.

        Args:
            inflight_embeddings: (N, D) mean embeddings from in-flight TGN
            num_nodes: Number of subsystem nodes

        Returns:
            dict with 'priors' (N, shared_dim), 'trust', 'flight_id'
        """
        N = inflight_embeddings.shape[0]
        D = inflight_embeddings.shape[1]

        # Project to shared space
        if D != self.embedding_dim:
            # Pad or truncate
            padded = np.zeros((N, self.embedding_dim), dtype=np.float32)
            padded[:, :min(D, self.embedding_dim)] = inflight_embeddings[:, :min(D, self.embedding_dim)]
            inflight_embeddings = padded

        shared = inflight_embeddings @ self._forward_proj  # (N, shared_dim)

        # Apply trust weighting
        priors = shared * self.trust

        # Store for history
        self._flight_embeddings.append(inflight_embeddings.copy())
        self._flight_count += 1

        logger.info(
            f"CLPX forward transfer: flight {self._flight_count}, "
            f"trust={self.trust:.3f}, prior norm={np.linalg.norm(priors):.3f}"
        )

        return {
            "priors": priors,
            "shared_embeddings": shared,
            "trust": self.trust,
            "flight_id": self._flight_count,
        }

    def backward_transfer(
        self,
        postflight_features: np.ndarray,
        damage_scores: np.ndarray,
    ) -> dict:
        """Transfer post-flight damage knowledge back to in-flight sensitivity.

        Uses damage scores from THERMAL-DIFF-GNN to adjust in-flight
        detection sensitivity for vulnerable subsystems.

        Args:
            postflight_features: (N, D) component features
            damage_scores: (N,) damage scores from THERMAL-DIFF-GNN

        Returns:
            dict with 'sensitivity_adjustments' (N,), 'trust'
        """
        N = postflight_features.shape[0]
        D = postflight_features.shape[1]

        # Project to shared space
        if D != self.embedding_dim:
            padded = np.zeros((N, self.embedding_dim), dtype=np.float32)
            padded[:, :min(D, self.embedding_dim)] = postflight_features[:, :min(D, self.embedding_dim)]
            postflight_features = padded

        shared = postflight_features @ self._backward_proj  # (N, shared_dim)

        # Components with higher damage get sensitivity boost
        sensitivity_adjustments = np.zeros(N, dtype=np.float32)
        for i in range(N):
            if damage_scores[i] > 0.7:
                # High damage: strong sensitivity boost
                sensitivity_adjustments[i] = damage_scores[i] * self.trust * 1.0
            elif damage_scores[i] > 0.3:
                # Moderate damage: moderate sensitivity boost
                sensitivity_adjustments[i] = damage_scores[i] * self.trust * 0.5

        self._postflight_embeddings.append(postflight_features.copy())

        logger.info(
            f"CLPX backward transfer: {np.sum(sensitivity_adjustments > 0)} nodes "
            f"with sensitivity boost"
        )

        return {
            "sensitivity_adjustments": sensitivity_adjustments,
            "shared_embeddings": shared,
            "trust": self.trust,
        }

    def update_trust(self, validation_accuracy: Optional[float] = None):
        """Update trust parameter after each flight cycle.

        Trust grows logarithmically with flight count, bounded by max_trust.
        If validation accuracy is provided, trust is also scaled by it.

        Args:
            validation_accuracy: Optional accuracy from validation (0-1)
        """
        old_trust = self.trust

        # Logarithmic growth: trust = min(max_trust, initial + rate * ln(1 + flights))
        base_trust = 0.1 + self.trust_growth_rate * np.log1p(self._flight_count)
        self.trust = min(self.max_trust, base_trust)

        # Scale by validation accuracy if available
        if validation_accuracy is not None:
            self.trust *= max(0.5, validation_accuracy)

        logger.info(f"CLPX trust updated: {old_trust:.3f} → {self.trust:.3f}")

    def adapt_projections(
        self,
        inflight_embeddings: np.ndarray,
        postflight_features: np.ndarray,
        learning_rate: float = 0.01,
    ):
        """Adapt projection matrices to better align embedding spaces.

        Uses a simple gradient-free alignment: minimizes distance between
        corresponding forward and backward projections.

        Args:
            inflight_embeddings: (N, D_in) recent in-flight embeddings
            postflight_features: (N, D_post) corresponding post-flight features
            learning_rate: Step size for adaptation
        """
        N = inflight_embeddings.shape[0]

        # Pad to embedding_dim
        def pad(x):
            p = np.zeros((x.shape[0], self.embedding_dim), dtype=np.float32)
            p[:, :min(x.shape[1], self.embedding_dim)] = x[:, :min(x.shape[1], self.embedding_dim)]
            return p

        inf_padded = pad(inflight_embeddings)
        post_padded = pad(postflight_features)

        # Project both to shared space
        shared_inf = inf_padded @ self._forward_proj
        shared_post = post_padded @ self._backward_proj

        # Gradient: minimize ||shared_inf - shared_post||^2
        diff = shared_inf - shared_post  # (N, shared_dim)

        grad_fwd = (2.0 / N) * inf_padded.T @ diff
        grad_bwd = -(2.0 / N) * post_padded.T @ diff

        self._forward_proj -= learning_rate * grad_fwd
        self._backward_proj -= learning_rate * grad_bwd

        alignment_loss = float(np.mean(diff ** 2))
        logger.debug(f"CLPX projection adaptation: loss={alignment_loss:.6f}")

    def get_status(self) -> dict:
        """Return CLPX operational status."""
        return {
            "flight_count": self._flight_count,
            "trust": float(self.trust),
            "max_trust": self.max_trust,
            "num_inflight_records": len(self._flight_embeddings),
            "num_postflight_records": len(self._postflight_embeddings),
            "shared_dim": self.shared_dim,
        }
