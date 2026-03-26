import sqlite3
from datetime import datetime

conn = sqlite3.connect('mcdonalds_monitor.db')
conn.row_factory = sqlite3.Row

today_str = datetime.now().strftime('%Y-%m-%d')
print(f"Today string: {today_str}")

# Check articles analyzed today
rows = conn.execute("SELECT id, title, analyzed_at, sentiment FROM articles WHERE analyzed_at >= ?", (today_str,)).fetchall()
print(f"Found {len(rows)} articles analyzed today.")

# Group by run (approx)
runs = {}
for row in rows:
    # Use hour/minute as run proxy
    run_key = row["analyzed_at"][:16] # YYYY-MM-DDTHH:MM
    if run_key not in runs:
        runs[run_key] = 0
    runs[run_key] += 1

print("Distribution by minute:")
for k, v in sorted(runs.items()):
    print(f"  {k}: {v} articles")

# Check logs
log_rows = conn.execute("SELECT run_at, total_analyzed FROM monitor_logs WHERE run_at >= ?", (today_str,)).fetchall()
print("\nLogs today:")
for log in log_rows:
    print(f"  {log['run_at']}: {log['total_analyzed']} analyzed")

conn.close()
