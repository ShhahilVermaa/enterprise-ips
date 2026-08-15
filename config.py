# config.py
"""
Central place for paths, thresholds, and the finalized class list.
Nothing else in the project should hardcode these values — import from here.
"""

import os

# ── Paths ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw", "MachineLearningCVE")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample")
MODEL_PATH = os.path.join(BASE_DIR, "detection", "models", "model.pkl")
DB_PATH = os.path.join(BASE_DIR, "backend", "ips.db")

# ── Finalized attack classes (from real dataset verification, Aug 2026) ──
# Merged: DoS Hulk/GoldenEye/slowloris/Slowhttptest -> "DoS"
# Merged: FTP-Patator/SSH-Patator -> "BruteForce"
# Dropped (too few samples): Web Attack*, Infiltration, Heartbleed
CLASS_LABELS = ["BENIGN", "DoS", "DDoS", "PortScan", "BruteForce", "Bot"]

# Maps raw dataset label strings -> our merged class names
LABEL_MERGE_MAP = {
    "BENIGN": "BENIGN",
    "DoS Hulk": "DoS",
    "DoS GoldenEye": "DoS",
    "DoS slowloris": "DoS",
    "DoS Slowhttptest": "DoS",
    "DDoS": "DDoS",
    "PortScan": "PortScan",
    "FTP-Patator": "BruteForce",
    "SSH-Patator": "BruteForce",
    "Bot": "Bot",
}
# Any label not in this map (Web Attack*, Infiltration, Heartbleed) gets
# dropped during preprocessing — Member 1 will filter these out in step 1.4.

# ── Detection & prevention thresholds ───────────────────────
MIN_CONFIDENCE_TO_ACT = 0.70   # below this, treat prediction as unreliable -> ALLOW
RISK_BLOCK_THRESHOLD = 0.75    # risk_score >= this -> BLOCK
BLOCKLIST_EXPIRY_MINUTES = 60  # auto-unblock after this long

# ── Detection model paths ──────────────────────────────
ANOMALY_MODEL_PATH = os.path.join(BASE_DIR, "detection", "models", "anomaly_model.pkl")


# ── Attack severity weights (used by Member 3's risk scoring) ──
ATTACK_SEVERITY_WEIGHTS = {
    "BENIGN": 0.0,
    "PortScan": 0.5,
    "Bot": 0.7,
    "BruteForce": 0.8,
    "DoS": 0.9,
    "DDoS": 1.0,
}