"""PRAJNA — CLI: Main command-line interface."""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("prajna")


def cmd_download(args):
    """Download real datasets from Kaggle."""
    from prajna.data import DataDownloader

    downloader = DataDownloader(data_dir=args.data_dir)

    if args.dataset == "all":
        paths = downloader.download_all(force=args.force)
        for name, path in paths.items():
            print(f"  ✅ {name} → {path}")
    else:
        path = downloader.download_dataset(args.dataset, force=args.force)
        print(f"  ✅ {args.dataset} → {path}")


def cmd_preprocess(args):
    """Preprocess downloaded data into unified format."""
    from prajna.data import DataAdapter
    from prajna.data.preprocessor import Preprocessor
    import numpy as np
    from pathlib import Path

    adapter = DataAdapter(data_dir=args.data_dir)
    preprocessor = Preprocessor(window_size=60)

    # Load NASA SMAP
    try:
        data = adapter.load_nasa_smap_msl(subset="smap")
        processed = preprocessor.fit_transform(data["telemetry"])

        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        np.save(out_dir / "smap_features.npy", processed["features"])
        np.save(out_dir / "smap_labels.npy", data["labels"])
        print(f"  ✅ SMAP preprocessed: {processed['features'].shape}")
    except Exception as e:
        logger.error(f"SMAP preprocessing failed: {e}")

    # Load C-MAPSS
    try:
        cmapss = adapter.load_nasa_cmapss(subset="FD001")
        out_dir = Path(args.output_dir)
        np.save(out_dir / "cmapss_sensors.npy", cmapss["sensor_data"])
        np.save(out_dir / "cmapss_rul.npy", cmapss["rul_labels"])
        print(f"  ✅ C-MAPSS preprocessed: {cmapss['sensor_data'].shape}")
    except Exception as e:
        logger.error(f"C-MAPSS preprocessing failed: {e}")


def cmd_train(args):
    """Train PRAJNA models on preprocessed data."""
    from prajna.config import Config
    from prajna.engine import LocalDetector, SDWAP, AEGIS, SHAKTI
    from prajna.graph import GraphBuilder
    import numpy as np
    import torch
    from pathlib import Path

    config = Config.load(args.config)
    print("🚀 PRAJNA Training Pipeline")
    print(f"   Config: {args.config}")

    # Load preprocessed data
    data_dir = Path(args.output_dir if hasattr(args, 'output_dir') else "data/processed")
    features_file = data_dir / "smap_features.npy"
    labels_file = data_dir / "smap_labels.npy"

    if not features_file.exists():
        print("❌ No preprocessed data found. Run 'prajna preprocess' first.")
        return

    features = np.load(features_file)
    labels = np.load(labels_file)
    T, N, D = features.shape
    print(f"   Data: {T} timesteps × {N} nodes × {D} features")

    # Split data
    train_end = int(T * 0.7)
    val_end = int(T * 0.85)

    train_data = features[:train_end]
    val_data = features[train_end:val_end]
    test_data = features[val_end:]
    test_labels = labels[val_end:]

    # 1. Build graph
    graph = GraphBuilder(num_nodes=N)
    graph.update_dynamic(train_data[-1000:])
    adjacency = graph.get_adjacency()
    print(f"   Graph: {N} nodes, {int(np.sum(adjacency > 0))} edges")

    # 2. Train local detectors
    detector = LocalDetector()
    detector.fit(train_data)
    print("   ✅ Local detectors trained")

    # 3. Run SDWAP on test data
    sdwap = SDWAP(
        max_iterations=config.get("sdwap", {}).get("max_iterations", 5) if isinstance(config.get("sdwap"), dict) else 5,
    )

    detection_result = detector.batch_score(test_data)
    scores = detection_result["scores"]
    confidences = detection_result["confidences"]

    propagated_results = sdwap.batch_propagate(scores, adjacency, confidences)
    propagated_scores = np.array([r["propagated_scores"] for r in propagated_results])

    print(f"   ✅ SDWAP propagation complete: {propagated_scores.shape}")

    # 4. Calibrate SHAKTI
    shakti = SHAKTI()
    flat_scores = propagated_scores.flatten()
    flat_labels = test_labels.flatten().astype(np.float32)

    # Use first half of test as calibration
    cal_end = len(flat_scores) // 2
    shakti.calibrate(flat_scores[:cal_end], flat_labels[:cal_end])
    print(f"   ✅ SHAKTI calibrated: quantile={shakti._quantile:.4f}")

    # 5. Evaluate
    from sklearn.metrics import roc_auc_score, f1_score

    threshold = 0.5
    preds_binary = (flat_scores[cal_end:] > threshold).astype(int)
    true_binary = flat_labels[cal_end:].astype(int)

    if len(np.unique(true_binary)) > 1:
        auc = roc_auc_score(true_binary, flat_scores[cal_end:])
        f1 = f1_score(true_binary, preds_binary, zero_division=0)
        print(f"\n   📊 Results:")
        print(f"      ROC-AUC: {auc:.4f}")
        print(f"      F1:      {f1:.4f}")
    else:
        print("   ⚠️  No anomalies in test split — adjust data split")

    # Save models
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    import pickle
    with open(models_dir / "local_detector.pkl", "wb") as f:
        pickle.dump(detector, f)
    with open(models_dir / "graph.pkl", "wb") as f:
        pickle.dump(graph, f)
    with open(models_dir / "shakti.pkl", "wb") as f:
        pickle.dump(shakti, f)

    print(f"\n   ✅ Models saved to {models_dir}/")
    print("   🎉 Training complete!")


def cmd_demo(args):
    """Run a live demo of the inference pipeline."""
    from prajna.graph import GraphBuilder
    from prajna.engine import SDWAP, LocalDetector, KAVACH, NLGEngine
    import numpy as np

    print("🛰️  PRAJNA Live Demo")
    print("=" * 60)

    # Build graph
    graph = GraphBuilder()
    adj = graph.get_adjacency()

    # Simulate inference on a single timestep
    N = 13
    D = 8
    np.random.seed(42)

    # Normal telemetry with one anomaly injected in EPS (node 0)
    telemetry = np.random.randn(N, D).astype(np.float32) * 0.1
    telemetry[0] += 3.0  # Inject anomaly in EPS

    # Fit quick detector on dummy normal data
    normal = np.random.randn(100, N, D).astype(np.float32) * 0.1
    detector = LocalDetector()
    detector.fit(normal)

    # Detect
    local_result = detector.score(telemetry)
    print(f"\n📡 Local Detection:")
    for i, name in enumerate(graph.node_names):
        score = local_result["scores"][i]
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        flag = " ⚠️" if score > 0.5 else ""
        print(f"   {name:8s} [{bar}] {score:.3f}{flag}")

    # SDWAP propagation
    sdwap = SDWAP()
    propagated = sdwap.propagate(local_result["scores"], adj, local_result["confidences"])

    print(f"\n🔄 SDWAP Propagation ({propagated['iterations']} iterations):")
    for i, name in enumerate(graph.node_names):
        before = local_result["scores"][i]
        after = propagated["propagated_scores"][i]
        delta = after - before
        flag = f" ↑{delta:.3f}" if delta > 0.01 else ""
        bar = "█" * int(after * 20) + "░" * (20 - int(after * 20))
        print(f"   {name:8s} [{bar}] {after:.3f}{flag}")

    # KAVACH verification
    kavach = KAVACH()
    verification = kavach.verify_all({
        "scores": propagated["propagated_scores"],
        "sdwap_iterations": propagated["iterations"],
        "sdwap_max_iter": 5,
    })

    print(f"\n🛡️  KAVACH Verification:")
    for r in verification["results"]:
        status = "✅" if r["satisfied"] else "❌"
        print(f"   {status} {r['property']}")

    print(f"\n   Decision: {'✅ SAFE' if verification['all_satisfied'] else '🚫 BLOCKED'}")

    # NLG Alerts
    nlg = NLGEngine()
    print(f"\n📋 NLG Alerts:")
    for i in range(N):
        if propagated["propagated_scores"][i] > 0.3:
            alert = nlg.generate_alert(
                i,
                local_result["scores"][i],
                propagated["propagated_scores"][i],
                propagated,
            )
            print(f"\n   [{alert['risk_level']}] {alert['node_name']}")
            print(f"   {alert['explanation']}")
            if alert["actions"]:
                for a in alert["actions"]:
                    print(f"     → {a}")

    print("=" * 60)


def cmd_synthetic(args):
    """Generate synthetic spacecraft telemetry data."""
    from prajna.data.synthetic_generator import SyntheticGenerator
    import numpy as np
    from pathlib import Path

    gen = SyntheticGenerator(num_nodes=13, feature_dim=8, seed=args.seed)

    print("🔧 Generating synthetic spacecraft telemetry...")
    num_faults = max(3, int(args.timesteps * args.anomaly_ratio / 100))
    dataset = gen.generate_dataset(
        T=args.timesteps,
        num_faults=num_faults,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    np.save(out_dir / "synthetic_features.npy", dataset["telemetry"])
    np.save(out_dir / "synthetic_labels.npy", dataset["labels"])

    T, N, D = dataset["telemetry"].shape
    anom_pct = dataset["labels"].mean() * 100
    print(f"   ✅ Generated: {T} timesteps × {N} nodes × {D} features")
    print(f"   Anomaly rate: {anom_pct:.1f}%")
    print(f"   Saved to: {out_dir}/")

    # Also generate post-flight data
    pf_data = gen.generate_postflight_data(num_flights=args.flights)
    np.save(out_dir / "postflight_features.npy", pf_data["component_features"])
    print(f"   ✅ Post-flight data: {args.flights} flights generated")


def cmd_evaluate(args):
    """Run evaluation on test data."""
    from prajna.evaluation import Evaluator, EvaluationResult
    from prajna.engine import LocalDetector, SDWAP
    from prajna.graph import GraphBuilder
    import numpy as np
    from pathlib import Path

    data_dir = Path(args.data_dir)
    evaluator = Evaluator()

    # Try synthetic data first, then real
    feat_file = data_dir / "synthetic_features.npy"
    label_file = data_dir / "synthetic_labels.npy"
    if not feat_file.exists():
        feat_file = data_dir / "smap_features.npy"
        label_file = data_dir / "smap_labels.npy"

    if not feat_file.exists():
        print("❌ No data found. Run 'prajna synthetic' or 'prajna preprocess' first.")
        return

    features = np.load(feat_file)
    labels = np.load(label_file)
    T, N, D = features.shape

    # Split
    train_end = int(T * 0.7)
    train_data = features[:train_end]
    test_data = features[train_end:]
    test_labels = labels[train_end:]

    print("📊 PRAJNA Evaluation")
    print(f"   Data: {T} timesteps, test split: {test_data.shape[0]}")

    # Train detector
    detector = LocalDetector()
    detector.fit(train_data)

    # Score test data
    det_result = detector.batch_score(test_data)
    scores = det_result["scores"]  # (T_test, N)

    # SDWAP
    graph = GraphBuilder(num_nodes=N)
    graph.update_dynamic(train_data[-500:])
    adj = graph.get_adjacency()

    sdwap = SDWAP()
    propagated_all = sdwap.batch_propagate(scores, adj, det_result["confidences"])
    prop_scores = np.array([r["propagated_scores"] for r in propagated_all])

    # Flatten for evaluation
    flat_scores = prop_scores.flatten()
    flat_labels = test_labels.flatten().astype(float)

    result = evaluator.full_evaluation(
        detection_labels=flat_labels,
        detection_scores=flat_scores,
        propagated_scores=prop_scores[-1] if len(prop_scores) > 0 else None,
        adjacency=adj,
        injection_node=0,
    )

    print(result.summary())


def cmd_dashboard(args):
    """Launch the PRAJNA web dashboard."""
    from prajna.dashboard import run_dashboard
    run_dashboard(host=args.host, port=args.port, debug=args.debug)


def main():
    parser = argparse.ArgumentParser(
        prog="prajna",
        description="PRAJNA — Spacecraft Health Intelligence Platform",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Download
    dl = subparsers.add_parser("download", help="Download real datasets")
    dl.add_argument("--dataset", default="all", choices=["all", "nasa_smap_msl", "nasa_cmapss", "esa_opssat"])
    dl.add_argument("--data-dir", default="data/raw")
    dl.add_argument("--force", action="store_true")

    # Preprocess
    pp = subparsers.add_parser("preprocess", help="Preprocess downloaded data")
    pp.add_argument("--data-dir", default="data/raw")
    pp.add_argument("--output-dir", default="data/processed")

    # Synthetic
    sy = subparsers.add_parser("synthetic", help="Generate synthetic telemetry data")
    sy.add_argument("--timesteps", type=int, default=5000)
    sy.add_argument("--anomaly-ratio", type=float, default=0.05)
    sy.add_argument("--flights", type=int, default=10)
    sy.add_argument("--seed", type=int, default=42)
    sy.add_argument("--output-dir", default="data/processed")

    # Train
    tr = subparsers.add_parser("train", help="Train PRAJNA models")
    tr.add_argument("--config", default="config/default.yaml")
    tr.add_argument("--output-dir", default="data/processed")

    # Evaluate
    ev = subparsers.add_parser("evaluate", help="Run evaluation metrics")
    ev.add_argument("--data-dir", default="data/processed")

    # Dashboard
    db = subparsers.add_parser("dashboard", help="Launch web dashboard")
    db.add_argument("--host", default="127.0.0.1")
    db.add_argument("--port", type=int, default=5000)
    db.add_argument("--debug", action="store_true")

    # Demo
    subparsers.add_parser("demo", help="Run live inference demo")

    args = parser.parse_args()

    if args.command == "download":
        cmd_download(args)
    elif args.command == "preprocess":
        cmd_preprocess(args)
    elif args.command == "synthetic":
        cmd_synthetic(args)
    elif args.command == "train":
        cmd_train(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "demo":
        cmd_demo(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
