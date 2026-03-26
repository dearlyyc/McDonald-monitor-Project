import sqlite3
from datetime import datetime

conn = sqlite3.connect('mcdonalds_monitor.db')
conn.row_factory = sqlite3.Row

# Get today by various methods
today = datetime.now().strftime('%Y-%m-%d')
print(f"Current System Date: {today}")

# Method 1 & 2
res1 = conn.execute("SELECT COUNT(*) FROM articles WHERE analyzed_at >= ?", (today,)).fetchone()[0]
print(f"Count (analyzed_at >= {today}): {res1}")

# Method 4: Check logs
total_log = 0
rows = conn.execute("SELECT total_analyzed, run_at FROM monitor_logs WHERE run_at LIKE ?", (f"{today}%",)).fetchall()
for l in rows:
    print(f"  Log Run at {l['run_at']} -> {l['total_analyzed']} analyzed")
    total_log += l['total_analyzed']
print(f"Total Log Sum: {total_log}")

conn.close()
