"""PRAJNA — Engine module package init.

Uses lazy imports to avoid hard dependency on torch-geometric
for modules that don't need it (demo, SDWAP, SHAKTI, KAVACH).
"""

from .sdwap import SDWAP
from .local_detector import LocalDetector
from .shakti import SHAKTI
from .kavach import KAVACH
from .nlg import NLGEngine
from .clpx import CLPX

# Lazy imports for modules that need torch-geometric
def get_tgn():
    from .tgn import TGNEncoder, FailurePredictor, FocalLoss
    return TGNEncoder, FailurePredictor, FocalLoss

def get_aegis():
    from .aegis import AEGIS
    return AEGIS

def get_phyrag():
    from .phyrag import PhyRAG
    return PhyRAG

def get_postflight():
    from .postflight import ThermalDiffGNN, RLVRUL
    return ThermalDiffGNN, RLVRUL

__all__ = [
    "SDWAP",
    "LocalDetector",
    "SHAKTI",
    "KAVACH",
    "NLGEngine",
    "CLPX",
    "get_tgn",
    "get_aegis",
    "get_phyrag",
    "get_postflight",
]
