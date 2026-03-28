import sqlite3
import config
import json

def inspect():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, published_at, raw_data FROM articles WHERE title LIKE ?", ('%小熊大鬍子%',))
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Published_at from DB: {row[2]}")
        try:
            raw = json.loads(row[3])
            print(f"Original Source: {raw.get('original_source')}")
        except:
            pass
    conn.close()

if __name__ == "__main__":
    inspect()
