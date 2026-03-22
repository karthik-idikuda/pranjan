"""PRAJNA — Evaluation: Comprehensive Metrics & Ablation Framework.

Computes all 10 core metrics from the RTM and generates evaluation reports.
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Container for all evaluation metrics."""
    roc_auc: float = 0.0
    pr_auc: float = 0.0
    f1_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    false_alarm_rate: float = 0.0
    lead_time_minutes: float = 0.0
    rca_accuracy: float = 0.0
    brier_score: float = 0.0
    rul_mape: float = 0.0
    sdwap_fidelity: float = 0.0
    requalification_accuracy: float = 0.0
    coverage_gap: float = 0.0
    extra: dict = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            "PRAJNA Evaluation Results",
            "=" * 40,
            f"  ROC-AUC:               {self.roc_auc:.4f}",
            f"  PR-AUC:                {self.pr_auc:.4f}",
            f"  F1 Score:              {self.f1_score:.4f}",
            f"  Precision:             {self.precision:.4f}",
            f"  Recall:                {self.recall:.4f}",
            f"  False Alarm Rate:      {self.false_alarm_rate:.4f}",
            f"  Lead Time (min):       {self.lead_time_minutes:.1f}",
            f"  RCA Accuracy:          {self.rca_accuracy:.4f}",
            f"  Brier Score:           {self.brier_score:.4f}",
            f"  RUL MAPE:              {self.rul_mape:.2f}%",
            f"  SDWAP Fidelity:        {self.sdwap_fidelity:.4f}",
            f"  Requalification Acc:   {self.requalification_accuracy:.4f}",
            f"  Coverage Gap:          {self.coverage_gap:.4f}",
            "=" * 40,
        ]
        return "\n".join(lines)


class Evaluator:
    """Computes detection, prediction, and requalification metrics."""

    def evaluate_detection(
        self,
        y_true: np.ndarray,
        y_scores: np.ndarray,
        threshold: float = 0.5,
    ) -> dict:
        """Evaluate anomaly detection performance.

        Args:
            y_true: (N,) binary ground truth labels
            y_scores: (N,) continuous anomaly scores [0, 1]
            threshold: Decision threshold

        Returns:
            dict with ROC-AUC, PR-AUC, F1, precision, recall, FAR
        """
        from sklearn.metrics import (
            roc_auc_score,
            average_precision_score,
            f1_score,
            precision_score,
            recall_score,
        )

        y_pred = (y_scores >= threshold).astype(int)
        y_true = y_true.astype(int)

        # Handle constant labels
        unique_labels = np.unique(y_true)
        if len(unique_labels) < 2:
            logger.warning("Only one class present in y_true — metrics may be undefined")
            auc = 0.0
            pr_auc = 0.0
        else:
            auc = roc_auc_score(y_true, y_scores)
            pr_auc = average_precision_score(y_true, y_scores)

        f1 = f1_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)

        # False alarm rate: FP / (FP + TN)
        fp = np.sum((y_pred == 1) & (y_true == 0))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        far = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        return {
            "roc_auc": float(auc),
            "pr_auc": float(pr_auc),
            "f1_score": float(f1),
            "precision": float(prec),
            "recall": float(rec),
            "false_alarm_rate": float(far),
        }

    def evaluate_lead_time(
        self,
        y_true: np.ndarray,
        y_scores: np.ndarray,
        threshold: float = 0.5,
        sampling_rate_hz: float = 1.0,
    ) -> float:
        """Compute average detection lead time before actual anomaly onset.

        Args:
            y_true: (T,) binary labels (anomaly = 1)
            y_scores: (T,) anomaly scores
            threshold: Detection threshold
            sampling_rate_hz: Samples per second

        Returns:
            Average lead time in minutes
        """
        y_pred = (y_scores >= threshold).astype(int)

        # Find anomaly onset points (rising edges in y_true)
        onsets = np.where(np.diff(y_true.astype(int)) == 1)[0] + 1

        lead_times = []
        for onset in onsets:
            # Look backwards from onset to find earliest detection
            search_start = max(0, onset - int(3600 * sampling_rate_hz))
            region = y_pred[search_start:onset]
            detections = np.where(region == 1)[0]
            if len(detections) > 0:
                first_detect = search_start + detections[0]
                lead_samples = onset - first_detect
                lead_times.append(lead_samples / sampling_rate_hz / 60.0)

        return float(np.mean(lead_times)) if lead_times else 0.0

    def evaluate_rca(
        self,
        predicted_root_causes: list[int],
        true_root_causes: list[int],
    ) -> float:
        """Compute root cause analysis accuracy.

        Args:
            predicted_root_causes: List of predicted root cause node indices
            true_root_causes: List of true root cause node indices

        Returns:
            Accuracy (fraction of correct identifications)
        """
        if not true_root_causes:
            return 1.0 if not predicted_root_causes else 0.0

        correct = sum(1 for p, t in zip(predicted_root_causes, true_root_causes) if p == t)
        return correct / len(true_root_causes)

    def evaluate_brier(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
    ) -> float:
        """Compute Brier score (calibration metric).

        Args:
            y_true: Binary labels
            y_prob: Predicted probabilities

        Returns:
            Brier score (lower is better)
        """
        return float(np.mean((y_prob - y_true.astype(float)) ** 2))

    def evaluate_rul(
        self,
        true_rul: np.ndarray,
        predicted_rul: np.ndarray,
    ) -> float:
        """Compute Mean Absolute Percentage Error for RUL predictions.

        Args:
            true_rul: Ground truth remaining useful life values
            predicted_rul: Predicted RUL values

        Returns:
            MAPE percentage
        """
        mask = true_rul > 0
        if not np.any(mask):
            return 0.0
        mape = np.mean(np.abs(true_rul[mask] - predicted_rul[mask]) / true_rul[mask]) * 100
        return float(mape)

    def evaluate_sdwap_fidelity(
        self,
        injection_node: int,
        propagated_scores: np.ndarray,
        adjacency: np.ndarray,
    ) -> float:
        """Evaluate SDWAP propagation fidelity.

        Checks whether propagation follows the physics-informed graph structure
        (high-weight neighbors should receive more anomaly than low-weight ones).

        Args:
            injection_node: The node where anomaly was injected
            propagated_scores: (N,) propagated scores
            adjacency: (N, N) adjacency matrix

        Returns:
            Spearman rank correlation between edge weights and score increase
        """
        from scipy.stats import spearmanr

        weights = adjacency[injection_node]
        neighbors = np.where(weights > 0)[0]

        if len(neighbors) < 2:
            return 1.0  # Not enough neighbors to evaluate

        neighbor_scores = propagated_scores[neighbors]
        neighbor_weights = weights[neighbors]

        corr, _ = spearmanr(neighbor_weights, neighbor_scores)
        return float(corr) if not np.isnan(corr) else 0.0

    def evaluate_coverage_gap(
        self,
        target_coverage: float,
        empirical_coverage: float,
    ) -> float:
        """Compute gap between target and achieved coverage (SHAKTI metric)."""
        return float(abs(target_coverage - empirical_coverage))

    def evaluate_requalification(
        self,
        true_decisions: list[str],
        predicted_decisions: list[str],
    ) -> float:
        """Compute requalification decision accuracy.

        Args:
            true_decisions: List of true decisions (GO/AMBER/REJECT)
            predicted_decisions: List of predicted decisions

        Returns:
            Accuracy as fraction
        """
        if not true_decisions:
            return 0.0
        correct = sum(1 for t, p in zip(true_decisions, predicted_decisions) if t == p)
        return correct / len(true_decisions)

    def full_evaluation(
        self,
        detection_labels: np.ndarray,
        detection_scores: np.ndarray,
        propagated_scores: Optional[np.ndarray] = None,
        adjacency: Optional[np.ndarray] = None,
        injection_node: Optional[int] = None,
        rul_true: Optional[np.ndarray] = None,
        rul_pred: Optional[np.ndarray] = None,
        rca_predicted: Optional[list] = None,
        rca_true: Optional[list] = None,
        coverage_target: float = 0.99,
        coverage_empirical: float = 0.99,
        requali_true: Optional[list] = None,
        requali_pred: Optional[list] = None,
        threshold: float = 0.5,
    ) -> EvaluationResult:
        """Run all evaluations and return a combined result."""

        # Core detection metrics
        det = self.evaluate_detection(detection_labels, detection_scores, threshold)

        # Lead time
        lead = self.evaluate_lead_time(detection_labels, detection_scores, threshold)

        # Brier
        brier = self.evaluate_brier(detection_labels, detection_scores)

        # RCA
        rca = self.evaluate_rca(rca_predicted or [], rca_true or [])

        # RUL
        rul_mape = 0.0
        if rul_true is not None and rul_pred is not None:
            rul_mape = self.evaluate_rul(rul_true, rul_pred)

        # SDWAP fidelity
        fidelity = 0.0
        if propagated_scores is not None and adjacency is not None and injection_node is not None:
            fidelity = self.evaluate_sdwap_fidelity(injection_node, propagated_scores, adjacency)

        # Coverage gap
        cov_gap = self.evaluate_coverage_gap(coverage_target, coverage_empirical)

        # Requalification
        requali_acc = self.evaluate_requalification(requali_true or [], requali_pred or [])

        result = EvaluationResult(
            roc_auc=det["roc_auc"],
            pr_auc=det["pr_auc"],
            f1_score=det["f1_score"],
            precision=det["precision"],
            recall=det["recall"],
            false_alarm_rate=det["false_alarm_rate"],
            lead_time_minutes=lead,
            rca_accuracy=rca,
            brier_score=brier,
            rul_mape=rul_mape,
            sdwap_fidelity=fidelity,
            requalification_accuracy=requali_acc,
            coverage_gap=cov_gap,
        )

        logger.info(f"Evaluation complete: AUC={result.roc_auc:.4f}, F1={result.f1_score:.4f}")
        return result


class AblationRunner:
    """Runs ablation studies by disabling individual components."""

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator

    def run_ablation(
        self,
        run_fn,
        labels: np.ndarray,
        components: list[str] | None = None,
    ) -> dict:
        """Run ablation study.

        Args:
            run_fn: Callable(disabled_component) → (scores, extra_dict)
                Called with None for full pipeline, or component name to disable.
            labels: Ground truth labels
            components: List of component names to ablate.
                Default: ["sdwap", "tgn", "aegis", "shakti", "postflight"]

        Returns:
            dict mapping component name → EvaluationResult
        """
        if components is None:
            components = ["sdwap", "tgn", "aegis", "shakti", "postflight"]

        results = {}

        # Full pipeline
        full_scores, _ = run_fn(None)
        results["full"] = self.evaluator.evaluate_detection(labels, full_scores)

        # Ablate each component
        for comp in components:
            try:
                ablated_scores, _ = run_fn(comp)
                results[f"no_{comp}"] = self.evaluator.evaluate_detection(labels, ablated_scores)
                delta = results["full"]["f1_score"] - results[f"no_{comp}"]["f1_score"]
                logger.info(f"Ablation -{comp}: ΔF1 = {delta:+.4f}")
            except Exception as e:
                logger.error(f"Ablation {comp} failed: {e}")
                results[f"no_{comp}"] = {"error": str(e)}

        return results
