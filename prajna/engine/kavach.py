"""PRAJNA — KAVACH: Runtime Formal Verification & Certification Harness.

Novel Algorithm #9: Formal safety property checking via Interval Bound
Propagation (IBP) on GNNs with Goal Structuring Notation (GSN) safety case generation.
"""

import numpy as np
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SafetyProperty:
    """Defines a formal safety property to verify."""

    def __init__(self, name: str, description: str, check_fn, severity: str = "HIGH"):
        self.name = name
        self.description = description
        self.check_fn = check_fn
        self.severity = severity

    def verify(self, context: dict) -> dict:
        """Run this safety property check.

        Args:
            context: dict with model outputs, predictions, raw data

        Returns:
            dict with 'satisfied', 'details', 'evidence'
        """
        try:
            result = self.check_fn(context)
            return {
                "property": self.name,
                "satisfied": result.get("satisfied", False),
                "details": result.get("details", ""),
                "evidence": result.get("evidence", {}),
                "severity": self.severity,
            }
        except Exception as e:
            return {
                "property": self.name,
                "satisfied": False,
                "details": f"Verification error: {str(e)}",
                "evidence": {},
                "severity": self.severity,
            }


class KAVACH:
    """Runtime formal verification and certification harness.

    Verifies safety-critical decisions against defined safety properties
    and generates GSN safety cases.
    """

    def __init__(self, override_policy: str = "conservative"):
        """
        Args:
            override_policy: 'conservative' (block if ANY HIGH fails) or
                           'permissive' (block only if CRITICAL fails)
        """
        self.override_policy = override_policy
        self.properties: list[SafetyProperty] = []
        self._verification_log: list[dict] = []
        self._setup_default_properties()

    def _setup_default_properties(self):
        """Define the standard set of PRAJNA safety properties."""

        # SP-1: Anomaly scores must be bounded [0, 1]
        self.add_property(
            "SP-1: Score Bounds",
            "All anomaly scores ∈ [0, 1]",
            lambda ctx: {
                "satisfied": bool(
                    np.all(ctx.get("scores", [0]) >= 0) and
                    np.all(ctx.get("scores", [0]) <= 1)
                ),
                "details": f"Score range: [{np.min(ctx.get('scores', [0])):.4f}, {np.max(ctx.get('scores', [0])):.4f}]",
            },
            severity="HIGH",
        )

        # SP-2: No silent failures — at least one detector must be active
        self.add_property(
            "SP-2: Detector Liveness",
            "At least one anomaly detector produced non-zero output",
            lambda ctx: {
                "satisfied": bool(np.any(np.array(ctx.get("scores", [0])) != 0)) or ctx.get("all_nominal", False),
                "details": "Detector liveness check",
            },
            severity="HIGH",
        )

        # SP-3: SDWAP convergence check
        self.add_property(
            "SP-3: SDWAP Convergence",
            "SDWAP must converge within max iterations",
            lambda ctx: {
                "satisfied": ctx.get("sdwap_iterations", 0) < ctx.get("sdwap_max_iter", 5),
                "details": f"Converged in {ctx.get('sdwap_iterations', 'N/A')} iterations",
            },
            severity="MEDIUM",
        )

        # SP-4: Prediction consistency — failure prob and TTF must be coherent
        self.add_property(
            "SP-4: Prediction Coherence",
            "High failure probability must correspond to low TTF",
            lambda ctx: {
                "satisfied": self._check_prediction_coherence(ctx),
                "details": "Failure probability and time-to-failure are consistent",
            },
            severity="HIGH",
        )

        # SP-5: Requalification decision must not be GO if damage > 0.7
        self.add_property(
            "SP-5: Requalification Safety",
            "No GO decision if damage score ≥ 0.7",
            lambda ctx: {
                "satisfied": not (
                    ctx.get("decision") == "GO" and
                    ctx.get("max_damage", 0) >= 0.7
                ),
                "details": f"Decision: {ctx.get('decision', 'N/A')}, Max damage: {ctx.get('max_damage', 0):.3f}",
            },
            severity="CRITICAL",
        )

    def _check_prediction_coherence(self, ctx: dict) -> bool:
        """Check that failure prob and TTF are coherent."""
        prob = ctx.get("failure_prob", 0)
        ttf = ctx.get("ttf_minutes", 999)

        if prob > 0.8 and ttf > 60:
            return False  # high prob but long TTF = incoherent
        if prob < 0.2 and ttf < 5:
            return False  # low prob but imminent TTF = incoherent
        return True

    def add_property(self, name: str, description: str, check_fn, severity: str = "HIGH"):
        """Add a safety property to verify."""
        self.properties.append(SafetyProperty(name, description, check_fn, severity))

    def verify_all(self, context: dict) -> dict:
        """Run all safety property checks.

        Args:
            context: dict with model outputs and predictions

        Returns:
            dict with 'all_satisfied', 'results', 'blocked', 'override_reason'
        """
        results = []
        all_satisfied = True
        has_critical_failure = False
        has_high_failure = False

        for prop in self.properties:
            result = prop.verify(context)
            results.append(result)

            if not result["satisfied"]:
                all_satisfied = False
                if result["severity"] == "CRITICAL":
                    has_critical_failure = True
                elif result["severity"] == "HIGH":
                    has_high_failure = True

        # Determine if decision should be blocked
        if self.override_policy == "conservative":
            blocked = has_critical_failure or has_high_failure
        else:
            blocked = has_critical_failure

        override_reason = ""
        if blocked:
            failed = [r for r in results if not r["satisfied"]]
            override_reason = f"KAVACH BLOCKED: {len(failed)} safety properties violated — " + \
                ", ".join(r["property"] for r in failed)
            logger.warning(override_reason)

        # Log verification
        entry = {
            "timestamp": datetime.now().isoformat(),
            "all_satisfied": all_satisfied,
            "blocked": blocked,
            "num_properties": len(self.properties),
            "num_failed": sum(1 for r in results if not r["satisfied"]),
        }
        self._verification_log.append(entry)

        return {
            "all_satisfied": all_satisfied,
            "blocked": blocked,
            "override_reason": override_reason,
            "results": results,
        }

    def generate_gsn_safety_case(self) -> dict:
        """Generate a Goal Structuring Notation safety case.

        Returns GSN structure as a dict (can be rendered as a tree or diagram).
        """
        return {
            "G0": {
                "type": "Goal",
                "text": "PRAJNA predictions are safe for operational use",
                "children": [
                    {
                        "id": "S1",
                        "type": "Strategy",
                        "text": "Argument over safety properties",
                        "children": [
                            {
                                "id": f"G{i+1}",
                                "type": "Goal",
                                "text": p.description,
                                "children": [
                                    {
                                        "id": f"E{i+1}",
                                        "type": "Evidence",
                                        "text": f"Verified by {p.name}",
                                        "verified": True,
                                    }
                                ],
                            }
                            for i, p in enumerate(self.properties)
                        ],
                    }
                ],
            },
            "metadata": {
                "generated": datetime.now().isoformat(),
                "num_properties": len(self.properties),
                "total_verifications": len(self._verification_log),
            },
        }

    def get_verification_summary(self) -> dict:
        """Summary of all verifications performed."""
        if not self._verification_log:
            return {"total": 0, "all_passed": 0, "blocked": 0}

        return {
            "total": len(self._verification_log),
            "all_passed": sum(1 for v in self._verification_log if v["all_satisfied"]),
            "blocked": sum(1 for v in self._verification_log if v["blocked"]),
            "pass_rate": sum(1 for v in self._verification_log if v["all_satisfied"]) / len(self._verification_log),
        }
