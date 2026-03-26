import sqlite3
from datetime import datetime

conn = sqlite3.connect('mcdonalds_monitor.db')
conn.row_factory = sqlite3.Row

today = datetime.now().strftime('%Y-%m-%d')
print(f"Checking for all articles analyzed on {today}...")

rows = conn.execute("SELECT id, title, analyzed_at, sentiment FROM articles WHERE analyzed_at LIKE ?", (f"{today}%",)).fetchall()
print(f"Total articles found starring '{today}': {len(rows)}")

for i, row in enumerate(rows, 1):
    print(f"{i}. [{row['analyzed_at']}] {row['sentiment']} - {row['title'][:30]}")

conn.close()
