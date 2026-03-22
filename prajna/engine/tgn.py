"""PRAJNA — Temporal Graph Neural Network (TGN).

Novel Algorithm #2: Temporal graph network for encoding spacecraft
subsystem states over time using graph attention + GRU memory.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Time2Vec(nn.Module):
    """Learnable time encoding (periodic + linear)."""

    def __init__(self, dim: int = 16):
        super().__init__()
        self.w0 = nn.Parameter(torch.randn(1))
        self.b0 = nn.Parameter(torch.randn(1))
        self.w = nn.Parameter(torch.randn(dim - 1))
        self.b = nn.Parameter(torch.randn(dim - 1))

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        """Encode timestamp into learned representation.

        Args:
            t: (B,) or (B, 1) timestamps

        Returns:
            (B, dim) time embeddings
        """
        if t.dim() == 1:
            t = t.unsqueeze(1)
        linear = self.w0 * t + self.b0
        periodic = torch.sin(self.w * t + self.b)
        return torch.cat([linear, periodic], dim=-1)


class TGNEncoder(nn.Module):
    """Temporal Graph Network encoder for spacecraft subsystems.

    Architecture:
      Input → Time2Vec ⊕ Node features → GAT Layer 1 → GAT Layer 2 → GRU Memory → Output
    """

    def __init__(
        self,
        input_dim: int = 8,
        hidden_dim: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        memory_dim: int = 64,
        time2vec_dim: int = 16,
        dropout: float = 0.1,
        num_nodes: int = 13,
    ):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.memory_dim = memory_dim

        # Time encoding
        self.time2vec = Time2Vec(time2vec_dim)

        # Input projection (features + time encoding → hidden)
        self.input_proj = nn.Linear(input_dim + time2vec_dim, hidden_dim)

        # GAT layers
        self.gat_layers = nn.ModuleList()
        for i in range(num_layers):
            in_channels = hidden_dim if i == 0 else hidden_dim
            self.gat_layers.append(
                GATConv(
                    in_channels=in_channels,
                    out_channels=hidden_dim // num_heads,
                    heads=num_heads,
                    dropout=dropout,
                    concat=True,
                )
            )

        # GRU memory module — maintains per-node temporal state
        self.gru = nn.GRUCell(hidden_dim, memory_dim)

        # Node memory (persistent across timesteps)
        self.register_buffer(
            "memory",
            torch.zeros(num_nodes, memory_dim),
        )

        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(hidden_dim)

    def reset_memory(self):
        """Reset node memory (call between sequences)."""
        self.memory.zero_()

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor | None = None,
        t: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Forward pass for one timestep.

        Args:
            x: (N, D) node features for current timestep
            edge_index: (2, E) edge indices
            edge_weight: (E,) optional edge weights
            t: (1,) or scalar — current timestamp

        Returns:
            (N, memory_dim) node embeddings
        """
        N = x.size(0)

        # Time encoding
        if t is not None:
            t_enc = self.time2vec(t.float().expand(N))  # (N, time2vec_dim)
        else:
            t_enc = torch.zeros(N, self.time2vec.w.size(0) + 1, device=x.device)

        # Concatenate features + time → project
        h = torch.cat([x, t_enc], dim=-1)
        h = F.relu(self.input_proj(h))
        h = self.dropout(h)

        # GAT message passing
        for gat in self.gat_layers:
            h = gat(h, edge_index)
            h = F.elu(h)
            h = self.dropout(h)

        h = self.norm(h)

        # GRU memory update
        self.memory = self.gru(h, self.memory.detach())

        return self.memory


class FailurePredictor(nn.Module):
    """Dual-head predictor: binary classifier + survival model.

    Head 1: P(failure in next 30 min) — binary classification
    Head 2: Time-to-failure — survival regression
    """

    def __init__(self, input_dim: int = 64, hidden_dim: int = 32):
        super().__init__()

        # Binary classification head
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
        )

        # Survival regression head (log-normal)
        self.survival = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 2),  # mu, log_sigma
        )

    def forward(self, embeddings: torch.Tensor) -> dict:
        """Predict failure probability and time-to-failure.

        Args:
            embeddings: (N, D) node embeddings from TGN

        Returns:
            dict with 'failure_prob' (N,), 'ttf_mu' (N,), 'ttf_sigma' (N,)
        """
        # Binary prediction
        logits = self.classifier(embeddings).squeeze(-1)
        failure_prob = torch.sigmoid(logits)

        # Survival prediction
        survival_out = self.survival(embeddings)
        ttf_mu = F.softplus(survival_out[:, 0])  # positive time
        ttf_sigma = F.softplus(survival_out[:, 1]) + 0.01  # positive std

        return {
            "failure_prob": failure_prob,
            "failure_logits": logits,
            "ttf_mu": ttf_mu,
            "ttf_sigma": ttf_sigma,
        }


class FocalLoss(nn.Module):
    """Focal loss for handling extreme class imbalance in anomaly detection."""

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        p_t = torch.exp(-bce)
        focal_weight = self.alpha * (1 - p_t) ** self.gamma
        return (focal_weight * bce).mean()
