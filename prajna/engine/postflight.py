"""PRAJNA — Post-Flight Pipeline: THERMAL-DIFF-GNN + RLV-RUL.

Novel Algorithms #3 and #5:
  - THERMAL-DIFF-GNN: Physics-ML hybrid graph diffusion for damage assessment
  - RLV-RUL: Triple-mode remaining useful life estimator
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ThermalDiffGNN(nn.Module):
    """THERMAL-DIFF-GNN: Graph diffusion network for avionics damage assessment.

    Combines physics-informed thermal diffusion with learned GNN parameters:
      D_i = λ · D_physics(cycles, ΔT) + (1-λ) · D_learned(GNN features)

    Where:
      D_physics: Coffin-Manson fatigue model
      D_learned: GNN-predicted damage from telemetry patterns
    """

    def __init__(
        self,
        input_dim: int = 21,
        hidden_dim: int = 32,
        lambda_physics: float = 0.8,
        num_diffusion_steps: int = 3,
    ):
        super().__init__()
        self.lambda_physics = lambda_physics
        self.num_diffusion_steps = num_diffusion_steps

        # Learned GNN component
        self.node_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        self.diffusion_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim) for _ in range(num_diffusion_steps)
        ])

        self.damage_head = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),  # damage ∈ [0, 1]
        )

    def coffin_manson(
        self,
        num_cycles: int,
        delta_T: float,
        epsilon_f: float = 0.325,
        c_cm: float = -0.442,
        E: float = 117e9,
        alpha: float = 17.3e-6,
    ) -> float:
        """Coffin-Manson thermal fatigue model.

        N_f = (ε_f / (α · ΔT / (2(1+ν)·E)))^(1/c)

        Args:
            num_cycles: Thermal cycles experienced
            delta_T: Temperature swing (°C)
            epsilon_f: Fatigue ductility coefficient
            c_cm: Fatigue ductility exponent
            E: Young's modulus (Pa)
            alpha: CTE (1/K)

        Returns:
            Fatigue damage ratio D ∈ [0, 1]
        """
        if delta_T < 1 or num_cycles < 1:
            return 0.0

        strain = alpha * delta_T / 2
        if strain < 1e-10:
            return 0.0

        N_f = max(1, (epsilon_f / strain) ** (1 / abs(c_cm)))
        damage_ratio = min(1.0, num_cycles / N_f)
        return float(damage_ratio)

    def forward(
        self,
        node_features: torch.Tensor,
        adjacency: torch.Tensor,
        num_cycles: int = 100,
        delta_T: float = 150.0,
    ) -> dict:
        """Compute hybrid damage scores.

        Args:
            node_features: (N, D) sensor features per component
            adjacency: (N, N) component connectivity
            num_cycles: Thermal cycles experienced
            delta_T: Temperature swing

        Returns:
            dict with 'damage_scores', 'decisions', 'physics_damage'
        """
        N = node_features.size(0)

        # Physics component
        D_physics = self.coffin_manson(num_cycles, delta_T)

        # Learned component
        h = self.node_encoder(node_features)

        # Graph diffusion
        A_norm = adjacency / (adjacency.sum(dim=1, keepdim=True) + 1e-8)
        for layer in self.diffusion_layers:
            h = F.relu(layer(h))
            h = torch.mm(A_norm, h)  # diffuse through graph

        D_learned = self.damage_head(h).squeeze(-1)  # (N,)

        # Hybrid combination
        damage_scores = self.lambda_physics * D_physics + (1 - self.lambda_physics) * D_learned

        # Classification decisions
        decisions = []
        for i in range(N):
            d = damage_scores[i].item()
            if d < 0.3:
                decisions.append("GO")
            elif d < 0.7:
                decisions.append("AMBER")
            else:
                decisions.append("REJECT")

        return {
            "damage_scores": damage_scores,
            "decisions": decisions,
            "physics_damage": D_physics,
            "learned_damage": D_learned,
        }


class RLVRUL(nn.Module):
    """RLV-RUL: Triple-mode Remaining Useful Life estimator.

    Combines three damage modes:
      1. Thermal fatigue (Coffin-Manson)
      2. Radiation dose (TID accumulation)
      3. Vibration fatigue (Miner's rule)

    Final RUL = min(RUL_thermal, RUL_radiation, RUL_vibration)
    """

    def __init__(self, input_dim: int = 21, hidden_dim: int = 32):
        super().__init__()

        # Learned RUL predictor (augments physics models)
        self.rul_net = nn.Sequential(
            nn.Linear(input_dim + 3, hidden_dim),  # +3 for physics features
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.ReLU(),  # RUL must be non-negative
        )

    def thermal_rul(
        self,
        cycles_done: int,
        delta_T: float,
        cycles_per_flight: int = 50,
    ) -> float:
        """Estimate remaining flights from thermal fatigue.

        Returns:
            Estimated remaining flights before thermal failure
        """
        diff = ThermalDiffGNN()
        D = diff.coffin_manson(cycles_done, delta_T)
        if D >= 1.0:
            return 0.0
        cycles_remaining = max(0, (1.0 - D) * cycles_done / max(D, 1e-6))
        return cycles_remaining / max(cycles_per_flight, 1)

    def radiation_rul(
        self,
        accumulated_dose_krad: float,
        dose_per_flight_krad: float = 0.5,
        tid_limit_krad: float = 100.0,
    ) -> float:
        """Estimate remaining flights from radiation dose.

        Returns:
            Estimated remaining flights before TID limit
        """
        remaining_dose = max(0, tid_limit_krad - accumulated_dose_krad)
        if dose_per_flight_krad <= 0:
            return float("inf")
        return remaining_dose / dose_per_flight_krad

    def vibration_rul(
        self,
        damage_fraction: float,
        damage_per_flight: float = 0.02,
    ) -> float:
        """Estimate remaining flights from vibration fatigue (Miner's rule).

        D_total = Σ(n_i / N_i) — failure when D_total ≥ 1

        Returns:
            Estimated remaining flights
        """
        remaining = max(0, 1.0 - damage_fraction)
        if damage_per_flight <= 0:
            return float("inf")
        return remaining / damage_per_flight

    def forward(
        self,
        sensor_data: torch.Tensor,
        cycles_done: int = 100,
        delta_T: float = 150.0,
        radiation_dose: float = 10.0,
        vibration_damage: float = 0.2,
    ) -> dict:
        """Predict Remaining Useful Life.

        Args:
            sensor_data: (D,) current sensor readings
            cycles_done: Thermal cycles completed
            delta_T: Temperature swing per cycle
            radiation_dose: Accumulated radiation dose (krad)
            vibration_damage: Accumulated vibration damage fraction

        Returns:
            dict with RUL estimates from each mode and combined
        """
        # Physics-based RUL for each mode
        rul_thermal = self.thermal_rul(cycles_done, delta_T)
        rul_radiation = self.radiation_rul(radiation_dose)
        rul_vibration = self.vibration_rul(vibration_damage)

        # Conservative: take minimum
        rul_combined = min(rul_thermal, rul_radiation, rul_vibration)

        # Learned refinement
        physics_features = torch.tensor(
            [rul_thermal, rul_radiation, rul_vibration],
            dtype=torch.float32,
        )
        combined_input = torch.cat([sensor_data, physics_features])
        rul_learned = self.rul_net(combined_input.unsqueeze(0)).squeeze().item()

        # Blend: 60% physics, 40% learned
        rul_final = 0.6 * rul_combined + 0.4 * rul_learned

        return {
            "rul_thermal": float(rul_thermal),
            "rul_radiation": float(rul_radiation),
            "rul_vibration": float(rul_vibration),
            "rul_combined": float(rul_combined),
            "rul_learned": float(rul_learned),
            "rul_final": float(max(0, rul_final)),
            "limiting_mode": (
                "thermal" if rul_thermal == rul_combined else
                "radiation" if rul_radiation == rul_combined else
                "vibration"
            ),
        }
