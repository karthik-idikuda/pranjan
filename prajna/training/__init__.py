"""PRAJNA — Training Pipeline: End-to-end model training.

Supports training of:
  - TGN (Temporal Graph Network) with Focal Loss
  - AEGIS adversarial guard (autoencoder, temporal GRU)
  - ThermalDiffGNN for post-flight
  - LocalDetector (scikit-learn, no gradient)
"""

import numpy as np
import torch
import torch.nn as nn
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Trainer:
    """Central training coordinator for all PRAJNA models."""

    def __init__(
        self,
        config: dict,
        device: str = "cpu",
        models_dir: str = "models",
    ):
        self.config = config
        self.device = torch.device(device)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def train_tgn(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
        val_features: Optional[np.ndarray] = None,
        val_labels: Optional[np.ndarray] = None,
    ) -> dict:
        """Train the Temporal Graph Network + FailurePredictor.

        Args:
            features: (T, N, D) training telemetry
            labels: (T, N) binary anomaly labels
            edge_index: (2, E) graph edges
            edge_weight: (E,) edge weights
            val_features: Optional validation features
            val_labels: Optional validation labels

        Returns:
            dict with trained models, training history
        """
        from prajna.engine.tgn import TGNEncoder, FailurePredictor, FocalLoss

        T, N, D = features.shape
        tgn_cfg = self.config.get("tgn", {})

        # Initialize models
        encoder = TGNEncoder(
            input_dim=D,
            hidden_dim=tgn_cfg.get("hidden_dim", 64),
            num_heads=tgn_cfg.get("num_heads", 4),
            num_layers=tgn_cfg.get("num_layers", 2),
            memory_dim=tgn_cfg.get("memory_dim", 64),
            time2vec_dim=tgn_cfg.get("time2vec_dim", 16),
            dropout=tgn_cfg.get("dropout", 0.1),
            num_nodes=N,
        ).to(self.device)

        predictor = FailurePredictor(
            input_dim=tgn_cfg.get("memory_dim", 64),
            hidden_dim=32,
        ).to(self.device)

        # Loss functions
        focal_loss = FocalLoss(
            gamma=self.config.get("training", {}).get("focal_loss_gamma", 2.0),
        )

        # Optimizer
        train_cfg = self.config.get("training", {})
        params = list(encoder.parameters()) + list(predictor.parameters())
        optimizer = torch.optim.AdamW(
            params,
            lr=train_cfg.get("learning_rate", 0.001),
            weight_decay=train_cfg.get("weight_decay", 1e-4),
        )

        # Scheduler
        epochs = train_cfg.get("epochs", 100)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        # Move data to tensors
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)

        best_val_loss = float("inf")
        patience_counter = 0
        patience = train_cfg.get("early_stopping_patience", 10)
        history = {"train_loss": [], "val_loss": []}

        logger.info(f"Training TGN: {epochs} epochs, {T} timesteps, {N} nodes")

        for epoch in range(epochs):
            encoder.train()
            predictor.train()
            encoder.reset_memory()

            epoch_loss = 0.0
            batch_size = train_cfg.get("batch_size", 64)

            for t in range(0, T - 1, batch_size):
                end = min(t + batch_size, T - 1)
                batch_loss = 0.0

                for step in range(t, end):
                    x = torch.tensor(features[step], dtype=torch.float32, device=self.device)
                    y = torch.tensor(labels[step], dtype=torch.float32, device=self.device)
                    ts = torch.tensor([step], dtype=torch.float32, device=self.device)

                    embeddings = encoder(x, edge_index, edge_weight, ts)
                    preds = predictor(embeddings)

                    loss = focal_loss(preds["failure_logits"], y)
                    batch_loss += loss

                optimizer.zero_grad()
                avg_batch_loss = batch_loss / (end - t)
                avg_batch_loss.backward()
                torch.nn.utils.clip_grad_norm_(params, max_norm=1.0)
                optimizer.step()

                epoch_loss += avg_batch_loss.item()

            scheduler.step()
            avg_epoch_loss = epoch_loss / max(1, T // batch_size)
            history["train_loss"].append(avg_epoch_loss)

            # Validation
            val_loss = self._validate_tgn(
                encoder, predictor, focal_loss,
                val_features, val_labels,
                edge_index, edge_weight,
            ) if val_features is not None else avg_epoch_loss

            history["val_loss"].append(val_loss)

            if epoch % 10 == 0:
                logger.info(
                    f"  Epoch {epoch:3d}/{epochs}: "
                    f"train_loss={avg_epoch_loss:.4f}, val_loss={val_loss:.4f}"
                )

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                torch.save(encoder.state_dict(), self.models_dir / "tgn_encoder.pt")
                torch.save(predictor.state_dict(), self.models_dir / "tgn_predictor.pt")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"  Early stopping at epoch {epoch}")
                    break

        logger.info(f"TGN training complete. Best val loss: {best_val_loss:.4f}")
        return {
            "encoder": encoder,
            "predictor": predictor,
            "history": history,
            "best_val_loss": best_val_loss,
        }

    @torch.no_grad()
    def _validate_tgn(self, encoder, predictor, loss_fn, features, labels, edge_index, edge_weight):
        encoder.eval()
        predictor.eval()
        encoder.reset_memory()

        T = features.shape[0]
        total_loss = 0.0

        for t in range(T - 1):
            x = torch.tensor(features[t], dtype=torch.float32, device=self.device)
            y = torch.tensor(labels[t], dtype=torch.float32, device=self.device)
            ts = torch.tensor([t], dtype=torch.float32, device=self.device)

            embeddings = encoder(x, edge_index, edge_weight, ts)
            preds = predictor(embeddings)
            loss = loss_fn(preds["failure_logits"], y)
            total_loss += loss.item()

        return total_loss / max(1, T - 1)

    def train_aegis(
        self,
        features: np.ndarray,
        labels: np.ndarray,
    ) -> dict:
        """Train AEGIS adversarial guard components.

        The autoencoder and temporal GRU are trained on normal data only.

        Args:
            features: (T, N, D) telemetry
            labels: (T, N) anomaly labels

        Returns:
            dict with trained AEGIS model
        """
        from prajna.engine.aegis import AEGIS

        # Separate normal vs anomalous data
        T, N, D = features.shape
        normal_mask = labels.sum(axis=1) == 0  # timesteps with no anomalies
        normal_data = features[normal_mask]

        logger.info(
            f"Training AEGIS on {len(normal_data)}/{T} normal timesteps"
        )

        aegis_cfg = self.config.get("aegis", {})
        aegis = AEGIS(
            input_dim=D,
            window_size=aegis_cfg.get("spectral", {}).get("window_size", 128),
            ae_latent_dim=aegis_cfg.get("autoencoder", {}).get("latent_dim", 16),
            gru_hidden=aegis_cfg.get("temporal", {}).get("gru_hidden", 32),
        )

        # Train autoencoder on normal data
        if hasattr(aegis, "ae_detector") and hasattr(aegis.ae_detector, "train_ae"):
            aegis.ae_detector.train_ae(normal_data, epochs=50)
        elif hasattr(aegis, "fit"):
            aegis.fit(normal_data)

        # Train temporal checker on normal sequences
        if hasattr(aegis, "temporal_checker") and hasattr(aegis.temporal_checker, "train_gru"):
            aegis.temporal_checker.train_gru(normal_data, epochs=30)

        logger.info("AEGIS training complete")
        return {"aegis": aegis}

    def train_local_detector(
        self,
        features: np.ndarray,
    ) -> dict:
        """Train local anomaly detectors (z-score + IsolationForest).

        Args:
            features: (T, N, D) training telemetry (normal data preferred)

        Returns:
            dict with trained LocalDetector
        """
        from prajna.engine.local_detector import LocalDetector

        detector = LocalDetector()
        detector.fit(features)
        logger.info("LocalDetector trained")

        import pickle
        with open(self.models_dir / "local_detector.pkl", "wb") as f:
            pickle.dump(detector, f)

        return {"detector": detector}

    def train_all(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
    ) -> dict:
        """Train all PRAJNA models in sequence.

        Args:
            features: (T, N, D) full dataset
            labels: (T, N) anomaly labels

        Returns:
            dict with all trained models
        """
        train_cfg = self.config.get("training", {})
        T = features.shape[0]
        train_end = int(T * train_cfg.get("train_ratio", 0.7))
        val_end = int(T * (train_cfg.get("train_ratio", 0.7) + train_cfg.get("val_ratio", 0.15)))

        train_f, train_l = features[:train_end], labels[:train_end]
        val_f, val_l = features[train_end:val_end], labels[train_end:val_end]

        results = {}

        # 1. Local detector
        logger.info("▶ Training LocalDetector...")
        results.update(self.train_local_detector(train_f))

        # 2. TGN
        logger.info("▶ Training TGN...")
        tgn_res = self.train_tgn(train_f, train_l, edge_index, edge_weight, val_f, val_l)
        results.update(tgn_res)

        # 3. AEGIS
        logger.info("▶ Training AEGIS...")
        aegis_res = self.train_aegis(train_f, train_l)
        results.update(aegis_res)

        logger.info("✅ All models trained")
        return results
