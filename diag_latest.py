import sqlite3
import config

def check_latest():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, published_at, analyzed_at FROM articles ORDER BY analyzed_at DESC LIMIT 20")
    rows = cursor.fetchall()
    
    print(f"{'ID':<6} | {'Published':<25} | {'Analyzed':<20} | Title")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<6} | {str(row[2]):<25} | {str(row[3])[:19]:<20} | {row[1]}")
    conn.close()

if __name__ == "__main__":
    check_latest()
