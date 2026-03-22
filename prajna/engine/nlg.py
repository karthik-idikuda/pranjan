"""PRAJNA — NLG: Natural Language Generation for Anomaly Alerts.

Generates human-readable contingency actions, root cause explanations,
and SDWAP propagation traces for spacecraft operators.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SUBSYSTEM_NAMES = [
    "EPS", "TCS", "PROP", "AOCS", "COMM", "OBC", "PL",
    "STRUCT", "HARNESS", "PYRO", "REA", "BATT", "SA",
]

# Contingency action templates per subsystem
CONTINGENCY_TEMPLATES = {
    "EPS": {
        "actions": [
            "Switch to backup power bus immediately",
            "Reduce non-essential payload power consumption",
            "Monitor battery charge state and solar array current",
        ],
        "description": "Electrical Power System anomaly detected",
    },
    "TCS": {
        "actions": [
            "Activate backup thermal control loop",
            "Reduce duty cycle on high-power components",
            "Monitor radiator panel temperatures",
        ],
        "description": "Thermal Control System anomaly detected",
    },
    "PROP": {
        "actions": [
            "Safe propulsion valves to closed position",
            "Switch to backup thruster set if available",
            "Monitor propellant tank pressure and temperature",
        ],
        "description": "Propulsion system anomaly detected",
    },
    "AOCS": {
        "actions": [
            "Switch to backup attitude determination mode",
            "Reduce pointing accuracy requirements temporarily",
            "Verify star tracker and gyroscope outputs",
        ],
        "description": "Attitude & Orbit Control anomaly detected",
    },
    "COMM": {
        "actions": [
            "Switch to backup transponder",
            "Reduce telemetry data rate",
            "Verify antenna pointing and signal strength",
        ],
        "description": "Communication system anomaly detected",
    },
    "OBC": {
        "actions": [
            "Toggle to backup flight computer if available",
            "Initiate watchdog timer reset sequence",
            "Dump critical data to safe storage",
        ],
        "description": "On-Board Computer anomaly detected",
    },
    "PL": {
        "actions": [
            "Power down payload instrument",
            "Switch to safe mode configuration",
            "Record last valid payload data",
        ],
        "description": "Payload anomaly detected",
    },
    "STRUCT": {
        "actions": [
            "Monitor structural vibration levels",
            "Reduce spacecraft agility maneuvers",
            "Check deployment mechanism status",
        ],
        "description": "Structure & Mechanisms anomaly detected",
    },
    "HARNESS": {
        "actions": [
            "Check harness continuity on affected circuits",
            "Reroute critical signals via backup paths",
            "Monitor insulation resistance",
        ],
        "description": "Wiring Harness anomaly detected",
    },
    "PYRO": {
        "actions": [
            "Safe all pyrotechnic circuits immediately",
            "Verify arming commands are inhibited",
            "Review pyro firing sequence timeline",
        ],
        "description": "Pyrotechnics system anomaly detected",
    },
    "REA": {
        "actions": [
            "Verify reaction wheel speeds and torques",
            "Switch to backup reaction wheel assembly",
            "Monitor momentum accumulation",
        ],
        "description": "Reaction/Entry Assembly anomaly detected",
    },
    "BATT": {
        "actions": [
            "Reduce charge rate to safe level",
            "Activate load-shedding protocol",
            "Monitor cell voltages and temperatures individually",
        ],
        "description": "Battery Pack anomaly detected",
    },
    "SA": {
        "actions": [
            "Verify solar array deployment angle",
            "Check for partial shadowing conditions",
            "Monitor string-level currents for degradation",
        ],
        "description": "Solar Array anomaly detected",
    },
}

RISK_THRESHOLDS = {
    "NOMINAL": 0.3,
    "WATCH": 0.5,
    "WARNING": 0.7,
    "CRITICAL": 0.9,
}


class NLGEngine:
    """Natural Language Generation engine for PRAJNA alerts."""

    def generate_alert(
        self,
        node_idx: int,
        score: float,
        propagated_score: float,
        sdwap_result: dict,
        prediction: dict | None = None,
    ) -> dict:
        """Generate a complete alert with explanation and contingency actions.

        Args:
            node_idx: Subsystem node index (0-12)
            score: Local anomaly score
            propagated_score: SDWAP-propagated score
            sdwap_result: Full SDWAP result dict
            prediction: Optional predictor output (failure_prob, ttf_mu, etc.)

        Returns:
            dict with 'summary', 'risk_level', 'explanation', 'actions',
            'propagation_trace', 'prediction_text'
        """
        name = SUBSYSTEM_NAMES[node_idx] if node_idx < len(SUBSYSTEM_NAMES) else f"Node-{node_idx}"
        template = CONTINGENCY_TEMPLATES.get(name, {"actions": ["Investigate anomaly"], "description": "Unknown subsystem"})

        # Determine risk level
        risk_level = "NOMINAL"
        for level, threshold in sorted(RISK_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if propagated_score >= threshold:
                risk_level = level
                break

        # Generate summary
        summary = (
            f"[{risk_level}] {template['description']} — "
            f"Local score: {score:.3f}, Propagated: {propagated_score:.3f}"
        )

        # Generate SDWAP propagation trace
        propagation_trace = self._build_propagation_trace(node_idx, sdwap_result)

        # Generate prediction text
        prediction_text = ""
        if prediction:
            prob = prediction.get("failure_prob", 0)
            ttf = prediction.get("ttf_mu", 0)
            prediction_text = (
                f"Failure probability (30 min): {prob:.1%}. "
                f"Estimated time to failure: {ttf:.1f} minutes."
            )

        # Build explanation
        explanation = self._build_explanation(name, score, propagated_score, propagation_trace)

        return {
            "timestamp": datetime.now().isoformat(),
            "node_idx": node_idx,
            "node_name": name,
            "risk_level": risk_level,
            "summary": summary,
            "explanation": explanation,
            "actions": template["actions"] if risk_level in ("WARNING", "CRITICAL") else [],
            "propagation_trace": propagation_trace,
            "prediction_text": prediction_text,
            "scores": {
                "local": float(score),
                "propagated": float(propagated_score),
                "delta": float(propagated_score - score),
            },
        }

    def _build_propagation_trace(self, target_node: int, sdwap_result: dict) -> list[dict]:
        """Extract SDWAP propagation trace for explainability.

        Shows which nodes contributed most to the target's score increase.
        """
        contribution_map = sdwap_result.get("contribution_map", None)
        if contribution_map is None:
            return []

        trace = []
        for j in range(contribution_map.shape[0]):
            contrib = contribution_map[j, target_node]
            if contrib > 0.01:
                src_name = SUBSYSTEM_NAMES[j] if j < len(SUBSYSTEM_NAMES) else f"Node-{j}"
                trace.append({
                    "source_node": j,
                    "source_name": src_name,
                    "contribution": float(contrib),
                })

        trace.sort(key=lambda x: x["contribution"], reverse=True)
        return trace[:5]  # top-5 contributors

    def _build_explanation(
        self,
        node_name: str,
        local_score: float,
        propagated_score: float,
        trace: list[dict],
    ) -> str:
        """Build human-readable root cause explanation."""
        parts = [f"Anomaly detected in {node_name} subsystem."]

        delta = propagated_score - local_score
        if delta > 0.05:
            parts.append(
                f"Score increased by {delta:.3f} due to dependency propagation "
                f"from upstream subsystems."
            )
            if trace:
                top = trace[0]
                parts.append(
                    f"Primary contributor: {top['source_name']} "
                    f"(contribution: {top['contribution']:.3f})."
                )
        else:
            parts.append("Anomaly is primarily local — minimal propagation from neighbors.")

        if propagated_score > 0.7:
            parts.append("IMMEDIATE ATTENTION REQUIRED — score exceeds critical threshold.")
        elif propagated_score > 0.5:
            parts.append("Elevated anomaly level — continued monitoring recommended.")

        return " ".join(parts)

    def generate_batch_report(
        self,
        scores: dict,
        sdwap_result: dict,
        alert_threshold: float = 0.5,
    ) -> dict:
        """Generate a report for all nodes at a single timestep.

        Args:
            scores: dict with 'local' (N,) and 'propagated' (N,)
            sdwap_result: Full SDWAP result
            alert_threshold: Minimum propagated score for alert

        Returns:
            dict with 'alerts' list, 'summary', 'overall_risk'
        """
        local = scores["local"]
        propagated = scores["propagated"]
        N = len(local)

        alerts = []
        for i in range(N):
            if propagated[i] >= alert_threshold:
                alert = self.generate_alert(i, local[i], propagated[i], sdwap_result)
                alerts.append(alert)

        # Overall risk
        max_score = float(max(propagated)) if len(propagated) > 0 else 0
        overall_risk = "NOMINAL"
        for level, threshold in sorted(RISK_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if max_score >= threshold:
                overall_risk = level
                break

        num_anomalous = sum(1 for s in propagated if s >= alert_threshold)

        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "num_alerts": len(alerts),
            "overall_risk": overall_risk,
            "summary": (
                f"{num_anomalous}/{N} subsystems above alert threshold. "
                f"Overall risk: {overall_risk}. Max score: {max_score:.3f}."
            ),
        }

    def generate_postflight_report(
        self,
        damage_results: dict,
        rul_results: list[dict],
    ) -> dict:
        """Generate post-flight requalification report.

        Args:
            damage_results: Output from ThermalDiffGNN
            rul_results: List of RUL results per component

        Returns:
            dict with decisions, explanations, maintenance priority
        """
        decisions = damage_results.get("decisions", [])
        damage_scores = damage_results.get("damage_scores", [])
        N = len(decisions)

        components = []
        maintenance_queue = []

        for i in range(N):
            name = SUBSYSTEM_NAMES[i] if i < len(SUBSYSTEM_NAMES) else f"Component-{i}"
            d_score = float(damage_scores[i]) if hasattr(damage_scores, '__len__') else 0
            decision = decisions[i] if i < len(decisions) else "UNKNOWN"
            rul = rul_results[i] if i < len(rul_results) else {}

            explanation = self._postflight_explanation(name, decision, d_score, rul)

            entry = {
                "component": name,
                "decision": decision,
                "damage_score": d_score,
                "rul_final": rul.get("rul_final", 0),
                "limiting_mode": rul.get("limiting_mode", "unknown"),
                "explanation": explanation,
            }
            components.append(entry)

            if decision in ("AMBER", "REJECT"):
                maintenance_queue.append(entry)

        # Sort maintenance queue by damage (highest first)
        maintenance_queue.sort(key=lambda x: x["damage_score"], reverse=True)

        go_count = sum(1 for d in decisions if d == "GO")
        amber_count = sum(1 for d in decisions if d == "AMBER")
        reject_count = sum(1 for d in decisions if d == "REJECT")

        overall = "GO" if reject_count == 0 and amber_count == 0 else \
                  "AMBER" if reject_count == 0 else "REJECT"

        return {
            "overall_decision": overall,
            "components": components,
            "maintenance_queue": maintenance_queue,
            "summary": {
                "total": N,
                "go": go_count,
                "amber": amber_count,
                "reject": reject_count,
            },
        }

    def _postflight_explanation(
        self,
        name: str,
        decision: str,
        damage_score: float,
        rul: dict,
    ) -> str:
        """Generate explanation for a single component's requalification decision."""
        parts = [f"{name}: {decision}."]

        if decision == "GO":
            parts.append(f"Damage score {damage_score:.3f} is within acceptable limits.")
        elif decision == "AMBER":
            parts.append(
                f"Damage score {damage_score:.3f} requires detailed inspection. "
                f"Estimated remaining life: {rul.get('rul_final', 0):.1f} flights "
                f"(limited by {rul.get('limiting_mode', 'unknown')})."
            )
        else:
            parts.append(
                f"Damage score {damage_score:.3f} exceeds rejection threshold. "
                f"Component must be replaced before next flight."
            )

        return " ".join(parts)
