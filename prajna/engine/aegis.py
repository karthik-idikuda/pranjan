"""PRAJNA — AEGIS: Adversarial-Hardened Ensemble Guard for Input Sanitization.

Novel Algorithm #7: 3-layer adversarial defence:
  Layer 1: Spectral anomaly filter (FFT energy analysis)
  Layer 2: Autoencoder reconstruction detector
  Layer 3: Temporal consistency GRU checker
  Ensemble: 2-of-3 majority vote to flag adversarial inputs
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SpectralFilter(nn.Module):
    """Layer 1: Detects adversarial perturbations via spectral energy deviation."""

    def __init__(self, window_size: int = 128, energy_threshold: float = 3.0):
        super().__init__()
        self.window_size = window_size
        self.energy_threshold = energy_threshold
        self._mean_energy: torch.Tensor | None = None
        self._std_energy: torch.Tensor | None = None

    def fit(self, clean_data: np.ndarray):
        """Learn spectral energy profile from clean training data.

        Args:
            clean_data: (T, D) clean telemetry
        """
        energies = []
        for t in range(self.window_size, clean_data.shape[0]):
            window = clean_data[t - self.window_size:t]
            fft = np.abs(np.fft.rfft(window, axis=0))
            energy = np.sum(fft ** 2, axis=0)
            energies.append(energy)

        energies = np.array(energies)
        self._mean_energy = torch.tensor(np.mean(energies, axis=0), dtype=torch.float32)
        self._std_energy = torch.tensor(np.std(energies, axis=0), dtype=torch.float32)
        self._std_energy[self._std_energy < 1e-8] = 1.0

    def check(self, window: torch.Tensor) -> dict:
        """Check if input has adversarial spectral signature.

        Args:
            window: (W, D) recent telemetry window

        Returns:
            dict with 'is_adversarial', 'deviation_score'
        """
        fft = torch.abs(torch.fft.rfft(window, dim=0))
        energy = torch.sum(fft ** 2, dim=0)

        if self._mean_energy is not None:
            deviation = torch.abs(energy - self._mean_energy.to(energy.device)) / self._std_energy.to(energy.device)
            max_dev = torch.max(deviation).item()
        else:
            max_dev = 0.0

        return {
            "is_adversarial": max_dev > self.energy_threshold,
            "deviation_score": max_dev,
        }


class AEDetector(nn.Module):
    """Layer 2: Autoencoder reconstruction error detector."""

    def __init__(self, input_dim: int = 8, latent_dim: int = 16, threshold: float = 2.5):
        super().__init__()
        self.threshold = threshold

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.decoder(z)

    def check(self, x: torch.Tensor) -> dict:
        """Check reconstruction error for adversarial detection.

        Args:
            x: (D,) or (B, D) input features

        Returns:
            dict with 'is_adversarial', 'reconstruction_error'
        """
        if x.dim() == 1:
            x = x.unsqueeze(0)

        with torch.no_grad():
            x_hat = self.forward(x)
            mse = F.mse_loss(x_hat, x, reduction="none").mean(dim=-1)
            max_error = mse.max().item()

        return {
            "is_adversarial": max_error > self.threshold,
            "reconstruction_error": max_error,
        }


class TemporalConsistencyChecker(nn.Module):
    """Layer 3: GRU-based temporal consistency checker."""

    def __init__(self, input_dim: int = 8, hidden_dim: int = 32, threshold: float = 2.0):
        super().__init__()
        self.threshold = threshold
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.predictor = nn.Linear(hidden_dim, input_dim)
        self._hidden: torch.Tensor | None = None

    def reset(self):
        self._hidden = None

    def check(self, x: torch.Tensor, history: torch.Tensor | None = None) -> dict:
        """Check temporal consistency.

        Args:
            x: (D,) current timestep features
            history: (T, D) recent history for context

        Returns:
            dict with 'is_adversarial', 'consistency_error'
        """
        if history is None or history.shape[0] < 2:
            return {"is_adversarial": False, "consistency_error": 0.0}

        with torch.no_grad():
            h_in = history.unsqueeze(0)  # (1, T, D)
            out, hidden = self.gru(h_in)
            predicted_next = self.predictor(out[:, -1, :])  # (1, D)

            error = F.mse_loss(predicted_next.squeeze(0), x).item()

        return {
            "is_adversarial": error > self.threshold,
            "consistency_error": error,
        }


class AEGIS(nn.Module):
    """AEGIS: 3-layer adversarial ensemble guard.

    Decision: Flag as adversarial if >= vote_threshold layers agree.
    Default: 2-of-3 majority vote.
    """

    def __init__(
        self,
        input_dim: int = 8,
        window_size: int = 128,
        spectral_threshold: float = 3.0,
        ae_latent_dim: int = 16,
        ae_threshold: float = 2.5,
        gru_hidden: int = 32,
        temporal_threshold: float = 2.0,
        vote_threshold: int = 2,
    ):
        super().__init__()
        self.vote_threshold = vote_threshold

        self.spectral = SpectralFilter(window_size, spectral_threshold)
        self.autoencoder = AEDetector(input_dim, ae_latent_dim, ae_threshold)
        self.temporal = TemporalConsistencyChecker(input_dim, gru_hidden, temporal_threshold)

    def check(
        self,
        x: torch.Tensor,
        window: torch.Tensor | None = None,
        history: torch.Tensor | None = None,
    ) -> dict:
        """Run full AEGIS adversarial check.

        Args:
            x: (D,) current features
            window: (W, D) recent spectral window
            history: (T, D) temporal history

        Returns:
            dict with 'is_adversarial', 'votes', 'layer_results'
        """
        results = {}
        votes = 0

        # Layer 1: Spectral
        if window is not None and window.shape[0] >= 4:
            r1 = self.spectral.check(window)
            results["spectral"] = r1
            if r1["is_adversarial"]:
                votes += 1
        else:
            results["spectral"] = {"is_adversarial": False, "deviation_score": 0.0}

        # Layer 2: Autoencoder
        r2 = self.autoencoder.check(x)
        results["autoencoder"] = r2
        if r2["is_adversarial"]:
            votes += 1

        # Layer 3: Temporal
        r3 = self.temporal.check(x, history)
        results["temporal"] = r3
        if r3["is_adversarial"]:
            votes += 1

        is_adversarial = votes >= self.vote_threshold

        if is_adversarial:
            logger.warning(f"AEGIS: Adversarial input detected! ({votes}/3 layers flagged)")

        return {
            "is_adversarial": is_adversarial,
            "votes": votes,
            "layer_results": results,
        }
