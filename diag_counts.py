import sqlite3
from datetime import datetime

conn = sqlite3.connect('mcdonalds_monitor.db')
conn.row_factory = sqlite3.Row

print(f"Current System Time: {datetime.now()}")
today_str = datetime.now().strftime('%Y-%m-%d')
print(f"Checking for Date >= {today_str}")

res_analyzed = conn.execute("SELECT COUNT(*) FROM articles WHERE analyzed_at >= ?", (today_str,)).fetchone()[0]
print(f"Count (analyzed_at >= {today_str}): {res_analyzed}")

res_collected = conn.execute("SELECT COUNT(*) FROM articles WHERE collected_at >= ?", (today_str,)).fetchone()[0]
print(f"Count (collected_at >= {today_str}): {res_collected}")

log_analyzed = conn.execute("SELECT SUM(total_analyzed) FROM monitor_logs WHERE run_at >= ?", (today_str,)).fetchone()[0]
print(f"Log Sum (total_analyzed today): {log_analyzed}")

conn.close()
