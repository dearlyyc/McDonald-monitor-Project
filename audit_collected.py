import sqlite3
import config

def check_collected_at():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, collected_at, analyzed_at FROM articles WHERE id = 4145")
    r = cursor.fetchone()
    if r:
        print(f"ID: {r['id']} | Title: {r['title']}")
        print(f"Collected at: {r['collected_at']} (Today should be 2026-03-28)")
        print(f"Analyzed at: {r['analyzed_at']}")
    else:
        print("找不到 ID 4145")
        
    conn.close()

if __name__ == "__main__":
    check_collected_at()
