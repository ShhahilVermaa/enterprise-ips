# backend/run_pipeline.py

import time
import os
import pandas as pd

from config import SAMPLE_DIR
from common.schemas import TrafficFeatures
from detection.predict import predict
from prevention.risk_scorer import score_and_decide
from prevention.blocklist_manager import reset_blocklist
from backend.database import init_db, log_result

LABEL_COLUMN = "Label"
IP_COLUMN = "Source IP"


def run(data_path: str = None):
    if data_path is None:
        data_path = os.path.join(SAMPLE_DIR, "sample.csv")

    print("Initializing database...")
    init_db()
    reset_blocklist()

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Processing {len(df):,} records...")

    blocked_count = 0
    allowed_count = 0
    anomaly_count = 0

    start_time = time.time()

    for _, row in df.iterrows():
        features = row.drop(labels=[LABEL_COLUMN, IP_COLUMN]).to_dict()
        traffic = TrafficFeatures(
            source_ip=row[IP_COLUMN],
            features=features,
            true_label=row[LABEL_COLUMN],
        )

        prediction = predict(traffic)
        decision = score_and_decide(prediction, traffic.source_ip)

        log_result(
            source_ip=traffic.source_ip,
            true_label=traffic.true_label,
            predicted_class=prediction.predicted_class,
            confidence=prediction.confidence,
            is_anomaly=prediction.is_anomaly,
            anomaly_score=prediction.anomaly_score,
            risk_score=decision.risk_score,
            action=decision.action,
            reason=decision.reason,
        )

        if decision.action == "BLOCK":
            blocked_count += 1
        else:
            allowed_count += 1

        if prediction.is_anomaly:
            anomaly_count += 1

    elapsed = time.time() - start_time
    throughput = len(df) / elapsed if elapsed > 0 else 0

    print(f"\nDone in {elapsed:.2f}s")
    print(f"Throughput: {throughput:.1f} records/sec")
    print(f"Allowed: {allowed_count:,} | Blocked: {blocked_count:,}")
    print(f"Flagged anomalous: {anomaly_count:,} ({anomaly_count/len(df):.1%})")


if __name__ == "__main__":
    run()