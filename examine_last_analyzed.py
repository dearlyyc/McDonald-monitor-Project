import sqlite3

conn = sqlite3.connect('mcdonalds_monitor.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, title, analyzed_at, sentiment FROM articles WHERE analyzed_at IS NOT NULL ORDER BY analyzed_at DESC LIMIT 30").fetchall()
for i, row in enumerate(rows, 1):
    print(f"{i}. [{row['analyzed_at']}] {row['sentiment']} - {row['title'][:30]}")

conn.close()
