import sqlite3
from datetime import datetime

def count():
    conn = sqlite3.connect('mcdonalds_monitor.db')
    today = datetime.now().strftime('%Y-%m-%d')
    # Check monitor_logs for today as well
    logs_count = conn.execute("SELECT COUNT(*) FROM monitor_logs WHERE run_at LIKE ?", (f"{today}%",)).fetchone()[0]
    articles_count = conn.execute("SELECT COUNT(*) FROM articles WHERE analyzed_at LIKE ?", (f"{today}%",)).fetchone()[0]
    print(f"[{datetime.now().isoformat()}]")
    print(f"Analyzed articles today: {articles_count}")
    print(f"Monitor logs today: {logs_count}")
    conn.close()

if __name__ == "__main__":
    count()
