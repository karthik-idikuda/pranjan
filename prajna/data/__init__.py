"""PRAJNA — Real Data Download & Adapter Pipeline.

Downloads and adapts real spacecraft telemetry from:
  1. NASA SMAP/MSL (Kaggle)
  2. NASA C-MAPSS (Kaggle)
  3. ESA OPS-SAT (Kaggle)
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataDownloader:
    """Downloads real spacecraft telemetry datasets via Kaggle API."""

    DATASETS = {
        "nasa_smap_msl": {
            "kaggle_id": "patrickfleith/nasa-anomaly-detection-dataset-smap-msl",
            "description": "NASA SMAP + MSL telemetry (81 channels, 105 anomalies)",
        },
        "nasa_cmapss": {
            "kaggle_id": "behrad3d/nasa-cmaps",
            "description": "NASA C-MAPSS Turbofan engine degradation (21 sensors)",
        },
        "esa_opssat": {
            "kaggle_id": "patrickfleith/opssat-ad",
            "description": "ESA OPS-SAT CubeSat telemetry with anomaly labels",
        },
    }

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._setup_kaggle_auth()

    def _setup_kaggle_auth(self):
        """Set up Kaggle authentication from environment or config."""
        token = os.environ.get("KAGGLE_API_TOKEN")
        if token:
            os.environ["KAGGLE_API_TOKEN"] = token
            logger.info("Kaggle API token found in environment")
        else:
            kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
            if kaggle_json.exists():
                logger.info(f"Using Kaggle credentials from {kaggle_json}")
            else:
                logger.warning("No Kaggle credentials found. Set KAGGLE_API_TOKEN env var.")

    def download_dataset(self, dataset_key: str, force: bool = False) -> Path:
        """Download a specific dataset from Kaggle."""
        if dataset_key not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_key}. Available: {list(self.DATASETS.keys())}")

        info = self.DATASETS[dataset_key]
        dest = self.data_dir / dataset_key

        if dest.exists() and not force:
            logger.info(f"Dataset {dataset_key} already exists at {dest}. Use force=True to re-download.")
            return dest

        dest.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading {info['description']}...")

        try:
            import kagglehub
            path = kagglehub.dataset_download(info["kaggle_id"])
            logger.info(f"Downloaded to: {path}")

            # Copy/link to our data directory
            import shutil
            if Path(path).is_dir():
                for item in Path(path).rglob("*"):
                    if item.is_file():
                        rel = item.relative_to(path)
                        target = dest / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target)

            logger.info(f"Dataset {dataset_key} ready at {dest}")
            return dest

        except Exception as e:
            logger.error(f"Failed to download {dataset_key}: {e}")
            raise

    def download_all(self, force: bool = False) -> dict[str, Path]:
        """Download all datasets."""
        paths = {}
        for key in self.DATASETS:
            try:
                paths[key] = self.download_dataset(key, force=force)
            except Exception as e:
                logger.error(f"Skipping {key}: {e}")
        return paths


class DataAdapter:
    """Adapts real telemetry datasets to PRAJNA's unified schema.

    Unified Schema:
        {
            "telemetry": np.ndarray (T, N, D),  # time × nodes × features
            "labels": np.ndarray (T, N),         # anomaly labels
            "timestamps": np.ndarray (T,),
            "metadata": dict
        }
    """

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)

    def load_nasa_smap_msl(self, subset: str = "smap") -> dict:
        """Load NASA SMAP or MSL telemetry dataset.

        Args:
            subset: 'smap' (55 channels) or 'msl' (26 channels)

        Returns:
            Unified schema dict with telemetry, labels, timestamps, metadata
        """
        base = self.data_dir / "nasa_smap_msl"

        # Find the data files
        train_dir = None
        test_dir = None
        labels_file = None

        for candidate in [base, *base.iterdir()] if base.exists() else []:
            if not Path(candidate).is_dir():
                continue
            for child in Path(candidate).iterdir():
                if child.name == "train":
                    train_dir = child
                elif child.name == "test":
                    test_dir = child
                elif child.name == "labeled_anomalies.csv":
                    labels_file = child

        # If not found at top level, search recursively
        if train_dir is None:
            for p in base.rglob("train"):
                if p.is_dir():
                    train_dir = p
                    break
        if test_dir is None:
            for p in base.rglob("test"):
                if p.is_dir():
                    test_dir = p
                    break
        if labels_file is None:
            for p in base.rglob("labeled_anomalies.csv"):
                labels_file = p
                break

        if train_dir is None or test_dir is None:
            raise FileNotFoundError(
                f"NASA SMAP/MSL data not found in {base}. Run download first."
            )

        # Load anomaly labels
        anomaly_df = pd.read_csv(labels_file) if labels_file else pd.DataFrame()
        if not anomaly_df.empty:
            anomaly_df = anomaly_df[anomaly_df["spacecraft"] == subset.upper()]

        # Load all channels for the subset
        channels_data = []
        channel_names = []

        for npy_file in sorted(test_dir.glob("*.npy")):
            chan_name = npy_file.stem
            # Filter by subset prefix
            if subset == "smap" and not chan_name.startswith(("P-", "S-", "E-", "D-", "A-", "G-", "T-", "F-", "M-", "B-", "R-")):
                continue
            if subset == "msl" and not chan_name.startswith(("M-", "C-", "T-", "D-")):
                continue

            data = np.load(npy_file)
            channels_data.append(data)
            channel_names.append(chan_name)

        if not channels_data:
            # Load all files if prefix filtering returned nothing
            for npy_file in sorted(test_dir.glob("*.npy")):
                data = np.load(npy_file)
                channels_data.append(data)
                channel_names.append(npy_file.stem)

        logger.info(f"Loaded {len(channels_data)} channels for {subset}")

        # Stack into unified tensor — each channel may have different features
        # Pad to max feature dimension
        T = min(arr.shape[0] for arr in channels_data) if channels_data else 0
        N = len(channels_data)
        D = max(arr.shape[1] for arr in channels_data) if channels_data else 0

        telemetry = np.zeros((T, N, D), dtype=np.float32)
        for i, arr in enumerate(channels_data):
            d = arr.shape[1]
            telemetry[:T, i, :d] = arr[:T, :]

        # Build anomaly labels (T, N)
        labels = np.zeros((T, N), dtype=np.int32)
        for _, row in anomaly_df.iterrows():
            chan_name = row.get("chan_id", "")
            if chan_name in channel_names:
                idx = channel_names.index(chan_name)
                start = int(row.get("anomaly_sequences", "").split(",")[0].strip("[]() ") or 0) if "anomaly_sequences" in row else 0
                end = min(start + 100, T)
                labels[start:end, idx] = 1

        timestamps = np.arange(T, dtype=np.float64)

        return {
            "telemetry": telemetry,
            "labels": labels,
            "timestamps": timestamps,
            "metadata": {
                "source": f"NASA {subset.upper()}",
                "num_channels": N,
                "num_features": D,
                "num_timesteps": T,
                "channel_names": channel_names,
            },
        }

    def load_nasa_cmapss(self, subset: str = "FD001") -> dict:
        """Load NASA C-MAPSS turbofan engine degradation dataset.

        Args:
            subset: FD001, FD002, FD003, or FD004

        Returns:
            Dict with engine_data, rul_labels, sensor_names
        """
        base = self.data_dir / "nasa_cmapss"

        # Find the data file
        train_file = None
        rul_file = None

        for p in base.rglob(f"train_{subset}.txt"):
            train_file = p
            break
        for p in base.rglob(f"RUL_{subset}.txt"):
            rul_file = p
            break

        if train_file is None:
            # Try alternative naming
            for p in base.rglob(f"*{subset}*train*"):
                train_file = p
                break
            for p in base.rglob(f"*{subset}*RUL*"):
                rul_file = p
                break

        if train_file is None:
            raise FileNotFoundError(f"C-MAPSS {subset} not found in {base}")

        # C-MAPSS columns: unit, cycle, op1, op2, op3, s1..s21
        sensor_names = [f"sensor_{i}" for i in range(1, 22)]
        cols = ["unit", "cycle", "op1", "op2", "op3"] + sensor_names

        df = pd.read_csv(train_file, sep=r"\s+", header=None, names=cols)

        # Compute RUL for each unit
        max_cycles = df.groupby("unit")["cycle"].max()
        df["rul"] = df.apply(lambda r: max_cycles[r["unit"]] - r["cycle"], axis=1)

        # Get sensor data per engine unit
        units = df["unit"].unique()
        sensor_cols = sensor_names

        # Stack all units into a single tensor
        all_sensors = df[sensor_cols].values.astype(np.float32)
        all_rul = df["rul"].values.astype(np.float32)

        logger.info(f"Loaded C-MAPSS {subset}: {len(units)} engines, {len(df)} total cycles")

        return {
            "sensor_data": all_sensors,
            "rul_labels": all_rul,
            "unit_ids": df["unit"].values,
            "cycles": df["cycle"].values,
            "metadata": {
                "source": f"NASA C-MAPSS {subset}",
                "num_engines": len(units),
                "num_sensors": len(sensor_cols),
                "num_cycles": len(df),
                "sensor_names": sensor_cols,
            },
        }

    def load_esa_opssat(self) -> dict:
        """Load ESA OPS-SAT CubeSat telemetry dataset."""
        base = self.data_dir / "esa_opssat"

        if not base.exists():
            raise FileNotFoundError(f"ESA OPS-SAT data not found in {base}")

        # OPS-SAT typically comes as CSV files
        csv_files = list(base.rglob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {base}")

        # Load the main telemetry file
        main_file = csv_files[0]  # Primary telemetry
        df = pd.read_csv(main_file)

        logger.info(f"Loaded ESA OPS-SAT: {len(df)} rows, {len(df.columns)} columns")

        # Extract numeric columns as features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        telemetry = df[numeric_cols].values.astype(np.float32)

        # Look for label column
        label_cols = [c for c in df.columns if "label" in c.lower() or "anomaly" in c.lower()]
        if label_cols:
            labels = df[label_cols[0]].values.astype(np.int32)
        else:
            labels = np.zeros(len(df), dtype=np.int32)

        return {
            "telemetry": telemetry,
            "labels": labels,
            "metadata": {
                "source": "ESA OPS-SAT",
                "num_features": len(numeric_cols),
                "num_timesteps": len(df),
                "feature_names": numeric_cols,
            },
        }
