"""PRAJNA — Preprocessor: normalize, impute, window, FFT features."""

import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Preprocessor:
    """Telemetry preprocessing pipeline.

    Steps:
      1. Resample to fixed rate
      2. Z-score normalization (per-channel)
      3. Forward-fill imputation + mask
      4. Rolling window features (mean, std, min, max, slope)
      5. FFT frequency band features
      6. Residual computation
    """

    def __init__(
        self,
        window_size: int = 60,
        fft_bands: int = 3,
        normalize: bool = True,
    ):
        self.window_size = window_size
        self.fft_bands = fft_bands
        self.normalize = normalize
        self._means: Optional[np.ndarray] = None
        self._stds: Optional[np.ndarray] = None

    def fit(self, telemetry: np.ndarray) -> "Preprocessor":
        """Compute normalization statistics from training data.

        Args:
            telemetry: (T, N, D) raw telemetry tensor
        """
        T, N, D = telemetry.shape
        flat = telemetry.reshape(-1, D)
        self._means = np.nanmean(flat, axis=0)
        self._stds = np.nanstd(flat, axis=0)
        self._stds[self._stds < 1e-8] = 1.0  # prevent division by zero
        logger.info(f"Fit preprocessor: {N} nodes, {D} features")
        return self

    def transform(self, telemetry: np.ndarray) -> dict:
        """Apply full preprocessing pipeline.

        Args:
            telemetry: (T, N, D) raw telemetry

        Returns:
            dict with:
              - 'features': (T, N, D') processed features
              - 'mask': (T, N, D) imputation mask
              - 'window_features': (T, N, 5*D) rolling window stats
              - 'fft_features': (T, N, fft_bands*D) frequency features
        """
        T, N, D = telemetry.shape

        # Step 1: Imputation — forward fill + mask
        mask = ~np.isnan(telemetry)
        filled = self._forward_fill(telemetry.copy())

        # Step 2: Z-score normalization
        if self.normalize and self._means is not None:
            normalized = (filled - self._means) / self._stds
        else:
            normalized = filled

        # Step 3: Rolling window features
        window_feats = self._rolling_window_features(normalized)

        # Step 4: FFT features
        fft_feats = self._fft_features(normalized)

        return {
            "features": normalized,
            "mask": mask.astype(np.float32),
            "window_features": window_feats,
            "fft_features": fft_feats,
        }

    def fit_transform(self, telemetry: np.ndarray) -> dict:
        """Fit and transform in one call."""
        return self.fit(telemetry).transform(telemetry)

    def _forward_fill(self, data: np.ndarray) -> np.ndarray:
        """Forward-fill NaN values along time axis."""
        for t in range(1, data.shape[0]):
            nan_mask = np.isnan(data[t])
            data[t][nan_mask] = data[t - 1][nan_mask]
        # Fill any remaining NaNs with 0
        data = np.nan_to_num(data, nan=0.0)
        return data

    def _rolling_window_features(self, data: np.ndarray) -> np.ndarray:
        """Compute rolling window statistics: mean, std, min, max, slope."""
        T, N, D = data.shape
        W = self.window_size
        out = np.zeros((T, N, 5 * D), dtype=np.float32)

        for t in range(T):
            start = max(0, t - W + 1)
            window = data[start : t + 1]  # (w, N, D)

            out[t, :, 0*D:1*D] = np.mean(window, axis=0)    # mean
            out[t, :, 1*D:2*D] = np.std(window, axis=0)     # std
            out[t, :, 2*D:3*D] = np.min(window, axis=0)     # min
            out[t, :, 3*D:4*D] = np.max(window, axis=0)     # max

            # Slope via linear regression
            if window.shape[0] > 1:
                x = np.arange(window.shape[0], dtype=np.float32)
                x_centered = x - x.mean()
                denominator = np.sum(x_centered ** 2) + 1e-8
                for n in range(N):
                    for d in range(D):
                        out[t, n, 4*D + d] = np.sum(x_centered * (window[:, n, d] - window[:, n, d].mean())) / denominator

        return out

    def _fft_features(self, data: np.ndarray) -> np.ndarray:
        """Compute FFT energy in frequency bands per sensor."""
        T, N, D = data.shape
        W = self.window_size
        bands = self.fft_bands
        out = np.zeros((T, N, bands * D), dtype=np.float32)

        for t in range(T):
            start = max(0, t - W + 1)
            window = data[start : t + 1]  # (w, N, D)
            L = window.shape[0]

            if L < 4:
                continue

            for n in range(N):
                for d in range(D):
                    fft_vals = np.abs(np.fft.rfft(window[:, n, d]))
                    freq_len = len(fft_vals)
                    band_size = max(1, freq_len // bands)

                    for b in range(bands):
                        s = b * band_size
                        e = min(s + band_size, freq_len)
                        out[t, n, b * D + d] = np.sum(fft_vals[s:e] ** 2)

        return out
