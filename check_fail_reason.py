import sqlite3
import config

def check_fail():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT id, source, title, sentiment_reason FROM articles WHERE analyzed_at IS NULL ORDER BY collected_at DESC LIMIT 10")
    print("=== 最近 10 篇未分析文章之失敗原因 ===")
    for r in cursor:
        print(f"ID: {r['id']} | 來源: {r['source']:15} | 標題: {r['title'][:30]}... | 理由: {r['sentiment_reason']}")
    conn.close()

if __name__ == "__main__":
    check_fail()
