import sqlite3
import config

def check():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT id, sentiment, sentiment_reason, analyzed_at FROM articles WHERE analyzed_at IS NOT NULL LIMIT 20")
    print("=== 分析成功之文章 (最近 20 篇) ===")
    for r in cursor:
        print(f"ID: {r['id']} | 情感: {r['sentiment']} | 理由: {r['sentiment_reason']} | 時間: {r['analyzed_at']}")
    
    # 統計失敗原因
    cursor = conn.execute("SELECT sentiment_reason, COUNT(*) as cnt FROM articles WHERE analyzed_at IS NOT NULL GROUP BY sentiment_reason")
    print("\n=== 分析理由統計 ===")
    for r in cursor:
        print(f"理由: {r['sentiment_reason']} | 數量: {r['cnt']}")
    
    conn.close()

if __name__ == "__main__":
    check()
