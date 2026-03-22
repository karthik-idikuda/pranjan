"""PRAJNA — Synthetic Spacecraft Telemetry Generator.

Generates realistic multi-subsystem telemetry with configurable fault injection
for training, testing, and demo without real data.

Fault Types:
  1. Gradual degradation (battery, solar array)
  2. Sudden spike (electrical, thermal)
  3. Cascade failure (EPS → TCS → BATT chain)
  4. Oscillation anomaly (AOCS, reaction wheels)
  5. Drift anomaly (sensor calibration shift)
"""

import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SUBSYSTEM_PROFILES = {
    0: {"name": "EPS", "features": 8, "nominal_range": (0.8, 1.2), "noise": 0.02},
    1: {"name": "TCS", "features": 6, "nominal_range": (-10, 40), "noise": 0.5},
    2: {"name": "PROP", "features": 6, "nominal_range": (0, 100), "noise": 0.1},
    3: {"name": "AOCS", "features": 5, "nominal_range": (-1, 1), "noise": 0.005},
    4: {"name": "COMM", "features": 5, "nominal_range": (-80, -40), "noise": 0.3},
    5: {"name": "OBC", "features": 5, "nominal_range": (30, 60), "noise": 0.2},
    6: {"name": "PL", "features": 4, "nominal_range": (0, 10), "noise": 0.05},
    7: {"name": "STRUCT", "features": 4, "nominal_range": (0, 0.1), "noise": 0.001},
    8: {"name": "HARNESS", "features": 4, "nominal_range": (0.9, 1.1), "noise": 0.01},
    9: {"name": "PYRO", "features": 3, "nominal_range": (0, 1), "noise": 0.005},
    10: {"name": "REA", "features": 4, "nominal_range": (0, 50), "noise": 0.1},
    11: {"name": "BATT", "features": 7, "nominal_range": (3.0, 4.2), "noise": 0.01},
    12: {"name": "SA", "features": 6, "nominal_range": (0, 120), "noise": 0.5},
}

NUM_NODES = 13
FEATURE_DIM = 8  # unified dimension (pad shorter nodes)


class SyntheticGenerator:
    """Generate synthetic spacecraft telemetry with fault injection."""

    def __init__(self, num_nodes: int = NUM_NODES, feature_dim: int = FEATURE_DIM, seed: int = 42):
        self.num_nodes = num_nodes
        self.feature_dim = feature_dim
        self.rng = np.random.RandomState(seed)

    def generate_nominal(self, T: int) -> np.ndarray:
        """Generate nominal (healthy) telemetry.

        Args:
            T: Number of timesteps

        Returns:
            (T, N, D) telemetry array
        """
        data = np.zeros((T, self.num_nodes, self.feature_dim), dtype=np.float32)
        t_axis = np.arange(T, dtype=np.float32)

        for n in range(self.num_nodes):
            profile = SUBSYSTEM_PROFILES.get(n, {"nominal_range": (0, 1), "noise": 0.01})
            lo, hi = profile["nominal_range"]
            mid = (lo + hi) / 2
            amp = (hi - lo) / 2
            noise = profile["noise"]

            for d in range(self.feature_dim):
                # Base signal: slow sinusoid + noise (simulates orbital variation)
                freq = 0.001 + self.rng.rand() * 0.005
                phase = self.rng.rand() * 2 * np.pi
                signal = mid + amp * 0.3 * np.sin(2 * np.pi * freq * t_axis + phase)
                signal += self.rng.randn(T) * noise
                data[:, n, d] = signal

        return data

    def inject_fault(
        self,
        data: np.ndarray,
        fault_type: str,
        target_node: int,
        start_t: int,
        duration: int,
        severity: float = 1.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Inject a specific fault pattern into telemetry.

        Args:
            data: (T, N, D) telemetry to modify (in-place)
            fault_type: 'degradation', 'spike', 'cascade', 'oscillation', 'drift'
            target_node: Primary node to affect
            start_t: Start timestep of fault
            duration: Duration in timesteps
            severity: Fault intensity multiplier

        Returns:
            (modified_data, labels) where labels is (T, N) binary
        """
        T, N, D = data.shape
        labels = np.zeros((T, N), dtype=np.int32)
        end_t = min(start_t + duration, T)

        if fault_type == "degradation":
            # Gradual ramping degradation
            ramp = np.linspace(0, severity * 3.0, end_t - start_t)
            for d in range(D):
                data[start_t:end_t, target_node, d] += ramp * (0.5 + self.rng.rand())
            labels[start_t:end_t, target_node] = 1

        elif fault_type == "spike":
            # Sudden spike at a random point within the window
            spike_t = start_t + duration // 3
            spike_end = min(spike_t + max(duration // 5, 10), T)
            data[spike_t:spike_end, target_node, :] += severity * 5.0
            labels[spike_t:spike_end, target_node] = 1

        elif fault_type == "cascade":
            # Cascade: target → neighbors with delay
            from prajna.graph import GraphBuilder
            graph = GraphBuilder(num_nodes=N)
            adj = graph.get_adjacency()

            # Phase 1: primary node
            ramp1 = np.linspace(0, severity * 2.0, min(duration // 2, end_t - start_t))
            data[start_t:start_t + len(ramp1), target_node, :] += ramp1[:, None]
            labels[start_t:start_t + len(ramp1), target_node] = 1

            # Phase 2: affected neighbors with delay
            delay = duration // 4
            for j in range(N):
                if adj[target_node, j] > 0.3:
                    t2 = start_t + delay
                    t2_end = min(t2 + duration // 2, T)
                    strength = adj[target_node, j] * severity
                    ramp2 = np.linspace(0, strength * 1.5, t2_end - t2)
                    data[t2:t2_end, j, :] += ramp2[:, None] * 0.5
                    labels[t2:t2_end, j] = 1

        elif fault_type == "oscillation":
            # High-frequency oscillation
            t_range = np.arange(end_t - start_t)
            osc = severity * 2.0 * np.sin(2 * np.pi * 0.1 * t_range)
            for d in range(D):
                data[start_t:end_t, target_node, d] += osc
            labels[start_t:end_t, target_node] = 1

        elif fault_type == "drift":
            # Slow calibration drift
            drift = np.linspace(0, severity * 1.5, end_t - start_t)
            for d in range(D):
                data[start_t:end_t, target_node, d] += drift
            labels[start_t:end_t, target_node] = 1

        return data, labels

    def generate_dataset(
        self,
        T: int = 10000,
        num_faults: int = 5,
        fault_types: Optional[list[str]] = None,
    ) -> dict:
        """Generate a complete dataset with mixed nominal and fault periods.

        Args:
            T: Total timesteps
            num_faults: Number of faults to inject
            fault_types: Allowed fault types (default: all)

        Returns:
            dict with 'telemetry' (T, N, D), 'labels' (T, N),
            'fault_log' (list of injected faults)
        """
        if fault_types is None:
            fault_types = ["degradation", "spike", "cascade", "oscillation", "drift"]

        data = self.generate_nominal(T)
        labels = np.zeros((T, self.num_nodes), dtype=np.int32)
        fault_log = []

        # Distribute faults across the timeline
        fault_window = T // (num_faults + 2)

        for i in range(num_faults):
            ft = fault_types[i % len(fault_types)]
            target = self.rng.randint(0, self.num_nodes)
            start = fault_window * (i + 1) + self.rng.randint(-fault_window // 4, fault_window // 4)
            start = max(100, min(start, T - 500))
            duration = self.rng.randint(100, 400)
            severity = 0.5 + self.rng.rand() * 1.5

            data, fault_labels = self.inject_fault(data, ft, target, start, duration, severity)
            labels = np.maximum(labels, fault_labels)

            fault_log.append({
                "type": ft,
                "target_node": int(target),
                "target_name": SUBSYSTEM_PROFILES.get(target, {}).get("name", f"Node-{target}"),
                "start": int(start),
                "duration": int(duration),
                "severity": float(severity),
            })

        timestamps = np.arange(T, dtype=np.float64)

        logger.info(
            f"Generated synthetic dataset: {T} timesteps, {self.num_nodes} nodes, "
            f"{num_faults} faults, anomaly rate={labels.mean():.4f}"
        )

        return {
            "telemetry": data,
            "labels": labels,
            "timestamps": timestamps,
            "fault_log": fault_log,
            "metadata": {
                "source": "synthetic",
                "num_nodes": self.num_nodes,
                "feature_dim": self.feature_dim,
                "num_timesteps": T,
                "num_faults": num_faults,
                "anomaly_rate": float(labels.mean()),
            },
        }

    def generate_postflight_data(
        self,
        num_components: int = 13,
        num_flights: int = 5,
        damage_level: str = "nominal",
    ) -> dict:
        """Generate synthetic post-flight telemetry for requalification testing.

        Args:
            num_components: Number of components to assess
            num_flights: Number of prior flights
            damage_level: 'nominal', 'moderate', 'damaged'

        Returns:
            dict with component features, flight history, damage params
        """
        D = 21  # features per component for THERMAL-DIFF-GNN
        features = self.rng.randn(num_components, D).astype(np.float32) * 0.1

        base_cycles = num_flights * 50
        base_radiation = num_flights * 0.5
        base_vibration = num_flights * 0.02

        if damage_level == "moderate":
            features += self.rng.randn(num_components, D).astype(np.float32) * 0.3
            base_cycles *= 2
            base_radiation *= 1.5
        elif damage_level == "damaged":
            # Inject severe damage in some components
            damaged = self.rng.choice(num_components, size=min(3, num_components), replace=False)
            for idx in damaged:
                features[idx] += self.rng.randn(D).astype(np.float32) * 2.0
            base_cycles *= 5
            base_radiation *= 3
            base_vibration = 0.6

        return {
            "component_features": features,
            "num_components": num_components,
            "num_flights": num_flights,
            "damage_level": damage_level,
            "thermal_cycles": base_cycles,
            "delta_T": 150.0 if damage_level != "nominal" else 80.0,
            "radiation_dose_krad": base_radiation,
            "vibration_damage": base_vibration,
        }
