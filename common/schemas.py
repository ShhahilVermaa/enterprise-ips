# common/schemas.py

from dataclasses import dataclass
from typing import Dict


@dataclass
class TrafficFeatures:
    """One cleaned traffic record, produced by preprocessing (Member 1)."""
    source_ip: str
    features: Dict[str, float]
    true_label: str = ""


@dataclass
class PredictionResult:
    """Output of the ML detection layer (Member 2)."""
    predicted_class: str    # from XGBoost classifier
    confidence: float       # 0.0 - 1.0
    is_anomaly: bool = False    # from Isolation Forest
    anomaly_score: float = 0.0  # lower = more anomalous


@dataclass
class Decision:
    """Output of threat scoring + prevention logic (Member 3)."""
    risk_score: float
    action: str
    reason: str