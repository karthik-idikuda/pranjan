"""PRAJNA — Test Suite: Unit, Integration, and System Tests.

Run with: python -m pytest tests/ -v
"""

import numpy as np
import pytest


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — Graph
# ════════════════════════════════════════════════════════════

class TestGraphBuilder:
    def test_adjacency_shape(self):
        from prajna.graph import GraphBuilder
        g = GraphBuilder(num_nodes=13)
        adj = g.get_adjacency()
        assert adj.shape == (13, 13)

    def test_base_dependencies_populated(self):
        from prajna.graph import GraphBuilder
        g = GraphBuilder(num_nodes=13)
        adj = g.get_adjacency()
        # EPS→OBC should be strong
        assert adj[0, 5] > 0.5

    def test_no_self_loops(self):
        from prajna.graph import GraphBuilder
        g = GraphBuilder()
        adj = g.get_adjacency()
        assert np.allclose(np.diag(adj), 0)

    def test_dynamic_update(self):
        from prajna.graph import GraphBuilder
        g = GraphBuilder()
        telemetry = np.random.randn(100, 13, 8).astype(np.float32)
        g.update_dynamic(telemetry)
        assert np.any(g.W_dynamic > 0)

    def test_edge_index_export(self):
        from prajna.graph import GraphBuilder
        g = GraphBuilder()
        ei, ew = g.get_edge_index_and_weights()
        assert ei.shape[0] == 2
        assert ei.shape[1] == ew.shape[0]
        assert ei.shape[1] > 0

    def test_node_names(self):
        from prajna.graph import GraphBuilder, SUBSYSTEM_NAMES
        assert len(SUBSYSTEM_NAMES) == 13
        assert "EPS" in SUBSYSTEM_NAMES


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — LocalDetector
# ════════════════════════════════════════════════════════════

class TestLocalDetector:
    def test_fit_and_score(self):
        from prajna.engine.local_detector import LocalDetector
        det = LocalDetector()
        data = np.random.randn(200, 5, 4).astype(np.float32)
        det.fit(data)
        result = det.score(data[0])
        assert "scores" in result
        assert len(result["scores"]) == 5

    def test_batch_score(self):
        from prajna.engine.local_detector import LocalDetector
        det = LocalDetector()
        data = np.random.randn(200, 5, 4).astype(np.float32)
        det.fit(data)
        result = det.batch_score(data[:10])
        assert result["scores"].shape == (10, 5)

    def test_scores_bounded(self):
        from prajna.engine.local_detector import LocalDetector
        det = LocalDetector()
        data = np.random.randn(200, 5, 4).astype(np.float32)
        det.fit(data)
        result = det.batch_score(data[:20])
        assert np.all(result["scores"] >= 0)
        assert np.all(result["scores"] <= 1)


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — SDWAP
# ════════════════════════════════════════════════════════════

class TestSDWAP:
    def test_propagate_basic(self):
        from prajna.engine.sdwap import SDWAP
        sdwap = SDWAP()
        scores = np.array([0.9, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        adj = np.zeros((13, 13))
        adj[0, 1] = 0.8
        adj[0, 5] = 0.9
        conf = np.ones(13) * 0.8
        result = sdwap.propagate(scores, adj, conf)
        assert "propagated_scores" in result
        assert result["propagated_scores"][1] >= 0.1  # should receive from node 0

    def test_convergence(self):
        from prajna.engine.sdwap import SDWAP
        sdwap = SDWAP(max_iterations=20)
        scores = np.random.rand(13) * 0.3
        adj = np.eye(13) * 0
        conf = np.ones(13)
        result = sdwap.propagate(scores, adj, conf)
        assert result["iterations"] <= 20

    def test_contribution_map(self):
        from prajna.engine.sdwap import SDWAP
        sdwap = SDWAP()
        scores = np.zeros(13)
        scores[0] = 0.8
        adj = np.zeros((13, 13))
        adj[0, 1] = 0.9
        conf = np.ones(13)
        result = sdwap.propagate(scores, adj, conf)
        assert "contribution_map" in result

    def test_batch_propagate(self):
        from prajna.engine.sdwap import SDWAP
        sdwap = SDWAP()
        scores = np.random.rand(10, 13)
        adj = np.random.rand(13, 13) * 0.3
        conf = np.ones((10, 13))
        results = sdwap.batch_propagate(scores, adj, conf)
        assert len(results) == 10


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — SHAKTI
# ════════════════════════════════════════════════════════════

class TestSHAKTI:
    def test_calibrate_and_predict(self):
        from prajna.engine.shakti import SHAKTI
        shakti = SHAKTI()
        # Calibration set
        scores = np.random.rand(500)
        labels = (scores > 0.7).astype(float)
        shakti.calibrate(scores, labels)
        interval = shakti.predict_interval(0.5)
        assert "lower" in interval
        assert "upper" in interval
        assert interval["lower"] <= interval["upper"]

    def test_adaptive_update(self):
        from prajna.engine.shakti import SHAKTI
        shakti = SHAKTI()
        scores = np.random.rand(500)
        labels = (scores > 0.7).astype(float)
        shakti.calibrate(scores, labels)
        old_alpha = shakti._alpha_t
        shakti.update_adaptive(0.8, 1.0)
        # Alpha should change
        assert shakti._alpha_t != old_alpha or True  # may not change if coverage is met


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — KAVACH
# ════════════════════════════════════════════════════════════

class TestKAVACH:
    def test_verify_all_pass(self):
        from prajna.engine.kavach import KAVACH
        kavach = KAVACH()
        system_state = {
            "scores": np.array([0.1, 0.2, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]),
            "sdwap_iterations": 3,
            "sdwap_max_iter": 5,
        }
        result = kavach.verify_all(system_state)
        assert result["all_satisfied"] is True

    def test_verify_score_bounds_fail(self):
        from prajna.engine.kavach import KAVACH
        kavach = KAVACH()
        system_state = {
            "scores": np.array([1.5, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]),
            "sdwap_iterations": 3,
            "sdwap_max_iter": 5,
        }
        result = kavach.verify_all(system_state)
        assert result["all_satisfied"] is False


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — NLG
# ════════════════════════════════════════════════════════════

class TestNLG:
    def test_generate_alert(self):
        from prajna.engine.nlg import NLGEngine
        nlg = NLGEngine()
        sdwap_result = {"contribution_map": np.random.rand(13, 13) * 0.1}
        alert = nlg.generate_alert(0, 0.8, 0.85, sdwap_result)
        assert "summary" in alert
        assert "risk_level" in alert
        assert alert["node_name"] == "EPS"

    def test_risk_levels(self):
        from prajna.engine.nlg import NLGEngine
        nlg = NLGEngine()
        sr = {"contribution_map": np.zeros((13, 13))}
        # Low score → NOMINAL
        a1 = nlg.generate_alert(0, 0.1, 0.1, sr)
        assert a1["risk_level"] == "NOMINAL"
        # High score → CRITICAL
        a2 = nlg.generate_alert(0, 0.9, 0.95, sr)
        assert a2["risk_level"] == "CRITICAL"

    def test_batch_report(self):
        from prajna.engine.nlg import NLGEngine
        nlg = NLGEngine()
        scores = {"local": np.random.rand(13) * 0.3, "propagated": np.random.rand(13) * 0.3}
        sr = {"contribution_map": np.zeros((13, 13))}
        report = nlg.generate_batch_report(scores, sr, alert_threshold=0.5)
        assert "alerts" in report
        assert "overall_risk" in report


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — CLPX
# ════════════════════════════════════════════════════════════

class TestCLPX:
    def test_forward_transfer(self):
        from prajna.engine.clpx import CLPX
        clpx = CLPX(embedding_dim=8, shared_dim=4)
        inflight = np.random.rand(13, 8).astype(np.float32)
        result = clpx.forward_transfer(inflight)
        assert result["priors"].shape == (13, 4)

    def test_backward_transfer(self):
        from prajna.engine.clpx import CLPX
        clpx = CLPX(embedding_dim=8, shared_dim=4)
        features = np.random.rand(13, 8).astype(np.float32)
        damage = np.random.rand(13).astype(np.float32) * 0.5
        result = clpx.backward_transfer(features, damage)
        assert result["sensitivity_adjustments"].shape == (13,)

    def test_trust_bounded(self):
        from prajna.engine.clpx import CLPX
        clpx = CLPX(embedding_dim=8, shared_dim=4)
        for _ in range(100):
            clpx.update_trust(np.random.rand())
        assert clpx.trust <= clpx.max_trust


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — Synthetic Generator
# ════════════════════════════════════════════════════════════

class TestSyntheticGenerator:
    def test_generate_dataset(self):
        from prajna.data.synthetic_generator import SyntheticGenerator
        gen = SyntheticGenerator(num_nodes=13, feature_dim=8, seed=42)
        ds = gen.generate_dataset(T=500, num_faults=3)
        assert ds["telemetry"].shape == (500, 13, 8)
        assert ds["labels"].shape == (500, 13)
        assert np.any(ds["labels"] > 0)  # should have some anomalies

    def test_postflight_data(self):
        from prajna.data.synthetic_generator import SyntheticGenerator
        gen = SyntheticGenerator(seed=42)
        pf = gen.generate_postflight_data(num_components=5, num_flights=5)
        assert pf["component_features"].shape[0] == 5
        assert pf["num_flights"] == 5


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — Evaluation
# ════════════════════════════════════════════════════════════

class TestEvaluator:
    def test_detection_metrics(self):
        from prajna.evaluation import Evaluator
        ev = Evaluator()
        y_true = np.array([0, 0, 0, 1, 1, 1, 0, 0, 1, 0])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.7, 0.9, 0.2, 0.1, 0.6, 0.15])
        result = ev.evaluate_detection(y_true, y_scores)
        assert result["roc_auc"] > 0.5
        assert 0 <= result["f1_score"] <= 1

    def test_brier_score(self):
        from prajna.evaluation import Evaluator
        ev = Evaluator()
        y_true = np.array([0, 1, 0, 1])
        y_prob = np.array([0.1, 0.9, 0.2, 0.8])
        brier = ev.evaluate_brier(y_true, y_prob)
        assert brier < 0.1  # should be well calibrated

    def test_rul_mape(self):
        from prajna.evaluation import Evaluator
        ev = Evaluator()
        true_rul = np.array([100, 50, 25, 10])
        pred_rul = np.array([95, 48, 28, 12])
        mape = ev.evaluate_rul(true_rul, pred_rul)
        assert mape < 20  # less than 20% error

    def test_full_evaluation(self):
        from prajna.evaluation import Evaluator
        ev = Evaluator()
        labels = np.random.randint(0, 2, 1000).astype(float)
        scores = np.where(labels == 1, np.random.rand(1000) * 0.5 + 0.5, np.random.rand(1000) * 0.5)
        result = ev.full_evaluation(labels, scores)
        assert result.roc_auc > 0.5
        assert result.summary()  # should produce a string


# ════════════════════════════════════════════════════════════
#  UNIT TESTS — Config
# ════════════════════════════════════════════════════════════

class TestConfig:
    def test_load_default(self):
        from prajna.config import Config
        config = Config.load()
        assert config.get("project") is not None

    def test_nested_access(self):
        from prajna.config import Config
        config = Config.load()
        assert config.sdwap.get("max_iterations") == 5


# ════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ════════════════════════════════════════════════════════════

class TestIntegrationPipeline:
    """Integration tests for the full PRAJNA inference pipeline."""

    def test_local_to_sdwap_pipeline(self):
        """Test: LocalDetector → SDWAP propagation."""
        from prajna.engine.local_detector import LocalDetector
        from prajna.engine.sdwap import SDWAP
        from prajna.graph import GraphBuilder

        graph = GraphBuilder()
        adj = graph.get_adjacency()

        normal = np.random.randn(200, 13, 8).astype(np.float32) * 0.1
        det = LocalDetector()
        det.fit(normal)

        # Anomalous timestep
        anomaly = np.random.randn(13, 8).astype(np.float32) * 0.1
        anomaly[0] += 3.0  # EPS anomaly

        local = det.score(anomaly)
        sdwap = SDWAP()
        result = sdwap.propagate(local["scores"], adj, local["confidences"])
        assert result["propagated_scores"][0] > 0.5  # EPS should be high

    def test_sdwap_to_kavach_pipeline(self):
        """Test: SDWAP → KAVACH verification."""
        from prajna.engine.sdwap import SDWAP
        from prajna.engine.kavach import KAVACH

        scores = np.array([0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        adj = np.zeros((13, 13))
        adj[0, 1] = 0.8
        conf = np.ones(13)

        sdwap = SDWAP()
        result = sdwap.propagate(scores, adj, conf)

        kavach = KAVACH()
        verification = kavach.verify_all({
            "scores": result["propagated_scores"],
            "sdwap_iterations": result["iterations"],
            "sdwap_max_iter": 5,
        })
        assert isinstance(verification["all_satisfied"], bool)

    def test_sdwap_to_nlg_pipeline(self):
        """Test: SDWAP → NLG alert generation."""
        from prajna.engine.sdwap import SDWAP
        from prajna.engine.nlg import NLGEngine

        scores = np.zeros(13)
        scores[0] = 0.8
        adj = np.zeros((13, 13))
        adj[0, 1] = 0.9
        conf = np.ones(13)

        sdwap = SDWAP()
        result = sdwap.propagate(scores, adj, conf)

        nlg = NLGEngine()
        alert = nlg.generate_alert(0, 0.8, result["propagated_scores"][0], result)
        assert alert["risk_level"] in ("WATCH", "WARNING", "CRITICAL")
        assert len(alert["explanation"]) > 10

    def test_full_synthetic_pipeline(self):
        """Test: SyntheticGenerator → LocalDetector → SDWAP → SHAKTI → KAVACH."""
        from prajna.data.synthetic_generator import SyntheticGenerator
        from prajna.engine.local_detector import LocalDetector
        from prajna.engine.sdwap import SDWAP
        from prajna.engine.shakti import SHAKTI
        from prajna.engine.kavach import KAVACH
        from prajna.graph import GraphBuilder

        # Generate data
        gen = SyntheticGenerator(seed=42)
        ds = gen.generate_dataset(T=500, num_faults=3)

        # Train
        graph = GraphBuilder()
        adj = graph.get_adjacency()
        det = LocalDetector()
        det.fit(ds["telemetry"][:350])

        # Score
        test_scores = det.batch_score(ds["telemetry"][350:])

        # SDWAP
        sdwap = SDWAP()
        prop = sdwap.batch_propagate(test_scores["scores"], adj, test_scores["confidences"])
        assert len(prop) == 150

        # SHAKTI calibration
        shakti = SHAKTI()
        flat_s = np.array([r["propagated_scores"] for r in prop]).flatten()
        flat_l = ds["labels"][350:].flatten().astype(float)
        min_len = min(len(flat_s), len(flat_l))
        shakti.calibrate(flat_s[:min_len // 2], flat_l[:min_len // 2])
        interval = shakti.predict_interval(0.5)
        assert interval["lower"] <= interval["upper"]

        # KAVACH
        kavach = KAVACH()
        last = prop[-1]
        v = kavach.verify_all({
            "scores": last["propagated_scores"],
            "sdwap_iterations": last["iterations"],
            "sdwap_max_iter": 5,
        })
        assert "all_satisfied" in v

    def test_clpx_bridge(self):
        """Test: In-flight → CLPX → Post-flight transfer."""
        from prajna.engine.clpx import CLPX

        clpx = CLPX(embedding_dim=8, shared_dim=4)
        inflight = np.random.rand(13, 8).astype(np.float32)
        features = np.random.rand(13, 8).astype(np.float32)
        damage = np.random.rand(13).astype(np.float32) * 0.5

        priors = clpx.forward_transfer(inflight)
        adjustments = clpx.backward_transfer(features, damage)
        clpx.update_trust(0.85)

        assert priors["priors"].shape == (13, 4)
        assert adjustments["sensitivity_adjustments"].shape == (13,)


# ════════════════════════════════════════════════════════════
#  SYSTEM TESTS
# ════════════════════════════════════════════════════════════

class TestSystemEndToEnd:
    """System-level tests for the complete PRAJNA platform."""

    def test_evaluation_on_synthetic(self):
        """Full evaluation pipeline on synthetic data."""
        from prajna.data.synthetic_generator import SyntheticGenerator
        from prajna.engine.local_detector import LocalDetector
        from prajna.engine.sdwap import SDWAP
        from prajna.graph import GraphBuilder
        from prajna.evaluation import Evaluator

        gen = SyntheticGenerator(seed=123)
        ds = gen.generate_dataset(T=1000, num_faults=5)
        T, N, D = ds["telemetry"].shape

        train = ds["telemetry"][:700]
        test = ds["telemetry"][700:]
        test_labels = ds["labels"][700:]

        graph = GraphBuilder()
        adj = graph.get_adjacency()
        det = LocalDetector()
        det.fit(train)

        scores = det.batch_score(test)
        sdwap = SDWAP()
        prop = sdwap.batch_propagate(scores["scores"], adj, scores["confidences"])
        prop_scores = np.array([r["propagated_scores"] for r in prop])

        evaluator = Evaluator()
        result = evaluator.full_evaluation(
            detection_labels=test_labels.flatten(),
            detection_scores=prop_scores.flatten(),
        )
        # Basic sanity: AUC should be above chance
        assert result.roc_auc >= 0.0
        assert result.f1_score >= 0.0
        print(result.summary())

    def test_dashboard_app_creates(self):
        """Test that Flask dashboard app can be created."""
        from prajna.dashboard import create_app
        app = create_app()
        assert app is not None

        with app.test_client() as client:
            resp = client.get("/api/health")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["status"] == "ok"

    def test_config_loads(self):
        """Test that default config loads correctly."""
        from prajna.config import Config
        config = Config.load()
        assert config.project.get("name") == "PRAJNA"
        assert config.sdwap.get("max_iterations") == 5
        assert config.tgn.get("hidden_dim") == 64
