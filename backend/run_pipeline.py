# backend/run_pipeline.py

import time
import os
import pandas as pd

from config import SAMPLE_DIR
from common.schemas import TrafficFeatures
from detection.predict import predict
from prevention.risk_scorer import score_and_decide
from prevention.blocklist_manager import reset_blocklist
from backend.database import init_db, log_result, get_connection
from preprocessing.replay_simulator import replay

LABEL_COLUMN = "Label"
IP_COLUMN = "Source IP"


def run(data_path: str = None):
    """
    Fast batch pipeline.

    Processes all records from the CSV as quickly as possible.
    Used for evaluation and performance testing.
    """

    if data_path is None:
        data_path = os.path.join(SAMPLE_DIR, "sample.csv")

    print("Initializing database...")
    init_db()
    reset_blocklist()

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Processing {len(df):,} records...")

    # One SQLite connection for the entire batch run
    conn = get_connection()

    blocked_count = 0
    allowed_count = 0
    anomaly_count = 0

    start_time = time.time()

    try:
        for i, (_, row) in enumerate(df.iterrows()):

            features = row.drop(
                labels=[LABEL_COLUMN, IP_COLUMN]
            ).to_dict()

            traffic = TrafficFeatures(
                source_ip=row[IP_COLUMN],
                features=features,
                true_label=row[LABEL_COLUMN],
            )

            prediction = predict(traffic)

            decision = score_and_decide(
                prediction,
                traffic.source_ip
            )

            log_result(
                conn,
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

            # Commit every 5,000 records
            if (i + 1) % 5000 == 0:
                conn.commit()
                print(f"  ...{i + 1:,} processed")

        # Commit remaining records
        conn.commit()

    finally:
        conn.close()

    elapsed = time.time() - start_time
    throughput = len(df) / elapsed if elapsed > 0 else 0

    print(f"\nDone in {elapsed:.2f}s")
    print(f"Throughput: {throughput:.1f} records/sec")
    print(
        f"Allowed: {allowed_count:,} | "
        f"Blocked: {blocked_count:,}"
    )
    print(
        f"Flagged anomalous: {anomaly_count:,} "
        f"({anomaly_count / len(df):.1%})"
    )


def run_live(
    data_path: str,
    delay_seconds: float = 0.1,
    max_records: int = None
):
    """
    Live/demo pipeline.

    Traffic is replayed one record at a time with a configurable
    delay between records. Each decision is immediately committed
    to SQLite so that a future dashboard can observe the changes
    in real time.
    """

    print("Initializing database...")
    init_db()
    reset_blocklist()

    print("Starting live traffic replay...")

    conn = get_connection()

    blocked_count = 0
    allowed_count = 0
    anomaly_count = 0
    processed = 0

    start_time = time.time()

    try:
        for row in replay(
            data_path,
            delay_seconds=delay_seconds,
            shuffle=True,
            max_records=max_records
        ):
            features = row.drop(
                labels=[LABEL_COLUMN, IP_COLUMN]
            ).to_dict()

            traffic = TrafficFeatures(
                source_ip=row[IP_COLUMN],
                features=features,
                true_label=row[LABEL_COLUMN],
            )

            prediction = predict(traffic)

            decision = score_and_decide(
                prediction,
                traffic.source_ip
            )

            log_result(
                conn,
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

            # Commit immediately in live mode so the database
            # always contains the latest processed record.
            conn.commit()

            processed += 1

            if decision.action == "BLOCK":
                blocked_count += 1

                print(
                    f"  🚫 BLOCKED | "
                    f"IP={traffic.source_ip} | "
                    f"Class={prediction.predicted_class} | "
                    f"Risk={decision.risk_score:.2f}"
                )

            else:
                allowed_count += 1

                print(
                    f"  ✅ ALLOWED | "
                    f"IP={traffic.source_ip} | "
                    f"Class={prediction.predicted_class} | "
                    f"Risk={decision.risk_score:.2f}"
                )

            if prediction.is_anomaly:
                anomaly_count += 1

    finally:
        conn.commit()
        conn.close()

    elapsed = time.time() - start_time

    print("\nLive demo finished.")
    print(f"Processed: {processed:,}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Allowed: {allowed_count:,}")
    print(f"Blocked: {blocked_count:,}")
    print(f"Anomalous: {anomaly_count:,}")


if __name__ == "__main__":
    # Default mode remains the fast batch pipeline.
    run()