# backend/export_dashboard_data.py
"""
Exports current traffic_log/blocklist_log state from SQLite into a
JSON file the dashboard (dashboard/index.html) can load directly in
the browser -- no backend server needed for Phase 1.
"""

import sqlite3
import json
import os
from config import DB_PATH

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard", "data.json")


def export_dashboard_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM traffic_log").fetchone()[0]

    action_counts = dict(cur.execute(
        "SELECT action, COUNT(*) FROM traffic_log GROUP BY action"
    ).fetchall())

    class_breakdown = cur.execute(
        "SELECT true_label, action, COUNT(*) FROM traffic_log GROUP BY true_label, action"
    ).fetchall()

    anomaly_count = cur.execute(
        "SELECT COUNT(*) FROM traffic_log WHERE is_anomaly = 1"
    ).fetchone()[0]

    blocked_ips = cur.execute(
        "SELECT DISTINCT source_ip, reason, blocked_at FROM blocklist_log ORDER BY blocked_at DESC LIMIT 20"
    ).fetchall()

    recent_alerts = cur.execute(
        "SELECT source_ip, true_label, predicted_class, risk_score, action, reason, timestamp "
        "FROM traffic_log WHERE action = 'BLOCK' ORDER BY id DESC LIMIT 20"
    ).fetchall()

    conn.close()

    # Build class_breakdown into a nested dict: {class: {ALLOW: n, BLOCK: n}}
    breakdown_dict = {}
    for label, action, count in class_breakdown:
        breakdown_dict.setdefault(label, {"ALLOW": 0, "BLOCK": 0})
        breakdown_dict[label][action] = count

    data = {
        "total_processed": total,
        "allowed": action_counts.get("ALLOW", 0),
        "blocked": action_counts.get("BLOCK", 0),
        "anomalous": anomaly_count,
        "class_breakdown": breakdown_dict,
        "blocked_ips": [
            {"ip": ip, "reason": reason, "blocked_at": blocked_at}
            for ip, reason, blocked_at in blocked_ips
        ],
        "recent_alerts": [
            {
                "source_ip": ip, "true_label": true_label, "predicted_class": pred,
                "risk_score": risk, "action": action, "reason": reason, "timestamp": ts
            }
            for ip, true_label, pred, risk, action, reason, ts in recent_alerts
        ],
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Exported dashboard data to {OUTPUT_PATH}")
    print(f"Total: {total:,} | Allowed: {data['allowed']:,} | Blocked: {data['blocked']:,}")


if __name__ == "__main__":
    export_dashboard_data()