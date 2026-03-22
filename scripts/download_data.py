"""PRAJNA — Download real datasets script.

Usage:
  export KAGGLE_API_TOKEN=KGAT_...
  python scripts/download_data.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prajna.data import DataDownloader


def main():
    print("=" * 60)
    print("  🛰️  PRAJNA — Real Dataset Downloader")
    print("=" * 60)
    print()
    print("  Downloading real spacecraft telemetry datasets:")
    print("  1. NASA SMAP + MSL (81 channels, expert-labeled anomalies)")
    print("  2. NASA C-MAPSS (turbofan engine degradation, 21 sensors)")
    print("  3. ESA OPS-SAT (CubeSat telemetry with anomaly labels)")
    print()

    downloader = DataDownloader(data_dir="data/raw")
    paths = downloader.download_all()

    print()
    print("  📊 Download Summary:")
    for name, path in paths.items():
        print(f"     ✅ {name} → {path}")

    print()
    print("  🎉 All datasets downloaded!")
    print("  Next: python -m prajna preprocess")
    print()


if __name__ == "__main__":
    main()
