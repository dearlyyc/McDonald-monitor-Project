import sqlite3
import config

def check_run():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # 查找 03/21 06:32 左右搜集到的文章
    cursor = conn.execute("""
        SELECT id, title, analyzed_at, sentiment_reason 
        FROM articles 
        WHERE collected_at >= '2026-03-21T06:32:00' 
          AND collected_at <= '2026-03-21T06:34:00'
    """)
    rows = cursor.fetchall()
    print(f"=== 06:32 搜集到的 {len(rows)} 篇文章之現況 ===")
    for r in rows:
        print(f"ID: {r['id']} | 標題: {r['title'][:30]}... | 分析時間: {r['analyzed_at']} | 理由: {r['sentiment_reason']}")
    
    conn.close()

if __name__ == "__main__":
    check_run()
