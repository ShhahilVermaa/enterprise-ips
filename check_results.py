# check_results.py
import sqlite3

conn = sqlite3.connect('backend/ips.db')

print("=== Why BENIGN rows got blocked ===")
rows = conn.execute("""
    SELECT reason, COUNT(*) 
    FROM traffic_log 
    WHERE true_label='BENIGN' AND action='BLOCK' 
    GROUP BY reason 
    ORDER BY COUNT(*) DESC 
    LIMIT 10
""").fetchall()
for reason, count in rows:
    print(f"  {count:>6}  {reason}")

print("\n=== Why PortScan rows got allowed ===")
rows = conn.execute("""
    SELECT reason, COUNT(*) 
    FROM traffic_log 
    WHERE true_label='PortScan' AND action='ALLOW' 
    GROUP BY reason 
    ORDER BY COUNT(*) DESC 
    LIMIT 10
""").fetchall()
for reason, count in rows:
    print(f"  {count:>6}  {reason}")

conn.close()