# backend/database.py

import sqlite3
import os
from config import DB_PATH


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS traffic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ip TEXT,
            true_label TEXT,
            predicted_class TEXT,
            confidence REAL,
            is_anomaly INTEGER,
            anomaly_score REAL,
            risk_score REAL,
            action TEXT,
            reason TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocklist_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ip TEXT,
            blocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database initialized at {DB_PATH}")


def log_result(
    conn,
    source_ip,
    true_label,
    predicted_class,
    confidence,
    is_anomaly,
    anomaly_score,
    risk_score,
    action,
    reason
):
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO traffic_log
            (
                source_ip,
                true_label,
                predicted_class,
                confidence,
                is_anomaly,
                anomaly_score,
                risk_score,
                action,
                reason
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        source_ip,
        true_label,
        predicted_class,
        confidence,
        int(is_anomaly),
        anomaly_score,
        risk_score,
        action,
        reason
    ))

    if action == "BLOCK":
        cur.execute("""
            INSERT INTO blocklist_log
                (source_ip, reason)
            VALUES (?, ?)
        """, (source_ip, reason))


if __name__ == "__main__":
    init_db()