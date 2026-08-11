# common/schemas.py
"""
Shared data structures passed between modules.
Member 1 -> Member 2 : TrafficFeatures
Member 2 -> Member 3 : PredictionResult
Member 3 -> Member 4 : Decision
These are plain in-memory objects -- no module writes to the database
except Member 4's orchestrator.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TrafficFeatures:
    """One cleaned traffic record, produced by preprocessing (Member 1)."""
    source_ip: str
    features: Dict[str, float]   # feature_name -> numeric value
    true_label: str = ""         # only present for training/eval data, not live traffic


@dataclass
class PredictionResult:
    """Output of the ML model (Member 2)."""
    predicted_class: str   # one of config.CLASS_LABELS
    confidence: float      # 0.0 - 1.0


@dataclass
class Decision:
    """Output of threat scoring + prevention logic (Member 3)."""
    risk_score: float
    action: str             # "ALLOW" or "BLOCK"
    reason: str