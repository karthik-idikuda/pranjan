"""PRAJNA — Dynamic Spacecraft Dependency Graph Builder.

Constructs a 13-node graph representing spacecraft subsystems with
physics-informed dependency edges.
"""

import numpy as np
import torch
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Physics-informed base dependency matrix W_base (13 × 13)
# Based on real spacecraft subsystem dependencies from ISRO IRS/INSAT heritage
BASE_DEPENDENCIES = {
    # (source, target): weight — "source failure affects target"
    (0, 1): 0.8,    # EPS → TCS (power feeds thermal pumps)
    (0, 4): 0.9,    # EPS → COMM (power feeds transponders)
    (0, 5): 0.95,   # EPS → OBC (power feeds computer)
    (0, 11): 0.7,   # EPS → BATT (charging circuit)
    (0, 12): 0.6,   # EPS → SA (regulation circuit)
    (1, 0): 0.5,    # TCS → EPS (thermal affects battery efficiency)
    (1, 5): 0.4,    # TCS → OBC (thermal affects CPU)
    (1, 11): 0.85,  # TCS → BATT (thermal critical for batteries)
    (2, 3): 0.9,    # PROP → AOCS (thrust affects attitude)
    (2, 7): 0.6,    # PROP → STRUCT (thrust loads on structure)
    (3, 2): 0.3,    # AOCS → PROP (attitude commands thrust)
    (3, 4): 0.5,    # AOCS → COMM (pointing affects antenna gain)
    (3, 6): 0.7,    # AOCS → PL (pointing affects payload)
    (4, 5): 0.4,    # COMM → OBC (command uplink)
    (5, 0): 0.3,    # OBC → EPS (power management commands)
    (5, 3): 0.8,    # OBC → AOCS (attitude commands)
    (5, 4): 0.6,    # OBC → COMM (telemetry downlink control)
    (5, 9): 0.9,    # OBC → PYRO (pyro firing commands)
    (7, 8): 0.7,    # STRUCT → HARNESS (structural vibration affects wiring)
    (8, 0): 0.5,    # HARNESS → EPS (wiring carries power)
    (8, 4): 0.4,    # HARNESS → COMM (signal cables)
    (11, 0): 0.9,   # BATT → EPS (battery is power source)
    (12, 0): 0.85,  # SA → EPS (solar array is power source)
    (12, 1): 0.3,   # SA → TCS (solar heating)
}

SUBSYSTEM_NAMES = [
    "EPS", "TCS", "PROP", "AOCS", "COMM", "OBC", "PL",
    "STRUCT", "HARNESS", "PYRO", "REA", "BATT", "SA",
]


class GraphBuilder:
    """Builds and maintains the dynamic spacecraft dependency graph.

    The graph has two components:
      1. W_base: Static physics-informed dependencies (hardcoded from domain knowledge)
      2. ΔW(t): Learned dynamic adjustments based on telemetry correlations
    """

    def __init__(self, num_nodes: int = 13, alpha: float = 0.3):
        """
        Args:
            num_nodes: Number of subsystem nodes (default 13)
            alpha: Blending factor for learned vs static edges (0 = all static)
        """
        self.num_nodes = num_nodes
        self.alpha = alpha
        self.W_base = self._build_base_matrix()
        self.W_dynamic = np.zeros_like(self.W_base)

    def _build_base_matrix(self) -> np.ndarray:
        """Construct the static base dependency matrix from domain knowledge."""
        W = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float32)
        for (i, j), weight in BASE_DEPENDENCIES.items():
            if i < self.num_nodes and j < self.num_nodes:
                W[i, j] = weight
        return W

    def get_adjacency(self, threshold: float = 0.1) -> np.ndarray:
        """Get current combined adjacency matrix.

        Args:
            threshold: Minimum edge weight to keep

        Returns:
            (N, N) combined dependency matrix
        """
        W = (1 - self.alpha) * self.W_base + self.alpha * self.W_dynamic
        W[W < threshold] = 0
        return W

    def get_edge_index_and_weights(self, threshold: float = 0.1):
        """Get PyTorch Geometric edge_index and edge_attr.

        Returns:
            edge_index: (2, E) tensor of edges
            edge_weight: (E,) tensor of weights
        """
        W = self.get_adjacency(threshold)
        rows, cols = np.nonzero(W)
        edge_index = torch.tensor(np.array([rows, cols]), dtype=torch.long)
        edge_weight = torch.tensor(W[rows, cols], dtype=torch.float32)
        return edge_index, edge_weight

    def update_dynamic(self, telemetry: np.ndarray, ema_decay: float = 0.95):
        """Update dynamic edge weights based on telemetry correlations.

        Uses EMA-smoothed pairwise correlation of node features to learn
        which subsystems are currently co-varying.

        Args:
            telemetry: (T, N, D) recent telemetry window
            ema_decay: Exponential moving average decay factor
        """
        T, N, D = telemetry.shape

        # Compute per-node mean signal (T, N)
        node_signals = np.mean(telemetry, axis=2)  # average across features

        # Pairwise Pearson correlation
        corr = np.corrcoef(node_signals.T)  # (N, N)
        corr = np.nan_to_num(corr, nan=0.0)
        corr = np.abs(corr)  # use absolute correlation as dependency strength
        np.fill_diagonal(corr, 0)

        # EMA update
        self.W_dynamic = ema_decay * self.W_dynamic + (1 - ema_decay) * corr.astype(np.float32)

    def get_node_features_dim(self) -> int:
        """Return the number of node feature dimensions."""
        return self.num_nodes

    @property
    def node_names(self) -> list[str]:
        """Return subsystem names."""
        return SUBSYSTEM_NAMES[:self.num_nodes]

    def to_dict(self) -> dict:
        """Serialize graph state."""
        return {
            "W_base": self.W_base.tolist(),
            "W_dynamic": self.W_dynamic.tolist(),
            "alpha": self.alpha,
            "num_nodes": self.num_nodes,
        }
