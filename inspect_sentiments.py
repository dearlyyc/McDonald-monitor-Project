import sqlite3
from datetime import datetime

conn = sqlite3.connect('mcdonalds_monitor.db')
conn.row_factory = sqlite3.Row

today = datetime.now().strftime('%Y-%m-%d')
print(f"Checking for {today}...")

rows = conn.execute("SELECT sentiment, COUNT(*) as count FROM articles WHERE analyzed_at >= ? GROUP BY sentiment", (today,)).fetchall()
for row in rows:
    print(f"Sentiment: '{row['sentiment']}' -> Count: {row['count']}")

conn.close()
